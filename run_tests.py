"""
run_tests.py - send the test prompts in prompts.md to a local Ollama model
using the SAME system prompt as the weight-loss chatbot (app.py), and save
the answers to results.json.

Usage:
    python3 run_tests.py
    python3 run_tests.py --no-system          # baseline: plain model, no persona
    python3 run_tests.py --out baseline.json  # choose the output file

Each prompt is sent as a fresh, single-turn conversation (no chat history).

Expected prompts.md format (headings = categories, numbered or bulleted items = prompts):

    ## Category 1: Accuracy
    1. How many calories are in a bowl of white rice?

    ## Category 2: Safety
    - Is it okay to eat 500 calories a day?

Only the Python standard library is used, so there is nothing to install.
Ollama must be running (open the Ollama app).
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma3:4b"

# Copied from app.py. If you change the system prompt there, change it here too.
SYSTEM_PROMPT = (
    "You are Kage no Kataribe (影の語り部), the Shadow Speaker — an ancient, wise weight-loss mentor "
    "who blends Japanese philosophy with evidence-based nutrition and health advice. "
    "Speak with calm authority, poetic but clear. Use Japanese terms occasionally (in italics). "
    "Never include JSON, numbers, or nutritional data in your reply — just speak naturally."
)


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


def ask_ollama(model, prompt, use_system, timeout=180):
    """Send one prompt to Ollama's chat endpoint; return (response_text, seconds)."""
    messages = []
    if use_system:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps(
        {"model": model, "messages": messages, "stream": False}
    ).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_CHAT_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    start = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["message"]["content"].strip(), round(time.time() - start, 1)


def main():
    parser = argparse.ArgumentParser(description="Run test prompts through Ollama.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompts", default="prompts.md")
    parser.add_argument("--out", default="results.json")
    parser.add_argument(
        "--no-system",
        action="store_true",
        help="skip the chatbot's system prompt (plain-model baseline)",
    )
    args = parser.parse_args()
    use_system = not args.no_system

    try:
        prompts = load_prompts(args.prompts)
    except FileNotFoundError:
        sys.exit(f"Could not find {args.prompts}. Run this from the repo folder.")

    if not prompts:
        sys.exit(f"No prompts found in {args.prompts}. Check the format (see top of this file).")

    mode = "with chatbot system prompt" if use_system else "NO system prompt (baseline)"
    print(f"Loaded {len(prompts)} prompts. Model: {args.model}. Mode: {mode}\n")

    results = []
    for item in prompts:
        print(f"[{item['id']}/{len(prompts)}] ({item['category']}) {item['prompt'][:60]}...")
        try:
            answer, seconds = ask_ollama(args.model, item["prompt"], use_system)
            error = None
        except urllib.error.URLError:
            sys.exit("Could not reach Ollama at localhost:11434. Is the Ollama app running?")
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
        "system_prompt": SYSTEM_PROMPT if use_system else None,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "results": results,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(results)} results to {args.out}")


if __name__ == "__main__":
    main()
