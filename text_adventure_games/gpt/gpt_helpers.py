import re
from ..utils.general import set_up_openai_client, enumerate_dict_options


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


def gpt_get_action_importance(statement, client, model, max_tokens):
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
        return matches[0]
    return None


def gpt_pick_an_option(instructions, options, input_str):
    """
    CREDIT: Dr. Chris Callison-Burch (UPenn)
    This function calls GPT to choose one option from a set of options.
    Its arguments are:
    * instructions - the system instructions
    * options - a dictionary of option_descriptions -> option_names
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

    # if self.verbose:
    #     v = "{instructions}\n\n{choices_str}\nReturn just the number.\n---\n> {input_str}"
    #     print(
    #         v.format(
    #             instructions=instructions,
    #             choices_str=choices_str,
    #             input_str=input_str,
    #         )
    #     )
    #     print("---\nGPT's response was:", content)

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
