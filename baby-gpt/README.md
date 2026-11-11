# Build Your Own GPT

A minimal GPT implementation from scratch in PyTorch. Understand how transformers actually work by building one.

## What You'll Learn
- Multi-head self-attention mechanism
- Positional embeddings
- Layer normalization and residual connections
- Training loop and loss optimization
- Text generation strategies (greedy, temperature, top-k, nucleus)

## Structure
```
model.py          - Transformer architecture (attention, blocks, GPT)
train.py          - Training loop with loss tracking
generate.py       - Text generation with various sampling methods
dataset.py        - Data loading and tokenization
config.py         - Model hyperparameters
```

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Train on Shakespeare (~35 min on RTX 4060)
python train.py

# Generate text
python generate.py --checkpoint checkpoints/latest.pt --prompt "To be or not to be"
```

## Model Size
- Default: ~10M parameters (10.79M exactly)
- Architecture: 6 layers, 6 heads, 384 embedding dim, 256 context window
- Training: 5000 iterations, batch size 64

---

## How This Actually Works (The Real Math)

### 1. Tokenization: Text → Numbers
```python
"Hello" → [H, e, l, l, o] → [47, 42, 49, 49, 52]  # Character IDs
```

### 2. Embeddings: Numbers → Vectors
```python
# Each character ID becomes a 384-dimensional vector
token_embedding = embedding_table[47]  # [0.12, -0.45, 0.87, ..., 0.33]

# Add position information
position_embedding = position_table[0]  # "This is position 0"

# Combined representation
x = token_embedding + position_embedding
```

### 3. Self-Attention: The Core Mechanism

For each token, compute 3 vectors:

**Query (Q):** "What am I looking for?"
```python
Q = query_weight @ x
```

**Key (K):** "What do I contain?"
```python
K = key_weight @ x
```

**Value (V):** "What information do I offer?"
```python
V = value_weight @ x
```

**Compute attention scores:**
```python
# Dot product measures similarity
scores = Q @ K.transpose() / sqrt(head_size)
# Example: [0.2, 0.8, 0.1, 0.5] - token at position 1 is most relevant

# Softmax converts to probabilities (sums to 1)
attention_weights = softmax(scores)  # [0.15, 0.55, 0.10, 0.20]

# Weighted average of values
output = attention_weights @ V  # Mix past tokens based on relevance
```

**Why this works:**
- High Q·K score = "this past token is relevant to predicting next"
- After seeing "Romeo and", the model learns to pay attention to "Juliet" from earlier in the context
- These patterns are learned from data, not hardcoded

### 4. Multi-Head Attention

Run 6 attention heads in parallel, each learning different patterns:
- Head 1: might learn subject-verb agreement
- Head 2: might track character names
- Head 3: might handle punctuation patterns
- etc.

Concatenate all heads and project back to 384 dimensions.

### 5. Feed-Forward Network (MLP)
```python
# After attention, transform the representation
hidden = GELU(W1 @ x)  # Expand to 4x size (1536 dim), add non-linearity
output = W2 @ hidden    # Compress back to 384 dim
```

### 6. Training: How It Learns

**Task:** Predict the next character
- Input: "To be or not to b"
- Target: next char should be "e"

**Forward Pass:**
```python
# Model outputs probability distribution over all 65 characters
probabilities = [0.02, 0.03, ..., 0.91, ..., 0.01]
#                                  ^ position 42 = 'e'
```

**Loss Calculation (Cross-Entropy):**
```python
loss = -log(probabilities[42])  # Punish if 'e' has low probability

# If model predicts 'e' with 91% confidence: loss = -log(0.91) = 0.09 ✓ good
# If model predicts 'e' with 10% confidence: loss = -log(0.10) = 2.30 ✗ bad
```

**Backpropagation (Chain Rule):**
```python
# Compute gradient: ∂loss/∂weight for every one of 10.79M weights
# Tells us: "increase/decrease this weight to reduce loss"
gradients = autograd(loss)  # PyTorch computes this automatically

