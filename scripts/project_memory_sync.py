#!/usr/bin/env python3
"""Generate Obsidian/Hermes project memory snapshots and delta packets."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".project-memory",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "__pycache__",
}

PROTECTED_PATTERNS = (
    re.compile(r"(^|/)\.env($|[./-])", re.I),
    re.compile(r"\.(pem|key|p12|sqlite|db|dump)$", re.I),
    re.compile(r"(^|/)(id_rsa|id_ed25519)$", re.I),
    re.compile(r"(^|/)(secrets|credentials)\.", re.I),
)

TEXT_EXTS = {
    ".c",
    ".cc",
    ".conf",
    ".config",
    ".css",
    ".csv",
    ".env.example",
    ".go",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class ProjectInfo:
    project_id: str
    repo: Path
    vault: Path
    now: datetime
    stamp: str
    readable_time: str
    iso_time: str
    commit: str


def run(cmd: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_root(repo: Path) -> Path | None:
    root = run(["git", "rev-parse", "--show-toplevel"], repo)
    return Path(root) if root else None


def ignores_project_memory(lines: Iterable[str]) -> bool:
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        normalized = stripped.replace("\\", "/").lstrip("/")
        if normalized in {".project-memory", ".project-memory/"}:
            return True
    return False


def ensure_project_memory_gitignore(repo: Path) -> tuple[Path, bool] | None:
    root = git_root(repo)
    if root is None:
        return None
    gitignore = root / ".gitignore"
    try:
        content = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    except OSError:
        return None
    if ignores_project_memory(content.splitlines()):
        return gitignore, False
    if content and not content.endswith(("\n", "\r")):
        content += "\n"
    content += ".project-memory/\n"
    write_text(gitignore, content)
    return gitignore, True


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def is_protected(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = set(normalized.split("/"))
    if parts.intersection(SKIP_DIRS):
        return True
    return any(pattern.search(normalized) for pattern in PROTECTED_PATTERNS)


def should_skip_dir(path: Path) -> bool:
    return path.name in SKIP_DIRS


def safe_read(path: Path, limit: int = 12000) -> str:
    rel = path.as_posix()
    if is_protected(rel):
        return ""
    if path.suffix.lower() not in TEXT_EXTS and path.name not in {"README", "LICENSE"}:
        return ""
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return data[:limit]


def list_files(repo: Path, limit: int = 200) -> list[str]:
    files: list[str] = []
    for root, dirs, names in os.walk(repo):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_skip_dir(root_path / d)]
        for name in sorted(names):
            full = root_path / name
            rel = full.relative_to(repo).as_posix()
            if is_protected(rel):
                continue
            files.append(rel)
            if len(files) >= limit:
                return files
    return files


def tree_lines(files: Iterable[str], max_items: int = 120) -> str:
    lines = []
    for rel in list(files)[:max_items]:
        depth = rel.count("/")
        indent = "  " * depth
        lines.append(f"{indent}- {Path(rel).name if depth else rel}")
    return "\n".join(lines) or "- No files found"


def detect_stack(repo: Path) -> list[str]:
    stack: list[str] = []
    markers = {
        "package.json": "Node.js / TypeScript or JavaScript",
        "tsconfig.json": "TypeScript",
        "vite.config.ts": "Vite",
        "next.config.js": "Next.js",
        "pyproject.toml": "Python",
        "requirements.txt": "Python",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "Dockerfile": "Docker",
    }
    for marker, label in markers.items():
        if (repo / marker).exists() and label not in stack:
            stack.append(label)
    if (repo / "manifest.json").exists() and (repo / "src" / "main.ts").exists():
        stack.append("Obsidian plugin")
    return stack or ["Unknown"]


def package_scripts(repo: Path) -> dict[str, str]:
    package_json = repo / "package.json"
    if not package_json.exists():
        return {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts")
    if isinstance(scripts, dict):
        return {str(k): str(v) for k, v in scripts.items()}
    return {}


def project_description(repo: Path) -> str:
    package_json = repo / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            desc = data.get("description")
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
        except (OSError, json.JSONDecodeError):
            pass
    readme = repo / "README.md"
    content = safe_read(readme, 4000) if readme.exists() else ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
            return stripped[:300]
    return "Project purpose needs human review."


def current_commit(repo: Path) -> str:
    commit = run(["git", "rev-parse", "--short", "HEAD"], repo)
    if not commit:
        return "working-tree"
    status = run(["git", "status", "--short"], repo)
    return f"{commit}+dirty" if status else commit


def load_state(repo: Path) -> dict | None:
    state_path = repo / ".project-memory" / "state.json"
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def frontmatter(**fields: str) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def make_info(repo: Path, vault: Path, project_id: str | None) -> ProjectInfo:
    now = datetime.now().astimezone()
    stamp = now.strftime("%Y%m%d-%H%M")
    readable_time = now.strftime("%Y-%m-%d %H:%M:%S")
    iso_time = now.isoformat(timespec="seconds")
    if not project_id:
        project_id = slugify(repo.name)
    return ProjectInfo(
        project_id=project_id,
        repo=repo,
        vault=vault,
        now=now,
        stamp=stamp,
        readable_time=readable_time,
        iso_time=iso_time,
        commit=current_commit(repo),
    )


def project_paths(info: ProjectInfo) -> dict[str, Path]:
    project_dir = info.vault / "20-Projects" / info.project_id
    packet_dir = info.vault / "90-Agent" / "Project-Uploads" / info.project_id
    return {
        "project_dir": project_dir,
        "packet_dir": packet_dir,
        "brief": project_dir / "00-project-brief.md",
        "architecture": project_dir / "01-architecture.md",
        "file_map": project_dir / "02-file-map.md",
        "runbook": project_dir / "03-runbook.md",
        "status": project_dir / "status.md",
        "progress": project_dir / "progress-log.md",
        "tasks": info.vault / "60-Tasks" / "open-tasks.md",
        "state": info.repo / ".project-memory" / "state.json",
    }


def command_list(scripts: dict[str, str]) -> str:
    if not scripts:
        return "- No package scripts detected."
    return "\n".join(f"- `{name}`: `{cmd}`" for name, cmd in scripts.items())


def initial_upload(info: ProjectInfo) -> dict[str, str]:
    paths = project_paths(info)
    files = list_files(info.repo)
    stack = detect_stack(info.repo)
    scripts = package_scripts(info.repo)
    desc = project_description(info.repo)
    file_tree = tree_lines(files)
    stack_lines = "\n".join(f"- {item}" for item in stack)
    important = "\n".join(f"- `{item}`" for item in files[:40])

    brief = f"""{frontmatter(type="project-brief", owner="skill", status="active", project=info.project_id, created=info.readable_time, modified=info.readable_time, source="project-memory-sync")}

