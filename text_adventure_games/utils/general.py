import re
import json

def extract_target_word(response):
    words = response.split()
    # For debugging purposes check when it fails to return only 1 word.
    if len(words) > 1:
        print("target word list returned is: ", words)
        return words[0]
    else:
        return words[0]


def extract_enumerated_list(response):
    # Split the response string into lines
    lines = response.split('\n')

    extracted_words = []
    # Regular expression to match lines with an 
    # enumeration format followed by a single word
    pattern = re.compile(r'^\d+\.\s*(\w+)')

    for line in lines:
        match = pattern.match(line)
        if match:
            extracted_words.append(match.group(1))
    return extracted_words


def extract_json_from_string(s):
    # Regular expression to match a JSON structure
    # It looks for an opening curly brace, followed by any character (non-greedily),
    # and then a closing curly brace. The DOTALL flag allows the dot to match newlines.
    pattern = re.compile(r'\{.*?\}', re.DOTALL)
    match = pattern.search(s)
    if match:
        # Extract the JSON string
        json_str = match.group(0)
        try:
            # Attempt to parse the JSON string to ensure it's valid
            json_obj = json.loads(json_str)
            # Return the JSON object if parsing is successful
            return json_obj
        except json.JSONDecodeError:
            # Return None or raise an error if the JSON is invalid
            return None
    return None
