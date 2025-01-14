#!/bin/sh
#BSUB -J fixed_full_z
#BSUB -q gpuv100
#BSUB -gpu "num=1:mode=exclusive_process"
#BSUB -n 4
#BSUB -W 24:00
#BSUB -R "span[hosts=1]"
#BSUB -R "rusage[mem=40GB]"
#BSUB -R "select[gpu32gb]"
#BSUB -N
#BSUB -o ../logs/mlp_taxi/%J_fixed.out
#BSUB -e ../logs/mlp_taxi/%J_fixed.err

EXP_NAME=final_models/taxi/short/
mkdir "../models/${EXP_NAME}"

ENCODER_TYPE=fixed
LOSS_TYPE=nll

EPOCHS=1000
KL_CYC=50
CUDA_DEVICE=0
BATCH_SIZE=128
BURN_IN_STEPS=48
SPLIT_LEN=60
PRED_STEPS=12
EDGE_RATE=0.1
GUMBEL_TAU=0.5
LR=0.0005
NLL_VARIANCE=0.0005
WEIGHT_DECAY=0.05

NORMALIZATION=z

PICKUP_DATA_PATH=taxi_data/full_manhattan/short_year_full_manhattan_2d.npy
WEATHER_DATA_PATH=taxi_data/mean_airport_weather_2019.csv


#PRIOR=loc
#PRIOR_ADJ_PATH=taxi_data/full_manhattan/full_year_full_manhattan_local_adj.npy
#CHECK_POINT_PATH=../models/final_models/taxi/fixed/fixed_loc_z_enc128_s42/checkpoint_model_dict.pth

#PRIOR=dtw
#PRIOR_ADJ_PATH=taxi_data/full_manhattan/short_year_train_full_manhattan_dtw_adj_bin.npy
#CHECK_POINT_PATH=../models/final_models/taxi/fixed/fixed_dtw_z_enc128_s42/checkpoint_model_dict.pth

#PRIOR=full
#PRIOR_ADJ_PATH=taxi_data/full_manhattan/full_adj.npy
#CHECK_POINT_PATH=../models/final_models/taxi/fixed/fixed_full_z_enc128_s42/checkpoint_model_dict.pth

PRIOR=empty
PRIOR_ADJ_PATH=taxi_data/full_manhattan/empty_adj.npy
CHECK_POINT_PATH=../models/final_models/taxi/fixed/fixed_empty_z_enc128_s42/checkpoint_model_dict.pth


ENC_N_HID=128
DEC_N_HID=32
DEC_MSG_HID=32
DEC_GRU_HID=32

SEED=42


python3 NRI_OD_train.py  --experiment_name ${EXP_NAME}/checkpoint_fixed_${PRIOR}_${NORMALIZATION}_enc${ENC_N_HID}_s${SEED} \
                        --epochs ${EPOCHS} \
                        --encoder_type ${ENCODER_TYPE} \
                        --loss_type ${LOSS_TYPE} \
                        --cuda_device ${CUDA_DEVICE} \
                        --pickup_data_name  ${PICKUP_DATA_PATH}\
                        --weather_data_name ${WEATHER_DATA_PATH} \
			--use_weather \
                        --batch_size ${BATCH_SIZE} \
                        --burn_in_steps ${BURN_IN_STEPS} \
                        --split_len ${SPLIT_LEN} \
			--pred_steps ${PRED_STEPS} \
                        --edge_rate ${EDGE_RATE} \
                        --enc_n_hid ${ENC_N_HID} \
			--dec_n_hid ${DEC_N_HID} \
			--dec_msg_hid ${DEC_MSG_HID} \
			--dec_gru_hid ${DEC_GRU_HID} \
			--gumbel_tau ${GUMBEL_TAU} \
			--weight_decay ${WEIGHT_DECAY} \
			--nll_variance ${NLL_VARIANCE} \
			--lr ${LR} \
			--kl_cyc ${KL_CYC} \
			--gumbel_hard \
			--use_seed ${SEED} \
			--normalize ${NORMALIZATION} \
			--fixed_adj_matrix_path ${PRIOR_ADJ_PATH} \
			--checkpoint_path ${CHECK_POINT_PATH} \
			
