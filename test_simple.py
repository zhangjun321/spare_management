#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('BAIDU_API_KEY', '')

print('Testing chat...')
url = "https://qianfan.baidubce.com/v2/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
payload = {
    "model": "ernie-4.0-turbo-8k",
    "messages": [{"role": "user", "content": "hi"}],
    "max_completion_tokens": 50
}

response = requests.post(url, headers=headers, json=payload, timeout=30)
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