# Update weights (tiny adjustment)
weight = weight - learning_rate * gradient
# Example: 0.342 → 0.341997
```

**Repeat 5000 times:**
- Batch 1: loss 4.15 → update weights
- Batch 2: loss 4.10 → update weights
- ...
- Batch 5000: loss 0.95 → model learned patterns!

### 7. What It Learns Over Time

**Early training (loss ~4.0):**
- Random gibberish: "xKz3!vB$"
- Learning: letters exist, basic frequency

**Middle training (loss ~2.0):**
- Common pairs: "the", "and", "ing"
- Learning: words, basic grammar

**Late training (loss ~1.0):**
- Shakespeare style: "ROMEO: Give me thy hand"
- Learning: character names, verse structure, dialogue format

### 8. Generation: Making New Text

**Autoregressive sampling:**
```python
context = "To be or not to"
for _ in range(100):  # Generate 100 more characters
    # Get probabilities for next character
    probs = model(context)[-1]  # [0.02, ..., 0.35, ..., 0.01]
    
    # Sample (with temperature for randomness)
    next_char = sample(probs, temperature=0.8)
    
    # Append and continue
    context = context + next_char
```

**Temperature effect:**
- Low (0.3): "To be or not to be, that is the question" (conservative)
- High (1.5): "To be or nix to bree, thutz zis the squibble" (creative/random)

**Top-k sampling:**
Only consider top 40 most likely characters, ignore rest. Prevents completely nonsensical choices.

---

## Understanding Scale: Your GPT vs ChatGPT

**Your Baby GPT:**
- 10M parameters
- 1M training tokens (Shakespeare)
- 35 min training on RTX 4060
- Cost: $0
- Capabilities: Mimic Shakespeare style, frequent errors, no reasoning

**ChatGPT (GPT-4):**
- ~1.7 **trillion** parameters (170,000x bigger)
- ~13 **trillion** training tokens (entire internet)
- Months of training on thousands of H100 GPUs
- Cost: ~$100M+
- Capabilities: Write, reason, code, multi-domain understanding, instruction following

**Why the difference?**
- **Scale:** More parameters = more knowledge capacity
- **Data:** Internet vs single book
- **Training:** RLHF (Reinforcement Learning from Human Feedback) for instruction following
- **Architecture:** GPT-4 likely uses mixture-of-experts, better positional encodings
- **Context:** Your 256 tokens vs GPT-4's 128k tokens

The jump is like paper airplane → 747. Same physics (lift, drag), completely different scale.

---

## Deep Dive Learning Path

### Week 1-2: Math Foundations
**Prerequisites:**
- Linear algebra: matrix multiplication, dot products, eigenvalues
- Calculus: derivatives, chain rule, gradients
- Probability: distributions, expectation

**Resources:**
- 3Blue1Brown "Essence of Linear Algebra" (YouTube series)
- 3Blue1Brown "Neural Networks" series
- Khan Academy calculus review

**Do:**
- Code matrix operations from scratch in NumPy
- Implement gradient descent on a simple function
- Visualize matrix transformations

### Week 3-4: Neural Network Basics
**Learn:**
- Perceptron, activation functions
- Backpropagation by hand
- Loss functions, optimization

**Resources:**
- Andrej Karpathy's "Neural Networks: Zero to Hero" (YouTube)
- Michael Nielsen's "Neural Networks and Deep Learning" (free book)

**Do:**
- Build 2-layer neural network from scratch (no PyTorch)
- Implement micrograd (60 lines of automatic differentiation)
- Train on MNIST handwritten digits

### Week 5-6: Attention Mechanism
**Learn:**
- Scaled dot-product attention
- Multi-head attention
- Positional encodings
- Causal masking

**Resources:**
- "Attention is All You Need" paper (original transformer)
- Jay Alammar's "Illustrated Transformer" blog post
- Annotated Transformer (Harvard NLP)

**Do:**
- Code single-head attention from scratch
- Visualize attention weights on example sentences
- Build baby transformer for toy task (e.g., learns "234 + 567 = 801")

### Week 7-8: Scale It Up
**Learn:**
- Tokenization (BPE, WordPiece)
- Training dynamics (learning rate schedules, warmup, decay)
- GPU optimization (batching, mixed precision, gradient accumulation)
- Debugging training (loss spikes, gradient norms, NaN handling)

**Resources:**
- SentencePiece documentation
- "Training Tips for Transformer Models" papers
- PyTorch Performance Tuning Guide

**Do:**
- Train 100M parameter model on Wikipedia
- Implement learning rate scheduler
- Use mixed precision training (fp16)
- Monitor with TensorBoard

### Week 9-10: Advanced Topics
**Learn:**
- RLHF (Reinforcement Learning from Human Feedback)
- Fine-tuning techniques (LoRA, prefix tuning)
- Quantization (8-bit, 4-bit inference)
- Efficient inference (KV-cache, speculative decoding)

**Resources:**
- InstructGPT paper (RLHF)
- LoRA paper + PEFT library
- bitsandbytes documentation
- vLLM inference engine

**Do:**
- Fine-tune Llama 3.2 1B with LoRA on custom dataset
- Implement 8-bit quantization
- Deploy model with FastAPI
- Build eval harness for your use case

### Supplementary Resources
**Papers (in order):**
1. "Attention is All You Need" (2017) - Original transformer
2. "BERT: Pre-training of Deep Bidirectional Transformers" (2018)
3. "Language Models are Few-Shot Learners" (GPT-3, 2020)
4. "Training language models to follow instructions" (InstructGPT, 2022)
5. "LLaMA: Open and Efficient Foundation Language Models" (2023)

**Code Repositories:**
- nanoGPT (Karpathy) - Clean GPT implementation
- llm.c - Transformer in pure C (see raw performance)
- minGPT - Minimal PyTorch implementation
- transformers (HuggingFace) - Production library

**Books:**
- "Deep Learning" by Goodfellow, Bengio, Courville (chapters 6-10)
- "Speech and Language Processing" by Jurafsky & Martin (chapter 9-10)

**YouTube Channels:**
- Andrej Karpathy
- StatQuest with Josh Starmer
- Yannic Kilcher (paper reviews)

### Practice Projects (Build These)
1. **Character-level language model** (this repo)
2. **Token-level GPT** on Wikipedia
3. **Code completion model** (train on GitHub repos)
4. **Chatbot fine-tuned** on conversation data
5. **Domain-specific model** (medical, legal, finance)

---

## Next Steps After Training

Once your model finishes training (~35 min):

1. **Generate text:**
```bash
python generate.py --prompt "ROMEO:" --tokens 200 --temperature 0.8
```

2. **Try different temperatures:**
```bash
# Conservative (0.3)
python generate.py --prompt "To be" --temperature 0.3

