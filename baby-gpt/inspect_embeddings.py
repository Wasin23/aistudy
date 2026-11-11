"""
Inspect Baby-GPT Embeddings - Exercise 1

This script loads your trained model and analyzes what the embeddings learned.
You should see patterns emerge that you NEVER programmed:
- Vowels cluster together
- Consonants cluster together
- Punctuation separates out
- Similar-sounding letters are nearby

All of this emerged purely from gradient descent trying to minimize loss.
Nobody told the model that 'a' and 'e' are similar vowels.
"""

import torch
import numpy as np
from model import GPT
from config import *
from dataset import CharTokenizer
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE

def load_trained_model():
    """Load the trained baby-gpt model"""
    print("Loading trained model...")
    
    checkpoint = torch.load('checkpoints/latest.pt', map_location='cpu')
    
    # Get vocab_size from checkpoint
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
    
    step = checkpoint.get('step', 'unknown')
    loss = checkpoint.get('loss', 'unknown')
    print(f"Model loaded (step: {step}, loss: {loss})")
    return model

def analyze_embeddings(model, tokenizer):
    """Analyze the learned embeddings"""
    # Extract embedding matrix: shape (vocab_size, n_embd)
    embeddings = model.token_embedding_table.weight.detach().cpu().numpy()
    print(f"\nEmbedding matrix shape: {embeddings.shape}")
    print(f"Vocabulary size: {embeddings.shape[0]}")
    print(f"Embedding dimension: {embeddings.shape[1]}")
    
    # Compute cosine similarity between all pairs
    print("\nComputing cosine similarity matrix...")
    from sklearn.metrics.pairwise import cosine_similarity
    similarity_matrix = cosine_similarity(embeddings)
    
    return embeddings, similarity_matrix

def visualize_similarity_matrix(similarity_matrix, tokenizer):
    """Visualize the similarity matrix as a heatmap"""
    chars = [tokenizer.decode([i]) for i in range(len(tokenizer.chars))]
    
    plt.figure(figsize=(20, 18))
    sns.heatmap(
        similarity_matrix,
        xticklabels=chars,
        yticklabels=chars,
        cmap='RdYlGn',
        center=0,
        square=True,
        linewidths=0.1,
        cbar_kws={"shrink": 0.8}
    )
    plt.title('Character Embedding Similarity Matrix\n(Learned through gradient descent)', fontsize=16)
    plt.xlabel('Characters', fontsize=12)
    plt.ylabel('Characters', fontsize=12)
    plt.tight_layout()
    plt.savefig('embedding_similarity.png', dpi=150)
    print("\n✓ Saved similarity heatmap to 'embedding_similarity.png'")

def find_most_similar(similarity_matrix, tokenizer, char):
    """Find the most similar characters to a given character"""
    char_idx = tokenizer.encode(char)[0]
    similarities = similarity_matrix[char_idx]
    
    # Get top 10 most similar (excluding itself)
    sorted_indices = np.argsort(similarities)[::-1]
    
    print(f"\nMost similar characters to '{char}':")
    for i, idx in enumerate(sorted_indices[1:11]):  # Skip first (itself)
        similar_char = tokenizer.decode([idx])
        score = similarities[idx]
        print(f"  {i+1}. '{similar_char}' - similarity: {score:.4f}")