# {info.project_id} Project Brief

## Purpose

{desc}

## Technology Stack

{stack_lines}

## Current Status

- Initial project snapshot created.
- Needs human review for project goals, risks, and next actions.

## Next Actions

- [ ] Review this initial project brief.
- [ ] Confirm active development priorities.
"""
    architecture = f"""{frontmatter(type="project-architecture", owner="skill", status="draft", project=info.project_id, created=info.readable_time, modified=info.readable_time, source="project-memory-sync")}

# Architecture

## Entry Points

{important}

## Core Modules

- Needs AI or human review after initial skeleton generation.

## Notes

This file was generated from repository structure and should be refined after code inspection.
"""
    file_map = f"""{frontmatter(type="project-file-map", owner="skill", status="active", project=info.project_id, created=info.readable_time, modified=info.readable_time, source="project-memory-sync")}

# File Map

## Repository Structure

{file_tree}

## Important Files

{important}
"""
    runbook = f"""{frontmatter(type="project-runbook", owner="skill", status="active", project=info.project_id, created=info.readable_time, modified=info.readable_time, source="project-memory-sync")}

# Runbook

## Commands

{command_list(scripts)}

## Build

- Use the build command above when available.

## Test

- Use the test command above when available.

## Deploy

- Needs project-specific instructions.
"""
    status = f"""{frontmatter(type="project-status", owner="mixed", status="active", project=info.project_id, modified=info.readable_time)}

