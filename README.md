# Study Buddy

A command-line study assistant built on Mistral (`mistral-small-latest`). It demonstrates
safe API-key handling, the `mistralai` SDK, system/user/assistant roles, conversation
memory, generation settings, error handling, and provider portability.

## Setup

1. **Python 3.9+** and a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Get a Mistral API key** at https://console.mistral.ai (API Keys).
3. **Store it in `.env`** (never in the code):
   ```bash
   cp .env.example .env
   # edit .env and set: MISTRAL_API_KEY=your_real_key
   ```
   `.env` is listed in `.gitignore`, so it won't be committed. Only `.env.example`
   (with a placeholder) is safe to share.

## Run

```bash
python study_buddy.py                        # Mistral SDK (mistral-small-latest)
python study_buddy.py --provider groq        # free Groq key (default model: openai/gpt-oss-20b)
python study_buddy.py --provider groq --list-models   # show model names your key can use
python study_buddy.py --provider mistral-openai   # Mistral via its OpenAI-compatible endpoint
```
`--openai` is a shortcut for `--provider mistral-openai`. Use `--model NAME` to override the model.
Type `quit` or `exit` to leave.

### Using a free Groq key instead of Mistral
Mistral's API may require paid credits on some accounts. For a free alternative, create a key at
https://console.groq.com (API Keys), put it in `.env` as `GROQ_API_KEY=...`, and run with
`--provider groq`. Only the key, endpoint and model change; the chat loop, memory, temperature
and error handling are identical.

## How it works

| Skill | Where |
|---|---|
| Safe key handling | `load_dotenv()` + `os.getenv("MISTRAL_API_KEY")`; `.env` in `.gitignore` |
| SDK usage | `client.chat.complete(...)` from `mistralai` |
| Roles | `system` (tutor personality), `user`, `assistant` |
| Memory | one `messages` list, every user message and reply appended, whole list resent each call |
| Generation settings | `temperature=0.3`, `max_tokens=500` |
| Error handling | `try/except` around the API call; friendly message, failed turn rolled back |
| Portability | `--provider` picks Mistral SDK, Mistral via OpenAI-compatible endpoint, or Groq; only `make_ask_function` changes |

**SDK version note:** newer `mistralai` releases (tested with 3.7.0) use
`from mistralai.client import Mistral`; older 1.x releases use `from mistralai import Mistral`.
The script tries both.

## Testing

- Offline logic test (no key needed): `python test_memory.py`
- Live test: run the assistant and ask connected questions, e.g.
  1. `What is photosynthesis?`
  2. `Where in the plant does it happen?`
  3. `Why does that make leaves green?`

  Question 3 only makes sense if the assistant remembers questions 1 and 2.
  Save your terminal output as `transcript.txt` (or take a screenshot) for submission.
