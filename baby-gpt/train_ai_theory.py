"""
Train Baby-GPT on AI Theory Text
"""
import torch
import torch.nn as nn
from torch.optim import AdamW
from tqdm import tqdm
import os

import config_ai_theory as config
from model import GPT
from dataset import TextDataset, CharTokenizer

def estimate_loss(model, dataset, eval_iters):
    """Estimate loss on train and val sets"""
    model.eval()
    out = {}
    
    for split in ['train', 'val']:
        losses = []
        for _ in range(eval_iters):
            x, y = dataset.get_batch(split, config.batch_size)
            x, y = x.to(config.device), y.to(config.device)
            with torch.no_grad():
                _, loss = model(x, y)
            losses.append(loss.item())
        out[split] = sum(losses) / len(losses)
    
    model.train()
    return out

def train():
    """Main training loop"""
    
    # Prepare dataset
    print("Loading AI theory dataset...")
    dataset = TextDataset(config.data_file, config.block_size, config.train_split)
    tokenizer = dataset.tokenizer
    
    print(f"Vocabulary size: {tokenizer.vocab_size}")
    print(f"Training examples: {len(dataset.train_data)}")
    print(f"Validation examples: {len(dataset.val_data)}")
    
    # Initialize model
    print("\nInitializing model...")
    model = GPT(
        vocab_size=tokenizer.vocab_size,
        n_embd=config.n_embd,
        n_head=config.n_head,
        n_layer=config.n_layer,
        block_size=config.block_size,
        dropout=config.dropout
    ).to(config.device)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M")
    
    # Optimizer
    optimizer = AdamW(model.parameters(), lr=config.learning_rate)
    
    # Training loop
    print(f"\nTraining for {config.max_iters} iterations...")
    print("=" * 60)
    
    model.train()
    pbar = tqdm(range(config.max_iters), desc="Training")
    
    for iter in pbar:
        # Get batch
        x, y = dataset.get_batch('train', config.batch_size)
        x, y = x.to(config.device), y.to(config.device)
        
        # Forward pass
        logits, loss = model(x, y)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Update progress bar
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        # Evaluate
        if (iter + 1) % config.eval_interval == 0:
            losses = estimate_loss(model, dataset, config.eval_iters)
            print(f"\nIteration {iter + 1}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")
            
            # Generate sample
            print("\nSample generation:")
            print("-" * 60)
            context = torch.zeros((1, 1), dtype=torch.long, device=config.device)  # Start with newline
            sample = model.generate(context, max_new_tokens=200, temperature=config.temperature, top_k=config.top_k)[0]
            print(tokenizer.decode(sample.tolist()))
            print("-" * 60)
        
        # Save checkpoint
        if (iter + 1) % config.checkpoint_interval == 0 or (iter + 1) == config.max_iters:
            os.makedirs(config.checkpoint_dir, exist_ok=True)
            checkpoint_path = os.path.join(config.checkpoint_dir, f'checkpoint_{iter + 1}.pt')
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'iteration': iter + 1,
                'config': {
                    'vocab_size': tokenizer.vocab_size,
                    'n_embd': config.n_embd,
                    'n_head': config.n_head,
                    'n_layer': config.n_layer,
                    'block_size': config.block_size,
                    'dropout': config.dropout,
                }
            }, checkpoint_path)
            print(f"\nCheckpoint saved: {checkpoint_path}")
    
    # Save final checkpoint
    final_path = os.path.join(config.checkpoint_dir, 'latest.pt')
    
    # Get tokenizer vocabulary
    if hasattr(tokenizer, 'itos'):
        tokenizer_vocab = [tokenizer.itos[i] for i in range(tokenizer.vocab_size)]
    else:
        tokenizer_vocab = None
    
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'iteration': config.max_iters,
        'tokenizer_vocab': tokenizer_vocab,
        'config': {
            'vocab_size': tokenizer.vocab_size,
            'n_embd': config.n_embd,
            'n_head': config.n_head,
            'n_layer': config.n_layer,
            'block_size': config.block_size,
            'dropout': config.dropout,
        }
    }, final_path)
    
    print(f"\n✓ Training complete! Final model saved to {final_path}")

if __name__ == "__main__":
    train()
