import argparse
import backoff
import json
import openai
import os

from hugchat import hugchat
from hugchat.login import Login

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

from oa_secrets import OA_KEY, OA_ORGANIZATION
from claude_key import CLAUDE_KEY


openai.organization = OA_ORGANIZATION
openai.api_key = OA_KEY
anthropic = Anthropic()
anthropic.api_key = CLAUDE_KEY

SYSTEM_PROMPT = "You are a skilled writer and editor. Evaluate the quality of a summary of a short story by answering the questions provided. Select from the four options indicated and choose whichever fits best. Be careful to evaluate the summary in relation to the short story provided."
COVER_Q = "Does the summary cover the important plot points of the story?\n1) No - critical details are left out that are necessary to understand the story\n2) Not really - it would be hard to appreciate the story from the details provided\n3) Mostly - covers the main points but small things missing\n4) Yes - the important details of the narrative are covered"
FAITH_Q = "Does the summary misrepresent details from the story or make things up?\n1) Yes - the summary includes incorrect details\n2) Somewhat - the summary misrepresents details\n3) Not really - mostly accurate but some details aren’t clear\n4) No - everything is correct in relation to the story"
COHER_Q = "Is the summary coherent, fluent and readable?\n1) No - contains grammar errors or non sequiturs\n2) Not really - confusing to follow but fluent\n3) Mostly - a bit clunky but coherent and fluent\n4) Yes - easy to read and understand"
INTERP_Q = "Does the summary provide any correct analysis of some of the main takeaways or themes from the story?\n1) No - there is no analysis in the summary\n2) Not really - there is some analysis but it’s not correct\n3) Somewhat - there is some correct analysis but it’s not very thoughtful\n4) Yes - the summary touches on some of the themes/feelings/interpretation that you hoped to communicate as the writer"
QUESTIONS = [COVER_Q, FAITH_Q, COHER_Q, INTERP_Q]


@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def chatgpt(messages, model, temperature, max_tokens=650):
    response = openai.ChatCompletion.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return response['choices'][0]['message']['content']


def get_summary(content, summary, model, temperature, max_tokens):
    if model == 'claude-2.1':
        message = f"{HUMAN_PROMPT} {SYSTEM_PROMPT}\n\nShort Story:\n{content}\n\nSummary:\n{summary}"
        answers = []
        for question in QUESTIONS:
            answer = anthropic.completions.create(
                model=model,
                max_tokens_to_sample=max_tokens,
                prompt=message + f'\n\n{question}\n\nYou must place your score within <score><\score> tags.\n\n{AI_PROMPT}',
                temperature=temperature,
            ).completion
            idx = answer.find("</score>")
            if answer.strip().startswith("I do not feel comfortable"):
                answers.append(-1)
            else:
                answers.append(int(answer[idx-1:idx]))
            message += f'{answer}'
    else:
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'Short Story:\n{content}\n\nSummary:\n{summary}'}
        ]
        answers = []
        for question in QUESTIONS:
            messages.append({'role': 'user', 'content': question})
            answer = chatgpt(messages=messages, model=model,
                          temperature=temperature, max_tokens=max_tokens)
            answers.append(int(answer[:1]))
            messages.append({'role': 'assistant', 'content': answer})
            
    return answers


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Script to score summaries.')
    parser.add_argument('--stories', default='stories')
    parser.add_argument('--summaries', default='gpt4_summaries')
    parser.add_argument('--temperature', default=0.0)
    parser.add_argument('--model', default='gpt-4-1106-preview', choices=[
        'gpt-4-1106-preview',
        'claude-2.1'
    ])
    parser.add_argument('--max_tokens', default=25, type=int)
    args = parser.parse_args()

    files = os.listdir(args.stories)
    if not os.path.exists(os.path.join('summary_scores', args.summaries)):
        os.makedirs(os.path.join('summary_scores', args.summaries))
    if os.path.exists(os.path.join('summary_scores', args.summaries, f"{args.model}_scores.json")):
        with open(os.path.join(args.summaries, f"{args.model}_scores.json"), 'r') as f:
            model_scores = json.loads(f.read())
    else:
        model_scores = {}
    for file in files:
        if file[:-4] in model_scores:
            continue
        print(f"Scoring {file}")
        story_file = os.path.join(args.stories, file)
        summary_file = os.path.join(args.summaries, file)

        with open(story_file, 'r') as f:
            story = f.read().strip()
        with open(summary_file, 'r') as f:
            summ = f.read().strip()
            # Remove Claude boilerplate if needed
            if "claude" in args.summaries and summ.startswith("Here is a "):
                summ = summ[summ.find(":\n\n")+3:].strip()

        answers = get_summary(story, summ, args.model, args.temperature, args.max_tokens)
        model_scores[file[:-4]] = answers
    
        with open(os.path.join('summary_scores', args.summaries, f"{args.model}_scores.json"), "w") as f:
            f.write(json.dumps(model_scores))

