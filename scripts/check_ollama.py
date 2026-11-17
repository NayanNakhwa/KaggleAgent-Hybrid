"""Check that Ollama answers at OLLAMA_HOST and has the model we need.

Run from the repo root:
    python scripts\\check_ollama.py
Exit code 0 means OK. Exit code 1 means not OK.
"""
import json
import os
import sys
import urllib.error
import urllib.request

MODEL = os.environ.get("KAGENT_DEFAULT_MODEL", "qwen2.5-coder:7b")
HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def main() -> int:
    url = HOST + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"FAILED: Ollama answered with HTTP {exc.code}.")
        return 1
    except urllib.error.URLError as exc:
        print(f"FAILED: cannot reach Ollama: {exc.reason}")
        return 1
    except json.JSONDecodeError:
        print("FAILED: the answer was not JSON.")
        return 1

    names = [m.get("name", "") for m in data.get("models", [])]
    if MODEL not in names:
        print(f"FAILED: model {MODEL} not found. Models: {', '.join(names) or 'none'}")
        return 1

    print(f"OK: Ollama is reachable and has {MODEL}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