# Project Status

## Current State

Initial snapshot created. Awaiting human review.

## Last Upload

- Mode: initial
- Commit: `{info.commit}`
- Time: {info.readable_time}

## Active Risks

- Project status is based on structural inspection only.

## Next Actions

- [ ] Review generated project memory files.

## Waiting For

- Human confirmation.

## Recent Changes

- Initial project memory baseline generated.
"""
    packet = f"""{frontmatter(type="project-upload", mode="initial", project=info.project_id, status="pending-hermes", created=info.readable_time, repo_commit=info.commit, source="project-memory-sync")}

# Initial Project Snapshot

## Project Purpose

{desc}

## Technology Stack

{stack_lines}

## How To Run

{command_list(scripts)}

## How To Build

{scripts.get("build", "No build command detected.")}

## How To Test

{scripts.get("test", "No test command detected.")}

## Directory Structure

{file_tree}

## Core Modules

- Needs semantic review.

## Current Status

- Initial snapshot generated from repository structure and manifests.

## Known Risks

- Generated summary needs human review.
- Protected and generated directories were excluded.

## Next Steps

- Review generated project files.
- Run a semantic pass to refine architecture and module descriptions.

## Important Files

{important}
"""
    packet_path = paths["packet_dir"] / f"initial-{info.stamp}.md"
    outputs = {
        str(paths["brief"]): brief,
        str(paths["architecture"]): architecture,
        str(paths["file_map"]): file_map,
        str(paths["runbook"]): runbook,
        str(paths["status"]): status,
        str(packet_path): packet,
    }
    for path, content in outputs.items():
        write_text(Path(path), content)

    state = {
        "project_id": info.project_id,
        "initial_upload_completed": True,
        "last_upload_commit": info.commit,
        "last_upload_at": info.iso_time,
        "vault_project_path": f"20-Projects/{info.project_id}",
        "upload_packet_path": f"90-Agent/Project-Uploads/{info.project_id}",
    }
    write_text(paths["state"], json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    return {"mode": "initial", "packet": str(packet_path), "state": str(paths["state"])}


def git_changed_files(repo: Path) -> list[str]:
    status = run(["git", "status", "--short"], repo)
    files: list[str] = []
    for line in status.splitlines():
        rel = line[3:].strip()
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        if rel and not is_protected(rel):
            files.append(rel)
    return files


def delta_upload(info: ProjectInfo, state: dict) -> dict[str, str]:
    paths = project_paths(info)
    previous = str(state.get("last_upload_commit") or "unknown")
    changed = git_changed_files(info.repo)
    diff_stat = run(["git", "diff", "--stat"], info.repo)
    staged_stat = run(["git", "diff", "--cached", "--stat"], info.repo)
    status_short = run(["git", "status", "--short"], info.repo)
    changed_lines = "\n".join(f"- `{item}`" for item in changed) or "- No changed files detected by Git."
    verification = "- Not run by project-memory-sync script."
    suggested = suggest_commit_message(changed)

    packet = f"""{frontmatter(type="project-upload", mode="delta", project=info.project_id, status="pending-hermes", created=info.readable_time, repo_commit=info.commit, previous_upload_commit=previous, source="project-memory-sync")}

# Project Delta

## Summary

Generated delta packet for current working tree changes. Needs AI or human refinement.

## Changed Files

{changed_lines}

## Git Status

```text
{status_short or "Clean working tree"}
```

## Diff Stat

```text
{diff_stat or staged_stat or "No diff stat available"}
```

## Behavior Impact

- Needs semantic review.

## Tests And Verification

{verification}

