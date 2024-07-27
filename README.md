# YandexGPT API to OpenAI API translator
This is a simple API server that translates OpenAI API requests to [YandexGPT](https://yandex.cloud/en/services/yandexgpt)/[YandexART](https://yandex.cloud/en/docs/foundation-models/quickstart/yandexart) API requests.  
It is useful for those who have a tool that expects OpenAI (like) API usage, but want to use YandexGPT API.  

## How it works
The API server listens for OpenAI API requests and sends them to Yandex GPT and returns translated response to the client.  
Supports text generation, text embeddings and image generation (learn [more](#what-is-implemented)).  

## How to use
### Setup
1. Get API key and catalog ID from [Yandex Cloud](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key). Roles needed: `ai.languageModels.user` and `ai.imageGeneration.user`.  
2. Clone this repository
3. Install the requirements
```bash
pip install -r requirements.txt
```
4. Create environment variables for the OpenAI API key and the YandexGPT API key. You can do this by creating a `.env` file in the root of the project with the following content:
```bash
Y2O_SecretKey=***
Y2O_CatalogID=***
Y2O_Host=127.0.0.1
Y2O_Port=8000
Y2O_ServerURL=http://127.0.0.1:8000
Y2O_LogFile=logs/y2o.log
Y2O_LogLevel=INFO
```
Here are default values, only `Y2O_SecretKey` and `Y2O_CatalogID` are required, others are optional.  
`Y2O_ServerURL` needed to send an URL of the generated image in the response, default is `http://localhost:8000`.  
If you want to use SSL, you can set paths to the SSL key and certificate files:  
```bash
Y2O_SSL_Key=ssl/private.key
Y2O_SSL_Cert=ssl/cert.pem
```
5. Create tokens by running the following command from project root directory:  
```bash
python utils/tokens.py
```
6. Run the API
```bash
python app.py
```
7. Use the API by setting `openai.base_url` to `http://<your_host>:<your_port>/v1` 

### Usage

#### cURL example
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

#### Python example
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

## What is implemented
### /chat/completions 
[Chat completions](https://platform.openai.com/docs/api-reference/chat/create) translates to [TextGeneration.completion](https://yandex.cloud/en/docs/foundation-models/text-generation/api-ref/TextGeneration/completion)  
* ✅ Streaming  
* ⬜ Vision (not supported)  
* ⬜ Tools (not supported)
### /embeddings
[Embeddings](https://platform.openai.com/docs/api-reference/embeddings) translates to [Embeddings.textEmbedding](https://yandex.cloud/en/docs/foundation-models/embeddings/api-ref/Embeddings/textEmbedding) (_not fully tested_)  
* ✅ encoding_format: `float`, `base64`  
### /images/generations
[Images generations](https://platform.openai.com/docs/api-reference/images/create) translates to [ImageGenerationAsync.generate](https://yandex.cloud/ru/docs/foundation-models/image-generation/api-ref/ImageGenerationAsync/generate).  
Generates one JPEG image, does not return revised prompt. When URL is requested, it saves generated image to the `data/images` directory and deletes it after one hour. Directory is cleaned on server start.  
* ✅ response_format: `base64`, `url`  
* ❕ size - sets aspect ratio, not width and height (weight of width and height in image)  
* ❌ n - number of images to generate (always 1)  
### /models
[Models](https://platform.openai.com/docs/api-reference/models) translates to list of [Yandex Foundation models](https://yandex.cloud/en/docs/foundation-models/concepts/) that is stored in `data/model_list.json` file (_can be incomplete_)