"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: logging_setup.py
Description: create a logger that exists for the entire program.
             Any external library logging should be captured as well, though we don't care about this info.
"""
from typing import Union
from os import PathLike
import os
import json
import logging.config
import pathlib
from datetime import datetime as dt

# local imports
from ..consts import (get_root_dir,
                      get_custom_logging_path, 
                      get_output_logs_path)

def setup_logger(experiment_name: str, 
                 simulation_id: int, 
                 # other_exp_info: dict
                 ):
    # TODO: how do we want to track experiments and runs of the simulation?
    # NOTE: maybe all runs for a single experiment need to be logged to the same file? -- what would max file size be in this case?
    logging_path = get_custom_logging_path()
    logger_config = pathlib.Path(os.path.join(logging_path, "logger_config.json"))
    if not os.path.exists(logger_config):
        raise FileNotFoundError("you must set up a logging configuration file to extract data from the simulation.")
    with open(logger_config, 'r') as log_cfg:
        config = json.load(log_cfg)

    # TODO: update this as needed to maintain 1 log per run or 1 log per experiment
    experiment_logfile_name = os.path.join(get_output_logs_path(), f"logs/sim_{experiment_name}-{simulation_id}.jsonl")
    
    # NOTE: keeping this static
    global_warnings_logfile = os.path.join(get_output_logs_path(), "logs/warnings/project_warnings.jsonl")

    set_logs_paths(config, experiment_logfile_name, global_warnings_logfile)
    
    logging.config.dictConfig(config)

    logger = logging.getLogger("survivor_global_logger")
    return logger

def set_logs_paths(logs_config, 
                   experiment_log_path: Union[str, PathLike], 
                   global_warnings_logfile: Union[str, PathLike]) -> None:
    """
    Set the log paths in the dictConfig file.
    Ensures log directories exist, else creates them.
    Assumes that path begins with the "logs" directory.

    Args:
        experiment_log_path (PathLike): The destination of data extracted from this simulation
    """
    try:
        logs_config["handlers"]["file_json"]["filename"] = experiment_log_path
        logs_config["handlers"]["warning_json"]["filename"] = global_warnings_logfile
    except KeyError:
        print('Your log config file structure is incorrect. Expects to set filename with: config["handlers"][<handler_name>]["filename"]')
        raise Exception("Fix your log config file before running a simulation.")
    
    # Check and create the necessary file structure for the experiment and global warning logs
    root = get_root_dir(n=3)
    dir_paths = map(os.path.dirname, 
                    [os.path.join(root, experiment_log_path), os.path.join(root, global_warnings_logfile)])
    
    for log_dir in dir_paths:
        if not os.path.exists(log_dir):
            # print("couldn't find path: ", dir_path)
            os.makedirs(log_dir)
