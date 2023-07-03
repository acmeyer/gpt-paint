import os
from flask import Flask, stream_template, stream_with_context, request, Response
from dotenv import load_dotenv
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv(".env")

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
GPT_4_MODEL = "gpt-4"
GPT_3_MODEL = "gpt-3.5-turbo"
DEFAULT_CHAT_MODEL = GPT_4_MODEL


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_chat_completion(
    system_prompt: str, messages: list[dict], model: str = DEFAULT_CHAT_MODEL
):
    """Returns ChatGPT's response to the given prompt."""
    system_message = [{"role": "system", "content": system_prompt}]
    conversation_messages = system_message + messages
    response = openai.ChatCompletion.create(
        model=model, messages=conversation_messages, temperature=0.7, stream=True
    )
    return response


@app.get("/")
def index():
    return stream_template("index.html")


@app.post("/paint")
def paint():
    with open("prompts/painting.txt") as f:
        prompt = f.read()
    user_message = {
        "role": "user",
        "content": "Please create HTML of a webpage that tells me more about what information is available about me on the web.",
    }

    def event_stream():
        for resp in get_chat_completion(system_prompt=prompt, messages=[user_message]):
            text = resp.choices[0].delta.get("content", "")
            if len(text):
                yield text

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
