# WebGen-Bench

(The code under `src` was executed on a Windows 11 system. It should also run on Linux with minor adjustments. The code under `src-remote` was executed on a Linux server. This README often uses `deepseek/deepseek-chat-v3-0324:free` as an example. You can replace it with other files.)

The experiment outputs are placed under `outputs.zip`. It includes the output of the LLM-based agents that were tested in the paper. 

If you wish to deploy Qwen2.5-VL-32B-Instruct yourself for UI agent testing, or you wish to reproduce the training of WebGen-LM, you can download the necessary models using `src-remote\download\download.py`.

## Testing Proprietary and Open-Source Models

### Installation

First, install Node.js following [Node.js Download Page](https://nodejs.org/en/download/).

Then, install pm2:
```batch
npm install -g pm2
```

To install WebVoyager:

```shell
conda create -p env\webvoyager python=3.10 -y
conda activate env\webvoyager
cd webvoyager
pip install -r requirements.txt
pip install numpy
# we encoungered a minor conflict, which we patched up by commenting proxies=proxies, in "env\webvoyager\lib\site-packages\openai\_base_client.py", line 738
```

### Testing Bolt.diy
<a name="test-bolt">
</a>

#### Installing and Starting Bolt.diy

First, install our forked version of Bolt.diy. Minor adjustments had been made to it in order to support automatic evaluation. 

```shell
git clone https://github.com/mnluzimu/bolt.diy-Fork.git
cd bolt.diy-Fork
npm install -g pnpm
pnpm install
```

Before starting the service, first copy the `.env.example` file and rename it as `.env.local`. Then configure the api keys and base urls. You should configure the LLM provider API of your choice in `.env.local`. (For example, create an openrouter api key at [Open Router AIP](https://openrouter.ai/settings/keys) and past it at `OPEN_ROUTER_API_KEY`.)

Also, remember to configer `VITE_GITHUB_ACCESS_TOKEN` with your github api, which will be used for importing templates.

Then run:

```shell
pnpm run dev
```

This will output something like:

```terminal

> bolt@0.0.7 dev D:\research\bolt\opensource\bolt.diy-Fork
> node pre-start.cjs  && remix vite:dev


★═══════════════════════════════════════★
          B O L T . D I Y
         ⚡️  Welcome  ⚡️
★═══════════════════════════════════════★

📍 Current Version Tag: v"0.0.7"
📍 Current Commit Version: "08d88c1"
  Please wait until the URL appears here
★═══════════════════════════════════════★
 warn  Data fetching is changing to a single fetch in React Router v7
┃ You can use the `v3_singleFetch` future flag to opt-in early.
┃ -> https://remix.run/docs/en/2.13.1/start/future-flags#v3_singleFetch
┗
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

You can get the url of the Bolt.diy service after `Local:` (in this case: `http://localhost:5173/`).

#### Starting Automatic Testing

You can start automatic testing of Bolt.diy by running the following command, for example:

```batch
python src\automatic_bolt_diy\eval_bolt_diy.py ^
    --jsonl_path data\test.jsonl ^
    --url http://localhost:5173/ ^
    --provider OpenRouter ^
    --desired_model deepseek/deepseek-chat-v3-0324:free
```

This example command would output the results under `downloads\OpenRouter\deepseek-chat-v3-0324_free_test`, including `.json` and `.zip` files for each test sample. The testing can sometimes be aborted due to connection issues, so you are recommanded to use `src\automatic_bolt_diy\loop.bat` by replacing the command inside the loop to achieve automatic restarting.

#### Evaluating Generated Websites with an UI Agent

You can deploy Qwen2.5-VL-32B-Instruct on a server with four GPUs using `src-remote/deploy/deploy_qwenvl_32b.sh`. After installation following commands in `src-remote/deploy/install.sh`.

Then we use the WebVoyager UI agent to perform test case operations and assess the outcome. Assuming you have installed the `env\webvoyager` conda environment previously, you can run `src\ui_test_bolt\run_ui_eval_with_answer.bat`, for example:

```batch
src\ui_test_bolt\run_ui_eval_with_answer.bat downloads\OpenRouter\deepseek-chat-v3-0324_free_test
```

This example command would output the UI agent testing results under `downloads\OpenRouter\deepseek-chat-v3-0324_free_test\extracted\results`.

#### Computing the Accuracy

Then you can compute the accuracy as well as other statistics such as yes rate, partial rate, and no rate using `src\ui_test_bolt\compute_acc.py`. For example:

```shell
python src\ui_test_bolt\compute_acc.py downloads\OpenRouter\deepseek-chat-v3-0324_free_test
```

This example would print the results in terminal, as well as record the results in `downloads\OpenRouter\deepseek-chat-v3-0324_free_test\extracted\table.md`.

#### Evaluating Appearance Score

Generate the appearance score of the websites using:

```shell
python src\grade_appearance_bolt_diy\eval_appearance.py downloads\OpenRouter\deepseek-chat-v3-0324_free_test -t data\test.jsonl
```

This would generate the screeshot and `result.json` file under `downloads\OpenRouter\deepseek-chat-v3-0324_free_test\extracted\000007\shots`. Then compute average appearance score using:

```shell
python src\grade_appearance_bolt_diy\compute_grade.py src\grade_appearance_bolt_diy\eval_appearance.py downloads\OpenRouter\deepseek-chat-v3-0324_free_test
```

### Testing OpenHands

You can test OpenHands using our forked repo [OpenHands-WebGen-Fork](https://github.com/mnluzimu/OpenHands-WebGen-Fork). You should configure it based on [OpenHands README](https://github.com/mnluzimu/OpenHands-WebGen-Fork/blob/main/README.md), then run:

```shell
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.25-nikolaik
cd OpenHands-WebGen-Fork
python src/test_webgen-bench/test_webgen_bench.py
```

### Testing Aider

You can test Aider using our forked repo [Aider-WebGen-Fork](https://github.com/YunqiaoYang/Aider-WebGen-Fork). You should configure it based on [Aider README](https://github.com/YunqiaoYang/Aider-WebGen-Fork/blob/main/README.md), then run:

```shell
cd .\working_dirs
python ..\src\batch_generate.py
```

## Training WebGen-LM

### Data Deduplication and Decontamination

This part is *not necessary for reproducing training*. It is our data deduplication and decontamination process, which was conducted to ensure that the training set is not contaminated by the test set. We place the files for deduplication and decontamination under `src-remote\process_train\deduplicate`.

```shell
pip install sentence-transformers scikit-learn editdistance
python src-remote/process_train/deduplicate/rule_deduplication.py
python src-remote/process_train/deduplicate/decontamination_ngram.py
python src-remote/process_train/deduplicate/test_decontamination_semantic.py --test_file data/test.jsonl --train_file data/train_processed/train_decontaminated_ngram5.jsonl --sim_threshold 0.55 --output_file data/train_processed/train_decontaminated_ngram5_semantic.jsonl --contaminated_file data/train_processed/train_contaminated_ngram5_semantic.jsonl
```

### Generating Training Data

(If you do not need to generate your own data, you can *skip this section* and directly use the data under `data/train_data`.)

#### Data Generation

First, generate training data using:

```batch
python src/automatic_bolt_diy/eval_bolt_diy.py ^
    --jsonl_path data/train.jsonl ^
    --url http://localhost:5173/ ^
    --provider OpenRouter ^
    --desired_model deepseek/deepseek-chat-v3-0324:free
```

Remember to replace `http://localhost:5173/` with the actual url of your bolt.diy service. This will output data under `downloads\OpenRouter\deepseek-chat-v3-0324_free_train`.

#### Data Filtering

Then, filter the data by generating the appearance score of each website using:

```shell
python src\grade_appearance_bolt_diy\eval_appearance.py downloads\OpenRouter\deepseek-chat-v3-0324_free_train -t data\train.jsonl
```

This would generate the screeshot and `result.json` file under `downloads\OpenRouter\deepseek-chat-v3-0324_free_train\extracted\000007\shots`. Then extract the filtered files using:

```shell
python src\grade_appearance_bolt_diy\filter_based_on_result.py downloads\OpenRouter\deepseek-chat-v3-0324_free_train
```

This would copy the filtered files under `downloads\OpenRouter\deepseek-chat-v3-0324_free_train\deepseek-chat-v3-0324_free_train_filtered`.

#### Converting to Training File Format

(We uplated the `downloads\OpenRouter\deepseek-chat-v3-0324_free_train\deepseek-chat-v3-0324_free_train_filtered` to a Linux server and executed the following files there.)

Convert the filtered files into the training format by running:

```shell
python src-remote/process_train/process_for_train/get_train.py 
```

### Finetuning

#### Installation

Create a conda environment:

```shell
conda create -p env/trainenv python=3.10
conda activate env/trainenv
```

First, install pytorch from [Pytorch Official Website](https://pytorch.org/) based on your cuda version. Then install other dependencies:

```shell
pip install -r requirements.txt
```

#### Training

The training scripts are under `src-remote/train`. You likely need to modify the files based on your own cluster before running:

```shell
bash src-remote/train/train_WebGen-LM-7B.sh
bash src-remote/train/train_WebGen-LM-14B.sh
bash src-remote/train/train_WebGen-LM-32B.sh
bash src-remote/train/train_Qwen2_5-Coder-32B-Instruct_ablation_150samples.sh
bash src-remote/train/train_Qwen2_5-Coder-32B-Instruct_ablation_300samples.sh
```

### Evaluation

This is the same as [Testing Bolt.diy](#test-bolt). The only difference is that you should host the trained model yourself using vllm. As in `src-remote/deploy/deploy_coder.sh`:

```shell
vllm serve models/Qwen2_5-Coder-32B-Instruct_app-bench_train_batch13_filtered_decontaminated_new \
    --dtype auto \
    --host 0.0.0.0 \
    --port 8000 \
    --pipeline-parallel-size 1 \
    --tensor-parallel-size 4 \
    --cpu-offload-gb 0 \
```

You should also configure the `.env.local` file in `bolt.diy-Fork` by setting the values of `OPENAI_LIKE_API_BASE_URL` to `http://IP_ADDRESS:PORT/v1`. Then you can start inference by running:

```shell
python src\automatic_bolt_diy\eval_bolt_diy.py ^
    --jsonl_path data\test.jsonl ^
    --url http://localhost:5173/ ^
    --provider OpenAILike ^
    --desired_model Qwen2_5-Coder-32B-Instruct_app-bench_train_batch13_filtered_decontaminated_new
```

Everything after is similar to [Testing Bolt.diy](#test-bolt).