# A Framework for Designing Generative Agents in Competitive Environments

------------
## Outline

1. [Project Summary](#project-summary)
2. [Game Environment](#game-environment)
3. [Installation](#installation)
4. [Quickstart](#quickstart)
5. [Results](#results)
6. [Project Wireframe](#project-wireframe)

-------------

## Project Summary

This repository accompanies our work in "[WORKING TITLE] A Framework for Designing Generative Agents in Competitive Environments". This work builds upon the great work of Joon Sung Park, Bodhisattwa Prasad Majumder, and others who have led the exploration of using LMs as generative agents. We develop a framework to extend prior works to new environments, namely competitive game environments that require agent collaboration, deception, and strategic planning. We hope to answer the following questions that fall into two categories: 

[THESE QUESTIONS ARE IN PROGRESS]
1. Agent performance and behavior:
  * how do generative agents perform in competitive environments?
  * What factors (such as group power dynamics or internal personality) influence agent performance and are these influences consistent across trials?

2. Agent goal setting and achievement:
  * Can we develop a better understanding of how generative agents process and develop goals?
  * How quickly are intermediate goals met and are agent actions consistent with prior planning?

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
    "organizations": [
        {"Penn":
            {"OPENAI_API_KEY": "sk-..."}
        },
        {"Helicone":
            {"OPENAI_API_KEY": "sk-...",
             "HELICONE_BASE_URL": "https://..."}
        }
    ]
}
```

-------------

## Quickstart

* point to `SurvivorWorld.build_game()`

-------------

## Results

* TBA

-------------

## Project Wirefraame



