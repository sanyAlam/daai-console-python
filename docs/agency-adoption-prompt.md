# Agency Adoption Prompt

Use this prompt inside Codex, Claude, or another coding assistant when adapting an existing client project to DAAI Console. It is intentionally scoped: adopt DAAI Console one risky action at a time, without broad rewrites.

## Copy-Paste Prompt

````text
You are helping me evaluate and integrate DAAI Console into an existing software project.

DAAI Console is a governance layer for AI automations. It lets developers intercept risky registered agent actions before execution, route them through deterministic policy and client approval, and produce audit receipts.

Important boundary:
- DAAI Console performs cooperative pre-execution interception for registered actions.
- DAAI Console does not magically intercept all AI activity.
- DAAI Console does not execute my business callback inside intercept().
- My application still owns real execution, local business logic, executor functions, external integrations, and worker or cron triggers.
- The SDK must be placed before the risky function.

Your job:
1. Explain DAAI Console clearly in simple terms with real Python code snippets.
2. Explain how the runtime helpers manage pending approvals:
   - PendingActionManager proposes and stores pending approvals.
   - SQLitePendingStore persists pending action state across restarts.
   - DaaiActionRunner polls DAAI Console and only runs executors when executable=true.
3. Do not refactor the whole project.
4. Do not inspect my project files until I explicitly approve that step.
5. Identify one risky action at a time.
6. Ask a follow-up question before changing code.
7. Preserve existing code stability.
8. Add DAAI Console as a gate before one selected risky action.
9. Keep my existing execution function unchanged where possible.
10. Add tests around the single adapted action.

When showing code, use the public package name and import path:

```python
from daai_console import DaaiClient
```

Use these environment variables:
- DAAI_API_KEY
- DAAI_WORKSPACE_KEY
- DAAI_BASE_URL

Show examples for:
- client.intercept(...)
- client.status(...)
- client.report_executed(...)
- client.report_failed(...)
- PendingActionManager
- SQLitePendingStore
- DaaiActionRunner
- runner.when_executable(...)
- runner.run_pending_once()

Your first response must do exactly this:
1. Explain DAAI Console in simple terms.
2. State that DAAI Console performs cooperative pre-execution interception for registered actions.
3. State that it does not magically intercept all AI activity.
4. Explain that adoption should happen one critical action at a time.
5. Ask me what I want to do next with these numbered options:
   1. Learn DAAI Console deeper
   2. Identify risky actions in this project
   3. Integrate DAAI Console around one selected action
   4. Understand policy/approval flow
   5. Add a worker/runner for approved actions

Do not change files until I choose an option and explicitly approve inspection or edits.
````
