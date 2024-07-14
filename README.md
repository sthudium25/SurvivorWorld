[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-310/)

# A Framework for Designing Generative Agents in Competitive Environments

------------
## Outline

1. [Project Summary](#project-summary)
2. [Game Environment](#game-environment)
3. [Installation](#requirements-and-installation)
4. [Quickstart](#quickstart)
5. [Repo Directory](#repo-directory)

-------------

## Project Summary

This repository accompanies our work, "Outwit, Outplay, Out-Generate: A Framework for Designing Strategic Generative Agents in Competitive Environments". This project builds upon the great work of Joon Sung Park, Bodhisattwa Prasad Majumder, and others who have led the exploration of using LMs as generative agents. We expand the congitive architecture driving the generative agents, providing new modules that tailor the agents to perform in competitive game environments requiring agent collaboration, deception, and strategic planning. We hope to answer the following questions that fall into two categories: 

1. Agent Persona:
  * Performance and behaviour depending on agent’s persona

2. Goal and Theory of Mind Architecture:
  * Performance with goal archtecture (e.g. without inference over relationships in the game, do goals become less directed toward interaction with other agents?)
  * Performance with Theory of Mind (impressions) architecture
  * Performance with both architectures
  * Preference of a certain priority level of goal by NPC and their completion rates

-------------

## Game Environment

We provide a sandbox environment in which all gameplay experiments were conducted. This sandbox is built upon a simple text-base adventure game created for UPenn CIS 7000 - [Interactive Fiction](https://interactive-fiction-class.org/) by Dr. Chris Callison-Burch of UPenn and James Dennis.

`game_setup.py` contains the game configuration used for this project (the map and items). If you want to make your own map, create a new class that extends the `games.SurvivorGame`. You can then create new locations and override the `is_won()` method to specify your custom termination criteria. Alternatively, feel free to fork the project entirely and adjust the base class as you wish (try adding a human player to compete against the agents!). 

-------------

## Requirements and Installation

### Create virtual environment: 

It is highly recommended that you create a virtual environment in which to install the package dependencies.
The commands below create a new directory to store the package, make a new environment, and activate it.

NOTE: requires Python 3.10 or above.

```bash
mkdir <my_folder>
cd <my_folder>
python3.10 -m venv "venv-name"  # optionally hide the environment by naming it ".venv-name"
source venv-name/bin/activate
```

### Clone repo and install package [CHANGE git link if necessary]

Next, clone the repo, assuming you're in `<my_folder>`. The install line puts the package in "editable" mode, but you can omit that if you don't intend to develop the code further.

```bash
git clone https://github.com/sthudium25/SurvivorWorld.git
cd SurvivorWorld
pip install -e .
```

### Set up configuration file

This package is heavily reliant upon calls to the OpenAI API (NOTE: at the moment, it is not configured to work with other APIs), so you must add your key or keys to your configuration file. Within the project root, create a JSON file with the following structure; add a configuration for each API key you want to use under the "organizations" key. The subkeys for each organization should follow the OpenAI Client structure, which requires at minimum an API key, but also supports the following optional arguements: `api_key`, `organization`, `base_url`, `timeout`, `max_retries`, `default_headers`, `default_query`, and `http_client`. If you want to add any of these arguments, add them as a key: value pair under the appropriate organization.

Save this file as `config.json` or `.config.json` at the package root.

```json
{
    "organizations": {
        "Penn": {
            "api_key": "sk-..."
        },
        "Helicone": {
            "api_key": "sk-...",
            "base_url": "https://..."
        }
    }
}
```

-------------

## Quickstart

If you want to run a game with a spcific set of characters, add their Persona JSON files to a folder and place this folder in the `assets` directory. You can find examples in [`assets`](assets/). If you want GPT to generate these characters for you, then create a user-specified character skeleton, following the format shown [here](assets/character_skeletons); this should also be placed in the assets directory.

### Using `run_game.py`:

This script can take a number of argument that allow you to set up the game you wish to run. Below are the argument descriptions:

```text
positional arguments:
  experiment_method     Method of the experiment.
                        Supported: 'classic', 'exploration', 'personas'.
  experiment_name       Name of the experiment.
  experiment_id         ID of the experiment.
  personas_path         The full path to persona files you want to use or
                        their folder name within the assests folder.

options:
  -h, --help            show this help message and exit
  --num_characters NUM_CHARACTERS
                        The number of agents to create in the game (default:
                        4)
  --max_ticks MAX_TICKS
                        Maximum number of ticks per round (default: 6).
  --num_finalists NUM_FINALISTS
                        Number of finalists (default: 2).
  --architecture ARCHITECTURE
                        Type of architecture (default: 'A').
  --random_placement RANDOM_PLACEMENT
                        Should characters be placed randomly across the map?
                        (default: False)
```

For example, to set up a classic voting-based game of Survivor that has 8, randomly distributed characters, you could create 8 character personas and place these in `assets/classic_personas`. Then, assuming you're in the project directory, run:

```bash
python3.10 run_game.py "classic" "classic-survivor" 1 "classic-personas" --num_characters=8 --max_ticks=5 --random_placement=True
```

### From a Jupyter Notebook

To run the same game set-up from a notebook, place a new `.ipynb` in the `test` directory and run the following chunk:

```python
import sys
sys.path.insert(0, "../")
sys.path.insert(0, "../..")
from SurvivorWorld.text_adventure_games.parsing import GptParser3
from game_setup import build_classic

game = build_classic(experiment_name="classic-survivor", experiment_id=1, num_characters=8, max_ticks=4, personas_path="classic_personas", random_placement=True)
game.give_hints = True
parser = GptParser3(game, verbose=False)
game.set_parser(parser)
parser.refresh_command_list()

try:
    game.game_loop()
except openai.APIConnectionError:
    print("Could not connect to OpenAI API")
finally:
    game.save_simulation_data()
```

-------------

## Repo Directory

To assist with navigation and readability of the code in this project, below is an breif description of the major components. Look within the `text_adventure_games` folder.

### Top-level interaction 
1. `run_game.py` and `test/game_setup.py`: These files enables the user to set up game(s) via a CLI.

### Environment and Game Engine
1. `games.py`: The Game class keeps track of the state of the world, and describes what the player sees as they move through different locations.
   * This class is extended to implement, `SurvivorGame`, a round and tick based system that handles game details specific to Survivor.
   * To extend this engine to your own game, you can do the same. Modifying the `game_loop` and `is_game_over` methods allows for customization of your game rules.

2. `parsing.py`: The parser is the module that handles the natural language understanding in the game.
   * Several `GptParser`s allow mapping of a wide range of natural language statements onto the valid action space.
  
3. `actions/`: defines base actions that are interpreted by the game engine. Agents supply natural language descriptions of actions which are then parsed into valid game actions if possible.

4. `blocks/` and `things/`: define game state objects such as locations, items, and characters.

5. `utils/`: contains various utility functions. Importantly, defines a **custom logging module** that was used to collect data from agent simulations.

### Agent
1. `agent/`: defines agent congition modules including: **persona**, **impressions**, and **goals**.
   
2. `charaters.py`: defines a base Character class and extended GenerativeAgent class. The latter was used to power the agents described in the accompying manuscript. A third class, DiscoveryAgent, was also created, but not used in the experiments described here.
