# Privacy & data handling

Short version: **this tool runs on your machine. Your data goes only to Anthropic, using your own API key. The authors of this tool never see your data, your key, or your results.**

---

## Where everything lives

| Thing | Where it goes |
|-------|---------------|
| Your workflow data | Read from your local file. Sent only to Anthropic's API for analysis. |
| Your API key | Stored locally at `~/.config/measure-twice/config.toml`, file permissions locked to your user (mode 600). Never transmitted anywhere except as the auth header on your own API calls to Anthropic. |
| Your results | Written to a local folder next to your input file. Stored in a local SQLite database (`workflow_analysis.db`). Never uploaded. |
| Telemetry / analytics | None. The tool phones home to nobody. |

There is no server. There is no hosted version. There is no account with us. The tool is an open-source program you run yourself.

---

## What Anthropic sees

When the tool analyzes your workflow, it sends that text to Anthropic's API — exactly as if you'd pasted it into Claude yourself. Anthropic's data-handling terms govern that exchange.

**For enterprise / sensitive data:**

- Use an API key from an Anthropic **Workspace** governed by your organization's commercial agreement (the Commercial Terms of Service, under which Anthropic does not train on your inputs/outputs).
- Confirm your Workspace's data-retention settings in the [Anthropic Console](https://console.anthropic.com) before running on sensitive material.
- If your organization prohibits sending certain data to third-party APIs, treat this tool the same as any other use of an external LLM and clear it through the same review.

---

## What this means for distributing the tool to teams

Because nothing touches our infrastructure, distributing this tool inside your organization carries the same data-governance profile as letting your teams use Claude or ChatGPT directly — no additional vendor, no additional data-processing agreement with us, no SOC 2 dependency on us. The only external party in the loop is Anthropic, under your own API key and your own terms.

If your security team asks "where does the data go," the answer is: **from the employee's laptop, directly to Anthropic, under our own API agreement. The tool authors are not in the data path.**

---

## Reading the code

This is open source. The entire network surface is the Anthropic API calls in `src/workflow_analyzer/runner.py`. There are no other outbound connections. Read it, or have your security team read it.
