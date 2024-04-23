from dataclasses import asdict, dataclass, field
import json
import logging
import os
import re
import time
from typing import ClassVar
import openai
import tiktoken

# local imports
from ..utils.general import enumerate_dict_options
from ..utils.consts import get_config_file, get_assets_path
from ..assets.prompts import gpt_helper_prompts as hp

logger = logging.getLogger(__name__)


class ClientInitializer:

    VALID_CLIENT_PARAMS = set(["api_key", "organization", "base_url", "timeout", "max_retries", 
                               "default_headers", "default_query", "http_client"])

    def __init__(self):
        self.load_count = 0
        self.api_info = self._load_api_keys()
        self.clients = {}

    def _load_api_keys(self):
        self.load_count += 1
        configs = get_config_file()
        return configs.get("organizations", None)
    
    def get_client(self, org):
        try:
            org_client = self.clients[org]
            return org_client
        except KeyError:
            self.set_client(org)
            return self.get_client(org)
    
    def set_client(self, org):
        if not self.api_info:
            raise AttributeError("api_info may not have been initialized correctly")
        try:
            org_api_params = self.api_info[org]
        except KeyError:
            raise ValueError(f"You have not set up an api key for {org}. Valid orgs are: {list(self.api_info.keys())}")
        else:
            valid_api_params = self._validate_client_params(org_api_params)
            self.clients[org] = openai.OpenAI(**valid_api_params)
    
    def _validate_client_params(self, params):
        # remove any invalid parameters they tried to add
        validated_params = {}
        if "api_key" not in params:
            raise ValueError("'api_key' must be included in your config.")
        for k, v in params.items():
            if k not in self.VALID_CLIENT_PARAMS:
                print(f"{k} is not a valid argument to openai.OpenAI(). Removing {k}.")
            else:
                validated_params[k] = v
        return validated_params


@dataclass
class GptCallHandler:
    """
    A class to make calls to GPT more uniform.
    User can pass desired OpenAI kwargs (right now just the basic ones) to set up a client and model params.
    Then use the "generate" method to initiate a call to GPT with error handling and retries

    Returns:
        _type_: _description_
    """
    # Class variables
    model_limits: ClassVar = field(init=False)
    client_handler: ClassVar = ClientInitializer()

    # Instance variables
    api_key_org: str = "Helicone"
    model: str = "gpt-4"
    max_tokens: int = 256
    temperature: float = 1.0
    top_p: float = 0.75
    frequency_penalty: float = 0
    presence_penalty: float = 0
    max_retries: int = 5
    # client: openai.types.Client = field(init=False)
    # Include if context limit checks done within this class
    # tokenizer: Any = field(default_factory=lambda: tiktoken.get_encoding("cl100k_base"))
    
    def __post_init__(self):
        self.original_params = self._save_init_params()
        self.client = self.client_handler.get_client(self.api_key_org)
        self.model_limits = self._load_model_limits()
        self._set_requested_model_limits()

    def _save_init_params(self):
        return asdict(self)

    def _load_model_limits(self):
        assets = get_assets_path()
        full_path = os.path.join(assets, "openai_model_limits.json")
        try:
            with open(full_path, "r") as f:
                limits = json.load(f)
        except IOError:
            print(f"Bad path. Couldn't find assest at {full_path}")
            # TODO: what to do in this case?
        else:
            return limits
        
    def _set_requested_model_limits(self):
        """
        Get the input/output limits for the requested model.
        Default to GPT-4 limits if not found.
        """
        if self.model_limits:
            limits = self.model_limits.get(self.model, None)
            self.model_context_limit = limits.get("context", 8192)
            self.max_tokens = min(self.max_tokens, limits.get("context", 8192))
        else:
            self.model_context_limit = 8192
            self.max_tokens = min(self.max_tokens, 8192)

    def update_params(self, **kwargs):
        for param, new_val in kwargs.items():
            if hasattr(self, param):
                setattr(self, param, new_val)
    
    def reset_defaults(self):
        # Reset the parameters to the original values
        for param, value in self.original_params.items():
            setattr(self, param, value)
        
    def generate(self, 
                 system: str = None, 
                 user: str = None, 
                 messages: list = None) -> str:
        """
        A wrapper for making a call to OpenAI API.
        It expects a function as an argument that should produce the messages argument.        

        Args:
            func (Callable): _description_

        Returns:
            str: _description_
        """
        if system and user:
            # Generate messages
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        elif not messages or not isinstance(messages, list):
            raise ValueError("You must supply 'system' and 'user' strings or a list of ChatMessages in 'messages'.")

        i = 0
        while i < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty
                )
                return response.choices[0].message.content
            except openai.RateLimitError as e:
                # use exponential backoff
                # openai requests 0.6ms delay so a max of 2s should be plenty
                duration = min(0.1**i, 2)
                print(f"rate limit reached, sleeping {duration} seconds")
                time.sleep(duration)
                self._log_gpt_error(e)
                continue
            except openai.BadRequestError as e:
                success, info = self._handle_BadRequestError(e)
                self._log_gpt_error(e)
                return success, info  # return to the module for redoing the message creation?
            except openai.ServiceUnavailableError as e:
                # This model or the servers may be down...so wait a while?
                self._handle_ServiceUnavailableError(e)
                self._log_gpt_error(e)
                continue
            except openai.APIConnectionError as e:
                # Adding some helpful prints but will still raise the error
                self._handle_APIConnectionError(e)
                self._log_gpt_error(e)

    def _log_gpt_error(self, e):
        logger.error("GPT Error: {}".format(e))                 
        
    def _handle_BadRequestError(self, e):
        if hasattr(e, 'response'):
            error_response = e.response.json()
            if "error" in error_response:
                error = error_response.get("error")
                if error.get("code") == "context_length_exceeded":
                    msg = error.get("message")
                    matches = re.findall(r"\d+", msg)
                    if matches and len(matches) > 1:
                        model_max = int(matches[0])
                        input_token_count = int(matches[1])
                        diff = input_token_count - model_max
                        return False, diff
        return False, None
    
    def _handle_APIConnectionError(self, e):
        print("APIConnectionError encountered:\n")
        print(e)
        print("Did you set your API key or organization base URL incorrectly?")
        print("This could also be raised by a poor internet connection.")
        raise e
    
    def _handle_ServiceUnavailableError(self, e):
        print("OpenAI Service Error encountered:\n")
        print(e)
        print("\nYou may want to stop the run and try later. Otherwise, waiting 2 minutes...")

        total_wait_time = 120
        interval = 1

        while total_wait_time > 0:
            # Clear the last printed line
            print(f"Resuming in {total_wait_time} seconds...", end='\r')
            time.sleep(interval)
            total_wait_time -= interval


