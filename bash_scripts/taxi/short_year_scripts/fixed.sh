##
# Script for running fixed encoder model on the NYC Yellow Taxi dataset. Note that prior is selected beneath
##

EXP_NAME=final_models/taxi/short/
mkdir -p "../models/${EXP_NAME}"

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

NORMALIZATION=ha

PICKUP_DATA_PATH=taxi_data/full_manhattan/short_year_full_manhattan_2d.npy
WEATHER_DATA_PATH=taxi_data/mean_airport_weather_2019.csv


#PRIOR=loc
#PRIOR_ADJ_PATH=taxi_data/full_manhattan/full_year_full_manhattan_local_adj.npy

#PRIOR=dtw
#PRIOR_ADJ_PATH=taxi_data/full_manhattan/short_year_train_full_manhattan_dtw_adj_bin.npy

#PRIOR=full
#PRIOR_ADJ_PATH=taxi_data/full_manhattan/full_adj.npy

PRIOR=empty
PRIOR_ADJ_PATH=taxi_data/full_manhattan/empty_adj.npy



ENC_N_HID=128
DEC_N_HID=32
DEC_MSG_HID=32
DEC_GRU_HID=32

SEED=42


python3 NRI_OD_train.py  --experiment_name ${EXP_NAME}/fixed_${PRIOR}_${NORMALIZATION}_enc${ENC_N_HID}_s${SEED} \
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
			
