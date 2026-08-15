# Agent findings inbox

Each monitoring agent writes one JSON file per daily run to:

```text
data/agent-findings/inbox/<agent-name>/YYYY-MM-DD.json
```

The file must contain the JSON contract from `AGENT_PROMPTS.md`. The daily
workflow merges every inbox file, deduplicates events, publishes only events
with `auto_publish: true` and valid evidence metadata, and deploys the Updates
page. Quarantined leads are retained in the agent output but are not published.
