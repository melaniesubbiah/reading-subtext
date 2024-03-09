import argparse
import backoff
import json
import openai
import os

from datetime import date
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

from oa_secrets import OA_KEY, OA_ORGANIZATION
from claude_key import CLAUDE_KEY


openai.organization = OA_ORGANIZATION
openai.api_key = OA_KEY
anthropic = Anthropic()
anthropic.api_key = CLAUDE_KEY


@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def chatgpt(messages, model, temperature, max_tokens=650):
    response = openai.ChatCompletion.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return response['choices'][0]['message']['content']


def get_summary(content, model, temperature, max_tokens):
    if model == 'claude-2.1':
        message = f"{HUMAN_PROMPT} You are an expert summary-writer. Summarize the provided passage in several paragraphs using only information from the passage provided.\n\n{content}\n\nWrite a coherent, chronological, and detailed summary for this passage in several paragraphs (about 400 words). Briefly introduce key entities like characters or settings when they are mentioned in the summary, and include some analysis of the story.{AI_PROMPT}"
        completion = anthropic.completions.create(
            model=model,
            max_tokens_to_sample=max_tokens,
            prompt=message,
            temperature=temperature,
        )
        summary = completion.completion
    else:
        messages = [
            {'role': 'system', 'content': f'You are an expert summary-writer. Summarize the provided passage in several paragraphs using only information from the passage provided.'},
            {'role': 'user',
                'content': f'{content}\n\nWrite a coherent, chronological, and detailed but brief summary for this passage in several paragraphs (about 400 words). Briefly introduce key entities like characters or settings when they are mentioned in the summary, and include some analysis of the story. If you are quoting directly from the story, make sure to put the copied text in quotes.\nSummary:'},
        ]
        summary = chatgpt(
            messages=messages, 
            model=model, 
            temperature=temperature, 
            max_tokens=max_tokens
        )
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Script to generate summaries from short stories.')
    parser.add_argument('--stories', default='stories')
    parser.add_argument('--outdir', default='gpt4_summaries')
    # setting comes from this https://arxiv.org/pdf/2109.10862.pdf and this https://arxiv.org/pdf/2301.13848.pdf
    parser.add_argument('--temperature', default=0.3)
    parser.add_argument('--model', default='gpt-3.5-turbo', choices=[
        'gpt-3.5-turbo',
        'gpt-4-1106-preview',
        'claude-2.1',
    ])
    parser.add_argument('--max_tokens', default=1000, type=int)
    args = parser.parse_args()

    files = os.listdir(args.stories)
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    for file in files:
        print(f"Summarizing {file}")
        with open(os.path.join(args.outdir, "settings.txt"), 'w') as f:
            argsdict = args.__dict__
            argsdict['last-modified-date'] = str(date.today())
            json.dump(argsdict, f, indent=2)

        story_file = os.path.join(args.stories, file)
        outpth = os.path.join(args.outdir, file)
        if os.path.exists(outpth):
            print('Skipping')
            continue

        with open(story_file, 'r') as f:
            content = f.read()

        summary = get_summary(content, args.model, args.temperature, args.max_tokens)

        with open(outpth, 'w') as f:
            f.write(summary)
