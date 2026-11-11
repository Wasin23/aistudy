"""
Training script for baby GPT.
"""
import os
import torch
from tqdm import tqdm

import config
from dataset import TextDataset, download_shakespeare
from model import GPT


def estimate_loss(model, dataset, device):
    """Estimate loss on train and val sets."""
    model.eval()
    out = {}
    for split in ['train', 'val']:
        losses = torch.zeros(config.eval_iters)
        for k in range(config.eval_iters):
            X, Y = dataset.get_batch(split, config.batch_size)
            X, Y = X.to(device), Y.to(device)
            logits, loss = model(X, Y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    model.train()
    return out


def train(dataset_name='shakespeare', epochs=10):
    """Train the model."""
    
    # Setup
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Load dataset
    if dataset_name == 'shakespeare':
        data_path = download_shakespeare()
    else:
        data_path = f"data/{dataset_name}.txt"
    
    dataset = TextDataset(
        data_path,
        block_size=config.block_size,
        train_split=config.train_split,
        use_char=True  # Character-level for simplicity
    )
    
    # Update vocab size in config
    config.vocab_size = dataset.vocab_size
    
    # Initialize model
    model = GPT(
        vocab_size=config.vocab_size,
        n_embd=config.n_embd,
        n_head=config.n_head,
        n_layer=config.n_layer,
        block_size=config.block_size,
        dropout=config.dropout
    ).to(device)
    
    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    
    # Training loop
    print(f"\n🚀 Starting training for {config.max_iters} iterations...")
    model.train()
    
    for iter in tqdm(range(config.max_iters)):
        # Evaluate periodically
        if iter % config.eval_interval == 0 or iter == config.max_iters - 1:
            losses = estimate_loss(model, dataset, device)
            print(f"\nStep {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")
            
            # Generate sample
            context = torch.zeros((1, 1), dtype=torch.long, device=device)
            sample = model.generate(context, max_new_tokens=100, temperature=0.8)[0].tolist()
            print(f"Sample: {dataset.tokenizer.decode(sample)}\n")
        
        # Get batch
        xb, yb = dataset.get_batch('train', config.batch_size)
        xb, yb = xb.to(device), yb.to(device)
        
        # Forward pass
        logits, loss = model(xb, yb)
        
        # Backward pass
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    
    # Save checkpoint
    os.makedirs('checkpoints', exist_ok=True)
    checkpoint = {
        'model': model.state_dict(),
        'optimizer': optimizer.state_dict(),
        'config': {
            'n_layer': config.n_layer,
            'n_head': config.n_head,
            'n_embd': config.n_embd,
            'block_size': config.block_size,
            'dropout': config.dropout,
        },
        'vocab_size': config.vocab_size,
    }
    checkpoint_path = 'checkpoints/latest.pt'
    torch.save(checkpoint, checkpoint_path)
    print(f"\n✅ Training complete! Model saved to {checkpoint_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default='shakespeare', help='Dataset name')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    args = parser.parse_args()
    
    train(args.dataset, args.epochs)