def visualize_2d_embeddings(embeddings, tokenizer):
    """Project embeddings to 2D using t-SNE and visualize"""
    print("\nProjecting embeddings to 2D using t-SNE...")
    print("(This takes ~30 seconds...)")
    
    tsne = TSNE(n_components=2, random_state=42, perplexity=20)
    embeddings_2d = tsne.fit_transform(embeddings)
    
    # Categorize characters
    chars = list(tokenizer.chars)
    vowels = set('aeiouAEIOU')
    consonants = set('bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ')
    digits = set('0123456789')
    
    colors = []
    for char in chars:
        if char in vowels:
            colors.append('red')
        elif char in consonants:
            colors.append('blue')
        elif char in digits:
            colors.append('green')
        elif char.isspace():
            colors.append('gray')
        else:
            colors.append('orange')
    
    plt.figure(figsize=(16, 14))
    scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=colors, s=100, alpha=0.6)
    
    # Add labels
    for i, char in enumerate(chars):
        label = repr(char)[1:-1]  # Remove quotes, handle special chars
        plt.annotate(label, (embeddings_2d[i, 0], embeddings_2d[i, 1]), 
                    fontsize=9, alpha=0.8, ha='center')
    
    plt.title('2D Projection of Character Embeddings\n' + 
              'Red=Vowels, Blue=Consonants, Green=Digits, Orange=Punctuation, Gray=Whitespace',
              fontsize=14)
    plt.xlabel('t-SNE Dimension 1', fontsize=12)
    plt.ylabel('t-SNE Dimension 2', fontsize=12)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='Vowels'),
        Patch(facecolor='blue', label='Consonants'),
        Patch(facecolor='green', label='Digits'),
        Patch(facecolor='orange', label='Punctuation'),
        Patch(facecolor='gray', label='Whitespace')
    ]
    plt.legend(handles=legend_elements, loc='best', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('embedding_2d_projection.png', dpi=150)
    print("✓ Saved 2D projection to 'embedding_2d_projection.png'")

def analyze_clustering(embeddings, tokenizer):
    """Analyze natural clusters in embeddings"""
    from sklearn.cluster import KMeans
    
    # Try k=5 clusters (vowels, consonants, digits, punctuation, whitespace)
    print("\nPerforming K-means clustering (k=5)...")
    kmeans = KMeans(n_clusters=5, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    
    # Group characters by cluster
    chars = list(tokenizer.chars)
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(chars[i])
    
    print("\nDiscovered clusters:")
    for cluster_id, cluster_chars in clusters.items():
        print(f"\nCluster {cluster_id}:")
        print(f"  Characters: {cluster_chars}")
        
        # Count character types
        vowels = sum(1 for c in cluster_chars if c in 'aeiouAEIOU')
        consonants = sum(1 for c in cluster_chars if c in 'bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ')
        digits = sum(1 for c in cluster_chars if c.isdigit())
        spaces = sum(1 for c in cluster_chars if c.isspace())
        
        print(f"  Vowels: {vowels}, Consonants: {consonants}, Digits: {digits}, Spaces: {spaces}")

def main():
    print("=" * 80)
    print("BABY-GPT EMBEDDING ANALYSIS")
    print("=" * 80)
    print("\nThis script reveals what the model learned about character relationships")
    print("through pure gradient descent. You NEVER told it that vowels are similar,")
    print("but it figured that out on its own.\n")
    
    # Load tokenizer
    with open('data/shakespeare.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    tokenizer = CharTokenizer(text)
    
    # Load model
    model = load_trained_model()
    
    # Analyze embeddings
    embeddings, similarity_matrix = analyze_embeddings(model, tokenizer)
    
    # Visualize similarity matrix
    print("\n" + "=" * 80)
    print("VISUALIZING SIMILARITY MATRIX")
    print("=" * 80)
    visualize_similarity_matrix(similarity_matrix, tokenizer)
    
    # Find similar characters
    print("\n" + "=" * 80)
    print("FINDING SIMILAR CHARACTERS")
    print("=" * 80)
    test_chars = ['e', 'a', 't', 'r', ' ', '.', 'T', 'A']
    for char in test_chars:
        find_most_similar(similarity_matrix, tokenizer, char)
    
    # 2D visualization
    print("\n" + "=" * 80)
    print("2D VISUALIZATION (t-SNE)")
    print("=" * 80)
    visualize_2d_embeddings(embeddings, tokenizer)
    
    # Clustering analysis
    print("\n" + "=" * 80)
    print("CLUSTERING ANALYSIS")
    print("=" * 80)
    analyze_clustering(embeddings, tokenizer)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - embedding_similarity.png (heatmap of character similarity)")
    print("  - embedding_2d_projection.png (2D visualization with colors)")
    print("\nKey insight: All of these patterns emerged from gradient descent.")
    print("You never told the model that 'a' and 'e' are both vowels.")
    print("It learned this purely by optimizing next-character prediction.")
    print("\nThis is how AI works: simple objectives + massive scale = emergent patterns.")

if __name__ == '__main__':
    main()
