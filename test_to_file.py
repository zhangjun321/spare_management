
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('BAIDU_API_KEY', '')

output_file = 'test_output.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('=== Testing Chat ===\n')
    
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": "ernie-4.0-turbo-8k",
        "messages": [{"role": "user", "content": "hello"}],
        "max_completion_tokens": 30
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        f.write(f'Status: {response.status_code}\n')
        f.write(f'Response: {response.text}\n')
    except Exception as e:
        f.write(f'Error: {e}\n')
    
    f.write('\n=== Testing Image ===\n')
    img_url = "https://qianfan.baidubce.com/v2/images/generations"
    img_payload = {
        "model": "irag-1.0",
        "prompt": "a bearing"
    }
    
    try:
        img_response = requests.post(img_url, headers=headers, json=img_payload, timeout=60)
        f.write(f'Image Status: {img_response.status_code}\n')
        f.write(f'Image Response: {img_response.text}\n')
    except Exception as e:
        f.write(f'Image Error: {e}\n')

print(f'Test output saved to {output_file}')

