# Recourse Security Principles

## Rule 1
The AI investigation agent must never receive `AdministratorAccess`.

## Rule 2
The investigation agent should eventually receive read-only diagnostic tools.

## Rule 3
Infrastructure modifications must happen through a separate remediation executor.

## Rule 4
The remediation executor receives only the minimum API actions required.

## Rule 5
The agent cannot approve its own action.

## Rule 6
A human approval step must precede remediation.

## Rule 7
Only explicitly enrolled resources are eligible for automated remediation. (e.g. `RecourseManaged=true`)

## Rule 8
All important incident transitions are written to the audit timeline.

## Architecture
```text
AI Investigator
      ↓
Recommendation
      ↓
Deterministic Policy
      ↓
Human Approval
      ↓
Restricted Executor
      ↓
AWS Resource
```
