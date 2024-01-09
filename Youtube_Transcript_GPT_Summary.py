import re
import pyperclip
from youtube_transcript_api import YouTubeTranscriptApi
import openai

def get_video_id():
    clipboard_content = pyperclip.paste()
    video_id = extract_video_id(clipboard_content)

    while not video_id:
        link = input("Enter a YouTube link or video ID: ")
        video_id = extract_video_id(link)

    return video_id

def extract_video_id(text):
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', text)
    return match.group(1) if match else None

def seconds_to_hms(seconds):
    h, m = divmod(int(seconds), 3600)
    m, s = divmod(m, 60)
    return f"[{h:02d}:{m:02d}:{s:02d}]"

openai_pricing = {
    "gpt-4": {
        "Input": 0.03 / 1000,
        "Output": 0.06 / 1000
    },
    "gpt-4-32k": {
        "Input": 0.06 / 1000,
        "Output": 0.12 / 1000
    },
    "gpt-4-1106-preview": {
        "Input": 0.01 / 1000,
        "Output": 0.03 / 1000
    }
}

def calculate_cost(model, input_tokens, output_tokens):
    pricing = openai_pricing.get(model, None)
    if pricing:
        input_cost = pricing["Input"] * input_tokens
        output_cost = pricing["Output"] * output_tokens
        return input_cost + output_cost
    else:
        return 0

video_id = get_video_id()

transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
transcript = transcript_list.find_transcript(['en'])
transcript_items = transcript.fetch()

compiled_transcript = "\n".join(f"{seconds_to_hms(item['start'])} {item['text']}" for item in transcript_items)
print(compiled_transcript)

model = 'gpt-4-1106-preview'

with open('OpenAIkey.txt', 'r') as file:
    openai.api_key = file.readline().strip()

def get_response(messages, model):
    response = openai.ChatCompletion.create(model=model, messages=messages)
    prompt_tokens = response['usage']['prompt_tokens']
    completion_tokens = response['usage']['completion_tokens']
    return response, prompt_tokens, completion_tokens

messages = [
    {"role": "system", "content": "Provide a brief bullet point summary of the video transcript."},
    {"role": "user", "content": compiled_transcript}
]

print(f"Getting GPT summary for transcript with model {model}...")
gpt_response, prompt_token_count, completion_token_count = get_response(messages, model)
response_message_content = gpt_response["choices"][0]["message"]["content"]

print(response_message_content, "\n")

# Calculate the cost
cost = calculate_cost(model, prompt_token_count, completion_token_count)
print(f"Cost: ${cost:.4f}")

input("Press any key to continue...")