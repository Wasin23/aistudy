from datasets import load_dataset
import json
import os
import random

random.seed(42)
DIR = os.path.dirname(__file__)
OUT = os.path.join(DIR, "testset.json")

questions = []

def add(source, context, question, answer, options=None):
    questions.append({
        "id": len(questions) + 1,
        "source": source,
        "context": context,
        "question": question,
        "options": options,
        "answer": answer
    })

# --- GSM8K (15) ---
print("Loading GSM8K...")
gsm = load_dataset("openai/gsm8k", "main", split="test")
sample = random.sample(list(gsm), 15)
for row in sample:
    add("gsm8k", "", row["question"], row["answer"])

# --- ARC Challenge (15) ---
print("Loading ARC Challenge...")
arc = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test")
sample = random.sample(list(arc), 15)
for row in sample:
    choices = {k: v for k, v in zip(row["choices"]["label"], row["choices"]["text"])}
    add("arc_challenge", "", row["question"], row["answerKey"], options=choices)

# --- BIG-bench Hard (10) ---
print("Loading BIG-bench Hard...")
bbh = load_dataset("lukaemon/bbh", "causal_judgement", split="test")
sample = random.sample(list(bbh), 10)
for row in sample:
    add("bigbench_hard_causal", "", row["input"], row["target"])

# --- LSAT via AGIEval (10) ---
print("Loading LSAT (AGIEval)...")
lsat = load_dataset("dmayhem93/agieval-lsat-lr", split="test")
sample = random.sample(list(lsat), 10)
for row in sample:
    options = {chr(65+i): v for i, v in enumerate(row["choices"])}
    correct = chr(65 + row["gold"][0])
    add("lsat_lr", "", row["query"], correct, options=options)

with open(OUT, "w") as f:
    json.dump(questions, f, indent=2)

print(f"\nSaved {len(questions)} questions to testset.json")