# Creative (1.2)
python generate.py --prompt "To be" --temperature 1.2
```

3. **Train on your own text:**
- Put text file in `data/mydata.txt`
- Update `train.py` to use your file
- Retrain and see it learn your style

4. **Increase model size:**
- Edit `config.py`: increase `n_layer`, `n_head`, `n_embd`
- Will take longer to train but can learn more complex patterns

5. **Add features:**
- Top-p (nucleus) sampling
- Repetition penalty
- Beam search
- Prompt engineering

---

## Common Questions

**Q: Why character-level instead of tokens?**
A: Simpler for learning. Real models use BPE/WordPiece for efficiency.

**Q: Why is training slow?**
A: Make sure you have CUDA PyTorch installed. Check with:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**Q: Can I train on longer context?**
A: Yes, increase `block_size` in config.py. Needs more memory.

**Q: How do I avoid overfitting?**
A: Increase dropout, add more diverse training data, use regularization.

**Q: What if loss stops improving?**
A: Lower learning rate, increase model size, or you've reached limit of data.

**Q: How is this different from RNNs/LSTMs?**
A: Transformers process all positions in parallel (faster) and have better long-range memory via attention.

---

## Test Your Understanding

After reading this, you should be able to:
1. Explain what Q, K, V matrices do and why we need all three
2. Draw the flow of data through one transformer block
3. Calculate parameter count (hint: embeddings + 6 * block_params)
4. Explain why we use causal masking during training
5. Describe what happens during one training iteration
6. Explain the difference between temperature and top-k sampling
7. Calculate the loss for a specific prediction
8. Trace backpropagation through one attention head

Ask for a test when ready!

---

## COMPREHENSIVE ANSWER KEY: Understanding Transformers

### PART 1: CONCEPTUAL QUESTIONS

#### Q1: Feed "HELLO" into baby-gpt. Walk through every transformation.

**COMPLETE ANSWER:**

**Step 1: Tokenization**
- Input: "HELLO"
- Characters: ['H', 'E', 'L', 'L', 'O']
- Token IDs: [20, 17, 24, 24, 27] (example IDs)
- Shape: (5,) - just a list of 5 integers

**Step 2: Token Embeddings**
- Each ID → 384-dimensional vector via lookup table
- Shape: (1, 5, 384) 
  - 1 = batch size
  - 5 = sequence length
  - 384 = embedding dimension
- This is just a matrix lookup: `embedding_table[token_id]`

**Step 3: Positional Embeddings**
- Add position information: position 0, 1, 2, 3, 4
- Each position has its own learned 384-dim vector
- Shape: (1, 5, 384)
- **ADD** (not concatenate) to token embeddings: `x = token_emb + pos_emb`
- Result shape: (1, 5, 384)

**Step 4: Transformer Blocks (6 layers)**
For each of 6 layers:
- **Layer Norm 1**
- **Multi-Head Attention:** Each token computes weighted average of previous tokens
  - Split into 6 heads, each processes different aspects
  - Compute Q, K, V matrices
  - Attention weights = softmax(QK^T / sqrt(head_dim))
  - Output = attention_weights @ V
  - Concatenate all 6 heads
- **Residual connection:** Add input back to output
- **Layer Norm 2**
- **Feed-Forward:** 2-layer MLP with ReLU
- **Residual connection:** Add input back to output
- Output shape: (1, 5, 384) - same shape throughout

**Step 5: Final Layer Norm**
- Normalize: shape stays (1, 5, 384)

**Step 6: Output Projection**
- Linear layer: 384 dims → 65 dims (vocab size)
- Shape: (1, 5, 65)
- These are **logits** (raw scores, not probabilities)

**Step 7: Take Last Position**
- We only care about position 4 (after "O")
- Extract: logits[0, 4, :] 
- Shape: (65,) - one score per character

**Step 8: Softmax**
- Convert logits to probabilities: `probs = softmax(logits)`
- Sum = 1.0
- Example: [0.001, 0.003, ..., 0.15, ..., 0.002]
- Character with highest probability is most likely next

**Step 9: Sampling**
- Randomly pick based on probabilities
- Temperature scaling optional: `logits / temperature`
- Sample: `next_char = random_choice(chars, probs)`

---

#### Q2: Why add positional embeddings instead of concatenating?

**Adding (what we do):**
```python
token_emb:  [0.2, -0.5,  0.8, ...]  (384 dims)
pos_emb:    [0.1,  0.3, -0.2, ...]  (384 dims)
result:     [0.3, -0.2,  0.6, ...]  (384 dims)
```
- Result is still 384 dimensions
- Token and position info **blend together** in the same space
- Model learns to interpret mixed representation

**Concatenating (wrong):**
```python
token_emb:  [0.2, -0.5,  0.8, ...]  (384 dims)
pos_emb:    [0.1,  0.3, -0.2, ...]  (384 dims)
result:     [0.2, -0.5, ..., 0.1, 0.3, ...]  (768 dims!)
```
- Result is 768 dimensions
- Token info and position info are **separate**
- Doubles model size unnecessarily
- Harder to learn relationships between token identity and position

**Why addition works:**
- Embeddings are high-dimensional (384 dims)
- Plenty of room for both token and position info
- Model learns to disentangle them through training
- More parameter-efficient

---

#### Q3: Why divide by sqrt(d_k) in attention?

**The formula:** softmax(QK^T / sqrt(d_k)) V

**Why the division:**

When you compute QK^T, you're doing dot products. Dot products grow with dimensionality:

```python
# If Q and K have large values and many dimensions
Q = [1, 1, 1, ..., 1]  # 64 dimensions
K = [1, 1, 1, ..., 1]  # 64 dimensions
Q · K = 64  # Large!
```

**Without scaling (d_k = 64):**
```
QK^T before softmax: [45.2, 38.7, 52.1, 29.4]
softmax([45.2, 38.7, 52.1, 29.4]) = [0.006, 0.0001, 0.9938, 0.00001]
```
- Dot products are huge
- Softmax saturates (one value near 1.0, others near 0)
- Gradients vanish
- Model can't learn

**With scaling (divide by sqrt(64) = 8):**
```
QK^T / sqrt(d_k): [5.65, 4.84, 6.51, 3.68]
softmax([5.65, 4.84, 6.51, 3.68]) = [0.26, 0.11, 0.60, 0.03]
```
- Scores are moderate
- Softmax produces distributed attention
- Gradients flow properly
- Model learns

**The math:** For random Q, K with unit variance, QK^T has variance d_k. Dividing by sqrt(d_k) normalizes variance to 1.

---

#### Q4: What does causal masking prevent?

Causal masking prevents tokens from attending to **future** tokens.

**Example with "The king said":**

**Without causal masking (BAD):**
```
Attention weights:
       The  king  said
