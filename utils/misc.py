#!/usr/bin/env python3
"""
Miscellaneous functions for the project

- setup_logging: Set up logging to log to a file
- messages_translation: Translate messages from YandexGPT to OpenAI  format
- chat_completion_translation: Translate chat completion from YandexGPT to OpenAI format
- chat_completion_chunk_translation: Translate chat completion chunk from YandexGPT to OpenAI format
- embeddings_translation: Translate embeddings from YandexGPT to OpenAI format
"""
import time
import os
import hashlib
import base64
import struct
import json

def setup_logging(log_file: str, log_level: str = 'CRITICAL', max_kb: int = 512, backup_count: int = 3) -> None:
    """
    Set up logging to log to a file.
    Rotate log files when they reach 128KB.
    """
    import logging
    import logging.handlers

    # create log folder if not exist
    log_folder = os.path.dirname(log_file)
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_kb*1024, backupCount=backup_count)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level, 'CRITICAL'))
    # drop existing handlers
    for h in logger.handlers:
        logger.removeHandler(h)
    logger.addHandler(handler)
    return logger

def get_model_list(path: str = 'data/model_list.json') -> list:
    """
    Get model list from a json file
    """
    with open(path, 'r') as f:
        model_list = json.load(f)
    return model_list

async def messages_translation(messages: list):
    """
    Translate messages from YandexGPT to OpenAI  format
    Input:
    - messages: list
    Output:
    - new_messages: list
    """
    try:
        new_messages = []
        for message in messages:
            new_message = {
                "role": message["role"],
                "text": message["content"]
            }
            new_messages.append(new_message)
        return new_messages
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        raise Exception(f'Error in messages_translation: {e}')
    
async def finish_reason_translation(finish_reason):
    """
    Translate finish reason from YandexGPT to OpenAI  format
    Input:
    - finish_reason: str
    Output:
    - new_finish_reason: str
    """
    try:
        # finish_reasons = {
        #     "stop": "ALTERNATIVE_STATUS_FINAL",
        #     "length": "ALTERNATIVE_STATUS_TRUNCATED_FINAL",
        #     "content_filter": "ALTERNATIVE_STATUS_CONTENT_FILTER",
        #     "incomplete": "ALTERNATIVE_STATUS_PARTIAL",
        #     "unknown": "ALTERNATIVE_STATUS_UNSPECIFIED",
        #     "tool_calls": "ALTERNATIVE_STATUS_TOOLS" # Not implemented in YandexGPT, just placeholder
        # }
        finish_reasons = {
            "ALTERNATIVE_STATUS_FINAL": "stop",
            "ALTERNATIVE_STATUS_TRUNCATED_FINAL": "length",
            "ALTERNATIVE_STATUS_CONTENT_FILTER": "content_filter",
            # "ALTERNATIVE_STATUS_PARTIAL": "incomplete",
            "ALTERNATIVE_STATUS_PARTIAL": None,
            "ALTERNATIVE_STATUS_UNSPECIFIED": "unknown",
            "ALTERNATIVE_STATUS_TOOLS": "tool_calls" # Not implemented in YandexGPT, just placeholder
        }
        new_finish_reason = finish_reasons[finish_reason]
        return new_finish_reason
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        raise Exception(f'Error in finish_reason_translation: {e}')
    
async def chat_completion_translation(chat_completion: dict, user_id: str, model: str):
    """
    Translate chat completion from YandexGPT to OpenAI format
    Input:
    - chat_completion: dict
    - user_id: str
    - model: str
    Output:
    - new_chat_completion: dict
    """
    try:
        alternatives = chat_completion["result"]["alternatives"] # List of alternatives from YandexGPT
        choices = [] # List of choices for OpenAI
        i = 0
        for choice in alternatives:
            new_choice = {
                "index": i,
                "message": {
                    "role": choice["message"]["role"],
                    "content": choice["message"]["text"]
                },
                "logprobs": None,
                "finish_reason": await finish_reason_translation(choice["status"])
            }
            i += 1
            choices.append(new_choice)
        userhash = hashlib.md5(user_id.encode()).hexdigest()
        current_time = int(time.time())
        new_chat_completion = {
            "id": f"y2o-{userhash}{current_time}",
            "model": f"{model}-{chat_completion['result']['modelVersion'].replace('.', '-')}",
            "object": "chat.completion",
            "created": int(current_time),
            "choices": choices,
            "usage": {
                "prompt_tokens": int(chat_completion['result']['usage']['inputTextTokens']),
                "completion_tokens": int(chat_completion['result']['usage']['completionTokens']),
                "total_tokens": int(chat_completion['result']['usage']['totalTokens'])
            },
            "system_fingerprint": f"fp_{userhash}"
        }
        return new_chat_completion
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        raise Exception(f'Error in chat_completion_translation: {e}')
    
async def chat_completion_chunk_translation(chunk: dict, deltatext: str, user_id: str, model: str, timestamp: int):
    """
    Translate chat completion chunk from YandexGPT to OpenAI format

    Input:
    - chunk: dict
    - user_id: str
    - model: str
    - timestamp: int
    Output:
    - new_chat_chunk_completion: dict
    """
    try:
        choice = chunk["result"]["alternatives"][0]
        choices = [] # List of choices for OpenAI
        i = 0

        delta = {}
        # if choice["message"]["role"] and deltatext == "":
        #     delta["role"] = choice["message"]["role"]
        delta["content"] = deltatext
        delta["role"] = choice["message"]["role"]
        new_choice = {
            "index": i,
            "delta": delta,
            "logprobs": None,
            "finish_reason": await finish_reason_translation(choice["status"])
        }
        # i += 1
        choices.append(new_choice)

        userhash = hashlib.md5(user_id.encode()).hexdigest()
        current_time = int(timestamp)
        new_chat_chunk_completion = {
            "id": f"y2o-{userhash}{current_time}",
            "model": f"{model}-{chunk['result']['modelVersion'].replace('.', '-')}",
            "object": "chat.completion.chunk",
            "created": current_time,
            "choices": choices,
            "system_fingerprint": f"fp_{userhash}"
        }
        return new_chat_chunk_completion
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        raise Exception(f'Error in chat_completion_chunk_translation: {e}')
    
async def embeddings_translation(embeddings: dict, user_id: str, model: str, b64: bool = False):
    """
    Translate embeddings from YandexGPT to OpenAI format
    Input:
    - embeddings: dict
    - user_id: str
    - model: str
    - b64: bool (default: False)
    Output:
    - new_embeddings: dict
    """
    try:
        emb = embeddings["embedding"]
        if b64:
            byte_array = b''.join(struct.pack('f', x) for x in emb)
            emb = base64.b64encode(byte_array).decode('utf-8')
        data = [
            {
                "object": "embedding",
                "embedding": emb,
                "index": 0
            }
        ]
        new_embeddings = {
            "object": "list",
            "data": data,
            "model": f"{model}_{embeddings['modelVersion'].replace('.', '-')}",
            "usage": {
                "prompt_tokens": int(embeddings['numTokens']),
                "total_tokens": int(embeddings['numTokens'])
            }
        }
        return new_embeddings
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        raise Exception(f'Error in embeddings_translation: {e}')