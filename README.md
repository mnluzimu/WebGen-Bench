# WebGen-Bench

(The code under `src` was executed on a Windows 11 system. It should also run on Linux with minor adjustments.)

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

### Testing OpenHands

You can test OpenHands using our forked repo [OpenHands-WebGen-Fork](https://github.com/mnluzimu/OpenHands-WebGen-Fork). You should configure it based on [OpenHands README](https://github.com/mnluzimu/OpenHands-WebGen-Fork/blob/main/README.md), then run:

```shell
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.25-nikolaik
cd OpenHands-WebGen-Fork
python src/test_webgen-bench/test_webgen_bench.py
```