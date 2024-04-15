import logging
import re
import time
from typing import Callable, Dict
import openai
import tiktoken
from types import SimpleNamespace

# local imports
from ..utils.general import set_up_openai_client, enumerate_dict_options

logger = logging.getLogger(__name__)

class GptCallHandler:
    """
    A class to make calls to GPT more uniform.
    User can pass desired OpenAI kwargs (right now just the basic ones) to set up a client and model params.
    Then use the "generate" method to initiate a call to GPT with error handling and retries

    Returns:
        _type_: _description_
    """
    
    DEFAULT_API_ORG = "Helicone"

    def __init__(self, kwargs: Dict, max_retries: int = 5):
        self.args = SimpleNamespace(**kwargs)
        self._set_default_args()
        self.max_retries = max_retries

    def _set_default_args(self):
        # set up a client
        if not hasattr(self.args, "client"):
            if not hasattr(self.args, "org"):
                self.args.client = set_up_openai_client(self.DEFAULT_API_ORG)
            else:
                self.args.client = set_up_openai_client(self.args.org)
        # set the model params
        if not hasattr(self.args, "model"):
            self.args.model = "gpt-4"
        if not hasattr(self.args, "temperature"):
            self.args.temperature = 1
        if not hasattr(self.args, "max_tokens"):
            self.args.max_tokens = 256
        if not hasattr(self.args, "top_p"):
            self.args.top_p = 0.75
        if not hasattr(self.args, "frequency_penalty"):
            self.args.freqency_penalty = 0
        if not hasattr(self.args, "presence_penalty"):
            self.args.presence_penalty = 0

    def generate(self, func: Callable) -> str:
        """
        A wrapper for making a call to OpenAI API.
        It expects a function as an argument that should produce the messages argument.        

        Args:
            func (Callable): _description_

        Returns:
            str: _description_
        """
        # Generate messages
        messages = func()

        i = 0
        while i < self.max_retries:
            try:
                response = self.args.client.chat.completions.create(
                    model=self.args.model,
                    messages=messages,
                    temperature=self.args.temperature,
                    max_tokens=self.args.max_tokens,
                    top_p=self.args.top_p,
                    frequency_penalty=self.args.frequency_penalty,
                    presency_penalty=self.args.presence_penalty
                )
            except (RuntimeError,
                    openai.error.RateLimitError,
                    openai.error.ServiceUnavailableError, 
                    openai.error.APIError, 
                    openai.error.APIConnectionError) as e:
                # log the error; should go to an error/warning specific log
                logger.error("GPT Error: {}".format(e)) 
                time.sleep(1)
                continue
            else:
                return response.choices[0].message.content
        

# Alternatively, heres a basic wrapper method to catch OpenAI related errors
def gpt_call_wrapper(gpt_call: Callable, retries=5):
    i = 0
    while i < retries:
        try:
            response = gpt_call()
        except (RuntimeError,
                openai.error.RateLimitError,
                openai.error.ServiceUnavailableError, 
                openai.error.APIError, 
                openai.error.APIConnectionError) as e:
            # log the error; should go to an error/warning specific log
            logger.error("GPT Error: {}".format(e)) 
            time.sleep(1)
            continue
        else:
            return response.choices[0].message.content


def gpt_get_summary_description_of_action(statement, client, model, max_tokens):

    system = "Construct a sentence out of the following information."
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": statement}]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=1,
        max_tokens=max_tokens,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0
    )

    summary_statement = response.choices[0].message.content
    return summary_statement


def gpt_get_action_importance(statement: str, client=None, model: str = "gpt-4", max_tokens: int = 10):

    if not client:
        client = set_up_openai_client("Helicone")

    system = "Gauge the importance of the provided sentence on a scale from 1 to 10, where 1 is mundane and 10 is critical."
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": statement}]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=1,
        max_tokens=max_tokens,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0
    )

    importance_str = response.choices[0].message.content
    pattern = r"\d+"
    matches = re.findall(pattern, importance_str)
    if matches:
        # Take the first number that it gave us
        for match in matches:
            try:
                return int(match)
            except ValueError:
                continue
        return None
    return None


def gpt_pick_an_option(instructions, options, input_str):
    """
    CREDIT: Dr. Chris Callison-Burch (UPenn)
    This function calls GPT to choose one option from a set of options.
    Its arguments are:
    * instructions - the system instructions
    * options - Dict[option_descriptions: option_names]
    * input_str - the user input which we are trying to match to one of the options

    The function generates an enumerated list of option descriptions
    that are shown to GPT. It then returns a number (which I match with a
    regex, in case it generates more text than is necessary), and then
    returns the option name.
    """
    # TODO: Need to improve client management throughout the package
    # Set up client
    client = set_up_openai_client("Helicone")

    choices_str, options_list = enumerate_dict_options(options)

    # Call the OpenAI API
    response = client.chat.completions.create(
        model='gpt-4',
        messages=[
            {
                "role": "system",
                "content": "{instructions}\n\n{choices_str}\nReturn just the number.".format(
                    instructions=instructions, choices_str=choices_str
                ),
            },
            {"role": "user", "content": input_str},
        ],
        temperature=1,
        max_tokens=256,
        top_p=0,
        frequency_penalty=0,
        presence_penalty=0,
    )
    content = response.choices[0].message.content

    # Use regular expressions to match a number returned by OpenAI and select that option.
    pattern = r"\d+"
    matches = re.findall(pattern, content)
    if matches:
        index = int(matches[0])
        if index >= len(options_list):
            return None
        option = options_list[index]
        return options[option]
    else:
        return None


