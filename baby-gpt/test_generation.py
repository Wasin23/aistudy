"""
Test Baby-GPT's generation on specific prompts
"""

import torch
from model import GPT
from dataset import CharTokenizer
from config import *

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

def generate(model, tokenizer, prompt, max_tokens=200, temperature=0.8):
    """Generate text from a prompt"""
    # Encode prompt
    context = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long)
    
    # Generate
    with torch.no_grad():
        for _ in range(max_tokens):
            # Crop context to block_size
            context_cropped = context[:, -block_size:]
            
            # Get predictions
            logits, _ = model(context_cropped)
            logits = logits[:, -1, :] / temperature
            
            # Sample from distribution
            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            
            # Append to context
            context = torch.cat([context, next_token], dim=1)
    
    # Decode
    generated = tokenizer.decode(context[0].tolist())
    return generated

if __name__ == '__main__':
    print("Loading model and tokenizer...")
    with open('data/shakespeare.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    tokenizer = CharTokenizer(text)
    model = load_model()
    
    print("\nModel loaded. Testing generation on various prompts...\n")
    print("=" * 80)
    
    prompts = [
        "ROMEO:",
        "To be or not to be",
        "The king said,",
        "My love",
        "What is",
        "First Citizen:\n",
    ]
    
    for prompt in prompts:
        print(f"\nPrompt: \"{prompt}\"")
        print("-" * 80)
        output = generate(model, tokenizer, prompt, max_tokens=150, temperature=0.8)
        print(output)
        print("=" * 80)
