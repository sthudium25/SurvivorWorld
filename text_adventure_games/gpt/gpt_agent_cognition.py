"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: gpt_agent.py
Description: Methods that access the OPENAI API and make a call to GPT
"""

from typing import List
from kani import Kani
from kani.engines.openai import OpenAIEngine

# local imports
from ..utils.consts import get_openai_api_key

# TODO: maybe a place to set up a customized Kani?
# class ReflectionKani(Kani):
#     def __init__(self, *args, **kwargs):
#         super.__init__(*args, **kwargs)


def get_top_reflection_questions(character, observations: List[str], model="gpt-3.5-turbo"):
    api_key = get_openai_api_key()
    engine = OpenAIEngine(api_key, model=model)
    system_prompt = """You """
    ai = Kani(engine)