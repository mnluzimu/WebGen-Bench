:loop
python src/automatic_bolt_diy/eval_bolt_diy.py ^
    --jsonl_path data/test.jsonl ^
    --url http://localhost:5173/ ^
    --provider OpenRouter ^
    --desired_model deepseek/deepseek-chat-v3-0324:free
timeout /t 30
goto loop