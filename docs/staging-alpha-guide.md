# Staging Alpha Guide

This guide is for alpha testers who already have a DAAI Console staging workspace, API key, and workspace key.

## Environment

Set these values in your server-side shell:

```bash
export DAAI_BASE_URL="https://your-staging-api.example.com"
export DAAI_API_KEY="your-sdk-api-key"
export DAAI_WORKSPACE_KEY="your-workspace-key"
```

Do not commit these values. Do not place them in browser code.

## Smoke Test

Run a dry run first:

```bash
python examples/staging_alpha_test.py --dry-run
```

Then run the staging example:

```bash
python examples/staging_alpha_test.py
```

The script proposes `send_invoice_reminder`, prints sanitized status fields, and reports execution only if DAAI Console returns `executable=true`. It does not auto-approve anything.