The   [0.2   0.3   0.5]  ← "The" can attend to "said" (future!)
king  [0.1   0.4   0.5]  ← "king" can attend to "said" (future!)
said  [0.2   0.3   0.5]  ← "said" attends to all
```
- "The" can see "said" is coming
- "king" can see "said" is coming
- During training, model learns to cheat: just copy the answer
- During generation, future tokens don't exist → model fails

**With causal masking (GOOD):**
```
Attention weights:
       The  king  said
The   [1.0   -∞    -∞ ]  ← Can only attend to "The"
king  [0.4   0.6   -∞ ]  ← Can attend to "The", "king" only
said  [0.2   0.3   0.5]  ← Can attend to all previous tokens
```
- Set future positions to `-∞` before softmax
- After softmax: `-∞` becomes 0.0 (no attention)
- Each position can only use information from the past
- Matches generation: when predicting token N, you only have tokens 0...N-1

**Implementation:**
```python
# Create mask matrix (lower triangular)
mask = torch.tril(torch.ones(seq_len, seq_len))
# [[1, 0, 0],
#  [1, 1, 0],
#  [1, 1, 1]]

# Apply mask
scores = Q @ K.T / sqrt(d_k)
scores = scores.masked_fill(mask == 0, float('-inf'))
weights = softmax(scores)
```

---

#### Q5: Why did vowels cluster together?

**CORRECT ANSWER:**

Vowels clustered together because of **distributional similarity** - they appear in similar contexts.

**How the model learned this:**

1. **Objective:** Predict next character
2. **Pattern in data:** After consonants, vowels often follow
   - "th**e**", "s**a**id", "k**i**ng", "l**o**ve", "y**o**u"
   
3. **Gradient descent logic:**
   - When model sees "th", it needs to predict 'e'
   - When model sees "s", it might predict 'a' or 'o'
   - The embedding for 'e' gets pushed to represent "thing that comes after 'th'"
   - The embedding for 'a' gets pushed to represent "thing that comes after 's'"
   - But both 'e' and 'a' follow CONSONANTS in general
   
4. **Convergence:**
   - All vowels share statistical property: they follow consonants
   - Gradient descent pushes their embeddings close together
   - They cluster in embedding space

**Example loss gradient:**
```
Input: "lov"
Target: "e"

