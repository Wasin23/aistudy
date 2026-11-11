# Configuration for AI Theory Model Training

# Model architecture (same as Shakespeare model for comparison)
n_embd = 384          # Embedding dimension
n_head = 6            # Number of attention heads
n_layer = 6           # Number of transformer blocks
block_size = 256      # Maximum context length
dropout = 0.2         # Dropout rate

# Training parameters
batch_size = 64       # Batch size
learning_rate = 3e-4  # Learning rate
max_iters = 5000      # Training iterations (same as Shakespeare)
eval_interval = 500   # How often to evaluate
eval_iters = 200      # Number of iterations for evaluation

# Data
data_file = 'ai_theory.txt'  # AI theory text file
train_split = 0.9     # 90% for training, 10% for validation

# Generation
temperature = 0.8     # Sampling temperature
top_k = 50            # Top-k sampling parameter

# Device
device = 'cuda'       # Use GPU if available

# Checkpoint
checkpoint_dir = 'checkpoints_ai_theory'
checkpoint_interval = 1000
