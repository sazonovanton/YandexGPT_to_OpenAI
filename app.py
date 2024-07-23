#!/usr/bin/env python3
"""
Simple translator from OpenAI API calls to YandexGPT/YandexART API calls
"""

from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordBearer
from pydantic import BaseModel
import aiohttp
import os
import json

from utils.misc import messages_translation, chat_completion_translation, setup_logging, get_headers
from utils.tokens import get_tokens

from dotenv import load_dotenv
load_dotenv()

logger = setup_logging(os.getenv('O2Y_LogFile', './logs/o2y.log'), os.getenv('O2Y_LogLevel', 'INFO').upper())

# Yandex API settings 
SECRETKEY = os.getenv('O2Y_SecretKey')
CATALOGID = os.getenv('O2Y_CatalogID')

tokens = get_tokens()

print("=== OpenAI to YandexGPT API translator ===")
logger.info(f"=== OpenAI to YandexGPT API translator: Starting server (tokens: {len(tokens)}) ===")

# API settings
app = FastAPI(docs_url=None, redoc_url=None, title="OpenAI to YandexGPT API translator", description="Simple translator from OpenAI API calls to YandexGPT/YandexART API calls")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    if credentials not in tokens.keys():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = tokens[credentials]
    return user_id

class ChatCompletions(BaseModel):
    """
    Chat completions model
    Variables:
    - model: str
    - max_tokens: int (default: None)
    - temperature: float (default: 0.7)
    - user: str
    - messages: list
    """
    model: str
    max_tokens: int = None
    temperature: float = 0.7
    messages: list

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(chat_completions: ChatCompletions, user_id: str = Depends(authenticate_user)):
    logger.info(f"* User `{user_id}` requested chat completions via `{chat_completions.model}`")
    logger.debug(f"** Headers:\n{chat_completions.headers}\n")
    logger.debug(f"** Messages: {chat_completions.messages}")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {SECRETKEY}",
        "x-folder-id": CATALOGID,
        "x-data-logging-enabled": "false"
    }
    data = {
        "modelUri": f"gpt://{CATALOGID}/{chat_completions.model}",
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
            response_data = await chat_completion_translation(response_data, user_id, chat_completions.model)
            logger.info(f"* User `{user_id}` received chat completions (id: `{response_data['id']}`). Tokens used (prompt/completion/total): {response_data['usage']['prompt_tokens']}/{response_data['usage']['completion_tokens']}/{response_data['usage']['total_tokens']}")
            logger.debug(f"** Response: {response_data['choices']}")
            return JSONResponse(content=response_data, media_type="application/json", headers=await get_headers(response))

@app.post("/v1/models")
@app.post("/models")
async def models_list(user_id: str = Depends(authenticate_user)):
    logger.info(f"* User `{user_id}` requested models list")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/models"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {SECRETKEY}"
    }
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
    # send response
    logger.info(f"* User `{user_id}` received models list")
    return JSONResponse(content=models, media_type="application/json")

@app.get("/v1/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Check certs
    if os.getenv('O2Y_SSL_Key') and os.getenv('O2Y_SSL_Cert'):
        logger.info("SSL keys found, starting server with SSL")
        uvicorn.run(app, host=os.getenv('O2Y_Host', '0.0.0.0'), port=int(os.getenv('O2Y_Port', 8000)), ssl_keyfile=os.getenv('O2Y_SSL_Key'), ssl_certfile=os.getenv('O2Y_SSL_Cert'))
    else:
        logger.info("Starting server without SSL")
        uvicorn.run(app, host=os.getenv('O2Y_Host', '0.0.0.0'), port=int(os.getenv('O2Y_Port', 8000)))
