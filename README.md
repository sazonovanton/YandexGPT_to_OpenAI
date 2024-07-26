# YandexGPT API to OpenAI API translator
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
Y2O_SecretKey=***
Y2O_CatalogID=***
Y2O_Host=127.0.0.1
Y2O_Port=8000
Y2O_LogFile=logs/y2o.log
Y2O_LogLevel=INFO
```
Here are default values, only `Y2O_SecretKey` and `Y2O_CatalogID` are required, others are optional.  
If you want to use SSL, you can set paths to the SSL key and certificate files:  
```bash
Y2O_SSL_Key=ssl/private.key
Y2O_SSL_Cert=ssl/cert.pem
```
4. Create tokens by running the following command from project root directory:  
```bash
python utils/tokens.py
```
5. Run the API
```bash
python app.py
```
6. Use the API by setting `openai.base_url` to `http://<your_host>:<your_port>` 

## How it works
The API listens for OpenAI API requests and translates them to YandexGPT API requests. Then it sends the request to the YandexGPT API and returns translated response to the client.  

## What is implemented
### /chat/completions 
* [Chat completions](https://platform.openai.com/docs/api-reference/chat/create) translates to [TextGeneration.completion](https://yandex.cloud/ru/docs/foundation-models/text-generation/api-ref/TextGeneration/completion) (streaming is supported)