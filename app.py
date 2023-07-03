import os
import json
from flask import Flask, stream_template, request, Response
from flask_caching import Cache
from dotenv import load_dotenv
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv(".env")

app = Flask(__name__)
cache = Cache(
    app,
    config={"CACHE_TYPE": "SimpleCache"},
)

openai.api_key = os.getenv("OPENAI_API_KEY")
GPT_4_MODEL = "gpt-4"
GPT_3_MODEL = "gpt-3.5-turbo"
DEFAULT_CHAT_MODEL = GPT_3_MODEL


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_chat_completion(
    system_prompt: str, messages: list[dict], model: str = DEFAULT_CHAT_MODEL
):
    """Returns ChatGPT's response to the given prompt."""
    system_message = [{"role": "system", "content": system_prompt}]
    conversation_messages = system_message + messages
    response = openai.ChatCompletion.create(
        model=model, messages=conversation_messages, temperature=0.9, stream=True
    )
    return response


@app.get("/")
def index():
    return stream_template("index.html")


def make_cache_key():
    return request.user_agent.string


@app.post("/paint")
def paint():
    with open("prompts/system.txt") as f:
        prompt = f.read()
    user_message = {
        "role": "user",
        "content": f"Please create an interesting webpage of your choosing. Be as creative as possible when coming up with your webpage.",
    }

    cache_key = make_cache_key()

    def event_stream():
        result = cache.get(cache_key)
        if result is None:
            result = []
            for resp in get_chat_completion(
                system_prompt=prompt, messages=[user_message]
            ):
                text = resp.choices[0].delta.get("content", "")
                if len(text):
                    yield text
                    result.append(text)
            cache.set(cache_key, result, timeout=60 * 60 * 24 * 7)
        else:
            for text in result:
                yield text

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
