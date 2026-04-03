#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('BAIDU_API_KEY', '')

url = "https://qianfan.baidubce.com/v2/images/generations"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": "Stable-Diffusion-XL",
    "prompt": "a simple industrial bearing, white background",
    "n": 1,
    "size": "512x512"
}

response = requests.post(url, headers=headers, json=payload, timeout=30)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