If embedding for 'e' is far from "things that follow 'v'",
loss is high. Gradient pushes 'e' closer.

Input: "you"  
Target: "u"

If embedding for 'u' is far from "things that follow 'o'",
loss is high. Gradient pushes 'u' closer.

Both 'e' and 'u' end up in similar region of embedding space
because they fulfill similar roles in the language.
```

**You never told it vowels are similar** - it discovered this by minimizing prediction loss across millions of examples.

---

### PART 2: MATH QUESTIONS

#### Q6: Matrix shapes in attention

Given:
- Q: (4, 3) - 4 tokens, 3 dimensions
- K: (4, 3)
- V: (4, 3)

**Q @ K^T:**
- Q: (4, 3)
- K^T: (3, 4) ← transposed
- **Q @ K^T: (4, 4)**

This is the attention score matrix - each token attends to each token.

**Final attention output:**
- Weights: (4, 4) ← after softmax of Q@K^T
- V: (4, 3)
- **Weights @ V: (4, 3)**

Output has same shape as input (4 tokens, 3 dimensions each).

---

#### Q7: Attention weights [0.1, 0.6, 0.2, 0.1] for token 3

Token 3 is creating its new representation by taking a **weighted average** of all token values:

- **60% from token 2** (strongest attention)
- **20% from token 3** (itself)
- **10% from token 1**
- **10% from token 0**

**Concrete example:** Sentence "The king said"
- Token 0: "The"
- Token 1: "king"
- Token 2: "said"
- Token 3: (predicting next)

Weights [0.1, 0.6, 0.2, 0.1] means:
- Token 3 pays most attention to "said" (60%)
- Some attention to itself (20%)
- Little attention to "king" (10%), "The" (10%)

**In code:**
```python
output_token_3 = (
    0.1 * value_token_0 +
    0.6 * value_token_1 +
    0.2 * value_token_2 +
    0.1 * value_token_3
)
```

Where each value_token is a 384-dim vector. You're making a **weighted smoothie** of previous tokens' representations.

---

### PART 3: DEBUGGING

#### Q8: Forgot causal masking during training

**During training WITHOUT causal mask:**
```
Input:  "The king said hello"
Target: "he king said hello "  (shifted by 1)

