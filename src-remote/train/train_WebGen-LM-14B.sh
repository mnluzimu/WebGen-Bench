DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export NCCL_DEBUG=WARN
export NCCL_SOCKET_IFNAME=eth0

export NCCL_IB_TIMEOUT=22   
export NCCL_IB_RETRY_CNT=13 
export NCCL_IB_AR_THRESHOLD=0

wandb login ""

model_name=Qwen2_5-Coder-14B-Instruct_app-bench_train_batch13_filtered_decontaminated_new

OMP_NUM_THREADS=1 torchrun --nnodes $WORLD_SIZE --node_rank $RANK --master_addr $MASTER_ADDR --master_port $MASTER_PORT --nproc_per_node 8 $DIR/train.py \
--ddp_timeout 3600 \
--processor qwen_agent \
--model_cfg models/Qwen2.5-Coder-14B-Instruct \
--train_file data/train_data/messages_generate_600.jsonl,data/train_data/messages_select_600.jsonl \
--output_dir models/$model_name \
--logging_dir models/$model_name \
--remove_unused_columns False \
--dataloader_num_workers 16 \
--max_len 16384 \
--max_steps -1 \
--num_train_epochs 2 \
--save_strategy "epoch" \
--warmup_ratio 0.1 \
--logging_steps 1 \
--learning_rate 4e-5 \
--lr_scheduler_type cosine \
--per_device_train_batch_size 1 \
--gradient_accumulation_steps 2 \
--seed 3407 \
--deepspeed src-remote/train/config/deepspeed.json \
--bf16 \
--do_train \
--save_safetensors \
--gradient_checkpointing \
--report_to wandb \
--run_name $model_name \
--save_total_limit 3 \
--save_only_model