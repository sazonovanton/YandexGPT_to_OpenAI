# YandexGPT API to OpenAI API Translator
A FastAPI server that translates OpenAI API requests to [YandexGPT](https://yandex.cloud/en/services/yandexgpt) and [YandexART](https://yandex.cloud/en/docs/foundation-models/quickstart/yandexart) API requests. This enables you to use tools and applications designed for OpenAI's API with Yandex's language and image generation models.

## Navigation

English | [Russian](README.ru.md)  

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage Examples](#usage-examples)
- [Environment Variables](#environment-variables)
- [OpenAI Model Aliases](#openai-model-aliases)

## Features
- **Text Generation**: Translates OpenAI chat completion requests to YandexGPT
  - ✅ Streaming support
  - ✅ Tools/Function calling - with YandexGPT 4 models
  - ⬜ Vision (not supported)
- **Text Embeddings**: Converts embedding requests to Yandex's text vectorization models
  - ✅ Supports both `float` and `base64` encoding formats
- **Image Generation**: Translates DALL-E style requests to YandexART
  - ✅ Supports both base64 and URL response formats
  - ✅ Configurable aspect ratios
  - ❌ Multiple images per request (limited to 1)

## Prerequisites
1. A Yandex Cloud account
2. API key and catalog ID from [Yandex Cloud](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key)
3. Required IAM roles:
   - `ai.languageModels.user` (for YandexGPT)
   - `ai.imageGeneration.user` (for YandexART)

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/sazonovanton/YandexGPT_to_OpenAI
cd YandexGPT_to_OpenAI
```

### 2. Choose Authentication Method
The server supports two authentication methods:

#### A. Generated Tokens
Generate tokens that users can use to access the API:
```bash
python utils/tokens.py
```
Tokens will be stored in `data/tokens.json`

#### B. Bring Your Own Key (BYOK)
Allow users to provide their own Yandex Cloud credentials in the format:
```
<CatalogID>:<SecretKey>
```

### 3. Deployment Options

#### Using Docker (Recommended)
1. Configure environment variables in `docker-compose.yml`:
```yaml
environment:
  - Y2O_SecretKey=your_secret_key
  - Y2O_CatalogID=your_catalog_id
  - Y2O_BringYourOwnKey=false
  - Y2O_ServerURL=http://127.0.0.1:8520
  - Y2O_LogFile=logs/y2o.log
  - Y2O_LogLevel=INFO
```

2. Start the server:
```bash
docker-compose up -d
```

#### Manual Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with configuration:
```bash
Y2O_SecretKey=your_secret_key
Y2O_CatalogID=your_catalog_id
Y2O_BringYourOwnKey=false
Y2O_Host=127.0.0.1
Y2O_Port=8520
Y2O_ServerURL=http://127.0.0.1:8520
Y2O_LogFile=logs/y2o.log
Y2O_LogLevel=INFO
```

3. Start the server:
```bash
python app.py
```

### 4. SSL Configuration (Optional)

To enable SSL, set the following environment variables:
```bash
Y2O_SSL_Key=ssl/private.key
Y2O_SSL_Cert=ssl/cert.pem
```

## Usage Examples

You can test API with your own keys (see [BYOK](#b-bring-your-own-key-byok)) setting base URL `https://sazonovanton.online:8520/v1`.  
Logging level is set to `INFO`, your keys will not be stored.  

### Chat Completion
#### Python
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("TOKEN"),
    base_url="http://<your_host>:<your_port>/v1",
)
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="yandexgpt/latest",
)
```
#### cURL
```bash
curl http://<your_host>:<your_port>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model": "yandexgpt/latest",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

### Image Generation

#### Python
```python
response = client.images.generate(
    model="yandex-art/latest",
    prompt="A painting of a cat",
    response_format="b64_json"  
)
```
#### cURL
```bash
curl http://<your_host>:<your_port>/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model": "yandex-art/latest",
    "prompt": "A painting of a cat",
    "response_format": "url"
  }'
```
```bash
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -O http://<your_host>:<your_port>/images/<id>.jpg
```

### Text Embeddings

```python
response = client.embeddings.create(
    model="text-search-query/latest",
    input=["Your text here"],
    encoding_format="float" 
)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| Y2O_SecretKey | Yandex Cloud API key | None |
| Y2O_CatalogID | Yandex Cloud catalog ID | None |
| Y2O_BringYourOwnKey | Allow users to provide their own credentials | False |
| Y2O_Host | Server host | 127.0.0.1 |
| Y2O_Port | Server port | 8520 |
| Y2O_ServerURL | Public server URL for image download | http://127.0.0.1:8520 |
| Y2O_LogFile | Log file path | logs/y2o.log |
| Y2O_LogLevel | Logging level | INFO |
| Y2O_SSL_Key | SSL private key path | None |
| Y2O_SSL_Cert | SSL certificate path | None |
| Y2O_CORS_Origins | Allowed CORS origins | * |
| Y2O_TestToken | Test token for utils/test.py (dev) | None |


## OpenAI Model Aliases
The translator supports automatic model name mapping from OpenAI to Yandex Foundation Models. However, this models may not have direct equivalents. It's recommended to use Yandex model names directly (e.g., `yandexgpt/latest`).  
The following aliases are supported:

### Chat Models
- `gpt-3.5*` → `yandexgpt-lite/latest`
- `*mini*` → `yandexgpt-lite/latest`
- `gpt-4*` → `yandexgpt/latest`
### Embedding Models
- `text-embedding-3-large` → `text-search-doc/latest`
- `text-embedding-3-small` → `text-search-query/latest`
- `text-embedding-ada-002` → `text-search-query/latest`
### Image Models
- `dall-e*` → `yandex-art/latest`
