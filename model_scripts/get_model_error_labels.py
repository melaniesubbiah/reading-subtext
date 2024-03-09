import argparse
import backoff
import json
import openai
import os

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

from oa_secrets import OA_KEY, OA_ORGANIZATION
from claude_key import CLAUDE_KEY


openai.organization = OA_ORGANIZATION
openai.api_key = OA_KEY
anthropic = Anthropic()
anthropic.api_key = CLAUDE_KEY


with open('faithinstruct.txt', 'r') as f:
    SYSTEM_PROMPT = f.read().strip()
Q1 = "Is this a faithfulness error? Answer Yes or No.\n"
Q2 = "What is the category? You must answer Feeling, Causation, Action, Character, or Setting.\n"
QUESTIONS = [Q1, Q2]


@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def chatgpt(messages, model, temperature, max_tokens=650):
    response = openai.ChatCompletion.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return response['choices'][0]['message']['content']


def get_labels(error, model, temperature, max_tokens):
    if model == 'claude-2.1':
        message = f"{HUMAN_PROMPT} {SYSTEM_PROMPT}\n\nError:\n{error}"
        answers = []
        for question in QUESTIONS:
            answer = anthropic.completions.create(
                model=model,
                max_tokens_to_sample=max_tokens,
                prompt=message + f'\n\n{question}\n\nPlace your answer within <answer></answer> tags.\n\n{AI_PROMPT}',
                temperature=temperature,
            ).completion
            if '<answer>' not in answer:
                answers.append('_')
            else:
                start = answer.find("<answer>") + 8
                end = answer.find("</answer>")
                # Check if Claude refused to answer
                if answer.strip().startswith("I do not feel comfortable"):
                    answers.append(-1)
                else:
                    answers.append(answer[start:end].strip())
                message += f'{answer}'
    else:
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'Error:\n{error}'}
        ]
        answers = []
        for question in QUESTIONS:
            messages.append({'role': 'user', 'content': question})
            answer = chatgpt(messages=messages, model=model,
                          temperature=temperature, max_tokens=max_tokens)
            answers.append(answer)
            messages.append({'role': 'assistant', 'content': answer})
            
    return answers


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Script to label faithfulness errors.')
    parser.add_argument('--errors', default='error_annotations/template/gpt4-errors.txt')
    parser.add_argument('--temperature', default=0.0)
    parser.add_argument('--model', default='gpt-4-1106-preview', choices=[
        'gpt-4-1106-preview',
        'claude-2.1',
        'mixtral',
    ])
    parser.add_argument('--max_tokens', default=25, type=int)

    args = parser.parse_args()

    if not os.path.exists(os.path.join('error_annotations', args.model)):
        os.makedirs(os.path.join('error_annotations', args.model))
    error_type = args.errors[args.errors.rfind('/')+1:-4]

    if os.path.exists(os.path.join('error_annotations', args.model, f"{args.model}_{error_type}.json")):
        with open(os.path.join('error_annotations', args.model, f"{args.model}_{error_type}.json"), 'r') as f:
            model_scores = json.loads(f.read())
    else:
        model_scores = {}

    with open(args.errors, 'r') as f:
        text = f.read().strip()

    idx = 0
    for i in range(1, 21):
        if f'Error {i}' in model_scores:
            continue
        start = text.find(f'Error {i}')
        error = text[text.find('\n', start):text.find(f'Error {i+1}')].strip()
        answer = get_labels(error, args.model, args.temperature, args.max_tokens)
        model_scores[f'Error {i}'] = (answer[0], answer[1].lower())

        with open(os.path.join('error_annotations', args.model, f"{args.model}_{error_type}.json"), "w") as f:
            f.write(json.dumps(model_scores))

