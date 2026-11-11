"""
Dataset loading and tokenization.
"""
import os
import requests
import torch
import tiktoken


def download_shakespeare():
    """Download Shakespeare dataset."""
    url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
    filepath = "data/shakespeare.txt"
    
    os.makedirs("data", exist_ok=True)
    
    if not os.path.exists(filepath):
        print("Downloading Shakespeare dataset...")
        response = requests.get(url)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Downloaded to {filepath}")
    
    return filepath


class CharTokenizer:
    """Simple character-level tokenizer."""
    
    def __init__(self, text_or_chars):
        if isinstance(text_or_chars, str):
            # Text provided - extract unique chars
            chars = sorted(list(set(text_or_chars)))
        else:
            # List of chars provided directly
            chars = text_or_chars
        
        self.chars = chars
        self.vocab_size = len(chars)
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for i, ch in enumerate(chars)}
    
    def encode(self, text):
        return [self.stoi[ch] for ch in text]
    
    def decode(self, tokens):
        return ''.join([self.itos[i] for i in tokens])


class TextDataset:
    """Dataset for language modeling."""
    
    def __init__(self, data_path, block_size, train_split=0.9, use_char=True):
        """
        Args:
            data_path: Path to text file
            block_size: Sequence length
            train_split: Fraction for training
            use_char: If True, use char tokenizer; else use GPT-2 BPE
        """
        with open(data_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Tokenize
        if use_char:
            self.tokenizer = CharTokenizer(text)
            data = torch.tensor(self.tokenizer.encode(text), dtype=torch.long)
        else:
            # Use GPT-2 tokenizer
            enc = tiktoken.get_encoding("gpt2")
            self.tokenizer = enc
            data = torch.tensor(enc.encode(text), dtype=torch.long)
            self.vocab_size = enc.n_vocab
        
        self.vocab_size = self.tokenizer.vocab_size if use_char else enc.n_vocab
        self.block_size = block_size
        
        # Split train/val
        n = int(train_split * len(data))
        self.train_data = data[:n]
        self.val_data = data[n:]
        
        print(f"Dataset loaded: {len(data):,} tokens")
        print(f"Vocab size: {self.vocab_size}")
        print(f"Train: {len(self.train_data):,} | Val: {len(self.val_data):,}")
    
    def get_batch(self, split, batch_size):
        """Get a batch of data."""
        data = self.train_data if split == 'train' else self.val_data
        
        # Random starting positions
        ix = torch.randint(len(data) - self.block_size, (batch_size,))
        
        # Build batch
        x = torch.stack([data[i:i + self.block_size] for i in ix])
        y = torch.stack([data[i + 1:i + self.block_size + 1] for i in ix])
        
        return x, y