def limit_context_length(history, max_tokens, max_turns=1000, tokenizer=None, keep_most_recent=True):
    """
    This method limits the length of the command_history 
    to be less than the max_tokens and less than max_turns. 
    The least recent messages are disregarded from the context unless
    keep_most_recent is changed to False. This function is non-destructive
    and doesn't modify command_history.

    Args:
        history (_type_): _description_
        max_tokens (_type_): _description_
        max_turns (int, optional): _description_. Defaults to 1000.
        tokenizer (_type_, optional): _description_. Defaults to None.
        keep_most_recent (bool, optional): If True, trim from the beginning values. 

    Raises:
        TypeError: _description_
        TypeError: _description_

    Returns:
        _type_: _description_
    """
    total_tokens = 0
    limited_history = []
    if not tokenizer:
        tokenizer = tiktoken.get_encoding("cl100k_base")
    if not isinstance(history, list):
        raise TypeError("history must be a list, not ", type(history))
    
    if len(history) > 0:
        if isinstance(history[0], dict):
            # this indicates that we're parsing ChatMessages, so extract the "content" and "role" strings
            # pad with 3 tokens and include both content & role
            extract = lambda x: get_prompt_token_count(content=x["content"], role=x["role"], pad_reply=False, tokenizer=tokenizer)
            
            # each reply carries 3 tokens via "<|start|>assistant<|message|>" that need to be added once
            total_tokens += 3
        elif isinstance(history[0], str):
            # this indicates that we're parsing a list of strings
            extract = lambda x: len(tokenizer.encode(x))
        else:
            raise TypeError("Elements in history must be either dict or str")
        
    # reverse the list if we are keeping only the most recent items
    if keep_most_recent:
        history.reverse()

    for message in history:
        msg_tokens = extract(message)
        
        if total_tokens + msg_tokens > max_tokens:
            break
        total_tokens += msg_tokens
        limited_history.append(message)
        if len(limited_history) >= max_turns:
            break

    # reverse the new list (back to normal) if we are keeping only the most recent items
    if keep_most_recent:
        limited_history.reverse()

    return list(limited_history)


def get_prompt_token_count(content=None, role=None, pad_reply=False, tokenizer=None):
    """
    This method retrieves the token count for a given prompt.
    It takes into consideration the content/role structure
    utilized by GPT's API.

    Args:
        content (str or list of strings): the prompt content; if passing
                                          a list of strings, this returns
                                          only the token count of the list
                                          (not accounting for any padding)
        role (str): the prompt role; if None, it is processed without the
                    GPT message padding - essentially just a plain token
                    counter if pad_reply is False
        pad_reply (bool): True adds a padding to account for GPT's reply
                          being primed with <|start|>assistant<|message|>.
                          GPT only adds one reply primer for the entire
                          collective messages given as input. Thus, this
                          defaults to False to avoid repeatedly
                          accounting for the reply primer in each message
                          in the larger passed messages. It should only
                          be set to true in the final message given in
                          GPT's prompt.
        tokenizer (_type_, optional): _description_. Defaults to None.

    Raises:
        TypeError: _description_
        TypeError: _description_

    Returns:
        int: number of tokens
    """

    if not content:
        return 0
    if content is not None and not isinstance(content, str) and not isinstance(content, list):
        raise TypeError("content must be a string or list, not ", type(content))
    if content is not None and isinstance(content, list) and (len(content) != 0 and not isinstance(content[0], str)):
        raise TypeError("content list must contain strings, not ", type(content[0]))
    if role is not None and not isinstance(role, str):
        raise TypeError("role must be a string, not ", type(role))
    
    if not tokenizer:
        tokenizer = tiktoken.get_encoding("cl100k_base")

    # initialize token count to 0
    token_count = 0

    # if accounting for GPT's reply being primed with <|start|>assistant<|message|>, add 3
    if pad_reply:
        token_count += 3

    # if checking string message content
    if content and isinstance(content, str):
        token_count += len(tokenizer.encode(content))

    # if checking list of strings message content
    elif content and isinstance(content, list):
        for c in content:
            token_count += len(tokenizer.encode(c))

    # if checking message role
    if role:
        # pad messages with 3 tokens to account for GPT's content/role JSON structure
        token_count += 3
        token_count += len(tokenizer.encode(role))

    return token_count
