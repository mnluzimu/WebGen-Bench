import openai
import base64
from openai import OpenAI
from prompt import appearance_prompt


client = OpenAI(
    api_key="sk-mah6FUel7jrB3lNj8c3cnqUGeKy1ovL5DAD1GFge92C7Fe864c8646B1B9DaB6C20a10A896",  
    base_url="https://platform.llmprovider.ai/v1"
)

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
 
image_path = r"F:\research\bolt\APP-Bench\data\oh_deepseek-v3\workspaces\results\taskworkspace_0_0\screenshot1.png"
 
#原图片转base64
base64_image = encode_image(image_path)
instruction = "The instruction describes a website focused on providing stock information, analysis, and generating customized reports based on user input, which aligns with the characteristics of analytics platforms that offer data visualization and insights, in this case, for stock market data and financial analysis."
prompt = appearance_prompt.format(
    instruction=instruction,
)


#提交信息至GPT4o
chat_response = client.chat.completions.create(
    model="gpt-4o",#选择模型
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content":[
            {
                "type": "text",
                "text": prompt
            },
            {
                "type": "image_url",
                "image_url":{
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            },
            ]
        }
    ],
)

print("Chat response:", chat_response.choices[0].message.content)