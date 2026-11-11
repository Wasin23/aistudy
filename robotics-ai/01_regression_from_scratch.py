"""
Linear regression, built with no ML libraries -- just numpy for arrays.
Goal: watch gradient descent find a line, so "training a model" stops being magic.

Every neural net does this same loop (predict -> measure error -> nudge weights)
just with more weights and a nonlinear stack. This is the atom.
"""
import numpy as np

rng = np.random.default_rng(0)

# fake data: y = 3x + 7, plus noise
x = rng.uniform(0, 10, size=50)
true_w, true_b = 3.0, 7.0
y = true_w * x + true_b + rng.normal(0, 1.5, size=50)

# model params we will learn, starting from garbage guesses
w, b = 0.0, 0.0
lr = 0.01

for epoch in range(200):
    y_pred = w * x + b
    error = y_pred - y

    # mean squared error -- the "loss" we're minimizing
    loss = np.mean(error ** 2)

    # gradients: how much moving w or b changes the loss
    dw = np.mean(2 * error * x)
    db = np.mean(2 * error)

    # step downhill
    w -= lr * dw
    b -= lr * db

    if epoch % 40 == 0:
        print(f"epoch {epoch:3d}  loss={loss:6.2f}  w={w:.2f}  b={b:.2f}")

print(f"\nlearned:  w={w:.2f}  b={b:.2f}")
print(f"true:     w={true_w:.2f}  b={true_b:.2f}")