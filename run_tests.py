"""
run_tests.py - send the test prompts in prompts.md to a local Ollama model
and save the answers to results.json.

Usage:
    python run_tests.py
    python run_tests.py --model gemma3:4b --prompts prompts.md --out results.json

Expected prompts.md format (headings = categories, numbered or bulleted items = prompts):

    ## Category 1: Accuracy
    1. How many calories are in a bowl of white rice?
    2. ...

    ## Category 2: Safety
    - Is it okay to eat 500 calories a day?

Only the Python standard library is used, so there is nothing to install.
Ollama must be running (open the Ollama app, or run `ollama serve`).
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:4b"


def load_prompts(path):
    """Parse prompts.md into a list of {id, category, prompt} dicts."""
    prompts = []
    category = "Uncategorized"
    item_pattern = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.*\S)\s*$")
    heading_pattern = re.compile(r"^\s*#{1,6}\s+(.*\S)\s*$")

    with open(path, encoding="utf-8") as f:
        for line in f:
            heading = heading_pattern.match(line)
            if heading:
                category = heading.group(1).strip()
                continue
            item = item_pattern.match(line)
            if item:
                text = item.group(1).strip().strip('"').strip("\u201c\u201d")
                prompts.append(
                    {"id": len(prompts) + 1, "category": category, "prompt": text}
                )
    return prompts


def ask_ollama(model, prompt, timeout=180):
    """Send one prompt to Ollama and return (response_text, seconds)."""
    payload = json.dumps(
        {"model": model, "prompt": prompt, "stream": False}
    ).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    start = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("response", "").strip(), round(time.time() - start, 1)


def main():
    parser = argparse.ArgumentParser(description="Run test prompts through Ollama.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompts", default="prompts.md")
    parser.add_argument("--out", default="results.json")
    args = parser.parse_args()

    try:
        prompts = load_prompts(args.prompts)
    except FileNotFoundError:
        sys.exit(f"Could not find {args.prompts}. Run this from the repo folder.")

    if not prompts:
        sys.exit(f"No prompts found in {args.prompts}. Check the format (see top of this file).")

    print(f"Loaded {len(prompts)} prompts. Model: {args.model}\n")

    results = []
    for item in prompts:
        print(f"[{item['id']}/{len(prompts)}] ({item['category']}) {item['prompt'][:60]}...")
        try:
            answer, seconds = ask_ollama(args.model, item["prompt"])
            error = None
        except urllib.error.URLError:
            sys.exit("Could not reach Ollama at localhost:11434. Is it running?")
        except Exception as e:  # keep going if a single prompt fails
            answer, seconds, error = "", None, str(e)
            print(f"    ERROR: {error}")

        results.append(
            {
                "id": item["id"],
                "category": item["category"],
                "prompt": item["prompt"],
                "response": answer,
                "seconds": seconds,
                "error": error,
            }
        )
        if seconds is not None:
            print(f"    done in {seconds}s")

    output = {
        "model": args.model,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "results": results,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(results)} results to {args.out}")


if __name__ == "__main__":
    main()