Token "The" can attend to entire sequence including "hello"
→ Learns to copy "h" from position 4
Token "king" can attend to "hello"
→ Learns to copy "e" from position 5
```

- Model memorizes: "just look at the answer and copy it"
- Training loss → 0 (perfect prediction)
- But this strategy doesn't work during generation!

**During generation WITHOUT causal mask:**
```
Input: "The king"
Trying to predict next token...

Token "king" tries to attend to future tokens
But future tokens don't exist yet!
Attention weights blow up or become undefined
Model outputs garbage
```

**Fix:** Causal mask forces training to match generation conditions.

---

#### Q9: Same positional embedding for all positions

If every position gets the same positional embedding:

```python
pos_emb = embedding_table[0]  # Always position 0
x = token_emb + pos_emb        # Every token gets same position info
```

**What breaks:**
- Model has NO IDEA about token order
- "The king said" looks identical to "said king The"
- Attention can't distinguish between "attend to previous token" vs "attend to token 3 positions back"
- Grammar breaks: subject-verb agreement fails
- Context understanding fails: can't tell what came before what

**Example:**
```
Input: "king said"
Without positions: Just knows [king_vec + pos0, said_vec + pos0]
Model can't tell which came first!

With positions: [king_vec + pos0, said_vec + pos1]
Model knows: "said" is AFTER "king"
```

Position embeddings encode **sequence order**. Without unique positions, you lose temporal structure entirely.

---

#### Q10: Massive learning rate (0.1 instead of 3e-4)

Learning rate controls how big the weight updates are.

**Normal learning rate (3e-4):**
```
weights = [0.5, -0.2, 0.8]
gradient = [0.1, -0.05, 0.02]
update = weights - 0.0003 * gradient
      = [0.49997, -0.19998, 0.79999]
Small, stable updates
```

**Huge learning rate (0.1):**
```
weights = [0.5, -0.2, 0.8]
gradient = [0.1, -0.05, 0.02]
update = weights - 0.1 * gradient
      = [0.49, -0.195, 0.798]

Next step: gradient might be [-0.3, 0.2, -0.1]
update = [0.52, -0.215, 0.808]

Next step: gradient is [0.5, -0.4, 0.3]
update = [0.47, -0.175, 0.778]
```

**The problem:**
- Updates are TOO BIG
- Model overshoots optimal weights
- Loss goes down, then UP, then down, then UP
- Like trying to land in a valley but taking huge jumps - you keep jumping past it
- Never converges

**Visualization:**
```
Loss landscape:
    |      *         *     ← oscillates
    |        \     /
    |         \   /
    |__________\_/_________ ← optimal (never reaches)

