import requests

# 1. Masukkan API Key kamu
CLOCKIFY_API_KEY = 'MDg3MjBlZTctODZmNi00NGNlLWFlMjQtYWEzZjVhMmViODY0'

# 2. Masukkan Workspace ID yang baru saja kamu dapatkan
WORKSPACE_ID = '68abcd9b-8c1e-4a3c-9f0e-1234567890ab'

# 3. URL Endpoint untuk melihat semua user di dalam workspace tersebut
url = f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/users"
headers = {
    "X-Api-Key": CLOCKIFY_API_KEY
}

# 4. Kirim request
response = requests.get(url, headers=headers)

if response.status_code == 200:
    users = response.json()
    print("=== DAFTAR USER DI BLUEROCK DIGITAL ===")
    for user in users:
        print(f"Nama    : {user['name']}")
        print(f"User ID : {user['id']}")
        print("-" * 30)
else:
    print(f"Gagal! Error {response.status_code}: {response.text}")