def gpt_get_summary_description_of_action(statement, 
                                          call_handler: GptCallHandler, 
                                          **handler_kwargs):

    if not isinstance(call_handler, GptCallHandler):
        raise TypeError("'call_handler' must be a GptCallHandler.")
    
    call_handler.update_params(**handler_kwargs)

    system = hp.action_summary_prompt
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": statement}]

    summary_statement = call_handler.generate(messages=messages)
    call_handler.reset_defaults()

    return summary_statement


def gpt_get_action_importance(statement: str, 
                              call_handler: GptCallHandler, 
                              **handler_kwargs):

    if not isinstance(call_handler, GptCallHandler):
        raise TypeError("'call_handler' must be a GptCallHandler.")
    
    call_handler.update_params(**handler_kwargs)

    system = hp.action_importance_prompt
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": statement}]

    importance_str = call_handler.generate(messages=messages)
    call_handler.reset_defaults()

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


def gpt_pick_an_option(instructions, 
                       options, 
                       input_str, 
                       call_handler: GptCallHandler, 
                       **handler_kwargs):
    """
    CREDIT of generalized option picking method: Dr. Chris Callison-Burch (UPenn)
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
    if not isinstance(call_handler, GptCallHandler):
        raise TypeError("'call_handler' must be a GptCallHandler.")
    
    call_handler.update_params(**handler_kwargs)

    choices_str, options_list = enumerate_dict_options(options)

    messages = [
        {
            "role": "system",
            "content": "{instructions}\n\n{choices_str}\nReturn just the number of the best match.".format(
                instructions=instructions, choices_str=choices_str
            ),
        },
        {"role": "user", "content": input_str},
    ]

    # Call the OpenAI API
    selection = call_handler.generate(messages=messages)
    call_handler.reset_defaults()

    # Use regular expressions to match a number returned by OpenAI and select that option.
    pattern = r"\d+"
    matches = re.findall(pattern, selection)
    if matches:
        index = int(matches[0])
        if index >= len(options_list):
            return None
        option = options_list[index]
        return options[option]
    else:
        return None


def limit_context_length(history, 
                         max_tokens, 
                         max_turns=1000, 
                         tokenizer=None, 
                         keep_most_recent=True, 
                         return_count=False):

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
        return_count (bool, optional): Also return the total token count that was consumed. Defaults to False.

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
        
    # reverse a copy of the list if we are only keeping the most recent items
    if keep_most_recent:
        copy_history = reversed(history)
    # otherwise make a normal copy of the list
    else:
        copy_history = history.copy()

    for message in copy_history:
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
        
    # return the total number of tokens consumed by this context list.
    if return_count:
        return list(limited_history), total_tokens
    
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

def get_token_remainder(max_tokens: int, *consumed_counts):
    """
    get the number of remaining available tokens given a max
    and any chunks used so far.

    Args:
        max_tokens (int): the maximum value for a model

    Returns:
        int: the number of remaining available tokens
    """
    return max_tokens - sum(consumed_counts)

def context_list_to_string(context, 
                           sep: str = "", 
                           convert_to_string: bool = False):
    if convert_to_string:
        return sep.join([f"{str(msg)}" for msg in context])
    else:
        return sep.join([msg for msg in context])
