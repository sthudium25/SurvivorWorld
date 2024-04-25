# A Framework for Designing Generative Agents in Competitive Environments

------------
## Outline

1. [Project Summary](#project-summary)
2. [Game Environment](#game-environment)
3. [Installation](#installation)
4. [Quickstart](#quickstart)
5. [Results](#results)
6. [Repo Directory](#repo-directory)

-------------

## Project Summary

This repository accompanies our work, "[WORKING TITLE] A Framework for Designing Generative Agents in Competitive Environments". This work builds upon the great work of Joon Sung Park, Bodhisattwa Prasad Majumder, and others who have led the exploration of using LMs as generative agents. We develop a framework to extend prior works to new environments, namely competitive game environments that require agent collaboration, deception, and strategic planning. We hope to answer the following questions that fall into two categories: 

1. Agent Persona:
  * Performance and behaviour depending on agent’s persona

2. Goal and Theory of Mind Architecture:
  * Performance with goal archtecture (e.g. without inference over relationships in the game, do goals become less directed toward interaction with other agents?)
  * Performance with Theory of Mind (impressions) architecture
  * Performance with both architectures
  * Preference of a certain priority level of goal by NPC and their completion rates

-------------

## Game Environment

We provide a sandbox environment in which all gameplay experiments were conducted. This sandbox is built upon a simple text-base adventure game created for UPenn CIS 7000 - Interactive Fiction by Dr. Chris Callison-Burch of UPenn and James Dennis [Affiliation??].

- - Discussion of game state set up?

-------------

## Installation

### Create virtual environment: 

It is highly recommended that you create a virtual environment in which to install the package dependencies.
The commands below create a new directory to store the package, make a new environment, and activate it.

```bash
mkdir <my_folder>
cd <my_folder>
python3 -m venv "venv-name"  # optionally hide the environment by naming it ".venv-name"
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

This package is heavily reliant upon calls to the OpenAI API, so you must add your key or keys to your configuration file. Within the project root, create a JSON file with the following structure; any API keys should be added to the "organizations" list with the organization name as a key and at minimum a sub-dict of {"OPENAI_API_KEY": `<your_key>`}. Optionally, you can add a custom base url if your organization requires it. 

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

* point to `SurvivorWorld.build_game()`

-------------

## Results

* TBA

-------------

## Repo Directory

To assist with navigation and readability of the code in this project, below is an breif description of the major components. Look within the `text_adventure_games` folder.

### Top-level interaction 
1. Game setup files...

### Environment and Game Engine
1. `games.py`: The Game class keeps track of the state of the world, and describes what the player sees as they move through different locations.
   * This class is extended to implement, `SurvivorGame`, a round and tick based system that handles game details specific to Survivor.
   * To extend this engine to your own game, you can do the same. Modifying the `game_loop` and `is_game_over` methods allows for customization of your game rules.

2. `parsing.py`: The parser is the module that handles the natural language understanding in the game.
   * Several `GptParser`s allow mapping of a wide range of natural language statements onto the valid action space.

### Agent
