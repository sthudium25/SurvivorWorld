import logging

# local imports
from .logging_setup import setup_logger


class CustomLogger():
    def __init__(self, experiment_name, sim_id):
        _, validated_id = setup_logger(experiment_name, sim_id)

        self.simulation_id = validated_id
        self.logger = logging.getLogger("survivor_global_logger")

    def get_logger(self):
        return self.logger
    
    def get_simulation_id(self):
        return self.simulation_id
