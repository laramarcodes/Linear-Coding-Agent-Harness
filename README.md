# Autonomous Coding Agent Harness (Linear-Integrated)

A template-based harness for long-running autonomous coding with the Claude Agent SDK. This demo implements a two-agent pattern (initializer + coding agent) with **Linear as the core project management system** for tracking all work.

**Build full-stack applications** by providing your own spec file. The harness automatically scaffolds a Next.js + Convex + Clerk project before agents begin.

## Key Features

- **Automatic Scaffolding**: Projects start with Next.js 14+, Convex, Clerk, and shadcn/ui pre-configured
- **Linear Integration**: All work is tracked as Linear issues, not local files
- **Real-time Visibility**: Watch agent progress directly in your Linear workspace
- **Session Handoff**: Agents communicate via Linear comments, not text files
- **Two-Agent Pattern**: Initializer creates Linear project & issues, coding agents implement them
- **Frontend Design Tools**: Agents use shadcn MCP and 21st.dev for high-quality UI
- **Browser Testing**: dev-browser skill (Playwright) for UI verification
- **Claude Opus 4.5**: Uses Claude's most capable model by default

## Prerequisites

### 1. Install Claude Code CLI and Python SDK

```bash
# Install Claude Code CLI (latest version required)
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up Authentication

You need two authentication tokens:

**Claude Code OAuth Token:**
```bash
# Generate the token using Claude Code CLI
claude setup-token

# Set the environment variable
export CLAUDE_CODE_OAUTH_TOKEN='your-oauth-token-here'
```

**Linear API Key (optional if you have Linear MCP configured globally):**
```bash
# Only needed if Linear MCP isn't already in your Claude Code config
# Get your API key from: https://linear.app/YOUR-TEAM/settings/api
export LINEAR_API_KEY='lin_api_xxxxxxxxxxxxx'
```

### 3. Verify Installation

```bash
claude --version  # Should be latest version
pip show claude-code-sdk  # Check SDK is installed
```

## Quick Start

### Option 1: Interactive Spec Generation (Recommended)

Use the built-in command to create your spec interactively:

```bash
cd /path/to/Linear-Coding-Agent-Harness
claude
# Then type: /generate-spec
```

The `/generate-spec` command guides you through questions about your app and generates a complete spec file.

### Option 2: Use the build-anything Skill

If you want to use the Next.js + Convex + Clerk stack:

1. **Plan your app** using the build-anything skill:
   ```bash
   claude
   # Describe your app and use the build-anything skill for planning
   # Plan outputs to ~/.claude/plans/<name>.md
   ```

2. **Convert the plan to spec format:**
   ```bash
   python3 scripts/plan_to_spec.py ~/.claude/plans/my-app.md -o my_app_spec.txt
   ```

3. **Run the agent:**
   ```bash
   python autonomous_agent_demo.py --project-dir ./my_project --spec ./my_app_spec.txt
   ```

### Option 3: Manual Spec Creation

1. **Copy the template and customize it:**
   ```bash
   cp prompts/app_spec_template.txt my_app_spec.txt
   ```

2. **Edit your spec** with your application details (project name, features, tech stack, etc.)

3. **Run the agent:**
   ```bash
   python autonomous_agent_demo.py --project-dir ./my_project --spec ./my_app_spec.txt
   ```

### Testing with Limited Iterations

For testing, you can limit the number of agent sessions:
```bash
python autonomous_agent_demo.py --project-dir ./my_project --spec ./my_app_spec.txt --max-iterations 3
```

## How It Works

### Linear-Centric Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    LINEAR-INTEGRATED WORKFLOW               │
├─────────────────────────────────────────────────────────────┤
│  app_spec.txt ──► Initializer Agent ──► Linear Issues (50) │
│                                              │               │
│                    ┌─────────────────────────▼──────────┐   │
│                    │        LINEAR WORKSPACE            │   │
│                    │  ┌────────────────────────────┐    │   │
│                    │  │ Issue: Auth - Login flow   │    │   │
│                    │  │ Status: Todo → In Progress │    │   │
│                    │  │ Comments: [session notes]  │    │   │
│                    │  └────────────────────────────┘    │   │
│                    └────────────────────────────────────┘   │
│                                              │               │
│                    Coding Agent queries Linear              │
│                    ├── Search for Todo issues               │
│                    ├── Update status to In Progress         │
│                    ├── Implement & test with dev-browser    │
│                    ├── Add comment with implementation notes│
│                    └── Update status to Done                │
└─────────────────────────────────────────────────────────────┘
```

