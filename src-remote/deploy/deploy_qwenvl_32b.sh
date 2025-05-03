vllm serve models/Qwen2.5-VL-32B-Instruct \
    --port 8000 \
    --host 0.0.0.0 \
    --dtype bfloat16 \
    --limit-mm-per-prompt image=5,video=5 \
    --gpu_memory_utilization 0.8 \
    --pipeline-parallel-size 1 \
    --tensor-parallel-size 4 \