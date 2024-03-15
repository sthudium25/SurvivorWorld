from ..utils.general import set_up_openai_client

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
