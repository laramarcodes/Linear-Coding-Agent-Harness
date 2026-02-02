#!/bin/bash
cd /Users/sfinnerty/CodingProjects/Linear-Coding-Agent-Harness
export CLAUDE_CODE_OAUTH_TOKEN=$(security find-generic-password -s "CLAUDE_CODE_OAUTH_TOKEN" -w)
export LINEAR_API_KEY=$(security find-generic-password -s "LINEAR_API_KEY" -w)
/opt/homebrew/bin/python3.11 autonomous_agent_demo.py --project-dir ./generations/embodex-crm --spec ./embodex_crm_spec.txt
