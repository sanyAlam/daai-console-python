# Security Model

DAAI Console alpha is a cooperative governance layer for registered agent actions. It is designed to help developers pause risky actions before execution, route those actions through deterministic policy and approval, and preserve an audit trail.

## Threat Model For Alpha

The alpha assumes a developer intentionally integrates the SDK before selected risky actions. The developer app is trusted to call DAAI Console before executing those actions and to respect `executable=false` decisions.

The alpha is mainly concerned with accidental execution before approval, unclear audit trails, local loss of pending approval state, and ambiguous execution reporting.

## What The SDK Protects Against

- Accidental execution before approval when developers use the SDK/runtime as intended.
- Missing approval audit trail for registered actions governed by DAAI Console.
- Loss of pending action state when `SQLitePendingStore` is used.
- Unclear execution reporting by providing explicit `report_executed()` and `report_failed()` calls.

## What The SDK Does Not Protect Against

- A malicious developer bypassing the SDK.
- Compromised API keys or workspace keys.
- A compromised host machine.
- A malicious external integration called by the developer app.
- A developer storing payloads insecurely.
- Arbitrary code execution that was never registered or gated through DAAI Console.

## Trust Boundary

The trust boundary has five parts:

- SDK: proposes actions, checks status, reports execution, and optionally stores pending actions locally.
- DAAI Console API: validates keys, evaluates deterministic policy, manages approval state, and records receipts.
- Developer application: decides where to place the gate and owns business logic.
- Local executor: performs the real external action only after approval or allow decision.
- Approval email recipient: reviews the approval context and approves or rejects the action.

## Key Handling Rules

- Keep API keys and workspace keys server-side only.
- Never place keys in browser JavaScript, mobile apps, public repositories, or logs.
- Rotate or revoke keys immediately if leaked.
- Use separate keys per environment when possible.

## Payload Handling

- Send only what is needed for approval and audit.
- Avoid unnecessary secrets, tokens, credentials, and sensitive PII in payloads.
- Approval links should not contain sensitive payload data.
- Local pending stores can contain sensitive business payloads.
- Protect SQLite files with normal server file permissions, disk encryption where appropriate, and environment-specific retention policies.
