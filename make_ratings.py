"""
make_ratings.py - turn results.json into two files for human rating:

  answers.md   - a readable list of each prompt and the chatbot's full answer
  ratings.csv  - one row per prompt with blank score columns to fill in

Usage:
    python3 make_ratings.py
    python3 make_ratings.py --results baseline.json --prefix baseline_

Existing rating files are never overwritten unless you pass --force,
so your scores are safe if you run this again by mistake.
"""

import argparse
import csv
import json
import os
import sys

SCORE_COLUMNS = ["accuracy", "safety", "clarity", "on_theme"]


def main():
    parser = argparse.ArgumentParser(description="Create rating files from results.json.")
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--prefix", default="", help="prefix for output file names")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args()

    csv_path = f"{args.prefix}ratings.csv"
    md_path = f"{args.prefix}answers.md"

    try:
        with open(args.results, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"Could not find {args.results}. Run run_tests.py first.")

    for path in (csv_path, md_path):
        if os.path.exists(path) and not args.force:
            sys.exit(f"{path} already exists. Use --force to overwrite it (your scores would be lost).")

    results = data["results"]

    # ratings.csv (utf-8-sig so Numbers/Excel show Japanese text correctly)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "category", "prompt"] + SCORE_COLUMNS + ["comments"])
        for r in results:
            writer.writerow([r["id"], r["category"], r["prompt"]] + [""] * len(SCORE_COLUMNS) + [""])

    # answers.md
    lines = [
        "# Chatbot answers",
        "",
        f"Model: {data.get('model')}  ",
        f"Run at: {data.get('run_at')}  ",
        f"System prompt used: {'yes' if data.get('system_prompt') else 'no (baseline)'}",
        "",
        "Score each answer in the ratings CSV using rubric.md.",
        "",
    ]
    for r in results:
        lines.append(f"## {r['id']}. {r['category']}")
        lines.append("")
        lines.append(f"**Prompt:** {r['prompt']}")
        lines.append("")
        if r.get("error"):
            lines.append(f"**ERROR:** {r['error']}")
        else:
            for line in r["response"].splitlines():
                lines.append(f"> {line}" if line.strip() else ">")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Created {md_path} and {csv_path} ({len(results)} rows)")


if __name__ == "__main__":
    main()
