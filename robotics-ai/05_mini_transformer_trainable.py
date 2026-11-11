"""
Same architecture as 04_mini_transformer.py, made TRAINABLE.

Difference from 04: numpy has no autodiff (no automatic gradient
computation), so there was no way to train it without hand-deriving every
backward pass -- extremely tedious and error-prone for something with this
many chained operations (attention especially).

Here we use PyTorch tensors instead of numpy arrays. The forward-pass
math is IDENTICAL to what you wrote by hand in 04 -- same Q/K/V, same
scaled dot product, same softmax, same residuals. The only difference:
every weight is a torch tensor with requires_grad=True, so PyTorch
records every operation and can compute d(loss)/d(every_weight)
automatically when you call loss.backward(). You still write the
training loop yourself (that part isn't automatic).

Task: character-level next-character prediction on a toy corpus.
Given some characters, predict the next one. Train it, watch loss drop,
then sample from it and see what it generates.

Every line below has a comment. Read top to bottom once before running.
"""
import os                          # just for building a file path to the checkpoint
import torch                       # the tensor library -- like numpy, but tracks gradients
import torch.nn.functional as F    # softmax, cross_entropy, relu live here

torch.manual_seed(0)               # fixes all random numbers so results are reproducible

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "mini_transformer.pt")
# ^ where the trained weights get saved/loaded from. "checkpoints" folder
# will be created automatically the first time we save.

# ------------------------------------------------------------------------
# corpus -- the training data, loaded from a real file now instead of a
# hardcoded string. Edit robotics-ai/text_data/corpus.txt with whatever
# text you want it to learn.
# ------------------------------------------------------------------------
CORPUS_PATH = os.path.join(os.path.dirname(__file__), "text_data", "corpus.txt")
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    corpus = f.read()

if len(corpus) < 200:
    print(f"warning: corpus is only {len(corpus)} characters -- pretty small, "
          f"the model won't have much to learn from. Consider adding more text "
          f"to {CORPUS_PATH}")

chars = sorted(set(corpus))        # every UNIQUE character that appears, sorted (e.g. [' ', '.', 'a', 'b', ...])
vocab_size = len(chars)            # how many unique characters = size of our "vocabulary"
stoi = {ch: i for i, ch in enumerate(chars)}   # "string to index": char -> its ID number
itos = {i: ch for i, ch in enumerate(chars)}   # "index to string": ID number -> char (reverse lookup)

def encode(s):
    return [stoi[c] for c in s]    # turn a string into a list of integer IDs, e.g. "hi" -> [7, 2]

def decode(ids):
    return "".join(itos[i] for i in ids)  # turn a list of integer IDs back into a string

data = torch.tensor(encode(corpus), dtype=torch.long)
# ^ the ENTIRE corpus, encoded as one long tensor of integers. dtype=torch.long
# because these are IDs/indices, not continuous numbers.

# ------------------------------------------------------------------------
# hyperparameters -- CHANGE THESE later to test theories once it's working.
# these are choices YOU make, not things the model learns.
# ------------------------------------------------------------------------
block_size = 16     # "context window" -- how many previous characters the model
                     # is allowed to look at when predicting the next one
d_model = 32         # size of each token's embedding vector (was 8 in script 04, bigger now)
n_heads = 4          # how many parallel attention heads per layer
d_head = d_model // n_heads   # each head's Q/K/V size = 32/4 = 8
d_ff = 64            # hidden layer size inside the feedforward block (bigger than d_model on purpose --
                     # this is where the model gets extra "thinking room" per token)
n_layers = 2         # how many transformer blocks stacked on top of each other
lr = 3e-3            # learning rate for the optimizer (same concept as script 01, different value)
n_steps = 2000       # how many training steps (batches) to run

# ------------------------------------------------------------------------
# parameters -- these are the actual numbers that get trained/updated.
# requires_grad=True is the ONLY thing different from script 04's random
# numpy arrays: it tells PyTorch "track every operation done to this
# tensor, so I can later compute how loss changes with respect to it."
# ------------------------------------------------------------------------
def param(*shape):
    # helper: make a randomly-initialized tensor of the given shape,
    # scaled small (*0.1, same reasoning as scale=0.1 in script 04),
    # and mark it as trainable.
    return (torch.randn(*shape) * 0.1).requires_grad_(True)

