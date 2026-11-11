"""
Primitive conversation loop with your trained mini transformer.

Loads the checkpoint from 05_mini_transformer_trainable.py, then lets you
type a prompt and watch it generate a continuation, repeatedly, like a
(very dumb, char-level, tiny) chat.

Note going in: this model has ~18k parameters and was trained on a few
sentences repeated 20x. It has no concept of "answering a question" --
it only knows "given these characters, what character is statistically
likely to come next" based on your tiny corpus. Don't expect coherent
conversation -- expect to SEE the mechanism (autoregressive generation)
working in real time, one character at a time, which is literally what
a real chat model like me does under the hood, just orders of magnitude
bigger and better trained.
"""
import os
import torch
import torch.nn.functional as F

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "mini_transformer.pt")

# must match training exactly -- same corpus defines the same vocab/char IDs
CORPUS_PATH = os.path.join(os.path.dirname(__file__), "text_data", "corpus.txt")
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    corpus = f.read()
chars = sorted(set(corpus))
vocab_size = len(chars)
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for i, ch in enumerate(chars)}

def encode(s):
    # unknown characters (not in training vocab) get silently dropped --
    # this model literally cannot represent a character it never saw.
    return [stoi[c] for c in s if c in stoi]

def decode(ids):
    return "".join(itos[i] for i in ids)

# must match the architecture in 05 exactly, or the saved weight shapes won't fit
block_size = 16
d_model = 32
n_heads = 4
d_head = d_model // n_heads
n_layers = 2

if not os.path.exists(CHECKPOINT_PATH):
    raise RuntimeError("No checkpoint found -- run 05_mini_transformer_trainable.py first to train one.")

saved = torch.load(CHECKPOINT_PATH)
token_emb = saved["token_emb"]
pos_emb = saved["pos_emb"]
W_out = saved["W_out"]
b_out = saved["b_out"]
layers = saved["layers"]

def attention_head(x, W_q, W_k, W_v):
    Q = x @ W_q
    K = x @ W_k
    V = x @ W_v
    scores = (Q @ K.transpose(-2, -1)) / (W_q.shape[1] ** 0.5)
    T = x.shape[0]
    mask = torch.tril(torch.ones(T, T)).bool()
    scores = scores.masked_fill(~mask, float("-inf"))
    weights = F.softmax(scores, dim=-1)
    return weights @ V

def multi_head_attention(x, layer):
    heads_out = [attention_head(x, layer["W_q"][h], layer["W_k"][h], layer["W_v"][h])
                 for h in range(n_heads)]
    return torch.cat(heads_out, dim=-1) @ layer["W_o"]

def feedforward(x, layer):
    hidden = torch.relu(x @ layer["W1"] + layer["b1"])
    return hidden @ layer["W2"] + layer["b2"]

def forward(token_ids):
    T = len(token_ids)
    x = token_emb[token_ids] + pos_emb[:T]
    for layer in layers:
        x = x + multi_head_attention(x, layer)
        x = x + feedforward(x, layer)
    return x @ W_out + b_out

@torch.no_grad()
def generate(prompt, n_new_chars=80, temperature=0.8):
    ids = encode(prompt)
    if not ids:
        return "(prompt had no characters this model recognizes -- try only using: " + "".join(chars) + ")"
    for _ in range(n_new_chars):
        context = ids[-block_size:]
        logits = forward(torch.tensor(context, dtype=torch.long))
        next_logits = logits[-1] / temperature
        # ^ temperature: divides logits before softmax. LOWER temperature (<1)
        # makes the distribution more peaked/confident (more repetitive,
        # "safer"). HIGHER temperature (>1) flattens it (more random,
        # more chaotic). This is the exact same softmax-amplification
        # idea from way back -- just being deliberately tuned here.
        probs = F.softmax(next_logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1).item()
        ids.append(next_id)
    return decode(ids)


print("mini transformer chat -- type a prompt, or 'quit' to exit")
print(f"(this model only knows these characters: {''.join(chars)!r})\n")

while True:
    prompt = input("you: ")
    if prompt.strip().lower() in ("quit", "exit"):
        break
    output = generate(prompt)
    print(f"model: {output}\n")
