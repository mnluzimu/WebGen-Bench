import openai
import base64
from openai import OpenAI
from prompt import appearance_prompt


client = OpenAI(
    api_key="token-123",
    base_url="http://PI_ADDRESS:PORT/v1" # replace with your own IP Adress and port
)

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


def get_score_result(image_paths, instruction, model="Qwen2.5-VL-32B-Instruct"): # If you are hosting the model with absolute path, model should be replaced with that
    base64_images = []
    
    for image_path in image_paths:    
        base64_image = encode_image(image_path)
        base64_images.append(base64_image)
        
    prompt = appearance_prompt.format(
        instruction=instruction,
    )
    
    user_content = [{
                        "type": "text",
                        "text": prompt
                    }]
    
    for base64_image in base64_images:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    chat_response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
    )

    return chat_response.choices[0].message.content
