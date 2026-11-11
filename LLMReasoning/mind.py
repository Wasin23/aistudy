from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()

client = OpenAI()
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "reasoning.json")


def get_lens(context: str) -> dict:
    prompt = f"""You are extracting the structural lens of a domain or context — not what it studies or concerns, but the underlying conditions that make it a distinct domain.

Context: "{context}"

Answer these two questions:
1. What fundamental conditions or forces does this context assume are operating? (What makes this domain's situations different from any other?)
2. What would have to change for this context to no longer apply?

Do not describe the field, subject, or topic. Extract only the structural conditions — the minimal set of assumptions that define what kind of situation this context describes.

Respond in this exact JSON shape:
{{
  "conditions": "...",
  "ceases_when": "..."
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )

    return json.loads(response.choices[0].message.content)


def decompose(context: str, lens: dict, word_a: str, word_b: str, word_c: str) -> dict:
    prompt = f"""You are analyzing the underlying structure of concepts through a specific lens.

Context: "{context}"
Lens — the structural conditions this context assumes:
  Conditions: {lens["conditions"]}
  Ceases when: {lens["ceases_when"]}

Words: "{word_a}", "{word_b}", "{word_c}"

For each word, answer two questions as they apply within the lens above:
1. What process generates this behavior under these conditions?
2. What would have to be true for it to stop on its own, given these conditions?

Do not describe surface properties or observable behavior. Extract the mechanism — how the word operates as a process within the structural conditions of this context.

Then identify the relational map: what structure or dynamic do these words share when viewed through this lens? What connects them in pairs?

Respond in this exact JSON shape:
{{
  "context": "{context}",
  "lens": {{
    "conditions": "{lens["conditions"]}",
    "ceases_when": "{lens["ceases_when"]}"
  }},
  "{word_a}": {{
    "process": "...",
    "self_termination": "..."
  }},
  "{word_b}": {{
    "process": "...",
    "self_termination": "..."
  }},
  "{word_c}": {{
    "process": "...",
    "self_termination": "..."
  }},
  "relational_map": {{
    "shared": "...",
    "pairwise": {{
      "{word_a}_{word_b}": "...",
      "{word_b}_{word_c}": "...",
      "{word_a}_{word_c}": "..."
    }}
  }}
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )

    return json.loads(response.choices[0].message.content)


def save(result: dict):
    with open(RESULTS_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print("saved to reasoning.json")


if __name__ == "__main__":
    print("Format: context, word1, word2, word3 — Ctrl+C to quit.")
    while True:
        try:
            line = input("\n> ").strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 4:
                print("Expected: context, word1, word2, word3")
                continue
            context, word_a, word_b, word_c = parts
            print("decomposing context...")
            lens = get_lens(context)
            print("analyzing words...")
            result = decompose(context, lens, word_a, word_b, word_c)
            save(result)
        except KeyboardInterrupt:
            print()
            break
