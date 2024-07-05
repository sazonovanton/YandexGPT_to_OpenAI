# OpenAI API to YandexGPT API translator
This is a simple API that translates OpenAI API requests to YandexGPT API requests.  
It is useful for those who have a tool that expects OpenAI (like) API requests, but want to use YandexGPT API instead.  

## How to use
1. Clone this repository
2. Install the requirements
```bash
pip install -r requirements.txt
```
3. Create environment variables for the OpenAI API key and the YandexGPT API key. You can do this by creating a `.env` file in the root of the project with the following content:
```bash
O2Y_SecretKey=***
O2Y_CatalogID=***
O2Y_Host=127.0.0.1
O2Y_Port=8000
O2Y_LogFile=logs/o2y.log
O2Y_LogLevel=INFO
```
Here are default values, only `O2Y_SecretKey` and `O2Y_CatalogID` are required, others are optional.  
If you want to use SSL, you can set paths to the SSL key and certificate files:  
```bash
O2Y_SSL_Key=ssl/private.key
O2Y_SSL_Cert=ssl/cert.pem
```
4. Run the API
```bash
python main.py
```
5. Use the API by setting `openai.base_url` to `http://<Your_Host>:<Your_Port>` 

## How it works
The API listens for OpenAI API requests and translates them to YandexGPT API requests. Then it sends the request to the YandexGPT API and returns translated response to the client.  

## What is implemented
### Chat 
[chat/completions](https://platform.openai.com/docs/api-reference/chat/create) translates to [TextGeneration.completion](https://yandex.cloud/ru/docs/foundation-models/text-generation/api-ref/TextGeneration/completion)