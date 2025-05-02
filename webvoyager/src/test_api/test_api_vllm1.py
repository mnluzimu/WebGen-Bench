from openai import OpenAI

client = OpenAI(api_key="token-123", 
                base_url="http://14.103.16.83:25822/v1")

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
            },
            {"type": "text", "text": "Describe this image."},
        ],
    }
]

openai_response = client.chat.completions.create(
                    model="/mnt/cache/sharemath/models/Qwen/Qwen2.5-VL-72B-Instruct", messages=messages, max_tokens=1000, seed=42
                )

print(openai_response.choices[0].message.content)