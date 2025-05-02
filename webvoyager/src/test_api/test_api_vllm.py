from openai import OpenAI

# Set OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://14.103.16.83:25822/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

chat_response = client.chat.completions.create(
    model="/mnt/cache/sharemath/models/Qwen/Qwen2.5-VL-7B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://modelscope.oss-cn-beijing.aliyuncs.com/resource/qwen.png"
                    },
                },
                {"type": "text", "text": "Describe the contents of the image"},
            ],
        },
    ],
)
print("Chat response:", chat_response)