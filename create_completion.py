#!/usr/bin/env python3

import sys
import os
import json
import requests
import configparser

STREAM = False

# Get config dir from environment or default to ~/.config
CONFIG_DIR = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
API_KEYS_LOCATION = os.path.join(CONFIG_DIR, 'openaiapirc')

api_base = ''
api_key = ''
api_version = ''
api_model = ''

# Read the organization_id and secret_key from the ini file ~/.config/openaiapirc
# The format is:
# [openai]
# organization_id=<your organization ID>
# secret_key=<your secret key>

# If you don't see your organization ID in the file you can get it from the
# OpenAI web site: https://openai.com/organizations
def create_template_ini_file():
    """
    If the ini file does not exist create it and add the organization_id and
    secret_key
    """
    if not os.path.isfile(API_KEYS_LOCATION):
        with open(API_KEYS_LOCATION, 'w') as f:
            f.write('[openai]\n')
            f.write('api_base=\n')
            f.write('api_key=\n')
            f.write('api_version=\n')
            f.write('api_model=\n')

        print('OpenAI API config file created at {}'.format(API_KEYS_LOCATION))
        print('Please edit it and add your organization ID and secret key')
        print('If you do not yet have an organization ID and secret key, you\n'
               'need to register for OpenAI Codex: \n'
                'https://openai.com/blog/openai-codex/')
        sys.exit(1)


def initialize_openai_api():
    """
    Initialize the OpenAI API
    """
    # Check if file at API_KEYS_LOCATION exists
    create_template_ini_file()
    config = configparser.ConfigParser()
    config.read(API_KEYS_LOCATION)
    
    global api_base, api_key, api_version, api_model
    api_base = config['openai']['api_base'].strip('"').strip("'")
    api_key = config['openai']['api_key'].strip('"').strip("'")
    api_version = config['openai']['api_version'].strip('"').strip("'")
    api_model = config['openai']['api_model'].strip('"').strip("'")

def send_message(content):
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    data = {
        "messages": [{"role": "user", "content": content}]
    }
    url = api_base + "openai/deployments/" + api_model + "/chat/completions?api-version=" + api_version
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()

    return "Error:" + str(response.status_code) + " " + response.text


initialize_openai_api()

cursor_position_char = int(sys.argv[1])

# Read the input prompt from stdin.
buffer = sys.stdin.read()
# prompt_prefix = '#!/bin/zsh\n\n' + buffer[:cursor_position_char]
prompt_prefix = 'Please provide the corresponding shell command based on the description information, without explanation. Do not enter the command unless instructed to do so. The description information is as follows.\n\n'

response = send_message(prompt_prefix + buffer[:cursor_position_char])

# {'id': 'chatcmpl-78i8c7ziDERbAyQfGZY9gux8f7eKA', 'object': 'chat.completion', 'created': 1682310646, 'model': 'gpt-4', 'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'ls -lh'}}], 'usage': {'completion_tokens': 4, 'prompt_tokens': 49, 'total_tokens': 53}}

if STREAM:
    while True:
        next_response = next(response)
        print("next_response:", next_response)
        print("        next_response['choices'][0]['finish_reason']:",         next_response['choices'][0]['finish_reason'])
        completion = next_response['choices'][0]['message']['content']
        print("completion:", completion)
else:
    completion_all = response['choices'][0]['message']['content']
    completion_list = completion_all.split('\n')
    if completion_all[:2] == '\n\n':
        print('\n' + completion_all)
    elif completion_list[0]:
        print('\n' + completion_list[0])
    elif len(completion_list) == 1:
        print('')
    else:
        print('\n' + completion_list[1])