token_emb = param(vocab_size, d_model)
# ^ the embedding table from script 04's embed_tokens(), now trainable.
# one row per character in the vocab.

pos_emb = param(block_size, d_model)
# ^ positional info, like script 04's positional_encoding(), but simpler:
# instead of the fixed sin/cos formula, we let the model LEARN its own
# positional vectors from scratch. one row per position (0..block_size-1).

layers = []                        # will hold one dict of weights per transformer block
for _ in range(n_layers):          # build n_layers=2 separate sets of weights
    layer = {
        "W_q": [param(d_model, d_head) for _ in range(n_heads)],  # one Q matrix per head
        "W_k": [param(d_model, d_head) for _ in range(n_heads)],  # one K matrix per head
        "W_v": [param(d_model, d_head) for _ in range(n_heads)],  # one V matrix per head
        "W_o": param(d_model, d_model),   # output projection after concatenating all heads
                                           # (mentioned as optional in script 04's docstring -- here it's included for real)
        "W1": param(d_model, d_ff), "b1": torch.zeros(d_ff, requires_grad=True),
        # ^ feedforward layer 1: d_model -> d_ff (expand)
        "W2": param(d_ff, d_model), "b2": torch.zeros(d_model, requires_grad=True),
        # ^ feedforward layer 2: d_ff -> d_model (compress back down)
    }
    layers.append(layer)

W_out = param(d_model, vocab_size)
b_out = torch.zeros(vocab_size, requires_grad=True)
# ^ the FINAL layer: turns a d_model-sized vector into vocab_size raw scores
# ("logits"), one score per possible next-character. This is the piece
# 04_mini_transformer.py never got to -- the actual prediction head.

# collect every trainable tensor into one flat list, so the optimizer
# knows what it's allowed to update.
all_params = [token_emb, pos_emb, W_out, b_out]
for layer in layers:
    all_params += layer["W_q"] + layer["W_k"] + layer["W_v"]
    all_params += [layer["W_o"], layer["W1"], layer["b1"], layer["W2"], layer["b2"]]

optimizer = torch.optim.Adam(all_params, lr=lr)
# ^ Adam is a smarter version of the plain gradient descent from script 01
# (w -= lr * dw). It adapts the step size per-parameter automatically.
# Mechanically it still does the same fundamental thing: nudge each
# parameter in the direction that reduces loss.

# ------------------------------------------------------------------------
# checkpoint loading -- if a saved checkpoint exists from a previous run,
# load those trained numbers IN PLACE of the fresh random ones above,
# so training resumes/continues instead of starting over from scratch.
# ------------------------------------------------------------------------
def state_dict():
    # bundle every trainable tensor into one nested structure, matching
    # the shape of `layers` above, so save/load can walk it consistently.
    return {
        "token_emb": token_emb,
        "pos_emb": pos_emb,
        "W_out": W_out,
        "b_out": b_out,
        "layers": [
            {
                "W_q": layer["W_q"], "W_k": layer["W_k"], "W_v": layer["W_v"],
                "W_o": layer["W_o"], "W1": layer["W1"], "b1": layer["b1"],
                "W2": layer["W2"], "b2": layer["b2"],
            }
            for layer in layers
        ],
    }

