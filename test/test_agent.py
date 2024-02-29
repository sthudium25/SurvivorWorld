import pytest
from dotenv import load_dotenv, find_dotenv
from text_adventure_games import agent
from text_adventure_games.utils.gpt import gpt_agent
from text_adventure_games.utils import consts, general, setup_agent


@pytest.fixture
def load_key():
    load_dotenv(find_dotenv())

def test_get_base_facts(load_key):
    facts = setup_agent.get_or_create_base_facts(description="a barista from the southwestern United States",
                                                 make_new=False)
    
    assert facts == {'Name': 'Jacob Harrison',
                     'Age': 25,
                     'Likes': ['coffee brewing', 'indie music', 'baking', 'dogs', 'reading'],
                     'Dislikes': ['rude customers', 'early mornings', 'negativity', 'instant coffee'],
                     'Occupation': 'Barista',
                     'Home city': 'Philadelphia, Pennsylvania'}
