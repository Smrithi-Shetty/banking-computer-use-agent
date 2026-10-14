# Banking Computer-Use Automation System

## Overview

This project implements a complete LLM-driven Computer Use Agent that discovers, records, replays, and escalates banking workflows performed on a live web application.

The system uses:

- Microsoft Azure AI Foundry
- GPT-4o
- Playwright
- Python
- ParaBank Demo Banking Application

The system demonstrates:

```text
Natural Language Goal
        ↓
Observe → Decide → Act
        ↓
Discovery Run
        ↓
Capability Artifact
        ↓
Deterministic Replay
        ↓
Evidence Collection
        ↓
Human Handoff
        ↓
Resume
```

---

# Objective

The goal of the project is to:

1. Accept a natural language instruction.
2. Use an LLM to interact with a live application.
3. Discover the workflow required to complete the task.
4. Record the workflow as a reusable capability artifact.
5. Replay the workflow deterministically without the LLM.
6. Escalate to a human when required.
7. Capture execution evidence throughout the process.

---

# Architecture

```text
                    USER GOAL
                        │
                        ▼
            Microsoft Foundry GPT-4o
                        │
                        ▼
                 Discovery Agent
                        │
              Observe → Decide → Act
                        │
                        ▼
               Capability Artifact
                        │
                        ▼
                  Replay Engine
                        │
      ┌────────────┬──────────────┬──────────────┐
      │            │              │
      ▼            ▼              ▼
  Success   Business Outcome   Hard Failure
                        │
                        ▼
                 Human Handoff
                        │
                        ▼
                      Resume
```

---

# Project Structure

```text
banking-computer-use-agent/

│
├── app/
│
├── artifacts/
│
├── evidence/
│
├── tests/
│
├── README.md
├── REPORT.md
├── requirements.txt
├── .env
└── .env.example
```

---

# Application Components

## app/config.py

Loads:

- Azure Foundry endpoint
- API keys
- Deployment configuration
- ParaBank configuration
- Agent settings

Purpose:

```text
Centralized configuration management
```

---

## app/runtime_data.py

Maintains runtime-generated user registration values.

Examples:

```python
runtime_first_name
runtime_last_name
runtime_username
runtime_password
```

Purpose:

```text
Avoid hard-coded registration values
Generate unique users for every execution
```

---

## app/foundry_client.py

Creates and returns the GPT-4o client.

Responsibilities:

```text
Authenticate with Microsoft Foundry
Execute model calls
Return model responses
```

---

## app/surface.py

Observation layer.

Responsibilities:

```text
Inspect current page
Identify links
Identify buttons
Identify inputs
Expose semantic table values
Build structured observations
```

Output Example:

```json
{
    "url": "...",
    "title": "...",
    "elements": [...]
}
```

---

## app/decision_engine.py

LLM reasoning layer.

Responsibilities:

```text
Receive goal
Receive current outputs
Receive page observation
Generate next action
```

Example Decision:

```json
{
    "action": "fill",
    "target_id": "input_3",
    "value_ref": "runtime_first_name"
}
```

---

## app/action_executor.py

Execution layer.

Supported Actions:

```text
click
fill
read
wait
finish
escalate
```

Purpose:

```text
Execute actions selected by GPT-4o
```

---

## app/agent_loop.py

Core orchestration loop.

Implements:

```text
Observe
↓
Decide
↓
Validate
↓
Act
↓
Observe Again
```

until:

```text
Success
Timeout
Human Intervention
Failure
```

---

## app/safety.py

Safety policy enforcement.

Validates:

```text
Allowed hosts
Allowed actions
Risky operations
Human intervention triggers
```

---

## app/artifact_generator.py

Creates reusable capability artifacts.

Example:

```text
read_account_balance_20261014_160005.json
```

Purpose:

```text
Record successful discovery runs
```

---

## app/replay_engine.py

Deterministic execution engine.

Responsibilities:

```text
Load Artifact
Replay Capability
Return Outputs
```

No GPT calls occur during replay.

---

## app/session_controller.py

Human-in-the-loop implementation.

Responsibilities:

```text
Pause
Transfer Control
Resume
Maintain Browser Session
Capture Handoff Evidence
```

