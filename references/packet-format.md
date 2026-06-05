# Packet Format Reference

Use this reference when writing or reviewing project upload packets.

## State File

```json
{
  "project_id": "project-slug",
  "initial_upload_completed": true,
  "last_upload_commit": "git-commit-sha-or-working-tree",
  "last_upload_at": "YYYY-MM-DDTHH:mm:ss+08:00",
  "vault_project_path": "20-Projects/project-slug",
  "upload_packet_path": "90-Agent/Project-Uploads/project-slug"
}
```

## Initial Packet

```markdown
---
type: project-upload
mode: initial
project: project-id
status: pending-hermes
created: YYYY-MM-DD HH:mm:ss
repo_commit: commit-sha-or-working-tree
source: project-memory-sync
---

# Initial Project Snapshot

## Project Purpose

## Technology Stack

## How To Run

## How To Build

## How To Test

## Directory Structure

## Core Modules

## Current Status

## Known Risks

## Next Steps

## Important Files
```

## Delta Packet

```markdown
---
type: project-upload
mode: delta
project: project-id
status: pending-hermes
created: YYYY-MM-DD HH:mm:ss
repo_commit: commit-sha-or-working-tree
previous_upload_commit: previous-commit-sha-or-working-tree
source: project-memory-sync
---

# Project Delta

## Summary

## Changed Files

## Behavior Impact

## Tests And Verification

## Risks

## Next Steps

## Suggested Commit Message
```

## Project Status

```markdown
---
type: project-status
owner: mixed
status: active
project: project-id
modified: YYYY-MM-DD HH:mm:ss
---

# Project Status

## Current State

## Last Upload

## Active Risks

## Next Actions

## Waiting For

## Recent Changes
```

## Progress Log Entry

```markdown
## YYYY-MM-DD HH:mm

- Mode: delta
- Commit: commit-sha-or-working-tree
- Summary:
- Changed files:
- Verification:
- Next actions:
```