### Three-Stage Pattern

**Stage 0: Automatic Scaffolding (before agents run)**
- Parses `<app_type>` from spec (landing, crud, dashboard, ai, game, saas, social, collaboration, ecommerce, directory)
- Runs `~/.claude/skills/build-anything/scripts/init_project.py`
- Creates Next.js 14+ project with App Router, TypeScript, Tailwind
- Installs Convex, Clerk, and archetype-specific shadcn/ui components
- Project is ready for feature development

**Stage 1: Initializer Agent (Session 1)**
- Reads `app_spec.txt` and verifies scaffolded project
- Lists teams and creates a new Linear project
- Creates Linear issues for all features (focus on features, not setup)
- Creates a META issue for session tracking
- Initializes git repository

**Stage 2: Coding Agent (Sessions 2+)**
- Queries Linear for highest-priority Todo issue
- Runs verification tests on previously completed features
- Claims issue (status → In Progress)
- Implements the feature using frontend design tools
- Tests via dev-browser (Playwright) browser automation
- Adds implementation comment to issue
- Marks complete (status → Done)
- Updates META issue with session summary

### Session Handoff via Linear

Instead of local text files, agents communicate through:
- **Issue Comments**: Implementation details, blockers, context
- **META Issue**: Session summaries and handoff notes
- **Issue Status**: Todo / In Progress / Done workflow

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code OAuth token (from `claude setup-token`) | Yes |
| `LINEAR_API_KEY` | Linear API key for MCP access | No (if Linear MCP configured globally) |

## Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--spec` | Path to your app spec file | Yes |
| `--project-dir` | Directory for the project | No (default: `./autonomous_demo_project`) |
| `--max-iterations` | Max agent iterations | No (default: unlimited) |
| `--model` | Claude model to use | No (default: `claude-opus-4-5-20251101`) |

## Project Structure

The harness keeps its source code separate from generated projects:

```
Linear-Coding-Agent-Harness/
├── autonomous_agent_demo.py  # Main entry point
├── agent.py                  # Agent session logic + Convex pre-flight check
├── client.py                 # Claude SDK + MCP client configuration
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── linear_config.py          # Linear configuration constants
├── prompts/
│   ├── app_spec_template.txt # Template for creating your app specs
│   ├── initializer_prompt.md # First session prompt (creates Linear issues)
│   └── coding_prompt.md      # Continuation session prompt (works issues)
├── scripts/
│   └── plan_to_spec.py       # Convert build-anything plans to spec format
├── .claude/
│   └── commands/
│       └── generate-spec.md  # Interactive spec generation command
├── generations/              # ← ALL GENERATED PROJECTS GO HERE
│   ├── README.md             # Explains the generations directory
│   ├── my-first-app/         # Each project is self-contained
│   ├── my-second-app/        # Can be opened in separate IDE workspaces
│   └── ...                   # Can have their own git repos
└── requirements.txt          # Python dependencies
```

**Note:** The `generations/` directory is git-ignored. Each generated project is a standalone application that should be managed separately from the harness.

## Generated Project Structure

After scaffolding and running, each project in `generations/` will contain:

```
my_project/
├── .linear_project.json      # Linear project state (marker file)
├── app_spec.txt              # Copied specification
├── .claude_settings.json     # Security settings
├── package.json              # Node dependencies (Next.js, Convex, Clerk)
├── next.config.js            # Next.js configuration
├── tailwind.config.ts        # Tailwind CSS configuration
├── convex/                   # Convex backend
│   ├── schema.ts             # Database schema
│   ├── _generated/           # Auto-generated Convex files
│   └── [functions]           # Queries, mutations, actions
├── src/
│   ├── app/                  # Next.js App Router pages
│   ├── components/           # React components
│   │   └── ui/               # shadcn/ui components
│   └── lib/                  # Utility functions
├── .env.local                # Environment variables (Clerk, Convex)
└── .env.example              # Example env file
```

## MCP Servers & Skills Used

