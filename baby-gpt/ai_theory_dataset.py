"""
AI Theory Dataset Loader
Downloads and prepares AI/ML theory text for training
"""
import os
import requests
from dataset import CharTokenizer

def download_ai_theory_texts():
    """Download various AI theory texts"""
    
    texts = []
    
    # Attention Is All You Need (Transformer paper) - excerpt
    print("Gathering transformer paper content...")
    transformer_text = """
    The dominant sequence transduction models are based on complex recurrent or 
    convolutional neural networks that include an encoder and a decoder. The best 
    performing models also connect the encoder and decoder through an attention 
    mechanism. We propose a new simple network architecture, the Transformer, 
    based solely on attention mechanisms, dispensing with recurrence and convolutions 
    entirely.
    
    The Transformer follows this overall architecture using stacked self-attention 
    and point-wise, fully connected layers for both the encoder and decoder. The 
    encoder maps an input sequence of symbol representations to a sequence of 
    continuous representations. Given the output, the decoder then generates an 
    output sequence of symbols one element at a time. At each step the model is 
    auto-regressive, consuming the previously generated symbols as additional input 
    when generating the next.
    
    An attention function can be described as mapping a query and a set of key-value 
    pairs to an output, where the query, keys, values, and output are all vectors. 
    The output is computed as a weighted sum of the values, where the weight assigned 
    to each value is computed by a compatibility function of the query with the 
    corresponding key. We call our particular attention Scaled Dot-Product Attention.
    
    Multi-head attention allows the model to jointly attend to information from 
    different representation subspaces at different positions. With a single attention 
    head, averaging inhibits this. The Transformer uses multi-head attention in three 
    different ways: encoder-decoder attention, encoder self-attention, and decoder 
    self-attention.
    """
    texts.append(transformer_text)
    
    # Neural networks basics
    print("Adding neural network fundamentals...")
    nn_basics = """
    A neural network is a computational model inspired by biological neural networks. 
    At its core, a neural network consists of layers of artificial neurons, each 
    performing a simple computation. Deep learning refers to neural networks with 
    many layers, enabling them to learn hierarchical representations of data.
    
    The fundamental operation in a neural network is the weighted sum followed by 
    a non-linear activation function. Each neuron receives inputs, multiplies them 
    by learned weights, adds a bias term, and passes the result through an activation 
    function like ReLU, sigmoid, or tanh. This non-linearity is crucial for learning 
    complex patterns.
    
    Training neural networks relies on backpropagation, an algorithm that computes 
    gradients of the loss function with respect to each parameter. These gradients 
    indicate how to adjust weights to minimize error. Optimization algorithms like 
    SGD, Adam, and RMSprop use these gradients to update parameters iteratively.
    
    Convolutional neural networks excel at processing grid-like data such as images. 
    They use convolutional layers that apply learned filters across the input, 
    detecting local patterns like edges and textures. Pooling layers reduce spatial 
    dimensions while retaining important features.
    
    Recurrent neural networks process sequential data by maintaining hidden states 
    that capture information from previous time steps. LSTMs and GRUs address the 
    vanishing gradient problem in standard RNNs, enabling them to learn long-range 
    dependencies in sequences.
    """
    texts.append(nn_basics)
    
    # Machine learning concepts
    print("Adding ML theory...")
    ml_theory = """
    Machine learning is the study of algorithms that improve through experience. 
    Supervised learning involves training on labeled examples to predict outputs 
    for new inputs. Unsupervised learning discovers patterns in unlabeled data. 
    Reinforcement learning learns through interaction with an environment.
    
    Overfitting occurs when a model learns the training data too well, including 
    noise and spurious patterns, leading to poor generalization. Regularization 
    techniques like L1 and L2 penalties, dropout, and early stopping help prevent 
    overfitting by constraining model complexity.
    
    The bias-variance tradeoff is fundamental in machine learning. High bias models 
    are too simple and underfit the data. High variance models are too complex and 
    overfit. The goal is finding the sweet spot that minimizes total error on unseen 
    data.
    
    Evaluation metrics depend on the task. Classification uses accuracy, precision, 
    recall, and F1 score. Regression uses MSE, RMSE, and MAE. Cross-validation 
    provides more robust performance estimates by training and testing on different 
    data splits.
    
    Feature engineering transforms raw data into representations that machine learning 
    algorithms can effectively use. This includes normalization, encoding categorical 
    variables, creating interaction terms, and dimensionality reduction through 
    techniques like PCA.
    """
    texts.append(ml_theory)
    
    # Embeddings and representations
    print("Adding embedding concepts...")
    embeddings = """
    Embeddings are dense vector representations that capture semantic relationships 
    between entities. Word embeddings like Word2Vec and GloVe map words to continuous 
    vectors where similar words have similar representations. These vectors enable 
    arithmetic operations on meaning, like king - man + woman = queen.
    
    The embedding space has geometric properties that reflect semantic structure. 
    Distance metrics like cosine similarity measure relatedness between embedded 
    entities. Clustering in embedding space groups semantically similar items together.
    
    Contextual embeddings from models like BERT and GPT produce different representations 
    for the same word based on surrounding context. This captures polysemy and nuanced 
    meaning better than static embeddings. Each token's embedding depends on the entire 
    input sequence through attention mechanisms.
    
    Position embeddings encode the order of tokens in sequences. Transformers use 
    positional encodings added to token embeddings, allowing the model to distinguish 
    between identical words at different positions. This is crucial since attention 
    operations are permutation-invariant.
    """
    texts.append(embeddings)
    
    # Attention mechanism
    print("Adding attention mechanism details...")
    attention = """
    The attention mechanism allows models to focus on relevant parts of the input 
    when producing each output. In the context of neural networks, attention computes 
    a weighted combination of values based on the similarity between a query and keys.
    
    Scaled dot-product attention computes attention weights by taking the dot product 
    of query and key vectors, scaling by the square root of the dimension, and 
    applying softmax. The scaling prevents gradients from becoming too small in high 
    dimensions. The output is the weighted sum of value vectors.
    
    Self-attention allows each position in a sequence to attend to all positions, 
    capturing dependencies regardless of distance. This is more powerful than recurrence 
    for modeling long-range dependencies. The query, key, and value for each position 
    come from the same sequence.
    
    Multi-head attention runs multiple attention mechanisms in parallel with different 
    learned linear projections. This allows the model to attend to different aspects 
    of the input simultaneously. The outputs are concatenated and projected to produce 
    the final representation.
    
    Causal or masked attention prevents positions from attending to future positions, 
    essential for autoregressive generation. During training, this ensures the model 
    only uses past context to predict the next token, matching the generation setting.
    """
    texts.append(attention)
    
    # Transformers architecture
    print("Adding transformer architecture...")
    transformers = """
    The Transformer architecture consists of an encoder and decoder, each composed 
    of stacked layers. Each layer contains a multi-head self-attention sublayer and 
    a position-wise feed-forward sublayer. Residual connections and layer normalization 
    surround each sublayer.
    
    The encoder processes the input sequence through multiple layers of self-attention 
    and feed-forward networks. Each position can attend to all other positions, 
    building rich contextual representations. The encoder's output provides context 
    for the decoder.
    
    The decoder generates output sequences autoregressively, one token at a time. 
    It uses masked self-attention to prevent attending to future positions, encoder-
    decoder attention to incorporate input context, and feed-forward layers. During 
    training, teacher forcing provides ground truth inputs.
    
    Position-wise feed-forward networks apply the same two-layer MLP to each position 
    independently. This typically expands to a larger dimension, applies ReLU or GELU 
    activation, then projects back. This adds non-linearity and capacity to transform 
    attended representations.
    
    Layer normalization stabilizes training by normalizing activations across features. 
    Residual connections allow gradients to flow directly through the network, 
    enabling very deep architectures. These techniques together make transformers 
    trainable at scale.
    """
    texts.append(transformers)
    
    # GPT and language modeling
    print("Adding GPT and language modeling...")
    gpt = """
    Generative Pre-trained Transformers are decoder-only transformer models trained 
    on language modeling. The objective is simple: predict the next token given 
    previous tokens. This self-supervised task enables learning from vast amounts 
    of unlabeled text.
    
    Language modeling provides a powerful pre-training objective. By learning to 
    predict the next word, models must understand syntax, semantics, world knowledge, 
    and reasoning. This learned knowledge transfers to downstream tasks through 
    fine-tuning or prompting.
    
    Scaling laws describe how model performance improves with increased parameters, 
    data, and compute. Performance follows predictable power-law relationships with 
    these factors. Larger models are more sample-efficient and achieve better final 
    performance.
    
    Few-shot learning emerges in large language models. Given a few examples in the 
    prompt, models can perform tasks without parameter updates. This in-context 
    learning suggests models develop general-purpose reasoning capabilities during 
    pre-training.
    
    Temperature controls randomness in generation. Low temperature makes the model 
    more confident and deterministic, selecting high-probability tokens. High 
    temperature increases diversity by sampling from a flatter distribution. Top-k 
    and nucleus sampling prevent selecting very low-probability tokens.
    """
    texts.append(gpt)
    
    # Training dynamics
    print("Adding training dynamics...")
    training = """
    Training neural networks involves finding parameters that minimize a loss function. 
    The loss measures the discrepancy between predictions and targets. For language 
    modeling, cross-entropy loss penalizes the negative log-probability of the true 
    next token.
    
    Gradient descent updates parameters in the direction that reduces loss. The 
    learning rate controls step size. Too large causes instability, too small causes 
    slow convergence. Adaptive optimizers like Adam adjust learning rates per parameter 
    based on gradient history.
    
    Batch size affects training dynamics. Larger batches provide more accurate gradient 
    estimates but require more memory. Smaller batches add noise that can help escape 
    local minima. Batch size interacts with learning rate - larger batches typically 
    need larger learning rates.
    
    Learning rate schedules modify the learning rate during training. Warmup gradually 
    increases the learning rate at the start to stabilize training. Decay reduces it 
    later to fine-tune parameters. Cosine annealing smoothly reduces the learning 
    rate following a cosine curve.
    
    Checkpointing saves model state periodically during training. This enables 
    resuming if training is interrupted and provides snapshots for evaluation. The 
    best checkpoint on a validation set is often used rather than the final checkpoint.
    """
    texts.append(training)
    
    return "\n\n".join(texts)

def prepare_ai_theory_data(output_file='ai_theory.txt'):
    """Download and save AI theory text"""
    print("Preparing AI theory dataset...")
    
    text = download_ai_theory_texts()
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"\nDataset prepared: {len(text)} characters")
    print(f"Saved to {output_file}")
    
    # Show sample
    print("\nSample text:")
    print(text[:500])
    print("...")
    
    return text

if __name__ == "__main__":
    prepare_ai_theory_data()
