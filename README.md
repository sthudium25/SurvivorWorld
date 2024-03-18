# SurvivorWorld

This repository accompanies our work in "[WORKING TITLE] A Framework for Designing Generative Agents in Competitive Environments". This work builds upon the great work of Joon Sung Park, Bodhisattwa Prasad Majumder, and others who have led the exploration of using LMs as generative agents. We develop a framework to extend prior works to new environments, namely competitive game environments that require agent collaboration, deception, and strategic planning. We hope to answer the following questions that fall into two categories: 

[THESE QUESTIONS ARE IN PROGRESS]
1. Agent performance and behavior:
  * how do generative agents perform in competitive environments?
  * What factors (such as group power dynamics or internal personality) influence agent performance and are these influences consistent across trials?

2. Agent goal setting and achievement:
  * Can we develop a better understanding of how generative agents process and develop goals?
  * How quickly are intermediate goals met and are agent actions consistent with prior planning?



The base A simple text-base adventure game created for UPenn CIS 7000 - Interactive Fiction 
The game builds off the framework developed by Dr. Chris Callison-Burch of UPenn and James Dennis.
Their work is contained within `text-adventure-games`.
SurvivorWorld is in no way related to CBS.

**SurvivorWorld** is an interactive text game simulating a real game of Survivor! Upon the success of the Survivor franchise and an epic Season 45, we wanted to create an experience where everyone can play the famous reality game! We are both big fans of this show, and thought it would make a great interactive game.

You are a contestant in Survivor 45.5. It is the final 4, meaning there are 3 other players left in the game, and things aren't looking too good! If you want to survive the next tribal council, you will need a hidden immunity idol! In order to win the game, you must find this idol and not perish in the dangerous island!

For future versions of this game, we want to implement voting and alliances mechanics, where you can win other NPCs over and get them to vote with you. We can also add challenges, a time or episodic element, where decisions that you make affect who is left and the game world, until you become the sole survivor, or get voted out. Eventually, we hope to implement these NPCs as intelligent agents, creating a challenging social puzzle for human (or AI!) players.
