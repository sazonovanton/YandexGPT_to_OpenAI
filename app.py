from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import aiohttp
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
import time

from utils.misc import messages_translation, chat_completion_translation, setup_logging, chat_completion_chunk_translation, embeddings_translation
from utils.tokens import get_tokens

load_dotenv()

logger = setup_logging(os.getenv('Y2O_LogFile', './logs/y2o.log'), os.getenv('Y2O_LogLevel', 'INFO').upper())

# Yandex API settings 
SECRETKEY = os.getenv('Y2O_SecretKey')
CATALOGID = os.getenv('Y2O_CatalogID')

tokens = get_tokens()
logger.info(f"Loaded tokens: {tokens}")

print("=== YandexGPT to OpenAI API translator ===")
logger.info(f"=== YandexGPT to OpenAI API translator: Starting server (tokens: {len(tokens)}) ===")

# API settings
app = FastAPI(docs_url=None, redoc_url=None, title="YandexGPT to OpenAI API translator", description="Simple translator from OpenAI API calls to YandexGPT/YandexART API calls")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def authenticate_user(token: str = Depends(oauth2_scheme)):
    logger.info(f"Authenticating token: {token}")
    if token not in tokens:
        logger.error(f"Invalid token: {token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = tokens[token]
    logger.info(f"Authenticated user ID: {user_id}")
    return user_id

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    if request.headers.get("Authorization"):
        logger.info(f"Authorization Header: {request.headers['Authorization']}")
    else:
        logger.info("Authorization Header: Not provided")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

####################################
#           API endpoints          #
####################################

# Chat completions
class ChatCompletions(BaseModel):
    model: str
    max_tokens: int = None
    temperature: float = 0.7
    messages: list
    stream: bool = False

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(chat_completions: ChatCompletions, user_id: str = Depends(authenticate_user)):
    logger.info(f"* User `{user_id}` requested chat completion via model `{chat_completions.model}` (stream: {chat_completions.stream})")
    if chat_completions.stream:
        return StreamingResponse(stream_chat_completions(chat_completions, user_id), media_type="text/event-stream")
    else:
        return await non_stream_chat_completions(chat_completions, user_id)

async def stream_chat_completions(chat_completions: ChatCompletions, user_id: str):
    logger.debug(f"** Authorization Token: {user_id}")

    model = chat_completions.model
    if model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
        model = "yandexgpt-lite/latest"

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {SECRETKEY}",
        "x-folder-id": CATALOGID,
        "x-data-logging-enabled": "false"
    }
    data = {
        "modelUri": f"gpt://{CATALOGID}/{model}",
        "completionOptions": {
            "stream": True,
            "temperature": chat_completions.temperature,
            "maxTokens": chat_completions.max_tokens
        },
        "messages": await messages_translation(chat_completions.messages)
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                logger.error(f"* User `{user_id}` received error: {response.status} - {await response.text()}")
                raise HTTPException(status_code=response.status, detail=await response.text())
            now = time.time()
            i = 0
            str_index = 0
            async for chunk in response.content.iter_any():
                if chunk:
                    chunk_text = chunk.decode('utf-8')
                    try:
                        data = json.loads(chunk_text)
                        deltatext = data['result']['alternatives'][0]['message']['text'][str_index:]
                        str_index = len(data['result']['alternatives'][0]['message']['text'])
                        new_chunk = await chat_completion_chunk_translation(data, deltatext, user_id, model, timestamp=now)
                        logger.info(f"* User `{user_id}` received chat completion chunk (id: `{new_chunk['id']}`).")
                        logger.debug(f"** Response: {new_chunk['choices']}")
                        # yield json.dumps(new_chunk)
                        yield f"data: {json.dumps(new_chunk)}\n\n"
                    except json.JSONDecodeError:
                        # Handle chunk that might not be complete JSON
                        pass

async def non_stream_chat_completions(chat_completions: ChatCompletions, user_id: str):
    logger.debug(f"** Authorization Token: {user_id}")

    model = chat_completions.model
    if model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
        model = "yandexgpt-lite/latest"

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {SECRETKEY}",
        "x-folder-id": CATALOGID,
        "x-data-logging-enabled": "false"
    }
    data = {
        "modelUri": f"gpt://{CATALOGID}/{model}",
        "completionOptions": {
            "stream": False,
            "temperature": chat_completions.temperature,
            "maxTokens": chat_completions.max_tokens
        },
        "messages": await messages_translation(chat_completions.messages)
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                logger.error(f"* User `{user_id}` received error: {response.status} - {await response.text()}")
                raise HTTPException(status_code=response.status, detail=await response.text())
            response_data = await response.json()
            response_data = await chat_completion_translation(response_data, user_id, model)
            logger.info(f"* User `{user_id}` received chat completions (id: `{response_data['id']}`). Tokens used (prompt/completion/total): {response_data['usage']['prompt_tokens']}/{response_data['usage']['completion_tokens']}/{response_data['usage']['total_tokens']}")
            logger.debug(f"** Response: {response_data['choices']}")
            new_headers = {
                "Date": f"{datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}",
                "Content-Type": "application/json",
                "Connection": "keep-alive",
            }
            return JSONResponse(content=response_data, headers=new_headers)

# Embeddings
class Embeddings(BaseModel):
    model: str
    input: str
    encoding_format: str = "float"

@app.post("/v1/embeddings")
@app.post("/embeddings")
async def embeddings(embeddings: Embeddings, user_id: str = Depends(authenticate_user)):
    logger.info(f"* User `{user_id}` requested embeddings for model `{embeddings.model}`")
    model = embeddings.model
    b64 = embeddings.encoding_format == "base64"

    if model in ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"]:
        logger.info(f"* `{model}` is OpenAI model, using `text-search-query/latest` model")
        model = "text-search-query/latest"

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {SECRETKEY}",
        "x-folder-id": CATALOGID,
        "x-data-logging-enabled": "false"
    }
    data = {
        "modelUri": f"emb://{CATALOGID}/{model}",
        "text": embeddings.input,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                logger.error(f"* User `{user_id}` received error: {response.status} - {await response.text()}")
                raise HTTPException(status_code=response.status, detail=await response.text())
            response_data = await response.json()
            response_data = await embeddings_translation(response_data, user_id, model=model, b64=b64)
            logger.info(f"* User `{user_id}` received embeddings for model `{model}`")
            logger.debug(f"** Response: {response_data}")
            return JSONResponse(content=response_data, media_type="application/json")
            

# Models
@app.get("/v1/models")
@app.get("/models")
async def models_list(user_id: str = Depends(authenticate_user)):
    logger.info(f"* User `{user_id}` requested models list")
    models = {
        "object": "list",
        "data": [
                {
                    "id": "yandexgpt/latest",
                    "object": "model",
                    "created": 1686935002,
                    "owned_by": "yandex"
                },
                {
                    "id": "yandexgpt-lite/rc",
                    "object": "model",
                    "created": 1686935002,
                    "owned_by": "yandex"
                },
                {
                    "id": "yandexgpt-lite/latest",
                    "object": "model",
                    "created": 1686935002,
                    "owned_by": "yandex"
                },
                {
                    "id": "yandexgpt-lite/deprecated",
                    "object": "model",
                    "created": 1686935002,
                    "owned_by": "yandex"
                }
            ],
            "object": "list"
        }
    logger.info(f"* User `{user_id}` received models list")
    return JSONResponse(content=models, media_type="application/json")

# Health check
@app.get("/v1/health")
@app.get("/health")
async def health_check():
    return {"status": "ok"}



####################################
#               Start              #
####################################
if __name__ == "__main__":
    import uvicorn
    if os.getenv('Y2O_SSL_Key') and os.getenv('Y2O_SSL_Cert'):
        logger.info("SSL keys found, starting server with SSL")
        uvicorn.run(app, host=os.getenv('Y2O_Host', '0.0.0.0'), port=int(os.getenv('Y2O_Port', 8000)), ssl_keyfile=os.getenv('Y2O_SSL_Key'), ssl_certfile=os.getenv('Y2O_SSL_Cert'))
    else:
        logger.info("Starting server without SSL")
        uvicorn.run(app, host=os.getenv('Y2O_Host', '0.0.0.0'), port=int(os.getenv('Y2O_Port', 8000)))
