---
name: project-memory-sync
description: Maintain an Obsidian/Hermes project memory mirror from a coding repo. Use when the user asks to sync, upload, submit, snapshot, record, close, summarize, or commit project progress; create an initial project snapshot on first use, then create delta upload packets for later changes.
---

# Project Memory Sync

Mirror a coding project into an Obsidian/Hermes Markdown vault.

## Core Rule

Always check `.project-memory/state.json` in the project root before deciding mode.

- If missing: run **initial upload**.
- If present and `initial_upload_completed` is true: run **delta upload**.
- If present but incomplete: repair or rerun initial upload.
- Never run delta mode before a completed initial upload exists.

## Inputs

Use local project evidence:

- `package.json`, manifests, config files, README, source tree.
- `git status`, `git diff --stat`, `git diff`, and recent `git log` when available.
- Existing `.project-memory/state.json`.
- Vault rules from `95-System/` when present in the workspace.

## Outputs

Write Markdown into the configured vault paths:

```text
20-Projects/<project-id>/
90-Agent/Project-Uploads/<project-id>/
60-Tasks/open-tasks.md
.project-memory/state.json
```

If this skill is being used from a repo that is itself the vault workspace, write these paths directly under the repo root.

If the user's actual vault is elsewhere, ask for or infer the vault path only when necessary.

## Initial Upload

Initial upload captures the project baseline:

- Project purpose.
- Technology stack.
- Run/build/test commands.
- Directory structure.
- Entry points.
- Core modules.
- Configuration.
- Current status.
- Known risks.
- Next steps.
- Important files.

Create:

```text
20-Projects/<project-id>/00-project-brief.md
20-Projects/<project-id>/01-architecture.md
20-Projects/<project-id>/02-file-map.md
20-Projects/<project-id>/03-runbook.md
20-Projects/<project-id>/status.md
90-Agent/Project-Uploads/<project-id>/initial-YYYYMMDD-HHMM.md
.project-memory/state.json
```

## Delta Upload

Delta upload records only changes since the last upload:

- Changed files.
- Behavior impact.
- Tests and verification.
- Risks.
- Next steps.
- Suggested commit message.

Create or update:

```text
90-Agent/Project-Uploads/<project-id>/delta-YYYYMMDD-HHMM.md
20-Projects/<project-id>/progress-log.md
20-Projects/<project-id>/status.md
60-Tasks/open-tasks.md
.project-memory/state.json
```

## Helper Script

Prefer using `scripts/project_memory_sync.py` for deterministic file generation.

Typical usage from a project root:

```powershell
python skills/project-memory-sync/scripts/project_memory_sync.py --repo . --vault . --mode auto
```

If the skill has been installed outside the repo, call the script from the installed skill folder and pass explicit paths:

```powershell
python <skill>/scripts/project_memory_sync.py --repo <repo> --vault <vault> --mode auto
```

After the script runs, read the generated packet and improve the human-facing summaries if needed.

## Secret Safety

Never copy contents from:

```text
.env
*.pem
*.key
*.p12
id_rsa
id_ed25519
secrets.*
credentials.*
*.sqlite
*.db
*.dump
node_modules/
dist/
build/
.git/
```

If a protected path changed, mention the path and exclusion reason only.

## Completion Checklist

Before finishing:

- Report whether the run was `initial` or `delta`.
- Report files written.
- Report packet path.
- Report state file path.
- Report suggested commit message if present.
- Do not push to remote unless the user explicitly asked.

## References

- Use `references/packet-format.md` for packet and project file templates.
- Use workspace `95-System/project-memory-sync-spec.md` when available for the authoritative local protocol.
