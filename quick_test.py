
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('BAIDU_API_KEY', '')

print('=== Testing Chat ===')
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
    print('Status:', response.status_code)
    print('Response:', response.text)
except Exception as e:
    print('Error:', e)

print('\n=== Testing Image ===')
img_url = "https://qianfan.baidubce.com/v2/images/generations"
img_payload = {
    "model": "irag-1.0",
    "prompt": "a bearing"
}

try:
    img_response = requests.post(img_url, headers=headers, json=img_payload, timeout=60)
    print('Image Status:', img_response.status_code)
    print('Image Response:', img_response.text)
except Exception as e:
    print('Image Error:', e)

