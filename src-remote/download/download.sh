DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export HF_ENDPOINT='https://hf-mirror.com'
export HF_HUB_URL='https://hf-mirror.com'

python $DIR/download.py