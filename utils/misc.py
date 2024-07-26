#!/usr/bin/env python3
"""
Miscellaneous functions for the project

- messages_translation: Translate messages from OpenAI to YandexGPT format
- chat_completion_translation: Translate chat completion from YandexGPT to OpenAI format
"""
import time
import os
import json
import hashlib
import datetime

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

async def messages_translation(messages: list):
    """
    Translate messages from OpenAI to YandexGPT format
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
        finish_reasons = {
            "ALTERNATIVE_STATUS_FINAL": "stop",
            "ALTERNATIVE_STATUS_TRUNCATED_FINAL": "length",
            "ALTERNATIVE_STATUS_CONTENT_FILTER": "content_filter",
            "ALTERNATIVE_STATUS_PARTIAL": "incomplete",
            "ALTERNATIVE_STATUS_UNSPECIFIED": "unknown",
            "ALTERNATIVE_STATUS_TOOLS": "tool_calls" # Not implemented in YandexGPT, just placeholder
        }
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
                "finish_reason": finish_reasons[choice["status"]]
            }
            i += 1
            choices.append(new_choice)
        userhash = hashlib.md5(user_id.encode()).hexdigest()
        current_time = int(time.time())
        new_chat_completion = {
            "id": f"o2y-{userhash}{current_time}",
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
    
