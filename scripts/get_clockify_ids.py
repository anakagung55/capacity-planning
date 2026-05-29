import os
import requests
from dotenv import load_dotenv

load_dotenv()
CLOCKIFY_API_KEY = os.getenv('CLOCKIFY_API_KEY')

print("Mengecek identitas akun Clockify...\n")

# Endpoint ini hanya meminta data si pemilik API Key
url = "https://api.clockify.me/api/v1/user"
headers = {"X-Api-Key": CLOCKIFY_API_KEY}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    user_data = response.json()
    print("✅ API Key Valid!")
    print(f"Nama Asli: {user_data.get('name')}")
    print(f"User ID Kamu: {user_data.get('id')}")
else:
    print(f"Gagal! Error: {response.status_code} - {response.text}")