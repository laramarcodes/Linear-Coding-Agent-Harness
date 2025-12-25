"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
"""

import asyncio
import re
import subprocess
from pathlib import Path
from typing import Optional

from claude_code_sdk import ClaudeSDKClient

from client import create_client
from progress import print_session_header, print_progress_summary, is_linear_initialized
from prompts import get_initializer_prompt, get_coding_prompt, copy_spec_to_project


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3

# Path to the build-anything scaffold script
SCAFFOLD_SCRIPT = Path.home() / ".claude" / "skills" / "build-anything" / "scripts" / "init_project.py"

# Valid app types for scaffolding
VALID_APP_TYPES = {"landing", "crud", "dashboard", "ai", "game", "saas", "social", "collaboration", "ecommerce", "directory"}


def spec_uses_convex(spec_path: Path) -> bool:
    """
    Check if the app spec indicates Convex is being used.

    Looks for mentions of "convex" in the spec file (case-insensitive).
    """
    if not spec_path or not spec_path.exists():
        return False

    content = spec_path.read_text().lower()
    # Check for common Convex indicators
    return any(indicator in content for indicator in [
        "convex",
        "real-time database",
        "realtime database",
        "serverless backend",
    ])


def is_convex_configured(project_dir: Path) -> bool:
    """
    Check if Convex is already configured for this project.

    Convex is configured when:
    - .env.local exists with CONVEX_URL or NEXT_PUBLIC_CONVEX_URL
    - OR convex/_generated folder exists
    """
    env_local = project_dir / ".env.local"
    convex_generated = project_dir / "convex" / "_generated"

    # Check for generated folder (most reliable indicator)
    if convex_generated.exists():
        return True

    # Check for .env.local with Convex URL
    if env_local.exists():
        content = env_local.read_text()
        if "CONVEX_URL" in content or "NEXT_PUBLIC_CONVEX_URL" in content:
            return True

    return False


def ensure_convex_configured(project_dir: Path, spec_path: Optional[Path] = None) -> bool:
    """
    Ensure Convex is configured before continuing. Prompts user if not.

    Args:
        project_dir: The project directory
        spec_path: Optional path to spec file (to check if Convex is used)

    Returns:
        True if Convex is configured (or not needed), False if user skipped setup
    """
    # Check if this project even uses Convex
    convex_folder = project_dir / "convex"
    uses_convex = convex_folder.exists() or (spec_path and spec_uses_convex(spec_path))

    if not uses_convex:
        # Project doesn't use Convex, no setup needed
        return True

    # Check if already configured
    if is_convex_configured(project_dir):
        print("✓ Convex is already configured")
        return True

    # Convex is needed but not configured - prompt user
    print("\n" + "=" * 70)
    print("  CONVEX SETUP REQUIRED (one-time per project)")
    print("=" * 70)
    print("\nConvex requires interactive setup. Please run in another terminal:")
    print()
    print(f"  cd {project_dir.resolve()}")
    print("  npx convex dev")
    print()
    print("Follow the prompts to:")
    print("  1. Log in to Convex (opens browser if needed)")
    print("  2. Select or create a team")
    print("  3. Create a new project (suggested name: " + project_dir.name + ")")
    print()
    print("After setup completes (you'll see 'Convex functions ready!'), ")
    print("return here and press Enter to continue...")
    print()
    print("(Or type 'skip' to continue without Convex - some features won't work)")
    print("=" * 70)

    try:
        response = input("\nPress Enter when ready (or 'skip'): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted - continuing without Convex")
        return False

    if response == "skip":
        print("\nSkipping Convex setup - agent will continue but database features won't work")
        return False

    # Verify Convex is now configured
    if is_convex_configured(project_dir):
        print("\n✓ Convex configured successfully!")

        # Also prompt to seed the database if seed function exists
        prospects_file = project_dir / "convex" / "prospects.ts"
        if prospects_file.exists() and "seed" in prospects_file.read_text():
            print("\nTip: Seed the database with mock data:")
            print(f"  cd {project_dir.resolve()}")
            print("  npx convex run prospects:seed")

        return True
    else:
        print("\n⚠ Convex setup not detected. Continuing anyway...")
        print("  (The agent may encounter errors related to Convex)")
        return False


def parse_spec_field(spec_content: str, field: str) -> Optional[str]:
    """Parse a field value from the spec XML content."""
    pattern = rf"<{field}>\s*([^<]+?)\s*</{field}>"
    match = re.search(pattern, spec_content, re.IGNORECASE)
    if match:
        value = match.group(1).strip()
        # Skip placeholder values
        if value.startswith("{{") and value.endswith("}}"):
            return None
        return value
    return None


def scaffold_project(project_dir: Path, spec_path: Path) -> bool:
    """
    Scaffold a new Next.js + Convex + Clerk project using build-anything script.

    Args:
        project_dir: Target directory for the project (will be created by scaffold)
        spec_path: Path to the spec file to parse app type and name

    Returns:
        True if scaffolding succeeded, False otherwise
    """
    print("\n" + "=" * 70)
    print("  SCAFFOLDING PROJECT (Next.js + Convex + Clerk)")
    print("=" * 70)

    # Check if scaffold script exists
    if not SCAFFOLD_SCRIPT.exists():
        print(f"\nWarning: Scaffold script not found at {SCAFFOLD_SCRIPT}")
        print("Skipping scaffolding - agent will set up project manually.")
        return False

    # Check if directory already exists (shouldn't scaffold over existing project)
    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"\nWarning: Directory {project_dir} already exists and is not empty.")
        print("Skipping scaffolding to avoid overwriting.")
        return False

    # Parse spec for app type
    spec_content = spec_path.read_text()

    app_type = parse_spec_field(spec_content, "app_type")
    if not app_type or app_type.lower() not in VALID_APP_TYPES:
        app_type = "crud"  # Default
        print(f"\nNo valid app_type in spec, defaulting to: {app_type}")
    else:
        app_type = app_type.lower()

    # Use the directory name as project name (keep it simple)
    project_name = project_dir.name

    print(f"\nProject name: {project_name}")
    print(f"App type: {app_type}")
    print(f"Location: {project_dir}")
    print()

    # Ensure parent directory exists
    project_dir.parent.mkdir(parents=True, exist_ok=True)

    # Run the scaffold script
    # The script creates project_dir.parent / project_name
    cmd = [
        "python3",
        str(SCAFFOLD_SCRIPT),
        "--name", project_name,
        "--type", app_type,
        "--path", str(project_dir.parent),
    ]

    print(f"Running: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Let output stream to terminal
            text=True,
        )

        if result.returncode != 0:
            print(f"\nWarning: Scaffold script exited with code {result.returncode}")
            print("Agent will continue and may need to fix setup issues.")
            return False

        print("\n" + "=" * 70)
        print("  SCAFFOLDING COMPLETE")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\nError running scaffold script: {e}")
        print("Agent will continue and set up project manually.")
        return False


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
) -> tuple[str, str]:
    """
    Run a single agent session using Claude Agent SDK.

    Args:
        client: Claude SDK client
        message: The prompt to send
        project_dir: Project directory path

    Returns:
        (status, response_text) where status is:
        - "continue" if agent should continue working
        - "error" if an error occurred
    """
    print("Sending prompt to Claude Agent SDK...\n")

    try:
        # Send the query
        await client.query(message)

        # Collect response text and show tool use
        response_text = ""
        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            # Handle AssistantMessage (text and tool use)
            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        response_text += block.text
                        print(block.text, end="", flush=True)
                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        print(f"\n[Tool: {block.name}]", flush=True)
                        if hasattr(block, "input"):
                            input_str = str(block.input)
                            if len(input_str) > 200:
                                print(f"   Input: {input_str[:200]}...", flush=True)
                            else:
                                print(f"   Input: {input_str}", flush=True)

            # Handle UserMessage (tool results)
            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "ToolResultBlock":
                        result_content = getattr(block, "content", "")
                        is_error = getattr(block, "is_error", False)

                        # Check if command was blocked by security hook
                        if "blocked" in str(result_content).lower():
                            print(f"   [BLOCKED] {result_content}", flush=True)
                        elif is_error:
                            # Show errors (truncated)
                            error_str = str(result_content)[:500]
                            print(f"   [Error] {error_str}", flush=True)
                        else:
                            # Tool succeeded - just show brief confirmation
                            print("   [Done]", flush=True)

        print("\n" + "-" * 70 + "\n")
        return "continue", response_text

    except Exception as e:
        print(f"Error during agent session: {e}")
        return "error", str(e)


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: Optional[int] = None,
    spec_path: Optional[Path] = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)
        spec_path: Optional path to a custom app spec file
    """
    print("\n" + "=" * 70)
    print("  AUTONOMOUS CODING AGENT DEMO")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Check if this is a fresh start or continuation
    # We use .linear_project.json as the marker for initialization
    is_first_run = not is_linear_initialized(project_dir)

    if is_first_run:
        print("Fresh start - will scaffold project and use initializer agent")
        if spec_path:
            print(f"Using spec: {spec_path}")
        print()

        # Scaffold the project first (Next.js + Convex + Clerk)
        # This creates the project directory
        scaffold_project(project_dir, spec_path)

        # Ensure directory exists (in case scaffold failed or was skipped)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Copy the app spec into the project directory for the agent to read
        copy_spec_to_project(project_dir, spec_path)

        # Check if Convex needs to be configured (pauses for user input if needed)
        # This prevents the agent from getting stuck on Convex setup later
        ensure_convex_configured(project_dir, spec_path)

        print()
        print("=" * 70)
        print("  NOTE: First session takes 10-20+ minutes!")
        print("  The agent is creating Linear issues for features.")
        print("  This may appear to hang - it's working. Watch for [Tool: ...] output.")
        print("=" * 70)
        print()
    else:
        print("Continuing existing project (Linear initialized)")
        print_progress_summary(project_dir)

        # Check Convex on continuation too (in case it was skipped earlier)
        ensure_convex_configured(project_dir, spec_path)

    # Main loop
    iteration = 0

    while True:
        iteration += 1

        # Check max iterations
        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print("To continue, run the script again without --max-iterations")
            break

        # Print session header
        print_session_header(iteration, is_first_run)

        # Create client (fresh context)
        client = create_client(project_dir, model)

        # Choose prompt based on session type
        if is_first_run:
            prompt = get_initializer_prompt()
            is_first_run = False  # Only use initializer once
        else:
            prompt = get_coding_prompt()

        # Run session with async context manager
        async with client:
            status, response = await run_agent_session(client, prompt, project_dir)

        # Handle status
        if status == "continue":
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir)
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        elif status == "error":
            print("\nSession encountered an error")
            print("Will retry with a fresh session...")
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)

    # Print instructions for running the generated application
    print("\n" + "-" * 70)
    print("  TO RUN THE GENERATED APPLICATION:")
    print("-" * 70)
    print(f"\n  cd {project_dir.resolve()}")
    print("  ./init.sh           # Run the setup script")
    print("  # Or manually:")
    print("  npm install && npm run dev")
    print("\n  Then open http://localhost:3000 (or check init.sh for the URL)")
    print("-" * 70)

    print("\nDone!")
