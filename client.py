"""
Claude SDK Client Configuration
===============================

Functions for creating and configuring the Claude Agent SDK client.
"""

import json
import os
from pathlib import Path
from typing import Optional

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from claude_code_sdk.types import HookMatcher

from security import bash_security_hook


def get_linear_oauth_from_credentials() -> Optional[dict]:
    """
    Extract Linear OAuth credentials from Claude Code's global config.

    Returns dict with 'accessToken' and 'serverUrl' if found, None otherwise.
    """
    credentials_path = Path.home() / ".claude" / ".credentials.json"
    if not credentials_path.exists():
        return None

    try:
        with open(credentials_path) as f:
            creds = json.load(f)

        # Find Linear MCP OAuth entry (key format: "linear-server|{hash}")
        mcp_oauth = creds.get("mcpOAuth", {})
        for key, value in mcp_oauth.items():
            if key.startswith("linear-server"):
                access_token = value.get("accessToken")
                server_url = value.get("serverUrl")
                if access_token and server_url:
                    return {
                        "accessToken": access_token,
                        "serverUrl": server_url,
                    }
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    return None


# Linear MCP tools for project management
# Official Linear MCP server at mcp.linear.app (server name: linear-server)
LINEAR_TOOLS = [
    # Team & Project discovery
    "mcp__linear-server__list_teams",
    "mcp__linear-server__get_team",
    "mcp__linear-server__list_projects",
    "mcp__linear-server__get_project",
    "mcp__linear-server__create_project",
    "mcp__linear-server__update_project",
    # Issue management
    "mcp__linear-server__list_issues",
    "mcp__linear-server__get_issue",
    "mcp__linear-server__create_issue",
    "mcp__linear-server__update_issue",
    # Comments
    "mcp__linear-server__list_comments",
    "mcp__linear-server__create_comment",
    # Workflow
    "mcp__linear-server__list_issue_statuses",
    "mcp__linear-server__get_issue_status",
    "mcp__linear-server__list_issue_labels",
    "mcp__linear-server__create_issue_label",
    # Users
    "mcp__linear-server__list_users",
    "mcp__linear-server__get_user",
    # Cycles
    "mcp__linear-server__list_cycles",
    # Documents
    "mcp__linear-server__list_documents",
    "mcp__linear-server__get_document",
    "mcp__linear-server__create_document",
    "mcp__linear-server__update_document",
]

# Built-in tools
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
]


def create_client(project_dir: Path, model: str) -> ClaudeSDKClient:
    """
    Create a Claude Agent SDK client with multi-layered security.

    Args:
        project_dir: Directory for the project
        model: Claude model to use

    Returns:
        Configured ClaudeSDKClient

    Security layers (defense in depth):
    1. Sandbox - OS-level bash command isolation prevents filesystem escape
    2. Permissions - File operations restricted to project_dir only
    3. Security hooks - Bash commands validated against an allowlist
       (see security.py for ALLOWED_COMMANDS)
    """
    api_key = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not api_key:
        raise ValueError(
            "CLAUDE_CODE_OAUTH_TOKEN environment variable not set.\n"
            "Run 'claude setup-token after installing the Claude Code CLI."
        )

    # Linear API key is optional - if not set, assumes user has Linear MCP configured globally
    linear_api_key = os.environ.get("LINEAR_API_KEY")

    # Create comprehensive security settings
    # Note: Using relative paths ("./**") restricts access to project directory
    # since cwd is set to project_dir
    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",  # Auto-approve edits within allowed directories
            "allow": [
                # Allow all file operations within the project directory
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                # Bash permission granted here, but actual commands are validated
                # by the bash_security_hook (see security.py for allowed commands)
                "Bash(*)",
                # Allow Linear MCP tools for project management
                *LINEAR_TOOLS,
                # Note: Browser automation uses dev-browser skill via Bash scripts
                # (no MCP tools needed - uses Playwright directly)
            ],
        },
    }

    # Ensure project directory exists before creating settings file
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write settings to a file in the project directory
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    print(f"Created security settings at {settings_file}")
    print("   - Sandbox enabled (OS-level bash isolation)")
    print(f"   - Filesystem restricted to: {project_dir.resolve()}")
    print("   - Bash commands restricted to allowlist (see security.py)")
    print("   - Browser automation: dev-browser skill (Playwright via Bash scripts)")
    print("   - MCP servers: linear (project management)")
    print()

    # Configure MCP servers
    # Linear MCP: try API key first, then OAuth from credentials
    # Note: Browser automation uses dev-browser skill via Bash scripts, not MCP
    mcp_servers = {}

    if linear_api_key:
        # Linear MCP with HTTP transport using API key
        mcp_servers["linear-server"] = {
            "type": "http",
            "url": "https://mcp.linear.app/mcp",
            "headers": {
                "Authorization": f"Bearer {linear_api_key}"
            }
        }
        print("   - Linear MCP: using LINEAR_API_KEY")
    else:
        # Try to extract OAuth token from Claude Code global config
        linear_oauth = get_linear_oauth_from_credentials()
        if linear_oauth:
            # Linear MCP with SSE transport using OAuth token
            mcp_servers["linear-server"] = {
                "type": "sse",
                "url": linear_oauth["serverUrl"],
                "headers": {
                    "Authorization": f"Bearer {linear_oauth['accessToken']}"
                }
            }
            print("   - Linear MCP: using OAuth from ~/.claude/.credentials.json")
        else:
            print("   - Linear MCP: NOT CONFIGURED (set LINEAR_API_KEY or authenticate via Claude Code)")

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt="You are an expert full-stack developer building a production-quality web application. You use Linear for project management and tracking all your work. For browser automation, you use the dev-browser skill via Bash scripts with Playwright.",
            allowed_tools=[
                *BUILTIN_TOOLS,
                *LINEAR_TOOLS,
            ],
            mcp_servers=mcp_servers,
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
                ],
            },
            max_turns=1000,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),  # Use absolute path
        )
    )