---

# Artifacts

## artifacts/

Stores generated capability definitions.

Example:

```text
artifacts/
└── read_account_balance_20261014_160005.json
```

The artifact contains:

```text
Capability Metadata
Inputs
Outputs
Discovery History
Execution Steps
```

---

# Evidence

## evidence/discovery

Contains discovery-run screenshots.

Example:

```text
account_overview_20261014_160005.png
```

---

## evidence/replay

Contains replay execution evidence.

Example:

```text
replay_result_20261014_164928.json
```

---

## evidence/handoff

Contains human intervention evidence.

Example:

```text
session_xxx_handoff.json

session_xxx_handoff_started.png

session_xxx_automation_resumed.png
```

---

# Discovery Workflow

Goal:

```text
Register a new ParaBank user.

Open Accounts Overview.

Extract:

- Account Number
- Total Balance
- Available Balance
```

Execution:

```text
Homepage
↓
Register
↓
Fill Registration Form
↓
Submit
↓
Accounts Overview
↓
Read Account Number
↓
Read Total Balance
↓
Read Available Balance
↓
Finish
```

Final Example Output:

```json
{
    "status": "SUCCESS",
    "outputs": {
        "account_number": "23667",
        "total_balance": "$515.50",
        "available_balance": "$515.50"
    }
}
```

---

# Deterministic Replay

Replay performs:

```text
Artifact
↓
No LLM
↓
Replay Execution
↓
Output Verification
```

Example Replay Output:

```json
{
    "status": "SUCCESS",
    "outputs": {
        "account_number": "23667",
        "total_balance": "$515.50",
        "available_balance": "$515.50"
    }
}
```

---

# Replay Outcomes

## Success

```json
{
    "status": "SUCCESS"
}
```

---

## Business Outcome

```json
{
    "status": "BUSINESS_OUTCOME",
    "code": "ACCOUNT_NOT_FOUND"
}
```

---

## Recoverable Error

```json
{
    "status": "RECOVERABLE_ERROR",
    "code": "TRANSIENT_PAGE_TIMEOUT"
}
```

---

## Hard Failure

```json
{
    "status": "HARD_FAILURE",
    "code": "AUTHENTICATION_FAILED"
}
```

---

# Human Handoff Workflow

```text
Automation
↓
Risky Action Detected
↓
Pause
↓
Browser Remains Open
↓
Human Takes Control
↓
Resume
↓
Automation Continues
```

Generated Evidence:

```text
handoff_started.png

automation_resumed.png

handoff.json
```

---

# Safety Controls

## Allowed Host

```text
parabank.parasoft.com
```

---

## Allowed Actions

```text
click
fill
read
wait
finish
escalate
```

---

## Risky Actions

```text
Open New Account
Transfer Funds
Bill Pay
Request Loan
Send Payment
```

---

# Setup

## Create Environment

```bash
python -m venv .venv
```

Activate:

```bash
.venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Install Browser

```bash
playwright install chromium
```

---

# Environment Variables

Create:

```text
.env
```

Example:

```env
PARABANK_BASE_URL=https://parabank.parasoft.com/parabank/index.htm

AZURE_OPENAI_ENDPOINT=<endpoint>

AZURE_OPENAI_API_KEY=<api_key>

AZURE_OPENAI_DEPLOYMENT=gpt-4o

MAX_AGENT_STEPS=25

AGENT_TIMEOUT_SECONDS=300

HEADLESS=false
```

---

# Running Discovery

```bash
python run_agent.py
```

---

# Running Replay

```bash
python app/replay_engine.py
```

---

# Current Capability

Implemented Capability:

```text
ReadAccountBalance
```

Outputs:

```text
Account Number
Total Balance
Available Balance
```

---

# Future Enhancements

```text
Additional Banking Capabilities

Replay Against Live Application

Multi-Capability Catalog

Operator Dashboard

Desktop App Support

Accessibility Tree Support

Multi-Tenant Support
```

---

# Author

Smrithi L Shetty

LLM-Driven Computer Use Automation System

Microsoft Foundry + GPT-4o + Playwright + Deterministic Replay + Human Handoff