if os.path.exists(CHECKPOINT_PATH):
    saved = torch.load(CHECKPOINT_PATH)
    # SAFETY CHECK: if you changed the corpus, vocab_size (and therefore
    # token_emb's shape) may no longer match what's in the old checkpoint.
    # Loading mismatched shapes would crash with a cryptic error, so check
    # explicitly and just start fresh instead if the corpus changed.
    if saved["token_emb"].shape != token_emb.shape:
        print(f"checkpoint found, but its vocab_size {tuple(saved['token_emb'].shape)} "
              f"doesn't match the current corpus's vocab_size {tuple(token_emb.shape)} "
              f"-- corpus must have changed. Starting fresh instead of loading.")
    else:
        print(f"found checkpoint at {CHECKPOINT_PATH} -- loading previous weights")
        # copy saved values INTO the existing tensors (.data.copy_, not a
        # plain reassignment) so we keep the same tensor objects the
        # optimizer above was already built around, and keep requires_grad=True.
        token_emb.data.copy_(saved["token_emb"])
        pos_emb.data.copy_(saved["pos_emb"])
        W_out.data.copy_(saved["W_out"])
        b_out.data.copy_(saved["b_out"])
        for layer, saved_layer in zip(layers, saved["layers"]):
            for h in range(n_heads):
                layer["W_q"][h].data.copy_(saved_layer["W_q"][h])
                layer["W_k"][h].data.copy_(saved_layer["W_k"][h])
                layer["W_v"][h].data.copy_(saved_layer["W_v"][h])
            layer["W_o"].data.copy_(saved_layer["W_o"])
            layer["W1"].data.copy_(saved_layer["W1"])
            layer["b1"].data.copy_(saved_layer["b1"])
            layer["W2"].data.copy_(saved_layer["W2"])
            layer["b2"].data.copy_(saved_layer["b2"])
else:
    print("no checkpoint found -- starting from random weights")


# ------------------------------------------------------------------------
# forward pass -- same math as 04, now using torch ops instead of numpy.
# these functions compute the model's PREDICTION. no learning happens
# in here -- this is just "given current weights, what does the model output."
# ------------------------------------------------------------------------
def attention_head(x, W_q, W_k, W_v):
    # x: (T, d_model) -- T = sequence length (number of characters so far)
    Q = x @ W_q         # (T, d_head) -- "what am I looking for," per token
    K = x @ W_k         # (T, d_head) -- "what do I contain," per token
    V = x @ W_v         # (T, d_head) -- "what I'll contribute if picked," per token
    scores = (Q @ K.transpose(-2, -1)) / (W_q.shape[1] ** 0.5)
    # ^ Q @ K.T = every token's query dotted against every token's key -> (T, T)
    # divided by sqrt(d_head) -- the scaling fix from earlier so softmax
    # doesn't saturate on high-dimensional vectors.

    # CAUSAL MASK -- this is NEW vs. script 04, and it matters a lot:
    # for next-character prediction, token i must NOT be allowed to see
    # tokens that come after it (that would be cheating -- looking at
    # the answer). We enforce this by setting those scores to -infinity
    # before softmax, so softmax gives them ~0 weight.
    T = x.shape[0]
    mask = torch.tril(torch.ones(T, T)).bool()
    # ^ torch.tril = "lower triangular" -- a TxT grid of 1s below/on the
    # diagonal, 0s above it. Row i, column j is True only if j <= i
    # (token i is allowed to see token j only if j comes at or before i).
    scores = scores.masked_fill(~mask, float("-inf"))
    # ^ everywhere mask is False (future tokens), set score to -infinity.
    # e^(-infinity) = 0, so after softmax those positions get exactly 0 weight.

    weights = F.softmax(scores, dim=-1)   # same softmax as script 04, now masked
    return weights @ V                     # (T, d_head) -- weighted blend of Values

def multi_head_attention(x, layer):
    # run attention_head() once per head, using that layer's own weights
    heads_out = [attention_head(x, layer["W_q"][h], layer["W_k"][h], layer["W_v"][h])
                 for h in range(n_heads)]
    concatenated = torch.cat(heads_out, dim=-1)   # (T, d_head * n_heads) = (T, d_model)
    return concatenated @ layer["W_o"]             # final learned mixing of all heads' info

def feedforward(x, layer):
    # identical logic to script 04's feedforward() -- two linear layers
    # with a relu (nonlinearity) in between, applied to every token.
    hidden = torch.relu(x @ layer["W1"] + layer["b1"])   # (T, d_ff)
    return hidden @ layer["W2"] + layer["b2"]              # (T, d_model)

def forward(token_ids):
    # token_ids: a 1D tensor/list of integer character IDs, e.g. [7, 2, 19, ...]
    T = len(token_ids)
    x = token_emb[token_ids] + pos_emb[:T]
    # ^ look up each token's embedding, add positional info for its slot.
    # same idea as script 04's "x = x + pos".
    for layer in layers:
        x = x + multi_head_attention(x, layer)   # residual connection (from script 04 step 7)
        x = x + feedforward(x, layer)             # residual connection
    logits = x @ W_out + b_out   # (T, vocab_size) -- raw prediction scores, one row per input position
    return logits
    # NOTE: logits are NOT probabilities yet -- softmax happens later,
    # either inside the loss function (during training) or explicitly
    # (during generation).


