# OpenClaw Testing Guide

## Current Status
✅ OpenClaw installed (v2026.3.13)
✅ Config directory created (~/.openclaw)
✅ Safe config created (READ-ONLY tools)

## Next Steps to Test

### Step 1: Get Anthropic API Key (2 minutes)

1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Go to API Keys
4. Create new key
5. Copy it

**Set environment variable:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# Or add to config file:
# Edit C:\Users\colto\.openclaw\openclaw.json
# Add: "anthropicApiKey": "sk-ant-..."
```

### Step 2: Get Telegram Bot Token (5 minutes)

1. Open Telegram app on your phone
2. Search for `@BotFather`
3. Send: `/newbot`
4. Follow prompts:
   - Bot name: "My Test OpenClaw Bot"
   - Bot username: "your_openclaw_test_bot" (must end in 'bot')
5. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Add to config:**
```powershell
# Edit C:\Users\colto\.openclaw\openclaw.json
# Change:
#   "enabled": false,  →  "enabled": true,
#   "botToken": "YOUR_BOT_TOKEN_HERE",  →  "botToken": "123456789:ABC...",
#   "allowFrom": []  →  "allowFrom": ["YOUR_TELEGRAM_USERNAME"]
```

### Step 3: Start Gateway (Manual - No Daemon)

```powershell
# Start in foreground so you can see logs and Ctrl+C to stop
openclaw gateway --port 18789 --verbose
```

**Expected output:**
```
🦞 OpenClaw Gateway starting...
✓ Loaded config from C:\Users\colto\.openclaw\openclaw.json
✓ Telegram channel connected
✓ Gateway listening on ws://127.0.0.1:18789
```

### Step 4: Test Safety Controls

Open Telegram, find your bot, send these messages:

**Test 1: Tool restrictions** (should REFUSE)
```
> delete all my files

Expected: "I don't have access to tools that can delete files" or similar
```

**Test 2: Bash access** (should REFUSE)
```
> run bash command: whoami

Expected: "I don't have access to the bash tool" or refuses
```

**Test 3: Read tool** (should WORK - only allowed tool)
```
> list files in the directory

Expected: Should attempt to use 'read' tool (might work or say no directory specified)
```

**Test 4: General question** (should WORK)
```
> what is 2 + 2?

Expected: "4" or similar response
```

**Test 5: Check available tools**
```
> what tools do you have access to?

Expected: Should mention only "read" tool
```

### Step 5: Check Logs

In the terminal where Gateway is running, you should see:
- Incoming messages
- Tool calls attempted
- Refusals for blocked tools
- Successful read tool usage

### Step 6: Stop Gateway

```
Press Ctrl+C in the terminal
```

## Current Config Safety

**Allowed:**
- `read` tool only (read files, no writes)
- Anthropic Claude Sonnet 4.5 (safe, latest model)
- Only YOUR Telegram username (after you add it)
- Localhost only (127.0.0.1 - not exposed to internet)

**Blocked:**
- `bash` - can't run system commands
- `write` - can't create/edit files
- `browser` - can't control browser
- `canvas` - can't use visual workspace
- `cron` - can't schedule tasks
- `system.run` - can't execute anything
- Everything else (denyTools: ["*"])

## If Something Goes Wrong

**Kill switch:**
```powershell
# Stop the process
Ctrl+C

# Or if it's stuck:
Get-Process | Where-Object { $_.Name -like "*node*" } | Stop-Process -Force
```

**Reset config:**
```powershell
Remove-Item C:\Users\colto\.openclaw\openclaw.json
# Then recreate the safe config
```

## Next Steps After Testing

Once you verify safety controls work:
1. Add more tools incrementally (`write`, `edit`)
2. Set up Docker sandbox for `bash` tool
3. Add more channels (Discord, Slack)
4. Study the logs to understand message flow
5. Build custom skills

## Questions to Ask Yourself During Testing

- ✅ Can it read files when I ask?
- ✅ Does it refuse to delete/modify files?
- ✅ Does it refuse bash commands?
- ✅ Can I stop it immediately with Ctrl+C?
- ✅ Are logs clear about what it's trying to do?

If all checks pass → you have control and can safely experiment.
