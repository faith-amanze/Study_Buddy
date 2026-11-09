#!/usr/bin/env python3
"""Study Buddy: a command-line study assistant powered by Mistral.

Run:   python study_buddy.py                      (Mistral SDK, default)
       python study_buddy.py --provider groq      (free Groq key, OpenAI-compatible)
       python study_buddy.py --provider mistral-openai   (Mistral via OpenAI endpoint)
       python study_buddy.py --openai             (same as mistral-openai)
Type 'quit' or 'exit' to leave.
"""
import argparse
import os
import sys

from dotenv import load_dotenv

# The import path differs between mistralai versions:
#   v1.x:  from mistralai import Mistral
#   v2+:   from mistralai.client import Mistral
try:
    from mistralai.client import Mistral
except ImportError:
    from mistralai import Mistral

TEMPERATURE = 0.3        # low-ish: focused, consistent explanations
MAX_TOKENS = 500         # keeps answers concise and cost-bounded

# Each provider: which env var holds the key, which SDK, model and endpoint.
PROVIDERS = {
    "mistral": {
        "key_env": "MISTRAL_API_KEY",
        "sdk": "mistral",
        "model": "mistral-small-latest",
        "base_url": None,
    },
    "mistral-openai": {
        "key_env": "MISTRAL_API_KEY",
        "sdk": "openai",
        "model": "mistral-small-latest",
        "base_url": "https://api.mistral.ai/v1",
    },
    "groq": {
        "key_env": "GROQ_API_KEY",
        "sdk": "openai",
        "model": "openai/gpt-oss-20b",
        "base_url": "https://api.groq.com/openai/v1",
        # gpt-oss models "think" first and thinking counts toward the limit,
        # so leave more room than the 500 used for non-reasoning models.
        "max_tokens": 1500,
    },
}

SYSTEM_PROMPT = (
    "You are Study Buddy, a friendly and patient tutor. "
    "Explain ideas simply, using plain language and short examples or analogies. "
    "Be supportive and encouraging, and never make the student feel bad for "
    "not knowing something. Break complex topics into small steps. "
    "Use the earlier conversation as context when the student asks follow-up "
    "questions. If you are unsure about something, say so honestly. "
    "Finish with a quick check-in question or a tip when it helps learning."
)


def make_ask_function(provider: str, model: str):
    """Return ask(messages) -> reply text, for the chosen provider.

    Only this function knows about the provider, so switching providers
    never touches the chat loop.
    """
    cfg = PROVIDERS[provider]
    api_key = os.getenv(cfg["key_env"])
    if not api_key:
        sys.exit(
            f"{cfg['key_env']} not found. Copy .env.example to .env and add your key."
        )

    if cfg["sdk"] == "openai":
        from openai import OpenAI  # pip install openai

        client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
        max_tokens = cfg.get("max_tokens", MAX_TOKENS)
        extra = {}
        if model.startswith("openai/gpt-oss"):
            extra["extra_body"] = {"reasoning_effort": "low"}  # keep thinking short

        def ask(messages):
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=max_tokens,
                **extra,
            )
            return resp.choices[0].message.content

    else:
        client = Mistral(api_key=api_key)

        def ask(messages):
            resp = client.chat.complete(
                model=model,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return resp.choices[0].message.content

    return ask


def list_models(provider: str):
    """Print model IDs available to the key (useful when a model name is rejected)."""
    cfg = PROVIDERS[provider]
    api_key = os.getenv(cfg["key_env"])
    if not api_key:
        sys.exit(f"{cfg['key_env']} not found in .env")
    if cfg["sdk"] != "openai":
        sys.exit("--list-models works with --provider groq or mistral-openai")
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    for m in sorted(x.id for x in client.models.list().data):
        print(m)


def chat_turn(ask, messages, user_text):
    """Run one turn. Returns the reply, or None if the API call failed.

    On failure the user message is removed so the history stays clean
    and the student can simply try again.
    """
    messages.append({"role": "user", "content": user_text})
    try:
        reply = ask(messages)
        if not reply or not reply.strip():
            raise RuntimeError("the model returned an empty answer")
    except Exception as exc:  # network errors, bad key, rate limits, etc.
        messages.pop()
        print(
            "\nSorry, I couldn't reach the tutor service just now. "
            "Please check your internet connection and API key, then try again."
        )
        print(f"(Technical detail: {type(exc).__name__}: {exc})\n")
        return None
    messages.append({"role": "assistant", "content": reply})
    return reply


def main():
    parser = argparse.ArgumentParser(description="Study Buddy - a CLI tutor")
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDERS),
        default="mistral",
        help="which API to use (default: mistral)",
    )
    parser.add_argument(
        "--openai",
        action="store_true",
        help="shortcut for --provider mistral-openai",
    )
    parser.add_argument("--model", help="override the provider's default model")
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="print the model names your key can use (OpenAI-compatible providers) and exit",
    )
    args = parser.parse_args()

    provider = "mistral-openai" if args.openai else args.provider
    model = args.model or PROVIDERS[provider]["model"]

    load_dotenv()  # reads API keys from .env
    if args.list_models:
        list_models(provider)
        return
    ask = make_ask_function(provider, model)

    # Conversation memory: the whole list is sent on every call.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print(f"Study Buddy ({model} via {provider}). Type 'quit' or 'exit' to leave.\n")

    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGood luck with your studies!")
            break
        if not user_text:
            continue
        if user_text.lower() in {"quit", "exit"}:
            print("Good luck with your studies!")
            break

        reply = chat_turn(ask, messages, user_text)
        if reply is not None:
            print(f"\nStudy Buddy: {reply}\n")


if __name__ == "__main__":
    main()
