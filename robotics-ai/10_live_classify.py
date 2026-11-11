"""
Live webcam classification -- opens your camera, runs your trained CNN
on every frame in real time, and overlays the predicted label on screen.

This is the payoff: point your camera at something, watch it get
identified live. Press 'q' to quit.
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
import numpy as np

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "classifier.pt")

if not os.path.exists(CHECKPOINT_PATH):
    raise RuntimeError("No trained classifier found -- run 09_train_classifier.py first.")

saved = torch.load(CHECKPOINT_PATH)
labels = saved["labels"]
img_size = saved["img_size"]

# must match the architecture in 09_train_classifier.py exactly
class SimpleCNN(nn.Module):
    def __init__(self, n_classes):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 16 * 16, 64)
        self.fc2 = nn.Linear(64, n_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)

model = SimpleCNN(n_classes=len(labels))
model.load_state_dict(saved["model_state"])
model.eval()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No camera found.")

print(f"classes: {labels}")
print("press 'q' to quit\n")

while True:
    ok, frame = cap.read()
    if not ok:
        break

    # preprocess exactly like training: resize, RGB, 0-1, (H,W,C) -> (1,C,H,W)
    img = cv2.resize(frame, (img_size, img_size))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    arr = img_rgb.astype(np.float32) / 255.0
    tensor = torch.tensor(arr).permute(2, 0, 1).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=-1)[0]
        pred_idx = probs.argmax().item()
        pred_label = labels[pred_idx]
        confidence = probs[pred_idx].item()

    # overlay prediction on the live frame
    text = f"{pred_label} ({confidence:.0%})"
    color = (0, 255, 0) if confidence > 0.6 else (0, 165, 255)   # green if confident, orange if unsure
    cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    # show all class probabilities as a small bar list
    for i, label in enumerate(labels):
        bar_text = f"{label}: {probs[i]:.0%}"
        cv2.putText(frame, bar_text, (10, 80 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("live classify", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