Small LR: smooth descent into valley
Large LR: bounces back and forth, never settles
```

---

### PART 4: DESIGN CHOICES

#### Q11: Why 6 layers instead of 1 giant layer?

**Hierarchical abstraction** - each layer learns different level of patterns.

**Layer 1:**
- Learns low-level patterns
- Character combinations ("th", "ing", "ed")
- Basic syntax (spaces after words)

**Layer 2-3:**
- Learns medium-level patterns
- Word relationships ("the king")
- Basic grammar (noun-verb patterns)

**Layer 4-5:**
- Learns high-level patterns
- Phrase structures ("said to the")
- Semantic relationships

**Layer 6:**
- Learns abstract patterns
- Story flow, character consistency
- Context-dependent meaning

**Why not 1 giant layer:**
- Harder to optimize (vanishing gradients)
- Less parameter-efficient (needs way more params for same capacity)
- Can't learn hierarchical features
- Empirically performs worse

**Analogy:** Like building a neural network for image recognition:
- Layer 1: edges
- Layer 2: corners, textures
- Layer 3: shapes
- Layer 4: object parts
- Layer 5: full objects

Each layer builds on previous, creating hierarchy.

---

#### Q12: Why 6 attention heads instead of 1 big head?

**Multiple heads learn different types of relationships simultaneously.**

**Head 1 might learn:** Subject-verb agreement
- "The king" → strong attention from "king" to "The"

**Head 2 might learn:** Adjective-noun relationships
- "brave king" → strong attention from "king" to "brave"

**Head 3 might learn:** Long-range dependencies
- "The king, who ruled for years, said" → "said" attends back to "king"

**Head 4 might learn:** Punctuation context
- Comma/period patterns

**Head 5 might learn:** Character name tracking
- When "ROMEO" appears, later "his" attends strongly back

**Head 6 might learn:** Dialogue structure
- "ROMEO: I love you." → structure recognition

**Why not 1 big head with 6x dimensions:**
- All attention patterns would be mixed together
- Harder to learn specialized relationships
- Less interpretable
- Empirically performs worse

**Math:**
- 6 heads × 64 dims each = 384 total
- Same parameter count as 1 head × 384 dims
- But better learning dynamics

---

### BONUS: OPTIMIZATION & PRODUCTION

#### Q13: Make baby-gpt 10x faster at generation

**1. KV Caching**
- **Problem:** Every token re-computes attention over all previous tokens
- **Solution:** Cache Key and Value matrices from previous tokens
- Generation step N: Only compute new K, V for token N, reuse K_0...K_{N-1}
- **Speedup:** 10-20x (saves ~90% of computation)

**2. Quantization (4-bit / 8-bit weights)**
- **Problem:** 16-bit floats use lots of memory and compute
- **Solution:** Convert weights to 4-bit or 8-bit integers
- Memory: 4x smaller
- Speed: 2-4x faster (less memory bandwidth)
- Quality loss: minimal (~1-2% worse)

**3. Flash Attention**
- **Problem:** Standard attention uses O(N²) memory for attention matrix
- **Solution:** Compute attention in chunks, never materialize full matrix
- Memory: O(N) instead of O(N²)
- Speed: 2-4x faster (fewer memory reads/writes)

**Other options:**
- Speculative decoding (draft model + verification)
- Distillation (train smaller model to mimic larger)
- Model pruning (remove unnecessary weights)
- Better hardware (GPU vs CPU)

---

#### Q14: Fine-tune Llama 3.1 8B on email dataset - 3 biggest risks

**Risk 1: Catastrophic Forgetting**
- Fine-tuning on small dataset (<10k examples) makes model forget general knowledge
- Loses grammar, punctuation, general writing ability
- Becomes overfitted to your specific email style
- **Mitigation:** Use LoRA (Low-Rank Adaptation) instead of full fine-tuning

**Risk 2: Data Quality Issues**
- If your email dataset has biases/errors, model learns them
- Example: If all examples are short, model only writes short emails
- If examples have templated language, model becomes repetitive
- **Mitigation:** Curate diverse, high-quality dataset (1k+ examples)

**Risk 3: Prompt Following Degradation**
- Llama learns your emails but forgets how to follow system prompts
- Ignores instructions like "write in friendly tone" or "mention [specific detail]"
- Becomes rigid, less controllable
- **Mitigation:** Include system prompt examples in fine-tuning data

**Bonus Risk 4: Inference Infrastructure**
- Llama 8B requires 16GB RAM (8-bit quant) or 8GB (4-bit quant)
- Need GPU for reasonable speed
- Must deploy model somewhere (Render won't cut it for GPU)
- **Mitigation:** Use serverless GPU (Modal, Replicate, Runpod)

---

## Key Takeaway

The most critical gap in understanding: **Attention is NOT nearest-neighbor search**. It's a weighted averaging mechanism where the model learns which past tokens are relevant for predicting the next token. Everything else in transformers exists to support this core mechanism.