## Risks

- Generated from Git metadata only; inspect changed files before relying on this summary.

## Next Steps

- Review changed files.
- Run relevant build or test commands.

## Suggested Commit Message

```text
{suggested}
```
"""
    packet_path = paths["packet_dir"] / f"delta-{info.stamp}.md"
    write_text(packet_path, packet)

    progress_entry = f"""
## {info.readable_time}

- Mode: delta
- Commit: `{info.commit}`
- Summary: Generated delta packet for current working tree changes.
- Changed files: {", ".join(changed) if changed else "none detected"}
- Verification: not run by script
- Next actions: review packet and run relevant checks
"""
    append_text(paths["progress"], progress_entry)

    status = f"""{frontmatter(type="project-status", owner="mixed", status="active", project=info.project_id, modified=info.readable_time)}

# Project Status

## Current State

Delta upload generated. Awaiting human or Hermes review.

## Last Upload

- Mode: delta
- Commit: `{info.commit}`
- Previous upload: `{previous}`
- Time: {info.readable_time}

## Active Risks

- Delta packet needs semantic review.

## Next Actions

- [ ] Review latest delta packet.
- [ ] Run relevant verification commands.

## Waiting For

- Hermes processing.

## Recent Changes

{changed_lines}
"""
    write_text(paths["status"], status)

    task_note = f"""
- [ ] Review project delta for `{info.project_id}` <!-- task-id:{info.project_id}-{info.stamp}-review source:project-memory-sync -->
"""
    if paths["tasks"].exists():
        append_text(paths["tasks"], task_note)
    else:
        write_text(
            paths["tasks"],
            f"""{frontmatter(type="task-index", owner="mixed", status="active")}

# Open Tasks

## Next Actions
{task_note}

## Waiting For

## Someday
""",
        )

    new_state = dict(state)
    new_state.update(
        {
            "project_id": info.project_id,
            "initial_upload_completed": True,
            "last_upload_commit": info.commit,
            "last_upload_at": info.iso_time,
            "vault_project_path": f"20-Projects/{info.project_id}",
            "upload_packet_path": f"90-Agent/Project-Uploads/{info.project_id}",
        }
    )
    write_text(paths["state"], json.dumps(new_state, indent=2, ensure_ascii=False) + "\n")
    return {"mode": "delta", "packet": str(packet_path), "state": str(paths["state"]), "commit_message": suggested}


def suggest_commit_message(changed: list[str]) -> str:
    if not changed:
        return "chore: record project memory sync"
    if any(path.startswith("95-System/") for path in changed):
        return "docs: add knowledge system protocol"
    if any(path.startswith("skills/") for path in changed):
        return "feat: add project memory sync skill"
    if any(path.startswith("src/") for path in changed):
        return "feat: update project implementation"
    return "chore: update project files"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Project repository path")
    parser.add_argument("--vault", default=".", help="Obsidian vault path")
    parser.add_argument("--project-id", default=None, help="Project slug")
    parser.add_argument("--mode", choices=["auto", "initial", "delta"], default="auto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    vault = Path(args.vault).resolve()
    if not repo.exists():
        raise SystemExit(f"repo path does not exist: {repo}")
    if not vault.exists():
        vault.mkdir(parents=True)

    gitignore_result = ensure_project_memory_gitignore(repo)
    state = load_state(repo)
    mode = args.mode
    if mode == "auto":
        mode = "delta" if state and state.get("initial_upload_completed") else "initial"
    info = make_info(repo, vault, args.project_id or (state or {}).get("project_id"))

    if mode == "delta":
        if not state or not state.get("initial_upload_completed"):
            raise SystemExit("delta mode requires completed .project-memory/state.json")
        result = delta_upload(info, state)
    else:
        result = initial_upload(info)

    if gitignore_result:
        gitignore_path, gitignore_updated = gitignore_result
        result["gitignore"] = str(gitignore_path)
        result["gitignore_updated"] = gitignore_updated

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
