"""
Q-learning on a tiny gridworld -- the RL equivalent of 01_regression_from_scratch.py.

No labels here. The agent only gets a reward signal (+10 for reaching the goal,
-1 per step) and has to figure out, purely through trial and error, which
actions lead to more reward. This is the "instinct" training loop we talked
about -- state -> action -> reward -> adjust -- same shape as gradient descent,
different object being learned (a Q-table instead of a line).

Grid (5x5), S = start, G = goal, agent can move up/down/left/right:

  S . . . .
  . . . . .
  . . . . .
  . . . . .
  . . . . G
"""
import numpy as np

rng = np.random.default_rng(0)

GRID_SIZE = 5
START = (0, 0)
GOAL = (4, 4)
ACTIONS = ["up", "down", "left", "right"]
ACTION_DELTAS = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}

# Q-table: one row per state (row, col), one column per action.
# Q[state][action] = "how good do I currently believe this action is, from this state"
Q = np.zeros((GRID_SIZE, GRID_SIZE, len(ACTIONS)))

alpha = 0.1      # learning rate -- how much each new experience updates Q
gamma = 0.95     # discount factor -- how much future reward matters vs immediate
epsilon = 1.0    # exploration rate -- chance of trying a random action instead of the "best" one
epsilon_decay = 0.995
epsilon_min = 0.05

def step(state, action):
    dr, dc = ACTION_DELTAS[action]
    r, c = state
    nr, nc = r + dr, c + dc
    # clamp to grid -- walking into a wall just keeps you in place
    nr = max(0, min(GRID_SIZE - 1, nr))
    nc = max(0, min(GRID_SIZE - 1, nc))
    new_state = (nr, nc)
    if new_state == GOAL:
        return new_state, 10.0, True
    return new_state, -1.0, False

def choose_action(state, epsilon):
    if rng.random() < epsilon:
        return rng.integers(len(ACTIONS))  # explore: random action
    return int(np.argmax(Q[state]))         # exploit: best known action

n_episodes = 500
episode_rewards = []

for ep in range(n_episodes):
    state = START
    total_reward = 0
    for t in range(100):  # cap steps per episode so it can't wander forever early on
        action_idx = choose_action(state, epsilon)
        action = ACTIONS[action_idx]
        next_state, reward, done = step(state, action)

        # Q-learning update: nudge Q[state][action] toward
        # (reward received) + (best possible future value from next_state)
        best_next = np.max(Q[next_state])
        td_target = reward + gamma * best_next
        Q[state][action_idx] += alpha * (td_target - Q[state][action_idx])

        state = next_state
        total_reward += reward
        if done:
            break

    epsilon = max(epsilon_min, epsilon * epsilon_decay)
    episode_rewards.append(total_reward)

    if ep % 50 == 0:
        avg_recent = np.mean(episode_rewards[-50:])
        print(f"episode {ep:4d}  epsilon={epsilon:.2f}  reward={total_reward:6.1f}  avg(last50)={avg_recent:6.1f}")

print(f"\nfinal avg reward (last 50 episodes): {np.mean(episode_rewards[-50:]):.1f}")

# print the learned policy: best action from every state, as arrows
arrows = {"up": "^", "down": "v", "left": "<", "right": ">"}
print("\nlearned policy (best action per cell):")
for r in range(GRID_SIZE):
    row_str = ""
    for c in range(GRID_SIZE):
        if (r, c) == GOAL:
            row_str += " G "
        else:
            best_action = ACTIONS[int(np.argmax(Q[r, c]))]
            row_str += f" {arrows[best_action]} "
    print(row_str)
