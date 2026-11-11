"""
Visualize the entire forward pass from input to output
Shows every step: tokens → embeddings → attention → layers → probabilities → sampling
"""

import torch
import numpy as np
from model import GPT
from dataset import CharTokenizer
from config import *
import matplotlib.pyplot as plt
import seaborn as sns

def load_model():
    """Load trained model"""
    checkpoint = torch.load('checkpoints/latest.pt', map_location='cpu')
    vocab_size = checkpoint['vocab_size']
    
    model = GPT(
        vocab_size=vocab_size,
        n_embd=n_embd,
        n_head=n_head,
        n_layer=n_layer,
        block_size=block_size,
        dropout=dropout
    )
    
    model.load_state_dict(checkpoint['model'])
    model.eval()
    return model

def visualize_forward_pass(model, tokenizer, text):
    """
    Visualize every step of the forward pass
    """
    print("=" * 80)
    print("COMPLETE FORWARD PASS VISUALIZATION")
    print("=" * 80)
    
    # STEP 1: TOKENIZATION
    print("\n" + "=" * 80)
    print("STEP 1: TOKENIZATION")
    print("=" * 80)
    print(f"\nInput text: \"{text}\"")
    
    tokens = tokenizer.encode(text)
    print(f"\nToken IDs: {tokens}")
    print(f"Number of tokens: {len(tokens)}")
    
    # Show character to ID mapping
    print("\nCharacter → Token ID mapping:")
    for char in text:
        token_id = tokenizer.encode(char)[0]
        print(f"  '{char}' → {token_id}")
    
    # STEP 2: EMBEDDINGS
    print("\n" + "=" * 80)
    print("STEP 2: TOKEN EMBEDDINGS")
    print("=" * 80)
    
    # Convert to tensor
    x = torch.tensor([tokens], dtype=torch.long)  # Shape: (1, seq_len)
    
    # Get token embeddings
    tok_emb = model.token_embedding_table(x)  # Shape: (1, seq_len, n_embd)
    print(f"\nEmbedding shape: {tok_emb.shape}")
    print(f"  Batch size: {tok_emb.shape[0]}")
    print(f"  Sequence length: {tok_emb.shape[1]}")
    print(f"  Embedding dimension: {tok_emb.shape[2]}")
    
    # Show first token's embedding (first 10 values)
    first_embedding = tok_emb[0, 0, :10].detach().numpy()
    print(f"\nFirst token '{text[0]}' embedding (first 10 dims): {first_embedding}")
    
    # STEP 3: POSITIONAL EMBEDDINGS
    print("\n" + "=" * 80)
    print("STEP 3: POSITIONAL EMBEDDINGS")
    print("=" * 80)
    
    pos = torch.arange(0, len(tokens), dtype=torch.long).unsqueeze(0)
    pos_emb = model.position_embedding_table(pos)
    
    print(f"Positional embedding shape: {pos_emb.shape}")
    print(f"Positions: {pos[0].tolist()}")
    
    # Show first position embedding
    first_pos_emb = pos_emb[0, 0, :10].detach().numpy()
    print(f"\nPosition 0 embedding (first 10 dims): {first_pos_emb}")
    
    # Combined embeddings
    x = tok_emb + pos_emb
    print(f"\nCombined embeddings shape: {x.shape}")
    
    # STEP 4: TRANSFORMER BLOCKS
    print("\n" + "=" * 80)
    print("STEP 4: TRANSFORMER BLOCKS (6 LAYERS)")
    print("=" * 80)
    
    for i, block in enumerate(model.blocks):
        x_before = x.clone()
        x = block(x)
        
        # Calculate how much the block changed the representation
        change = torch.norm(x - x_before).item()
        print(f"\nLayer {i+1}:")
        print(f"  Output shape: {x.shape}")
        print(f"  Magnitude of change: {change:.4f}")
    
    # STEP 5: FINAL LAYER NORM
    print("\n" + "=" * 80)
    print("STEP 5: LAYER NORMALIZATION")
    print("=" * 80)
    
    x = model.ln_f(x)
    print(f"Normalized output shape: {x.shape}")
    
    # STEP 6: OUTPUT PROJECTION
    print("\n" + "=" * 80)
    print("STEP 6: OUTPUT PROJECTION (LOGITS)")
    print("=" * 80)
    
    logits = model.lm_head(x)  # Shape: (1, seq_len, vocab_size)
    print(f"Logits shape: {logits.shape}")
    print(f"  Batch: {logits.shape[0]}")
    print(f"  Sequence: {logits.shape[1]}")
    print(f"  Vocabulary: {logits.shape[2]}")
    
    # Get logits for the last token (this predicts the next token)
    last_logits = logits[0, -1, :]
    print(f"\nLogits for last position (predicting next token): {last_logits.shape}")
    
    # Show top 10 raw logits
    top_logits, top_indices = torch.topk(last_logits, 10)
    print("\nTop 10 raw logits (before softmax):")
    for i, (logit, idx) in enumerate(zip(top_logits, top_indices)):
        char = tokenizer.decode([idx.item()])
        print(f"  {i+1}. '{char}' → logit: {logit.item():.4f}")
    
    # STEP 7: SOFTMAX (CONVERT TO PROBABILITIES)
    print("\n" + "=" * 80)
    print("STEP 7: SOFTMAX (LOGITS → PROBABILITIES)")
    print("=" * 80)
    
    probs = torch.softmax(last_logits, dim=-1)
    print(f"Probability shape: {probs.shape}")
    print(f"Sum of all probabilities: {probs.sum().item():.6f} (should be 1.0)")
    
    # Show top 10 probabilities
    top_probs, top_indices = torch.topk(probs, 10)
    print("\nTop 10 most likely next characters:")
    for i, (prob, idx) in enumerate(zip(top_probs, top_indices)):
        char = tokenizer.decode([idx.item()])
        print(f"  {i+1}. '{char}' → {prob.item()*100:.2f}%")
    
    # STEP 8: SAMPLING
    print("\n" + "=" * 80)
    print("STEP 8: SAMPLING NEXT TOKEN")
    print("=" * 80)
    
    # Sample with temperature
    temperature = 1.0
    scaled_logits = last_logits / temperature
    probs_temp = torch.softmax(scaled_logits, dim=-1)
    
    print(f"Temperature: {temperature}")
    print("Sampling strategy: Multinomial (random choice weighted by probability)")
    
    # Sample 10 times to show variety
    print("\n10 random samples from the distribution:")
    samples = torch.multinomial(probs_temp, num_samples=10, replacement=True)
    for i, sample in enumerate(samples):
        char = tokenizer.decode([sample.item()])
        prob = probs_temp[sample].item()
        print(f"  Sample {i+1}: '{char}' (probability: {prob*100:.2f}%)")
    
    # STEP 9: VISUALIZATION - ATTENTION WEIGHTS
    print("\n" + "=" * 80)
    print("STEP 9: ATTENTION PATTERN VISUALIZATION")
    print("=" * 80)
    print("\nExtracting attention weights from layer 3...")
    
    # Re-run forward pass to capture attention
    x = torch.tensor([tokens], dtype=torch.long)
    tok_emb = model.token_embedding_table(x)
    pos_emb = model.position_embedding_table(torch.arange(0, len(tokens)).unsqueeze(0))
    x = tok_emb + pos_emb
    
    # Get attention from one layer
    block = model.blocks[2]  # Use layer 3
    
    # Run through the block and extract attention
    # This requires modifying how we call the attention
    ln1_out = block.ln1(x)
    
    # Get Q, K, V from the attention heads
    B, T, C = ln1_out.shape
    
    # Get one head's attention pattern
    head = block.sa.heads[0]
    k = head.key(ln1_out)
    q = head.query(ln1_out)
    
    # Compute attention weights
    wei = q @ k.transpose(-2, -1) * (C ** -0.5)
    wei = wei.masked_fill(block.sa.heads[0].tril[:T, :T] == 0, float('-inf'))
    wei = torch.softmax(wei, dim=-1)
    
    # Visualize
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        wei[0].detach().numpy(),
        xticklabels=[f"'{c}'" for c in text],
        yticklabels=[f"'{c}'" for c in text],
        cmap='YlOrRd',
        square=True,
        cbar_kws={'label': 'Attention Weight'}
    )
    plt.title('Attention Weights (Layer 3, Head 1)\nRows = Query tokens, Columns = Key tokens', fontsize=14)
    plt.xlabel('Attending TO (keys)', fontsize=12)
    plt.ylabel('Attending FROM (queries)', fontsize=12)
    plt.tight_layout()
    plt.savefig('attention_weights.png', dpi=150, bbox_inches='tight')
    print("✓ Saved attention heatmap to 'attention_weights.png'")
    
    print("\nInterpretation:")
    print("  - Each row shows what one token attends to")
    print("  - Brighter = stronger attention")
    print("  - Lower triangle only (causal masking prevents looking ahead)")
    
    # STEP 10: PROBABILITY DISTRIBUTION VISUALIZATION
    print("\n" + "=" * 80)
    print("STEP 10: PROBABILITY DISTRIBUTION")
    print("=" * 80)
    
    plt.figure(figsize=(14, 6))
    
    # Show top 20 probabilities
    top_probs, top_indices = torch.topk(probs, 20)
    labels = [tokenizer.decode([idx.item()]) for idx in top_indices]
    
    plt.bar(range(20), top_probs.detach().numpy())
    plt.xticks(range(20), labels, rotation=0, fontsize=10)
    plt.xlabel('Character', fontsize=12)
    plt.ylabel('Probability', fontsize=12)
    plt.title(f'Top 20 Next Character Predictions after "{text}"', fontsize=14)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('probability_distribution.png', dpi=150, bbox_inches='tight')
    print("✓ Saved probability distribution to 'probability_distribution.png'")
    
    # STEP 11: COMPLETE GENERATION
    print("\n" + "=" * 80)
    print("STEP 11: COMPLETE GENERATION (50 TOKENS)")
    print("=" * 80)
    
    print(f"\nStarting text: \"{text}\"")
    print("\nGenerating...")
    
    context = torch.tensor([tokens], dtype=torch.long)
    
    with torch.no_grad():
        for i in range(50):
            context_cropped = context[:, -block_size:]
            logits, _ = model(context_cropped)
            logits = logits[:, -1, :] / 0.8  # Temperature
            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            context = torch.cat([context, next_token], dim=1)
    
    generated = tokenizer.decode(context[0].tolist())
    print(f"\nFinal output:\n{generated}")
    
    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - attention_weights.png")
    print("  - probability_distribution.png")
    print("\nKey insight: This entire process (tokenization → embeddings → attention →")
    print("layers → probabilities → sampling) happens for EVERY SINGLE TOKEN during")
    print("generation. The model predicts one token at a time, then feeds it back in.")

if __name__ == '__main__':
    # Load model and tokenizer
    print("Loading model and tokenizer...")
    with open('data/shakespeare.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    tokenizer = CharTokenizer(text)
    model = load_model()
    
    print("Model loaded!\n")
    
    # Visualize with a prompt
    test_text = "ROMEO: "
    visualize_forward_pass(model, tokenizer, test_text)