# ------------------------------------------------------------------------
# training loop -- this is where actual learning happens.
# ------------------------------------------------------------------------
def get_batch():
    # pick one random starting point in the corpus, grab a block_size
    # chunk as input (x), and the SAME chunk shifted one character to
    # the right as the target (y) -- "given these chars, predict the
    # next char at every position."
    i = torch.randint(0, len(data) - block_size - 1, (1,)).item()
    x = data[i:i + block_size]              # e.g. characters 0..15
    y = data[i + 1:i + block_size + 1]      # characters 1..16 (each one is "the next char after x's same position")
    return x, y

print(f"vocab_size={vocab_size}  params={sum(p.numel() for p in all_params)}")
print("training...\n")

for step in range(n_steps):
    x, y = get_batch()               # get one random training example
    logits = forward(x)              # run the forward pass -> (T, vocab_size) predictions
    loss = F.cross_entropy(logits, y)
    # ^ cross-entropy loss: the classification version of the mean-squared-error
    # loss from script 01. It compares the predicted probability distribution
    # (after an internal softmax) against the true next-character at every
    # position, and penalizes the model more the further off its
    # confidence was from the correct answer.

    optimizer.zero_grad()   # clear old gradients (they'd otherwise accumulate/add up across steps)
    loss.backward()
    # ^ THIS is the automatic differentiation. PyTorch walks backward
    # through every operation used to compute `loss` -- cross_entropy,
    # W_out, both feedforward layers, both attention layers, the
    # embeddings, all of it -- and computes d(loss)/d(param) for every
    # single trainable tensor, automatically. This is what you'd have had
    # to derive by hand in numpy.
    optimizer.step()
    # ^ actually applies the update: nudges every parameter using its
    # freshly computed gradient (Adam's version of `w -= lr * dw`).

    if step % 200 == 0:                                   # progress printout every 200 steps
        print(f"step {step:4d}  loss={loss.item():.3f}")

print(f"\nfinal loss: {loss.item():.3f}")

# ------------------------------------------------------------------------
# checkpoint saving -- write current weights to disk so next time this
# script runs, it loads (above) and keeps improving instead of
# starting over from random.
# ------------------------------------------------------------------------
os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)   # create checkpoints/ folder if it doesn't exist yet
torch.save(state_dict(), CHECKPOINT_PATH)
# ^ torch.save pickles the whole nested dict of tensors to one file.
# nothing fancy -- same idea as json.dump, just for tensors.
print(f"saved checkpoint to {CHECKPOINT_PATH}")


# ------------------------------------------------------------------------
# generate: after training, feed it a prompt and sample new characters
# one at a time, using its own predictions.
# ------------------------------------------------------------------------
@torch.no_grad()   # tells PyTorch "don't bother tracking gradients here" -- we're not training, just predicting
def generate(prompt, n_new_chars=60):
    ids = encode(prompt)                     # turn the starting text into IDs
    for _ in range(n_new_chars):             # generate one character at a time, n_new_chars times
        context = ids[-block_size:]          # only the last block_size chars fit in the model's context window
        logits = forward(torch.tensor(context, dtype=torch.long))
        next_logits = logits[-1]             # we only care about the prediction for the NEXT character
                                              # (last row = prediction that comes after the last input token)
        probs = F.softmax(next_logits, dim=-1)   # turn logits into an actual probability distribution
        next_id = torch.multinomial(probs, num_samples=1).item()
        # ^ randomly SAMPLE one character according to those probabilities
        # (not always picking the single highest -- that would make output
        # repetitive/deterministic. sampling adds natural variation, same
        # tradeoff every LLM chat model makes with "temperature").
        ids.append(next_id)                  # add the new character, then loop -- it becomes part of the next context
    return decode(ids)

print("\ngenerated:")
print(generate("i am the "))
