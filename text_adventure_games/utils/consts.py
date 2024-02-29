"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: consts.py
Description: get/set any necessary API keys, constant values, etc.
"""


import os


def get_openai_api_key(path='.'):
    """
    Get the OpenAI API key from config file.

    Args:
        path (str, optional): path to location of config file. Defaults to '.'.
    """
    pass

def get_assets_path():
    asset_path = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "assets"))
    return asset_path

# TODO: set up any global variables
# TODO: I want a global list of the default archetype profiles we have access to in ../assets
