"""
Generate text from trained model.
"""
import torch
from dataset import download_shakespeare, CharTokenizer

import config
from model import GPT


def load_model(checkpoint_path):
    """Load trained model."""
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    
    # Restore config (handle both old module format and new dict format)
    model_config = checkpoint['config']
    if not isinstance(model_config, dict):
        # Old format with module object
        cfg = model_config
    else:
        # New dict format
        class ConfigObj:
            pass
        cfg = ConfigObj()
        for k, v in model_config.items():
            setattr(cfg, k, v)
    
    # Initialize model
    model = GPT(
        vocab_size=checkpoint['vocab_size'],
        n_embd=cfg.n_embd,
        n_head=cfg.n_head,
        n_layer=cfg.n_layer,
        block_size=cfg.block_size,
        dropout=0.0  # No dropout for inference
    )
    
    # Load weights
    model.load_state_dict(checkpoint['model'])
    model.eval()
    
    return model


def generate_text(
    model,
    tokenizer,
    prompt="",
    max_tokens=500,
    temperature=0.8,
    top_k=40,
    device='cpu'
):
    """Generate text from prompt."""
    model = model.to(device)
    
    # Encode prompt
    if prompt:
        context = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long, device=device)
    else:
        context = torch.zeros((1, 1), dtype=torch.long, device=device)
    
    # Generate
    with torch.no_grad():
        generated = model.generate(
            context,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k
        )[0].tolist()
    
    # Decode
    return tokenizer.decode(generated)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', default='checkpoints/latest.pt', help='Model checkpoint')
    parser.add_argument('--prompt', default='', help='Starting prompt')
    parser.add_argument('--tokens', type=int, default=500, help='Tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8, help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=40, help='Top-k sampling')
    args = parser.parse_args()
    
    # Load model
    print("Loading model...")
    model = load_model(args.checkpoint)
    
    # Load tokenizer (reconstruct from Shakespeare dataset)
    data_path = download_shakespeare()
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    tokenizer = CharTokenizer(text)
    
    # Generate
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n{'='*60}")
    print(f"Prompt: {args.prompt or '[empty]'}")
    print(f"Temperature: {args.temperature} | Top-k: {args.top_k}")
    print(f"{'='*60}\n")
    
    output = generate_text(
        model,
        tokenizer,
        prompt=args.prompt,
        max_tokens=args.tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        device=device
    )
    
    print(output)
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()
