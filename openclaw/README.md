# OpenClaw Setup & Learning

Everything related to OpenClaw installation, configuration, and learning.

## Folder Structure

```
C:\Users\colto\OneDrive\aistudy\openclaw\
├── README.md                  # You are here
├── 00-setup-plan.md          # 4-week learning plan for consulting expertise
├── 01-testing-guide.md       # How to test safety controls
└── workspace\                # OpenClaw agent workspace (skills, prompts)
    ├── skills\               # Custom skills (will be created)
    ├── AGENTS.md             # Agent configuration (will be created)
    └── SOUL.md               # Agent personality (will be created)

C:\Users\colto\.openclaw\     # Config folder (standard location)
└── openclaw.json             # Main configuration file
```

## Configuration Location

**Config file**: `C:\Users\colto\.openclaw\openclaw.json`
- This is the standard location for OpenClaw config (dotfile in home directory)
- Contains: API keys, channel settings, tool permissions, model selection
- **Workspace path points here**: `C:\Users\colto\OneDrive\aistudy\openclaw\workspace`

## Current Setup Status

✅ OpenClaw installed (v2026.3.13)
✅ Safe config created (READ-ONLY tools)
✅ Workspace folder created
⏳ API key needed (Anthropic or OpenAI)
⏳ Telegram bot token needed
⏳ Gateway testing

## Quick Start

1. **Add API key** (choose one):
   ```powershell
   # Option A: Anthropic
   $env:ANTHROPIC_API_KEY = "sk-ant-your-key"
   
   # Option B: OpenAI  
   $env:OPENAI_API_KEY = "sk-proj-your-key"
   ```

2. **Get Telegram bot** (2 minutes):
   - Open Telegram → search `@BotFather`
   - Send: `/newbot` → follow prompts
   - Copy token to config

3. **Start Gateway**:
   ```powershell
   cd C:\Users\colto\OneDrive\aistudy\openclaw
   openclaw gateway --port 18789 --verbose
   ```

4. **Test safety** (see `01-testing-guide.md`)

## Files in this Folder

### 00-setup-plan.md
Complete 4-week learning roadmap to become OpenClaw expert for consulting work. Includes:
- Week 1-2: Core architecture & deployment
- Week 3: Skills & customization
- Week 4: Advanced features & client readiness
- Revenue model ($2,500-20,000 per setup)
- Target clients (law firms, healthcare, finance)

### 01-testing-guide.md
Step-by-step guide for testing OpenClaw safety controls. Covers:
- Getting API keys
- Creating Telegram bot
- Starting Gateway manually
- Testing tool restrictions
- Verifying safety (can't delete files, run bash, etc.)

### workspace/
OpenClaw agent workspace where custom skills and configuration live. When you create custom skills or modify agent behavior, files go here.

## Next Steps

See `01-testing-guide.md` for immediate next steps to get OpenClaw running.
