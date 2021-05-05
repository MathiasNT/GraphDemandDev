"""The trainer clases
"""
import time
import os
import numpy as np
import pandas as pd
from tqdm import tqdm


import torch
from torch import optim
from torch.autograd import Variable
from torch.utils.tensorboard import SummaryWriter
from torch.profiler import tensorboard_trace_handler
import torch.nn.functional as F

from ..utils.data_utils import create_test_train_split_max_min_normalize
from ..utils import encode_onehot
from ..utils import test_lstm, train_lstm
from ..utils.losses import torch_nll_gaussian, kl_categorical, cyc_anneal
from ..models import SimpleLSTM


class SimpleLSTMTrainer:
    """The trainer class"""

    def __init__(
        self,
        batch_size=25,
        n_epochs=100,
        dropout_p=0,
        shuffle_train=True,
        shuffle_test=False,
        experiment_name="test",
        normalize=True,
        train_frac=0.8,
        burn_in_steps=30,
        split_len=40,
        burn_in=True,  # maybe remove this
        lstm_hid=128,
        lstm_dropout=0,
    ):

        # Training settings
        self.batch_size = batch_size
        self.n_epochs = n_epochs
        self.dropout_p = dropout_p
        self.shuffle_train = shuffle_train
        self.shuffle_test = shuffle_test

        # Saving settings

        # Set up results folder
        self.experiment_name = experiment_name
        self.experiment_folder_path = f"../models/{self.experiment_name}"
        next_version = 2
        while os.path.exists(self.experiment_folder_path):
            new_experiment_name = f"{self.experiment_name}_v{next_version}"
            self.experiment_folder_path = f"../models/{new_experiment_name}"
            next_version += 1
        os.mkdir(self.experiment_folder_path)
        print(f"Created {self.experiment_folder_path}")

        # Setup logger
        self.experiment_log_path = f"{self.experiment_folder_path}/runs"
        self.writer = SummaryWriter(log_dir=self.experiment_log_path)
        print(f"Logging at {self.experiment_log_path}")

        # Data settings
        self.normalize = normalize
        self.train_frac = train_frac

        # Model settings
        self.burn_in_steps = burn_in_steps
        self.split_len = split_len
        self.pred_steps = self.split_len - self.burn_in_steps
        self.encoder_steps = self.split_len
        assert self.burn_in_steps + self.pred_steps == self.split_len

        self.burn_in = burn_in
        self.lstm_dropout = lstm_dropout

        # Net sizes
        self.n_in = 1  # TODO update this hardcode
        self.lstm_hid = lstm_hid

        self.model_settings = {
            "batch_size": self.batch_size,
            "n_epochs": self.n_epochs,
            "dropout_p": self.dropout_p,
            "shuffle_train": self.shuffle_train,
            "shuffle_test": self.shuffle_test,
            "experiment_name": self.experiment_name,
            "normalize": self.normalize,
            "train_frac": self.train_frac,
            "burn_in_steps": self.burn_in_steps,
            "split_len": self.split_len,
            "burn_in": self.burn_in,  # maybe remove this
            "lstm_hid": self.lstm_hid,
            "lstm_dropout": self.lstm_dropout,
        }

        (
            self.train_dataloader,
            self.test_dataloader,
            self.train_max,
            self.train_min,
            self.test_dates,
            self.train_dates,
        ) = self._load_data()

        self._init_model()

    def _load_data(self):
        dataset_folder = "../datafolder"
        proc_folder = f"{dataset_folder}/procdata"

        # Load data
        pickup_data_path = f"{proc_folder}/full_year_manhattan_vector_pickup.npy"
        pickup_data = np.load(pickup_data_path)
        dropoff_data_path = f"{proc_folder}/full_year_manhattan_vector_dropoff.npy"
        dropoff_data = np.load(dropoff_data_path)
        weather_data_path = f"{proc_folder}/LGA_weather_full_2019.csv"
        weather_df = pd.read_csv(weather_data_path, parse_dates=[0, 7])

        # temp fix for na temp
        weather_df.loc[weather_df.temperature.isna(), "temperature"] = 0
        sum(weather_df.temperature.isna())

        # Create weather vector
        weather_vector = weather_df.loc[:, ("temperature", "precipDepth")].values

        # Create data tensor
        pickup_tensor = torch.Tensor(pickup_data)
        dropoff_tensor = torch.Tensor(dropoff_data)
        weather_tensor = torch.Tensor(weather_vector)

        # Stack data tensor
        data_tensor = torch.cat([pickup_tensor, dropoff_tensor], dim=0)

        # Create data loader with max min normalization
        (
            train_dataloader,
            test_dataloader,
            train_max,
            train_min,
        ) = create_test_train_split_max_min_normalize(
            data=data_tensor,
            weather_data=weather_tensor,
            split_len=self.split_len,
            batch_size=self.batch_size,
            normalize=self.normalize,
            train_frac=self.train_frac,
        )

        min_date = pd.Timestamp(year=2019, month=1, day=1)
        max_date = pd.Timestamp(year=2019 + 1, month=1, day=1)

        # Note that this misses a bit from the beginning but this will not be a big problem when we index finer
        bins_dt = pd.date_range(start=min_date, end=max_date, freq="1H")
        split_bins_dt = bins_dt[: -(self.split_len + 1)]

        test_dates = split_bins_dt[int(self.train_frac * len(split_bins_dt)) :]
        train_dates = split_bins_dt[: int(self.train_frac * len(split_bins_dt))]

        print(f"train_dates len: {len(train_dates)}")
        print(f"test_dates len: {len(test_dates)}")

        return (
            train_dataloader,
            test_dataloader,
            train_max,
            train_min,
            test_dates,
            train_dates,
        )

    def _init_model(self):
        self.model = SimpleLSTM(
            input_dims=self.n_in, hidden_dims=self.lstm_hid, dropout=self.lstm_dropout
        ).cuda()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

    def train(self):
        print("Starting training")
        train_mse_arr = []

        test_mse_arr = []

        for i in tqdm(range(self.n_epochs)):
            t = time.time()

            train_mse = train_lstm(
                model=self.model,
                train_dataloader=self.train_dataloader,
                optimizer=self.optimizer,
                burn_in=self.burn_in,
                burn_in_steps=self.burn_in_steps,
                split_len=self.split_len,
            )
            self.writer.add_scalar("Train_MSE", train_mse, i)

            if i % 10 == 0:
                test_mse = test_lstm(
                    model=self.model,
                    test_dataloader=self.test_dataloader,
                    optimizer=self.optimizer,
                    burn_in=self.burn_in,
                    burn_in_steps=self.burn_in_steps,
                    split_len=self.split_len,
                )
                self.writer.add_scalar("Test_MSE", test_mse, i)

                test_mse_arr.append(test_mse)
            train_mse_arr.append(train_mse)
            self.train_dict = {
                "test": {"mse": test_mse_arr},
                "train": {"mse": train_mse_arr},
            }

    def save_model(self):
        model_path = f"{self.experiment_folder_path}/model_dict.pth"

        model_dict = {
            "model": self.model.state_dict(),
            "settings": self.model_settings,
            "train_res": self.train_dict,
        }

        torch.save(model_dict, model_path)
        print(f"Model saved at {model_path}")