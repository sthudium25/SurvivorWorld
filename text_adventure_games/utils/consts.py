"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: consts.py
Description: get/set any necessary API keys, constant values, etc.
"""

import json
import os

def get_root_dir():
    root = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir))
    return root

def get_config_file():
    config_path = os.path.join(get_root_dir(), "config.json")
    if not os.path.exists(config_path):
        print("visible config not found, trying invisible option")
        config_path = os.path.join(get_root_dir(), ".config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError("No config file found. Store your OpenAI key in a variable \"OPENAI_API_KEY\".")

    with open(config_path, 'r') as cfg:
        config_vars = json.load(cfg)
    return config_vars

def get_openai_api_key(organization):
    # TODO: Specify Helicone vs Personal API key
    """
    Get the OpenAI API key from config file.

    Args:
        organization (str, optional): The organizational API KEY to get
    """
    
    config_vars = get_config_file()
    
    for org in config_vars["organizations"]:
        if organization in org:
            api_key = org[organization].get("OPENAI_API_KEY", None)
            # print(f"{api_key[:5]}...")
            return api_key
    
    # If no matches found for org
    print(f"{organization} not found in list of valid orgs. You may not have a key set up for {organization}.")
    return None

def get_helicone_base_path(organization="Helicone"):
    # TODO: Specify Helicone vs Personal API key
    """
    Get the BASE URL for HELICONE from config file.

    Args:
        organization (str, optional): The organizational base url to get
    """
    if organization != "Helicone":
        raise ValueError("Method only valid for organization == 'Helicone'.")
    
    config_vars = get_config_file()
    
    for org in config_vars["organizations"]:
        if organization in org:
            base_url = org[organization].get("HELICONE_BASE_URL", None)
            return base_url
    
    # If no matches found for org
    print(f"{organization} not found in list of valid orgs. You may not have a base url set up for {organization}.")
    return None
    

def get_assets_path():
    asset_path = os.path.join(get_root_dir(), "assets")
    return asset_path

# TODO: set up any global variables
# TODO: I want a global list of the default archetype profiles we have access to in ../assets
