# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

An autonomous coding agent harness that scaffolds and builds full-stack web applications using Claude Agent SDK. All work is tracked in Linear (not local files), enabling long-running agent sessions with proper handoff between sessions.

## Commands

**Run the agent:**
```bash
python autonomous_agent_demo.py --spec ./my_app_spec.txt --project-dir ./my_project
```

**Interactive spec generation:**
```bash
claude
# Then type: /generate-spec
```

**Convert build-anything plan to spec:**
```bash
python3 scripts/plan_to_spec.py ~/.claude/plans/my-app.md -o my_spec.txt
```

**Test with limited iterations:**
```bash
python autonomous_agent_demo.py --spec ./my_app_spec.txt --max-iterations 3
```

## Architecture

### Two-Agent Pattern

1. **Initializer Agent (Session 1)**: Reads spec, creates Linear project with 50 feature issues, creates META issue for session tracking
2. **Coding Agent (Sessions 2+)**: Queries Linear for highest-priority Todo issue, implements feature, tests with dev-browser, updates Linear status

### Key Files

| File | Purpose |
|------|---------|
| `autonomous_agent_demo.py` | Main entry point - orchestrates the full agent loop |
| `agent.py` | Core agent session logic, scaffolding, Convex pre-flight check |
| `client.py` | Claude SDK client config, MCP server setup, Linear OAuth |
| `security.py` | Bash command allowlist with defense-in-depth validation |
| `prompts/initializer_prompt.md` | First session prompt (creates Linear issues) |
| `prompts/coding_prompt.md` | Continuation session prompt (works issues) |

### Session Handoff via Linear

Agents communicate through Linear, not local files:
- **Issue Comments**: Implementation details, blockers
- **META Issue**: Session summaries, progress notes
- **Issue Status**: Todo → In Progress → Done workflow

### Automatic Scaffolding

Before agents run, the harness:
1. Parses `<app_type>` from spec (landing, crud, dashboard, ai, game, saas, social, collaboration, ecommerce, directory)
2. Runs `~/.claude/skills/build-anything/scripts/init_project.py`
3. Creates Next.js 14+ with App Router, TypeScript, Tailwind, Convex, Clerk, shadcn/ui

### Project Locations

- **Harness source**: Root of this repo
- **Generated projects**: `generations/` directory (git-ignored)
- **State marker**: `.linear_project.json` in each generated project

## Security Model

Bash commands are validated against an explicit allowlist in `security.py`:
- File inspection: `ls`, `cat`, `head`, `tail`, `wc`, `grep`
- Node.js: `npm`, `npx`, `node`, `tsx`
- Version control: `git`
- Scripts: `init.sh`, `server.sh`

Extra validation for `pkill` (only dev processes), `chmod` (only `+x`), and script paths.

## MCP Servers

| Server | Purpose |
|--------|---------|
| Linear (HTTP) | Project management - issues, status, comments |
| shadcn | Search and install UI components |
| 21st.dev (Magic) | Generate custom components |

## Environment Variables

| Variable | Required | Notes |
|----------|----------|-------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Yes | From `claude setup-token` |
| `LINEAR_API_KEY` | No | Only if Linear MCP not configured globally |

## Convex Setup

The harness includes a pre-flight check. If Convex isn't configured:
1. Open another terminal
2. Run `cd generations/your-project && npx convex dev`
3. Complete browser auth and project creation
4. Press Enter in the harness terminal
