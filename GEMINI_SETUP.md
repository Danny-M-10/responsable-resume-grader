# How to Use Google Gemini API

The application supports **Google Gemini** as the primary AI provider (with optional OpenAI fallback). Follow these steps to get a Gemini API key and enable AI features.

## Step 1: Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **Get API key** (or open the API keys section)
4. Create a new API key for your project
5. Copy the key (it may start with `AIza...`)

## Step 2: Configure the Application

**Option A: Environment variable**

```bash
export GEMINI_API_KEY='AIza-your-actual-key-here'
```

**Option B: `.env` file (recommended)**

In your project root, create or edit `.env`:

```
GEMINI_API_KEY=AIza-your-actual-key-here
```

Optional:

- `GEMINI_MODEL=gemini-1.5-pro` — default model (or use `gemini-1.5-flash` for lower cost/latency)
- `LLM_PROVIDER=gemini` — force Gemini even if `OPENAI_API_KEY` is set

## Step 3: Verify Configuration

From the project root:

```bash
python -c "from config import is_ai_configured, get_llm_provider; print('AI configured:', is_ai_configured()); print('Provider:', get_llm_provider())"
```

You should see `AI configured: True` and `Provider: gemini`.

Quick test of the LLM client:

```bash
python -c "
from llm_client import generate
text = generate([{'role': 'user', 'content': 'Say hello in one word.'}], max_tokens=20, temperature=0)
print('Response:', text)
"
```

## Provider Selection

- If **only** `GEMINI_API_KEY` is set → the app uses Gemini.
- If **only** `OPENAI_API_KEY` is set → the app uses OpenAI.
- If **both** are set → use `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` to choose; otherwise Gemini is preferred when its key is set.

## Model Names

Common Gemini models:

- `gemini-1.5-pro` — default, strong for reasoning and long context
- `gemini-1.5-flash` — faster and cheaper, good for most tasks

Set via `GEMINI_MODEL` in `.env` or the environment.

## Troubleshooting

- **"No AI provider configured"** — Ensure `GEMINI_API_KEY` (or `OPENAI_API_KEY`) is set and loaded (e.g. in `.env` in the project root).
- **Quota / rate limits** — Check [Google AI Studio](https://aistudio.google.com/) for usage and limits.
- **Safety blocks** — If Gemini blocks a response, the app will surface a short error; you can retry or adjust the input.

## References

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API documentation](https://ai.google.dev/gemini-api/docs)
