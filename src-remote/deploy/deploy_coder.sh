vllm serve models/Qwen2_5-Coder-32B-Instruct_app-bench_train_batch13_filtered_decontaminated_new \
    --dtype auto \
    --host 0.0.0.0 \
    --port 8000 \
    --pipeline-parallel-size 1 \
    --tensor-parallel-size 4 \
    --cpu-offload-gb 0 \