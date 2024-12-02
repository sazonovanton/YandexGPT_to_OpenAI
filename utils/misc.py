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
import asyncio

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

async def tools_translation(tools: list):
    """
    Translate tools from OpenAI to YandexGPT format
    Input:
    - tools: list of tools in OpenAI format
    Output:
    - new_tools: list of tools in YandexGPT format
    """
    try:
        new_tools = []
        for tool in tools:
            if tool["type"] == "function":
                new_tool = {
                    "function": {
                        "name": tool["function"]["name"],
                        "description": tool["function"].get("description", ""),
                        "parameters": tool["function"]["parameters"]
                    }
                }
                new_tools.append(new_tool)
        return new_tools
    except Exception as e:
        raise Exception(f'Error in tools_translation: {e}')

async def messages_translation(messages: list):
    """
    Translate messages from OpenAI to YandexGPT format
    Input:
    - messages: list of messages in OpenAI format
    Output:
    - new_messages: list of messages in YandexGPT format
    """
    try:
        new_messages = []
        for message in messages:
            new_message = {
                "role": message["role"]
            }

            # Обработка обычного текстового сообщения
            if "content" in message and message["content"] is not None:
                new_message["text"] = message["content"]

            # Обработка tool_calls (если есть)
            if "tool_calls" in message:
                new_message["toolCallList"] = {
                    "toolCalls": [
                        {
                            "functionCall": {
                                "name": tool_call["function"]["name"],
                                "arguments": tool_call["function"]["arguments"]
                            }
                        }
                        for tool_call in message["tool_calls"]
                    ]
                }

            # Обработка function_call (устаревший формат OpenAI)
            elif "function_call" in message:
                new_message["toolCallList"] = {
                    "toolCalls": [{
                        "functionCall": {
                            "name": message["function_call"]["name"],
                            "arguments": message["function_call"]["arguments"]
                        }
                    }]
                }

            # Обработка результатов выполнения функций
            if "function_name" in message and "content" in message:
                new_message["toolResultList"] = {
                    "toolResults": [{
                        "functionResult": {
                            "name": message["function_name"],
                            "content": message["content"]
                        }
                    }]
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
        finish_reasons = {
            "ALTERNATIVE_STATUS_FINAL": "stop",
            "ALTERNATIVE_STATUS_TRUNCATED_FINAL": "length",
            "ALTERNATIVE_STATUS_CONTENT_FILTER": "content_filter",
            # "ALTERNATIVE_STATUS_PARTIAL": "incomplete",
            "ALTERNATIVE_STATUS_PARTIAL": None,
            "ALTERNATIVE_STATUS_UNSPECIFIED": "unknown",
            "ALTERNATIVE_STATUS_TOOL_CALLS": "tool_calls" 
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
        alternatives = chat_completion["result"]["alternatives"]
        choices = []
        current_time = int(time.time())
        i = 0
        for choice in alternatives:
            new_choice = {
                "index": i,
                "message": {
                    "role": choice["message"]["role"],
                },
                "logprobs": None,
                "finish_reason": await finish_reason_translation(choice["status"])
            }

            if "text" in choice["message"]:
                new_choice["message"]["content"] = choice["message"]["text"]
            else:
                new_choice["message"]["content"] = None

            if "toolCallList" in choice["message"]:
                tool_calls = []
                for idx, tool_call in enumerate(choice["message"]["toolCallList"]["toolCalls"]):
                    if "functionCall" in tool_call:
                        arguments = tool_call["functionCall"]["arguments"]
                        if isinstance(arguments, dict):
                            arguments = json.dumps(arguments)

                        new_tool_call = {
                            "id": f"call_{current_time}_{i}_{idx}",
                            "type": "function",
                            "function": {
                                "name": tool_call["functionCall"]["name"],
                                "arguments": arguments
                            }
                        }
                        tool_calls.append(new_tool_call)
                if tool_calls:
                    new_choice["message"]["tool_calls"] = tool_calls

            if "toolResultList" in choice["message"]:
                function_results = choice["message"]["toolResultList"]["toolResults"]
                if function_results:
                    new_choice["message"]["function_name"] = function_results[0]["functionResult"]["name"]
                    new_choice["message"]["content"] = function_results[0]["functionResult"]["content"]

            i += 1
            choices.append(new_choice)

        userhash = hashlib.md5(user_id.encode()).hexdigest() if user_id else "none"
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

        userhash = hashlib.md5(user_id.encode()).hexdigest() if user_id else "none"
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
    
async def embeddings_translation(embeddings: list, user_id: str, model: str, b64: bool = False):
    """
    Translate embeddings from YandexGPT to OpenAI format
    Input:
    - embeddings: list
    - user_id: str
    - model: str
    - b64: bool (default: False)
    Output:
    - new_embeddings: dict
    """
    try:
        i = 0
        prompt_tokens = 0
        total_tokens = 0
        data = []
        for embedding in embeddings:
            emb = embedding["embedding"]
            if b64:
                byte_array = b''.join(struct.pack('f', x) for x in emb)
                emb = base64.b64encode(byte_array).decode('utf-8')
            datum = {
                    "object": "embedding",
                    "embedding": emb,
                    "index": i
                }
            prompt_tokens += int(embedding['numTokens'])
            total_tokens += int(embedding['numTokens'])
            data.append(datum)
            i += 1

        new_embeddings = {
            "object": "list",
            "data": data,
            "model": f"{model}_{embeddings[0]['modelVersion'].replace('.', '-')}",
            "usage": {
                "prompt_tokens": prompt_tokens,
                "total_tokens": total_tokens
            }
        }
        return new_embeddings
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        raise Exception(f'Error in embeddings_translation: {e}')
    
async def delete_image(image_path: str):
    """
    Delete image
    Input:
    - image_path: str
    """
    if os.path.exists(image_path):
        os.remove(image_path)

async def image_generation_translation(data: dict, user_id: str, created_at: int, b64: bool = False):
    """
    Translate image generation from YandexGPT to OpenAI format
    Input:
    - data: dict
    - user_id: str
    - model: str
    - b64: bool (default: False)
    Output:
    - data: dict
    """
    try:
        image = data["response"]["image"] # base64 image
        response = {
            "created": created_at,
            "data": [{}]
        }
        if b64:
            response["data"][0]["b64_json"] = image
        else:
            if not os.path.exists("data/images"):
                os.makedirs("data/images")
            oid = data["id"]
            image_path = f"data/images/{oid}.jpg"
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image))
            response["data"][0]["url"] = f"{oid}.jpg"
            # schedule deleting in an hour
            asyncio.get_event_loop().call_later(3600, asyncio.create_task, delete_image(image_path))
        return response
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        raise Exception(f'Error in image_generation_translation: {e}')