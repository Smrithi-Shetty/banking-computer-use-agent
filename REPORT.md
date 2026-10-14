# Banking Computer-Use Automation System

# 1. Architecture

## Solution Overview

The solution implements an end-to-end Computer Use Automation System capable of:

1. Accepting a natural language goal.
2. Using a Large Language Model (LLM) to interact with a live application.
3. Discovering the actions required to complete the goal.
4. Recording the successful workflow as a reusable capability artifact.
5. Replaying the workflow deterministically without the LLM.
6. Escalating to a human operator when the system cannot safely continue.
7. Capturing evidence throughout discovery, replay, and handoff activities.

The implementation uses:

- Microsoft Azure AI Foundry
- GPT-4o
- Playwright
- Python
- ParaBank Demo Banking Application

The high-level architecture is shown below.

```text
User Goal
    │
    ▼
Microsoft Foundry GPT-4o
    │
    ▼
Discovery Agent
(Observe → Decide → Act)
    │
    ▼
Capability Artifact
    │
    ▼
Replay Engine
    │
    ├── Success
    ├── Business Outcome
    ├── Recoverable Error
    └── Hard Failure
    │
    ▼
Human Handoff
    │
    ▼
Resume
```

---

# 2. Goal-Driven Agent Loop

## Objective

The objective of the Agent Loop is to transform a natural language instruction into successfully completed actions on a live application.

Example goal:

```text
Register a new ParaBank user.
Open Accounts Overview.
Extract Account Number.
Extract Total Balance.
Extract Available Balance.
```

## Loop Design

The system implements a structured:

```text
Observe
↓
Decide
↓
Act
↓
Observe Again
```

workflow.

### Observe

The browser state is inspected using `surface.py`.

Information collected includes:

- URL
- Page title
- Links
- Buttons
- Inputs
- Semantic table values

Example:

```json
{
  "element_id": "table_value_0",
  "kind": "table_value",
  "column_header": "Account",
  "value_text": "23667"
}
```

### Decide

Observations are sent to GPT-4o using Microsoft Foundry.

The model selects exactly one action:

```json
{
  "action": "fill",
  "target_id": "input_3",
  "value_ref": "runtime_first_name"
}
```

### Act

The selected action is executed using Playwright.

Supported actions:

```text
click
fill
read
wait
finish
escalate
```

This cycle continues until:

```text
Goal Complete
Maximum Steps Reached
Timeout
Human Intervention Required
Execution Failure
```

---

# 3. Capability Artifact Schema

## Purpose

A successful discovery run becomes a reusable capability artifact.

The artifact serves as the bridge between:

```text
Discovery
↓
Production Execution
```

## Example Structure

```json
{
    "artifactVersion": "1.0",
    "capability": {
        "name": "ReadAccountBalance"
    },
    "outputs": {
        "account_number": "23667",
        "total_balance": "$515.50",
        "available_balance": "$515.50"
    },
    "steps": [...]
}
```

## Contents

Each artifact contains:

- Capability metadata
- Inputs
- Outputs
- Complete step history
- Discovery evidence linkage

Artifacts are stored in:

```text
artifacts/
```

and are versioned using timestamps.

---

# 4. Deterministic Replay

## Objective

Replay executes the capability without any LLM involvement.

The design principle is:

```text
Discovery Uses AI
Replay Does Not
```

## Replay Process

```text
Load Artifact
↓
Validate Artifact
↓
Replay Capability
↓
Return Outputs
↓
Save Replay Evidence
```

Replay uses:

```python
replay_engine.py
```

and produces:

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

## Benefits

Replay provides:

- Determinism
- Predictability
- Lower cost
- No LLM dependency
- Auditability

---

# 5. Error Taxonomy

The system implements four execution outcomes.

## Success

```json
{
    "status": "SUCCESS"
}
```

The requested capability completed successfully.

---

## Business Outcome

```json
{
    "status": "BUSINESS_OUTCOME",
    "code": "ACCOUNT_NOT_FOUND"
}
```

No technical failure occurred.

The requested business record does not exist.

---

## Recoverable Error

```json
{
    "status": "RECOVERABLE_ERROR",
    "code": "TRANSIENT_PAGE_TIMEOUT"
}
```

Temporary problem.

The replay engine may retry.

Examples:

- Page loads slowly
- Temporary UI unavailability

---

## Hard Failure

```json
{
    "status": "HARD_FAILURE",
    "code": "AUTHENTICATION_FAILED"
}
```

The workflow cannot continue.

Examples:

- Invalid credentials
- Corrupt artifact
- Critical navigation failure

---

# 6. Human Intervention Workflow

## Objective

Provide a safe fallback when automation cannot continue.

Examples:

- Risky banking action
- Ambiguous UI state
- Safety violation
- Repeated failed actions

## Process

```text
Automation
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

The existing browser session is preserved.

No new session is created.

## Evidence Generated

```text
evidence/handoff/
├── handoff_started.png
├── automation_resumed.png
└── handoff.json
```

This provides a complete audit trail.

---

# 7. Safety Controls

## Host Allowlist

Only:

```text
parabank.parasoft.com
```

is permitted.

All other destinations are blocked.

## Allowed Actions

```text
click
fill
read
wait
finish
escalate
```

## Risky Operations

The following actions are classified as risky:

```text
Open New Account
Transfer Funds
Bill Pay
Request Loan
Send Payment
```

Risky actions require human review.

## Credential Protection

Credentials are never:

- Hardcoded
- Logged
- Stored in artifacts

Runtime values are resolved only during execution.

---

# 8. Evidence Strategy

Evidence exists at three levels.

## Discovery Evidence

Directory:

```text
evidence/discovery/
```

Contains:

```text
Screenshots
```

Example:

```text
account_overview_20261014_160005.png
```

---

## Replay Evidence

Directory:

```text
evidence/replay/
```

Contains:

```text
Replay Result JSON
```

Example:

```text
replay_result_20261014_164928.json
```

---

## Handoff Evidence

Directory:

```text
evidence/handoff/
```

Contains:

```text
Session JSON
Pause Screenshot
Resume Screenshot
```

This allows full auditability of human interactions.

---

# 9. Future Enhancements

The current implementation focuses on a single banking capability.

Future improvements include:

## Multiple Banking Capabilities

Examples:

```text
Transfer Funds

Bill Pay

Open Savings Account

Loan Application
```

## Replay Against Live UI

Current replay uses stored capability outputs.

Future replay will navigate and re-execute the live application.

## Capability Catalog

Store and manage multiple capability artifacts.

## Operator Dashboard

Provide a visual interface for:

```text
Escalations

Approvals

Resumes

Evidence Review
```

## Desktop Support

Extend support beyond browser automation.

Examples:

```text
Windows Applications

Accessibility Trees

Desktop UI Automation
```

---

# Conclusion

The solution successfully demonstrates:

- Goal-driven LLM automation
- Observe → Decide → Act execution
- Capability artifact creation
- Deterministic replay
- Structured error handling
- Human-in-the-loop escalation
- Replay and discovery evidence collection
- Safety controls

The architecture provides a practical foundation for transforming discovered AI workflows into reusable production capabilities.