import requests
import time

url = "http://127.0.0.1:7725/translate"
data = {
    "text": "Hello World !",
    "src": "en",
    "trg": "pt"
}

start = time.time()
response = requests.post(url, json=data)
response_data = response.json()

print(f"Time taken: {time.time() - start} seconds")

print(response_data["translated_text"])
