from pathlib import Path
import requests, base64

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False

IMAGE_MIME_TYPES = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
}

def find_image_path(index):
  for suffix in IMAGE_MIME_TYPES:
    path = Path(f"image_{index}{suffix}")
    if path.exists():
      return path
  raise FileNotFoundError(f"Expected image_{index}.png/.jpg/.jpeg/.webp")

def read_image_data_url(path):
  with open(path, "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()
  return f"data:{IMAGE_MIME_TYPES[path.suffix.lower()]};base64,{image_b64}"


headers = {
  "Authorization": "Bearer $NVIDIA_API_KEY",
  "Accept": "text/event-stream" if stream else "application/json"
}

payload = {
  "model": "stepfun-ai/step-3.7-flash",
  "messages": [{"role":"user","content":""}],
  "max_tokens": 16384,
  "temperature": 1.00,
  "top_p": 0.95,
  "stream": stream,
  
}

response = requests.post(invoke_url, headers=headers, json=payload, stream=stream)
if stream:
    for line in response.iter_lines():
        if line:
            print(line.decode("utf-8"))
else:
    print(response.json())