| Tool | Type | Purpose |
|------|------|---------|
| **Linear** | MCP (HTTP) | Project management - issues, status, comments |
| **dev-browser** | Skill (Playwright) | Browser automation for UI testing via Bash scripts |
| **shadcn** | MCP (stdio) | Search and install UI components |
| **21st.dev (Magic)** | MCP (stdio) | Generate custom components, inspiration, refinement |

## Security Model

This demo uses defense-in-depth security (see `security.py` and `client.py`):

1. **OS-level Sandbox:** Bash commands run in an isolated environment
2. **Filesystem Restrictions:** File operations restricted to project directory
3. **Bash Allowlist:** Only specific commands permitted (npm, node, git, etc.)
4. **MCP Permissions:** Tools explicitly allowed in security settings

## Linear Setup

Before running, ensure you have:

1. A Linear workspace with at least one team
2. An API key with read/write permissions (from Settings > API)
3. The agent will automatically detect your team and create a project

The initializer agent will create:
- A new Linear project named after your app
- 50 feature issues based on `app_spec.txt`
- 1 META issue for session tracking and handoff

All subsequent coding agents will work from this Linear project.

## Customization

### Spec Generation Tools

| Method | Best For |
|--------|----------|
| `/generate-spec` command | Interactive guided creation |
| `build-anything` skill + conversion | Next.js + Convex + Clerk apps |
| Manual template editing | Full control, any stack |

### Writing Your Application Spec

The spec file defines what the agent will build. Key sections:

| Section | Purpose |
|---------|---------|
| `<project_name>` | Your application's name |
| `<app_type>` | Archetype for scaffolding: landing, crud, dashboard, ai, game, saas, social, collaboration, ecommerce, directory |
| `<overview>` | What it does and who it's for |
| `<technology_stack>` | Frontend, backend, database choices (auto-configured) |
| `<core_features>` | All features organized by category |
| `<database_schema>` | Your Convex data model |
| `<api_endpoints_summary>` | Convex functions structure |
| `<ui_layout>` | Page structure and navigation |
| `<design_system>` | Colors, typography, component styles |
| `<implementation_steps>` | Logical build order |
| `<success_criteria>` | What "done" looks like |

### Spec Writing Tips

- **Be specific** - Detailed specs produce better results
- **Think in features** - Each item in `<core_features>` becomes a Linear issue
- **Order by priority** - Put foundational features first
- **Include test steps** - How should each feature be verified?
- **Define success** - The agent uses `<success_criteria>` to know when it's done

### Using the build-anything Skill

The `build-anything` skill provides comprehensive planning for Next.js + Convex + Clerk apps:

1. Start Claude and describe your app idea
2. The skill guides you through questions about purpose, features, design
3. Outputs a plan to `~/.claude/plans/<name>.md`
4. Convert to spec: `python3 scripts/plan_to_spec.py ~/.claude/plans/<name>.md -o my_spec.txt`

Supported app types: Landing Page, CRUD, Dashboard, AI App, Game, SaaS, Social, Collaboration, E-commerce, Directory

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

## Troubleshooting

**"CLAUDE_CODE_OAUTH_TOKEN not set"**
Run `claude setup-token` to generate a token, then export it.

**"LINEAR_API_KEY not set"**
Get your API key from `https://linear.app/YOUR-TEAM/settings/api`

**"CONVEX SETUP REQUIRED" prompt appears**
This is the pre-flight check. Convex requires interactive setup:
1. Open another terminal
2. Run `cd generations/your-project && npx convex dev`
3. Complete the browser auth and project creation
4. Press Enter in the harness terminal to continue
You can also type `skip` to continue without Convex (some features won't work).

**"Appears to hang on first run"**
Normal behavior. The initializer is creating a Linear project and issues with detailed descriptions. Watch for `[Tool: mcp__linear__create_issue]` output.

**"Command blocked by security hook"**
The agent tried to run a disallowed command. Add it to `ALLOWED_COMMANDS` in `security.py` if needed.

**"MCP server connection failed"**
Verify your `LINEAR_API_KEY` is valid and has appropriate permissions. The Linear MCP server uses HTTP transport at `https://mcp.linear.app/mcp`.

## Viewing Progress

Open your Linear workspace to see:
- The project created by the initializer agent
- All issues organized under the project (count depends on your spec complexity)
- Real-time status changes (Todo → In Progress → Done)
- Implementation comments on each issue
- Session summaries on the META issue

## License

MIT License - see [LICENSE](LICENSE) for details.
