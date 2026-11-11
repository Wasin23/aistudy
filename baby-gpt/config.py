"""
Model configuration.
"""

# Model architecture
n_layer = 6          # Number of transformer blocks
n_head = 6           # Number of attention heads
n_embd = 384         # Embedding dimension
block_size = 256     # Max sequence length (context window)
dropout = 0.2        # Dropout rate

# Training
batch_size = 64      # Batch size
learning_rate = 3e-4 # Learning rate
max_iters = 5000     # Training iterations
eval_interval = 500  # How often to evaluate
eval_iters = 200     # Number of batches for evaluation

# Data
train_split = 0.9    # Train/val split

# Vocab size (set by tokenizer, will be overwritten)
vocab_size = None
