from . import experiment_game

import sys
sys.path.insert(0, "../")
sys.path.insert(0, "../..")
from SurvivorWorld.text_adventure_games.parsing import GptParser3
import experiment_game
import openai

def run_experiment():
    game = experiment_game.build_experiment(experiment_name="architecture", experiment_id=34, max_ticks=6)
    game.give_hints = True
    parser = GptParser3(game, verbose=False)
    game.set_parser(parser)
    parser.refresh_command_list()

    try:
        game.game_loop()
    except openai.APIConnectionError:
        print("Could not connect to OpenAI API")
    finally:
        # This will run once the simulation has finished or if an error occurs.
        # We can probably still use the partial data even though it isn't ideal
        game.save_simulation_data()


if __name__ == '__main__':
    run_experiment()