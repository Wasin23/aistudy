# Post-Restart: OpenClaw Setup in WSL

## After Restart - Follow These Steps

### Step 1: Open WSL (First Time Setup)
```powershell
# In PowerShell, run:
wsl
```

**First time only:**
- It will ask for a username (use: `colto` or your choice)
- It will ask for a password (set one, remember it)
- This creates your Ubuntu environment

### Step 2: Install Node.js in WSL
```bash
# Inside WSL terminal:
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version  # Should show v22.x.x
```

### Step 3: Install OpenClaw in WSL
```bash
npm install -g openclaw@latest
openclaw --version  # Should show: OpenClaw 2026.3.13
```

### Step 4: Copy Config to WSL
```bash
# Create config directory
mkdir -p ~/.openclaw

# Copy config from Windows (adjust path if needed)
cp /mnt/c/Users/colto/.openclaw/openclaw.json ~/.openclaw/

# Verify it copied
cat ~/.openclaw/openclaw.json
```

### Step 5: Fix Workspace Path in Config
```bash
nano ~/.openclaw/openclaw.json

# Change this line:
# "workspace": "C:\\Users\\colto\\OneDrive\\aistudy\\openclaw\\workspace"
# To:
# "workspace": "/mnt/c/Users/colto/OneDrive/aistudy/openclaw/workspace"

# Save: Ctrl+O, Enter, Ctrl+X
```

### Step 6: Start Gateway
```bash
openclaw gateway --verbose
```

**Expected output:**
```
🦞 OpenClaw Gateway starting...
✓ Loaded config from /home/colto/.openclaw/openclaw.json
✓ Telegram channel connected
✓ Gateway listening on ws://127.0.0.1:18789
```

### Step 7: Test from Phone
1. Open Telegram
2. Find your bot (search for the name you created)
3. Send: `hello`
4. Should get response from Claude

**Test safety:**
- Send: `delete all my files` → should REFUSE
- Send: `run bash command` → should REFUSE  
- Send: `what is 2+2?` → should answer "4"

### Step 8: Stop Gateway
```bash
# Press Ctrl+C to stop
```

---

## Quick Reference

**Enter WSL:** `wsl` (from PowerShell)

**Exit WSL:** `exit` or Ctrl+D

**Access Windows files in WSL:** `/mnt/c/Users/colto/...`

**Access WSL files from Windows:** `\\wsl$\Ubuntu\home\colto\...`

**Start OpenClaw:** `openclaw gateway --verbose`

**Stop OpenClaw:** Ctrl+C

---

## Troubleshooting

**If node not found:**
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**If config not found:**
```bash
# Manually create it:
nano ~/.openclaw/openclaw.json
# Paste the config, save with Ctrl+O, Enter, Ctrl+X
```

**If Telegram doesn't connect:**
- Check bot token in config
- Check username is correct (no spaces)
- Try: `openclaw doctor` to diagnose

---

## Config Quick Reference

Your config location in WSL: `~/.openclaw/openclaw.json`

**Current settings:**
- Model: anthropic/claude-sonnet-4.6
- API Key: Already set (sk-ant-...)
- Bot Token: Already set (8199...)
- Username: colefidelman
- Tools: READ ONLY (safe mode)
- Workspace: /mnt/c/Users/colto/OneDrive/aistudy/openclaw/workspace

---

See you after restart! Just open PowerShell and type `wsl` to get started.
