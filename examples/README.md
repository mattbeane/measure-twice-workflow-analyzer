# Example workflows

Three sample datasets, each one instance of a real-shaped workflow with the messy exhaust the tool is built to read — timestamped emails, Slack threads, and meeting notes. Use them to smoke-test your setup or to see what good output looks like before running on your own data.

| Folder | Workflow | Domain |
|--------|----------|--------|
| `feature-deploy/` | Feature request → customer deployment | Engineering / product |
| `sales-pipeline/` | Inbound lead → signed contract | Sales / revenue |
| `support-resolution/` | Escalated ticket → resolution | Customer support / ops |

Run any of them:

```bash
mtso analyze examples/sales-pipeline/workflow.txt --quick
```

`--quick` keeps it to ~10 runs/prompt (cents, ~1 min). Drop the flag for a full run.

## Why three domains

The method is function-agnostic — process and skill signals live in the exhaust of *any* team's work, not just engineering. The three samples exist to make that obvious to a mixed-function room. If your workflow looks nothing like these, that's fine: the tool reads whatever text you give it.

## Building your own

There's no required format. Dump real emails, Slack, and meeting notes for one complete cycle of a process into a `.txt` file. The denser the timestamps and named actors, the better the cycle-time and handoff metrics. See any `workflow.txt` here for the shape.
