# OpenClaw Expert Learning Plan

**Goal**: Become expert enough to charge $150-300/hr for installation/customization consulting

## Week 1-2: Core Architecture & Installation

### Days 1-3: Local Setup
- [ ] Install OpenClaw with `openclaw onboard --install-daemon`
- [ ] Understand Gateway architecture (WebSocket control plane)
- [ ] Connect 1 channel (Telegram - easiest, just bot token)
- [ ] Read `/docs/concepts/architecture` 
- [ ] Map to Meridian architecture (you already know this pattern)

**Deliverable**: Working local OpenClaw with Telegram bot responding to messages

### Days 4-7: Multi-Channel Setup
- [ ] Add Discord channel (understand OAuth flow)
- [ ] Add Slack channel (Socket Mode vs webhooks)
- [ ] Add WhatsApp channel (Baileys, device pairing)
- [ ] Study session routing (how messages map to conversations)
- [ ] Document each channel's security model (allowFrom, dmPolicy)

**Deliverable**: 4 channels working simultaneously, documented setup process

### Days 8-14: Security & Production Deployment
- [ ] Docker sandbox setup (non-main sessions)
- [ ] Tailscale Serve/Funnel exposure
- [ ] Tool allowlist/denylist configuration
- [ ] DM pairing flow (understand security model)
- [ ] Deploy to DigitalOcean/Hetzner droplet ($5-10/month)

**Deliverable**: Production deployment you can show clients, written security checklist

## Week 3: Skills & Customization

### Days 15-18: Skills System
- [ ] Install skills from ClawHub registry
- [ ] Study skill structure (`SKILL.md` format)
- [ ] Create custom skill (e.g., "company_knowledge" skill)
- [ ] Understand workspace injection (`AGENTS.md`, `SOUL.md`, `TOOLS.md`)
- [ ] Test skill tool restrictions (security implications)

**Deliverable**: Custom skill that demonstrates business value (e.g., CRM integration, company-specific knowledge)

### Days 19-21: Agent Customization
- [ ] Multi-agent routing (different agents for different channels)
- [ ] Session management (`sessions_list`, `sessions_send`)
- [ ] Thinking levels (cost vs quality tradeoffs)
- [ ] Model failover configuration (cost optimization)
- [ ] Usage tracking and cost monitoring

**Deliverable**: Multi-tenant setup demo (different departments get different agents)

## Week 4: Advanced Features & Client Readiness

### Days 22-25: Advanced Integration
- [ ] Browser control (Puppeteer/CDP)
- [ ] Canvas + A2UI (visual workspace)
- [ ] Cron jobs + webhooks (automation)
- [ ] Gmail Pub/Sub integration
- [ ] Node pairing (macOS/iOS/Android devices)

**Deliverable**: "Enterprise demo" showing full feature set

### Days 26-28: Business Operations
- [ ] Write installation runbook (step-by-step for clients)
- [ ] Create pricing calculator (channels + features + maintenance)
- [ ] Build troubleshooting guide (common issues you encountered)
- [ ] Document backup/restore procedure
- [ ] Create monitoring dashboard (health checks, uptime)

**Deliverable**: Client-facing package (proposal template, runbook, pricing)

### Days 29-30: Portfolio & Marketing
- [ ] Write blog post: "I Installed OpenClaw for 5 Companies - Here's What I Learned"
- [ ] Create demo video (5 min walkthrough)
- [ ] Build comparison guide (OpenClaw vs Slack AI vs Microsoft Copilot)
- [ ] Set up consulting landing page (simple Carrd/Notion page)
- [ ] Post on Reddit r/selfhosted, Hacker News "Show HN"

**Deliverable**: Inbound lead pipeline

## Revenue Model

### Service Tiers

**Basic Setup** ($2,500-5,000):
- Gateway installation (Linux VPS)
- 2 channels (Telegram + Slack)
- Basic security (DM pairing, allowlists)
- 2 hours training for admin
- 30 days support

**Enterprise Setup** ($10,000-20,000):
- Multi-agent routing (departments/teams)
- 5+ channels (WhatsApp, Slack, Discord, Teams, email)
- Docker sandboxing + Tailscale exposure
- Custom skills (3-5 company-specific)
- SSO/SAML integration (if needed)
- Monitoring + backup automation
- 90 days support + monthly maintenance ($500/mo)

**Custom Development** ($150-300/hr):
- New skill development
- Channel integration (custom platform)
- Advanced automation (workflows, integrations)
- Training workshops for teams

### Target Clients

1. **Law firms** (data privacy, can't use ChatGPT)
2. **Healthcare orgs** (HIPAA compliance, need self-hosted)
3. **Finance companies** (regulatory requirements)
4. **Tech startups** (want "AI assistant" for team, cheaper than building)
5. **Consulting firms** (bill AI time to clients, need audit trail)

### Lead Generation

1. **Reddit r/selfhosted** - "I'll install OpenClaw for your company (AMA)"
2. **Hacker News** - "Show HN: Installed OpenClaw for 5 companies, here's what works"
3. **LinkedIn** - Post weekly tips, tag "OpenClaw" "Self-hosted AI"
4. **Cold email** to VPs of Engineering at 100-500 person companies
5. **Referrals** - First client discount if they refer 2 others

## Success Metrics

**Month 1**: Expert (can install blindfolded)
**Month 2**: First paying client ($2,500)
**Month 3**: 3 clients ($10,000 total)
**Month 6**: $5,000/month recurring (maintenance contracts)

## Skills Needed (You Already Have)

✓ Node.js/TypeScript (Meridian)
✓ OAuth flows (Gmail API, Meridian uses it)
✓ WebSocket architecture (Meridian has real-time)
✓ Multi-agent systems (Meridian core competency)
✓ Docker/deployment (Meridian on Render)
✓ Security mindset (Meridian handles OAuth scopes, allowlists)

**New stuff to learn**:
- Baileys (WhatsApp protocol) - 2 days
- Discord.js - 1 day
- Tailscale - 1 day
- Linux daemon setup (systemd) - 1 day

## Next Steps

1. Install OpenClaw locally RIGHT NOW
2. Connect Telegram first (easiest - just bot token)
3. Message yourself "Hello" and get response
4. Study the Gateway logs to understand message flow
5. Add Discord tomorrow
6. Deploy to $10 Hetzner VPS by end of week

## Resources

- Official docs: https://docs.openclaw.ai/
- GitHub: https://github.com/openclaw/openclaw (326k stars, read Issues for common problems)
- Discord: https://discord.gg/clawd (lurk, see what people struggle with)
- ClawHub: https://clawhub.com/ (5,400+ skills to study)

## Anti-Portfolio (Don't Do This)

❌ Try to learn everything at once
❌ Build custom skills before understanding core
❌ Skip security setup (clients will ask about this FIRST)
❌ Charge too little ($50/hr = not sustainable, you're specialized)
❌ Offer free pilots (charge $500 minimum for "setup audit")

## Why This Will Work

1. **Market**: Companies need this (data privacy > convenience)
2. **Complexity**: High enough barrier that they'll pay expert
3. **Low competition**: Not many OpenClaw consultants yet (new project)
4. **Your edge**: You built Meridian = you think in systems
5. **Recurring revenue**: Maintenance contracts = predictable income
6. **UCLA sophomore**: This pays better than tutoring, relevant to career
7. **Portfolio**: "Deployed AI systems for 10 companies" = recruiting gold

Start now. Install it today, one client by end of March, five by summer.
