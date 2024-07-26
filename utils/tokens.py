#!/usr/bin/env python3

import json
import uuid
import time

def get_tokens(path='./data/tokens.json'):
    """
    Load tokens from file.
    Example of JSON file:
        {
            "1": {
                "token": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "timestamp": "2024-01-01 00:00:00"
            },
        }
    """
    try:
        with open(path, 'r') as f:
            tokens_json = json.load(f)
            tokens = {v['token']: k for k, v in tokens_json.items()}
        return tokens
    except FileNotFoundError:
        raise FileNotFoundError('Tokens file not found, generate tokens first with `python3 utils/tokens.py`.')
    except Exception as e:
        raise Exception(f'An error occurred while loading tokens: {e}')

def generate_tokens(number, interactive=False):
    """
    Generate new tokens and append them to the tokens file.
    Example of JSON file:
        {
            "1": {
                "token": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "timestamp": "2024-01-01 00:00:00"
            },
        }
    """
    try:
        # Load tokens from file if it exists
        try:
            with open('./data/tokens.json', 'r') as f:
                tokens_json = json.load(f)
        except FileNotFoundError:
            tokens_json = {}

        if interactive:
            if len(tokens_json) == 0:
                print('No tokens found in file.')
            else:
                print(f'Loaded {len(tokens_json)} tokens from file.')

        # Generate new tokens and append them to the tokens file
        for i in range(number):
            token = str(uuid.uuid4())
            token = f'sk-y2o-{token}'
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            tokens_json[len(tokens_json)+1] = {
                "token": token,
                "timestamp": timestamp
            }
            if interactive:
                print(f'* New token: {token}')

        # Write tokens to file
        with open('./data/tokens.json', 'w') as f:
            json.dump(tokens_json, f, indent=4)
            if interactive:
                print(f'Wrote {number} new tokens to file.')
        return True
    except Exception as e:
        if interactive:
            print(f'An error occurred: {e}')
        return False

if __name__ == '__main__':
    number = input("How many tokens do you want to generate? (write a one number): ")
    try:
        number = int(number)
    except ValueError:
        print("Please write a valid number. Exiting.")
        exit(1)
    generate_tokens(number, interactive=True)
    print("Done. Please restart the server.")