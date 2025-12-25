# Generate App Spec

You are helping the user create an `app_spec.txt` file for the Linear Coding Agent Harness. This spec will be used by autonomous agents to build a complete application.

## Your Task

Guide the user through creating a comprehensive application specification. Use `AskUserQuestion` to gather information, then generate a complete `app_spec.txt` file.

## Phase 1: Core Understanding

First, ask these essential questions using `AskUserQuestion`:

**Question 1 - App Type:**
- Header: "App Type"
- Question: "What type of application are you building?"
- Options:
  - "Landing Page - Marketing site, portfolio, product page"
  - "CRUD App - Data management, admin panel, internal tool"
  - "Dashboard - Analytics, metrics, monitoring"
  - "AI App - Chat interface, LLM integration"
  - "SaaS - Multi-tenant platform with billing"
  - "Social - User content, feeds, follows"
  - "E-commerce - Products, cart, checkout"
  - "Other - I'll describe it"

**Question 2 - Purpose:**
- Header: "Purpose"
- Question: "What problem does this app solve? (1-2 sentences)"
- Free text (use "Other" option pattern)

**Question 3 - Users:**
- Header: "Users"
- Question: "Who are the target users?"
- Options:
  - "Developers/Technical users"
  - "Business professionals"
  - "General consumers"
  - "Internal team/employees"
  - "Other - I'll specify"

## Phase 2: Features

Ask about core features:

**Question 4 - Core Features:**
- Header: "Features"
- Question: "What are the must-have features? (Select all that apply)"
- multiSelect: true
- Options:
  - "User authentication (login/signup)"
  - "Data CRUD (create, read, update, delete)"
  - "Real-time updates"
  - "Search and filtering"
  - "File uploads"
  - "Notifications"
  - "API integrations"
  - "Payment processing"

**Question 5 - Additional Features:**
- Ask for any specific features not covered above

## Phase 3: Tech Stack

**Question 6 - Stack Preference:**
- Header: "Tech Stack"
- Question: "What technology stack do you prefer?"
- Options:
  - "Next.js + Convex + Clerk (Recommended - real-time, modern)"
  - "React + Node.js + Express + SQLite (Classic full-stack)"
  - "React + Vite + any backend (Flexible)"
  - "Let the agent decide based on requirements"

## Phase 4: Design

**Question 7 - Aesthetic:**
- Header: "Design"
- Question: "What visual style fits your app?"
- Options:
  - "Neo-minimalist - Clean, lots of whitespace, professional"
  - "Editorial - Magazine-like, dramatic typography"
  - "Maximalist - Dense, information-rich"
  - "Organic - Soft curves, natural colors"
  - "Industrial - Utilitarian, functional"
  - "Match an existing site (provide URL)"

## Phase 5: Generate Spec

After gathering all information:

1. Create a comprehensive `app_spec.txt` file using the template at `prompts/app_spec_template.txt`
2. Fill in ALL sections based on user answers
3. Expand features into detailed feature lists with test criteria
4. Design a database schema that supports all features
5. Create implementation steps ordered by priority
6. Write the file to the user's specified location (or suggest a path)

## Output Format

Generate a complete `app_spec.txt` following the XML template structure with:
- `<project_name>` - Clear, descriptive name
- `<overview>` - Problem, users, value proposition
- `<technology_stack>` - Based on their stack choice
- `<core_features>` - Expanded from their selections
- `<database_schema>` - Tables, fields, relationships
- `<api_endpoints_summary>` - All needed endpoints
- `<ui_layout>` - Pages, navigation, components
- `<design_system>` - Colors, typography, aesthetic
- `<implementation_steps>` - Ordered phases
- `<success_criteria>` - What "done" looks like

## Important Notes

- Be thorough - autonomous agents will use this spec to create Linear issues
- Each feature should be specific enough to become 1-3 issues
- Include test steps in feature descriptions
- Design the database to support ALL features
- Order implementation from foundational to advanced
