"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: consts.py
Description: get/set any necessary API keys, constant values, etc.
"""


import json
import os


def get_root_dir():
    root = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
    return root

def get_openai_api_key():
    # TODO: Specify Helicone vs Personal API key
    """
    Get the OpenAI API key from config file.

    Args:
        path (str, optional): path to location of config file. Defaults to '.'.
    """
    
    config_path = os.path.join(get_root_dir(), "env")
    if not os.path.exists(config_path):
        print("visible env not found, trying invisible option")
        config_path = os.path.join(get_root_dir(), ".env")
        if not os.path.exists(config_path):
            raise FileNotFoundError("No env file found. Store your OpenAI key in a variable \"OPENAI_API_KEY\".")

    with open(config_path, 'r') as cfg:
        config_vars = json.load(cfg)
    api_key = config_vars["OPENAI_API_KEY"]
    return api_key
    
    

def get_assets_path():
    asset_path =  os.path.join(get_root_dir(), "assets")
    return asset_path

# TODO: set up any global variables
# TODO: I want a global list of the default archetype profiles we have access to in ../assets
