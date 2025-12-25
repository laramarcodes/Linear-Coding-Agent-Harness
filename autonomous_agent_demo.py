#!/usr/bin/env python3
"""
Autonomous Coding Agent Demo
============================

A minimal harness demonstrating long-running autonomous coding with Claude.
This script implements the two-agent pattern (initializer + coding agent) and
incorporates all the strategies from the long-running agents guide.

Example Usage:
    python autonomous_agent_demo.py --project-dir ./claude_clone_demo
    python autonomous_agent_demo.py --project-dir ./claude_clone_demo --max-iterations 5
"""

import argparse
import asyncio
import os
from pathlib import Path

from agent import run_autonomous_agent


# Configuration
# Using Claude Opus 4.5 as default for best coding and agentic performance
# See: https://www.anthropic.com/news/claude-opus-4-5
DEFAULT_MODEL = "claude-opus-4-5-20251101"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Coding Agent Demo - Long-running agent harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create spec from template, then run
  cp prompts/app_spec_template.txt my_app_spec.txt
  # (edit my_app_spec.txt with your application details)
  python autonomous_agent_demo.py --project-dir ./my_project --spec ./my_app_spec.txt

  # Use a specific model
  python autonomous_agent_demo.py --project-dir ./my_project --spec ./my_app_spec.txt --model claude-opus-4-5-20251101

  # Limit iterations for testing
  python autonomous_agent_demo.py --project-dir ./my_project --spec ./my_app_spec.txt --max-iterations 5

  # Continue existing project (spec not needed after first run)
  python autonomous_agent_demo.py --project-dir ./my_project --spec ./my_app_spec.txt

Environment Variables:
  CLAUDE_CODE_OAUTH_TOKEN    Claude Code OAuth token (required)
  LINEAR_API_KEY             Linear API key (required)
        """,
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("./autonomous_demo_project"),
        help="Directory for the project (default: generations/autonomous_demo_project). Relative paths automatically placed in generations/ directory.",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent iterations (default: unlimited)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="Path to your app_spec.txt file (create from prompts/app_spec_template.txt)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Check for Claude Code OAuth token
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        print("Error: CLAUDE_CODE_OAUTH_TOKEN environment variable not set")
        print("\nRun 'claude setup-token' after installing the Claude Code CLI.")
        print("\nThen set it:")
        print("  export CLAUDE_CODE_OAUTH_TOKEN='your-token-here'")
        return

    # Linear API key is optional if user has Linear MCP configured globally
    if not os.environ.get("LINEAR_API_KEY"):
        print("Note: LINEAR_API_KEY not set - assuming Linear MCP is configured globally")
        print("      (If Linear tools fail, set LINEAR_API_KEY from https://linear.app/settings/api)")
        print()

    # Automatically place projects in generations/ directory to keep them
    # separate from the harness source code
    project_dir = args.project_dir
    generations_dir = Path("generations")

    if project_dir.is_absolute():
        # Absolute paths are used as-is (user explicitly chose location)
        print(f"Using absolute path: {project_dir}")
    elif str(project_dir).startswith("generations/") or str(project_dir).startswith("generations\\"):
        # Already in generations/, use as-is
        pass
    else:
        # Relative path - place under generations/
        # Strip leading ./ if present for cleaner paths
        clean_name = str(project_dir).lstrip("./").lstrip(".\\")
        project_dir = generations_dir / clean_name
        print(f"Project will be created in: {project_dir}")

    # Ensure generations directory exists with a README
    if not generations_dir.exists():
        generations_dir.mkdir(parents=True, exist_ok=True)
    readme_path = generations_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text("""# Generated Projects

This directory contains projects created by the Linear Coding Agent Harness.

Each subdirectory is a complete, standalone project that can be:
- Opened in its own IDE workspace
- Committed to its own git repository
- Deployed independently

## Structure

```
generations/
├── project-1/          # First generated project
│   ├── src/
│   ├── convex/
│   ├── package.json
│   └── ...
├── project-2/          # Second generated project
│   └── ...
└── README.md           # This file
```

## Note

This directory is excluded from the harness git repository (via .gitignore).
Each generated project should be initialized as its own git repo if needed.
""")

    # Run the agent
    try:
        asyncio.run(
            run_autonomous_agent(
                project_dir=project_dir,
                model=args.model,
                max_iterations=args.max_iterations,
                spec_path=args.spec,
            )
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("To resume, run the same command again")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise


if __name__ == "__main__":
    main()
