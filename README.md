# Weight-Loss Chatbot Evaluation

Testing how a local Gemma 3 chatbot answers weight-loss questions, including safety cases.

> **Disclaimer:** This is a demo project, not medical advice. It is not a
> substitute for a doctor or registered dietitian.

## What this is
A small test of how a local model (gemma3:4b, run with Ollama) answers
weight-loss questions. The chatbot being tested is my
[japanese-theme-weight-loss-chatbot](https://github.com/JonPaulTokyo/japanese-theme-weight-loss-chatbot).

## Method
- [Number] test prompts in 3 categories: everyday questions, safety cases,
  and edge cases (see `prompts.md`)
- Each answer rated 1–5 on accuracy, safety, clarity, and staying on theme
  (see `rubric.md`)
- Model: gemma3:4b, run locally. Date tested: [fill in]

## Results
[Summary table and 3–5 key findings, with example answers. Add after testing.]

## Limitations
Small test set, one rater, small model, and answers can vary between runs.

## How to repeat
Install Ollama, run `ollama pull gemma3:4b`, then run `python run_tests.py`.
