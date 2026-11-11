"""
Generate AI theory text from trained model
"""
import torch
import argparse
import os

from model import GPT
from dataset import CharTokenizer

def load_model(checkpoint_path='checkpoints_ai_theory/latest.pt'):
    """Load trained model and tokenizer"""
    print(f"Loading model from {checkpoint_path}...")
    
    checkpoint = torch.load(checkpoint_path, map_location='cuda' if torch.cuda.is_available() else 'cpu')
    
    # Get config
    if 'config' in checkpoint and isinstance(checkpoint['config'], dict):
        config = checkpoint['config']
    else:
        raise ValueError("Checkpoint missing config dict")
    
    # Initialize tokenizer
    if 'tokenizer_vocab' in checkpoint:
        tokenizer = CharTokenizer(checkpoint['tokenizer_vocab'])
    else:
        # Fallback: load from data file
        with open('ai_theory.txt', 'r', encoding='utf-8') as f:
            text = f.read()
        chars = sorted(list(set(text)))
        tokenizer = CharTokenizer(chars)
    
    # Initialize model
    model = GPT(
        vocab_size=config['vocab_size'],
        n_embd=config['n_embd'],
        n_head=config['n_head'],
        n_layer=config['n_layer'],
        block_size=config['block_size'],
        dropout=config['dropout']
    )
    
    # Load weights
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    
    print(f"Model loaded: {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M parameters")
    print(f"Vocabulary size: {tokenizer.vocab_size}")
    
    return model, tokenizer, device

def generate_text(model, tokenizer, device, prompt="", max_tokens=500, temperature=0.8, top_k=50):
    """Generate text from prompt"""
    
    if prompt:
        context = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long, device=device)
    else:
        # Start with newline character
        context = torch.zeros((1, 1), dtype=torch.long, device=device)
    
    # Generate
    with torch.no_grad():
        generated = model.generate(context, max_new_tokens=max_tokens, temperature=temperature, top_k=top_k)[0]
    
    return tokenizer.decode(generated.tolist())

def main():
    parser = argparse.ArgumentParser(description='Generate AI theory text')
    parser.add_argument('--prompt', type=str, default='', help='Starting prompt')
    parser.add_argument('--tokens', type=int, default=500, help='Number of tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8, help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=50, help='Top-k sampling parameter')
    parser.add_argument('--checkpoint', type=str, default='checkpoints_ai_theory/latest.pt', help='Checkpoint path')
    
    args = parser.parse_args()
    
    # Load model
    model, tokenizer, device = load_model(args.checkpoint)
    
    # Generate
    print("\n" + "="*60)
    print("GENERATING AI THEORY TEXT")
    print("="*60)
    if args.prompt:
        print(f"Prompt: {args.prompt}")
        print("-"*60)
    
    text = generate_text(model, tokenizer, device, args.prompt, args.tokens, args.temperature, args.top_k)
    
    print(text)
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
