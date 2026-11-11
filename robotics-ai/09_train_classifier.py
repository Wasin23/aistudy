"""
Trains a real CNN image classifier on whatever images you captured with
08_capture_images.py (folders under image_data/<label>/).

This is a standard, real architecture -- a small convolutional neural
net (CNN). Different from the transformer/attention stuff: CNNs work by
sliding small learned filters across the image, detecting local patterns
(edges, textures, shapes) and building them up into more complex features
layer by layer. This is the proven, standard approach for image
classification -- what most real-world vision systems are built on at
small-to-medium scale.

Run this after capturing at least 2 classes of images.
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import numpy as np

torch.manual_seed(0)

DATA_DIR = os.path.join(os.path.dirname(__file__), "image_data")
CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "classifier.pt")
IMG_SIZE = 64   # every image gets resized to 64x64 before training -- keeps things fast

# ------------------------------------------------------------------------
# load images
# ------------------------------------------------------------------------
labels = sorted(os.listdir(DATA_DIR))
if len(labels) < 2:
    raise RuntimeError(
        f"Need at least 2 classes in {DATA_DIR}. "
        f"Run: python 08_capture_images.py <label>  (at least twice, different labels)"
    )

label_to_idx = {label: i for i, label in enumerate(labels)}
print(f"classes found: {labels}")

images = []
targets = []
for label in labels:
    folder = os.path.join(DATA_DIR, label)
    files = [f for f in os.listdir(folder) if f.endswith(".png")]
    print(f"  {label}: {len(files)} images")
    for fname in files:
        img = Image.open(os.path.join(folder, fname)).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
        arr = np.array(img, dtype=np.float32) / 255.0   # normalize pixel values to 0-1
        images.append(arr)
        targets.append(label_to_idx[label])

if len(images) < 10:
    raise RuntimeError("Very few images captured -- grab more with 08_capture_images.py before training.")

# stack into tensors. shape: (N, H, W, C) -> (N, C, H, W) which is what PyTorch conv layers expect
X = torch.tensor(np.stack(images)).permute(0, 3, 1, 2)
y = torch.tensor(targets, dtype=torch.long)

n = len(X)
n_val = max(1, n // 5)   # hold out ~20% to check it's actually generalizing, not just memorizing
perm = torch.randperm(n)
X, y = X[perm], y[perm]
X_train, y_train = X[n_val:], y[n_val:]
X_val, y_val = X[:n_val], y[:n_val]

print(f"\ntrain: {len(X_train)}  val: {len(X_val)}")


# ------------------------------------------------------------------------
# the CNN
# ------------------------------------------------------------------------
class SimpleCNN(nn.Module):
    def __init__(self, n_classes):
        super().__init__()
        # each conv layer: slides small filters over the image, learning
        # to detect patterns (edges -> textures -> shapes as you go deeper)
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)   # 3 input channels (RGB) -> 16 learned filters
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)  # 16 -> 32 filters, deeper = more complex patterns
        self.pool = nn.MaxPool2d(2, 2)   # shrinks the image by half each time, keeping the strongest signal
        # after 2 pools: 64x64 -> 32x32 -> 16x16
        self.fc1 = nn.Linear(32 * 16 * 16, 64)   # flatten, then a regular layer (like feedforward() from script 05)
        self.fc2 = nn.Linear(64, n_classes)       # final layer -> one score per class

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.flatten(1)               # (batch, 32, 16, 16) -> (batch, 32*16*16)
        x = F.relu(self.fc1(x))
        return self.fc2(x)             # raw logits, one per class

model = SimpleCNN(n_classes=len(labels))
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

# ------------------------------------------------------------------------
# training loop -- same shape as every training loop you've written today:
# predict -> loss -> backward -> step
# ------------------------------------------------------------------------
n_epochs = 30
batch_size = 8

for epoch in range(n_epochs):
    model.train()
    perm = torch.randperm(len(X_train))
    total_loss = 0
    for i in range(0, len(X_train), batch_size):
        idx = perm[i:i + batch_size]
        xb, yb = X_train[idx], y_train[idx]

        logits = model(xb)
        loss = F.cross_entropy(logits, yb)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    # check validation accuracy -- did it actually learn, or just memorize?
    model.eval()
    with torch.no_grad():
        val_logits = model(X_val)
        val_acc = (val_logits.argmax(dim=1) == y_val).float().mean().item()

    if epoch % 5 == 0 or epoch == n_epochs - 1:
        print(f"epoch {epoch:3d}  train_loss={total_loss:.3f}  val_acc={val_acc:.2%}")

# ------------------------------------------------------------------------
# save
# ------------------------------------------------------------------------
os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
torch.save({"model_state": model.state_dict(), "labels": labels, "img_size": IMG_SIZE}, CHECKPOINT_PATH)
print(f"\nsaved to {CHECKPOINT_PATH}")
print("now run: python 10_live_classify.py")
