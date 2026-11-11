"""
Load the trained checkpoint and actually look at what's inside it --
real numbers, not binary garbage.
"""
import os
import torch

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "mini_transformer.pt")

# need the same vocab the model was trained with, to label rows by character
CORPUS_PATH = os.path.join(os.path.dirname(__file__), "text_data", "corpus.txt")
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    corpus = f.read()
chars = sorted(set(corpus))

saved = torch.load(CHECKPOINT_PATH)

print("keys in checkpoint:", list(saved.keys()))
print()

token_emb = saved["token_emb"]   # shape (vocab_size, d_model)
print(f"token_emb shape: {tuple(token_emb.shape)}  (one row per character)\n")

# print each character next to its learned embedding vector
for i, ch in enumerate(chars):
    label = repr(ch)  # repr so space/period are visible, e.g. ' ' -> "' '"
    vec = token_emb[i].detach().numpy()
    print(f"{label:>5}: {vec.round(2)}")

print("\n---")
print("Two characters with SIMILAR vectors means the model learned they")
print("behave similarly in context. Try eyeballing 'i' vs other vowels,")
print("or '.' vs ' ' -- both are 'boundary' characters, might end up close.")

# --------------------------------------------------------------------
# cosine similarity between every pair -- the actual measurement,
# not eyeballing. remember: dot product / (|A| * |B|) = angle only,
# magnitude-independent.
# --------------------------------------------------------------------
print("\ncosine similarity between each pair of characters:\n")
norm_emb = token_emb / token_emb.norm(dim=1, keepdim=True)   # normalize each row to length 1
sim_matrix = norm_emb @ norm_emb.T                            # now dot product = cosine similarity

header = "     " + " ".join(f"{repr(c):>5}" for c in chars)
print(header)
for i, ch in enumerate(chars):
    row = " ".join(f"{sim_matrix[i, j]:5.2f}" for j in range(len(chars)))
    print(f"{repr(ch):>5} {row}")

# print the single most similar OTHER character to each one
print("\nmost similar character to each (excluding itself):")
for i, ch in enumerate(chars):
    sims = sim_matrix[i].clone()
    sims[i] = -2   # exclude itself (cosine sim maxes at 1, so -2 guarantees it's not picked)
    best_j = sims.argmax().item()
    print(f"  {repr(ch):>5}  ~  {repr(chars[best_j]):>5}   (sim={sims[best_j]:.2f})")
