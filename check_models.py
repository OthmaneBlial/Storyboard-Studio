"""Small diagnostic for a locally configured Gemini key.

Run this only after exporting GEMINI_API_KEY in your shell. It never reads or
stores a key from the repository.
"""

from __future__ import annotations

import os


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set. Export it before running this diagnostic.")
        return 2
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        models = client.models.list(config={"page_size": 100})
        names = [model.name for model in models if "gemini" in model.name.lower()]
        print("Configured Gemini models:")
        print("\n".join(names[:30]))
        return 0
    except Exception as exc:
        print(f"Could not list models. Check the key and network connection: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
