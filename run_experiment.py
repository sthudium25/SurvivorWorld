from typing import TYPE_CHECKING
import argparse
import sys

if TYPE_CHECKING:
    from text_adventure_games.games import Game
from text_adventure_games.parsing import GptParser3
from test.experiment_game_runner import build_exploration, build_classic

def main():
    args = parse_args()
    experiment_game = setup(args)
    run(experiment_game)

def parse_args():
    parser = argparse.ArgumentParser(description="Run an experiment with specified parameters.")

    # Required arguments
    parser.add_argument("experiment_method", type=str, choices=['classic', 'exploration', 'personas'], help="Method of the experiment. Supported: 'classic', 'exploration', 'personas'.")
    parser.add_argument("experiment_name", type=str, help="Name of the experiment.")
    parser.add_argument("experiment_id", type=int, help="ID of the experiment.")
    parser.add_argument("personas_path", type=str, help="The full path to persona files you want to use or their folder name within the assests folder.")

    # Optional arguments with default values
    parser.add_argument("--num_characters", type=int, default=4, help="The number of agents to create in the game (default: 4)")
    parser.add_argument("--max_ticks", type=int, default=6, help="Maximum number of ticks per round (default: 6).")
    parser.add_argument("--num_finalists", type=int, default=2, help="Number of finalists (default: 2).")
    parser.add_argument("--architecture", type=str, default="A", help="Type of architecture (default: 'A').")
    parser.add_argument("--random_placement", type=bool, default=False, help="Should characters be placed randomly across the map? (default: False)")

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

def setup(args) -> "Game":
    print("Setting up the game")
    game_created = False
    game_args = {
        "experiment_name": args.experiment_name,
        "experiment_id": args.experiment_id,
        "max_ticks": args.max_ticks,
        "num_finalists": args.num_finalists,
        "personas_path": args.personas_path,
        "random_placement": args.random_placement
    }
    if args.experiment_method == "classic":
        game_args["num_characters"] = args.num_characters
        game = build_classic(**game_args)
    if args.experiment_method == "exploration":
        game_args["architecture"] = args.architecture
        game = build_exploration(**game_args)
        game_created = True
    
    if game_created:
        game.give_hints = True
        parser = GptParser3(game, verbose=False)
        game.set_parser(parser)
        parser.refresh_command_list()
        return game

def run(game):
    try:
        game.game_loop()
    except Exception as e:
        print(e)
    finally:
        # This will run once the simulation has finished or if an error occurs.
        # We can probably still use the partial data even though it isn't ideal
        game.save_simulation_data()

if __name__ == "__main__":
    print("Entering main")
    main()
