"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: consts.py
Description: get/set any necessary API keys, constant values, etc.
"""

import json
import os
from os import PathLike
from typing import Union

def get_root_dir(n=2) -> Union[str, PathLike]:
    """
    With respect to this file (consts.py), get root directories n levels above.

    Args:
        n (int, optional): number of parents to climb. Defaults to 2.

    Returns:
        path: PathLike
    """
    path_components = [__file__] + [os.pardir] * n

    root = os.path.abspath(os.path.join(*path_components))
    # print(f"ROOT DIR: {root}")
    return root

# TODO: helper method for finding any dir or file in this project
# def find_path(name: Union[str, PathLike]) -> Union[str, PathLike]:
#     """
#     Given a name or path of a directory or file, discover its path within this project.

#     Args:
#         name (Union[str, PathLike]): _description_

#     Returns:
#         Union[str, PathLike]: _description_
#     """

def get_config_file():
    config_path = os.path.join(get_root_dir(n=3), "config.json")
    if not os.path.exists(config_path):
        print("visible config not found, trying invisible option")
        config_path = os.path.join(get_root_dir(n=3), ".config.json")
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
    org_config = config_vars.get("organizations", None).get(organization, None)
    
    if org_config:
        api_key = org_config.get("api_key", None)
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
    
    org_config = config_vars.get("organizations", None).get(organization, None)
    if org_config:
        base_url = org_config.get("base_url", None)
        return base_url
    
    # If no matches found for org
    print(f"{organization} not found in list of valid orgs. You may not have a base url set up for {organization}.")
    return None
    
def get_assets_path() -> Union[str, PathLike]:
    asset_path = os.path.join(get_root_dir(n=2), "assets")
    return asset_path

def get_custom_logging_path():
    logging_path = os.path.join(get_root_dir(n=1), "custom_logging")
    return logging_path

def get_output_logs_path():
    output_logs = get_root_dir(n=3)
    return output_logs

def validate_output_dir(fp, name, sim_id):
    overwrite = False
    if os.path.exists(fp):
        print()
        decision = check_user_input(name, sim_id)
        if not decision:
            print("Incrementing id...")
            new_log_path = os.path.join(get_output_logs_path(), f"logs/{name}-{sim_id+1}/")
            return validate_output_dir(new_log_path, name, sim_id+1)
        else:
            print("Overwriting log file is data...")
            print("The game data will be overwritten when you run `game.save_simulation_data()`")
            overwrite = True
            return overwrite, fp, sim_id
    else:
        return overwrite, fp, sim_id
    
def check_user_input(name, sim_id):
    p1 = f"It appears you've already saved data using '{name}-{sim_id}. Do you want to overwrite the data?"
    p2 = "Type 'y' or 'n'"
    decision = input(f"{p1}\n{p2}\n")
    if decision not in ["y", "n"]:
        return check_user_input()
    elif decision == "y":
        decision = input("Are you like REALLY sure you want to do this??? y or n\n")
        if decision == "y":
            return True
        else:
            return False
    else:
        return False
