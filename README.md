# Project Memory Sync

English | [中文](#中文)

Project Memory Sync is a Codex / Claude Code skill for mirroring coding projects into an Obsidian + Hermes Markdown vault.

It creates a full project snapshot on first use, then records only incremental changes for later sessions. The generated Markdown packets are designed for Hermes to process into project status pages, daily briefs, tasks, and wiki updates.

## What It Does

- Creates an initial project baseline for a repository.
- Generates delta upload packets from later Git changes.
- Writes Obsidian-friendly Markdown files.
- Maintains `.project-memory/state.json` so future runs know whether to use initial or delta mode.
- Avoids copying secrets, credentials, generated builds, dependencies, and Git internals.
- Suggests commit messages without automatically pushing to a remote.

## Repository Structure

```text
project-memory-sync/
  SKILL.md
  README.md
  .gitignore
  agents/
    openai.yaml
  references/
    packet-format.md
  scripts/
    project_memory_sync.py
```

## Install

### Codex

Copy this folder to:

```text
~/.codex/skills/project-memory-sync/
```

### Claude Code

Copy this folder to:

```text
~/.claude/skills/project-memory-sync/
```

You can also keep it inside a project-specific skills folder if your local toolchain supports project-level skills.

## Usage

Ask Codex or Claude Code:

```text
Use project-memory-sync to upload this project.
Use project-memory-sync to record this session.
Create initial project snapshot.
Create delta upload for this change.
Sync project progress to Obsidian.
```

The skill will inspect `.project-memory/state.json`:

- If missing, it performs an initial upload.
- If present and completed, it performs a delta upload.

## Helper Script

From a repository root:

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault <path-to-vault> --mode auto
```

If the repository itself is also the vault workspace:

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault . --mode auto
```

Force initial mode:

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault <path-to-vault> --mode initial
```

Force delta mode:

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault <path-to-vault> --mode delta
```

## Generated Files

Initial upload creates:

```text
20-Projects/<project-id>/00-project-brief.md
20-Projects/<project-id>/01-architecture.md
20-Projects/<project-id>/02-file-map.md
20-Projects/<project-id>/03-runbook.md
20-Projects/<project-id>/status.md
90-Agent/Project-Uploads/<project-id>/initial-YYYYMMDD-HHMM.md
.project-memory/state.json
```

Delta upload creates or updates:

```text
90-Agent/Project-Uploads/<project-id>/delta-YYYYMMDD-HHMM.md
20-Projects/<project-id>/progress-log.md
20-Projects/<project-id>/status.md
60-Tasks/open-tasks.md
.project-memory/state.json
```

## Safety

The skill and helper script avoid copying protected content such as:

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

If a protected file is relevant, only the path and exclusion reason should be mentioned.

## Upload This Skill To GitHub

Create a new GitHub repository, then run:

```powershell
cd path/to/project-memory-sync
git init
git add SKILL.md README.md .gitignore agents references scripts
git commit -m "feat: add project memory sync skill"
git branch -M main
git remote add origin https://github.com/<your-user>/project-memory-sync.git
git push -u origin main
```

## License

MIT License. See [LICENSE](LICENSE).

---

# 中文

Project Memory Sync 是一个给 Codex / Claude Code 使用的 Skill，用来把本地代码项目同步到 Obsidian + Hermes Markdown Vault。

它会在第一次使用时生成项目全貌快照，之后每次只记录增量修改。生成的 Markdown 上传包可以交给 Hermes 继续整理成项目状态、日报、任务和 Wiki 更新。

## 它能做什么

- 为代码仓库创建首次项目基线。
- 根据后续 Git 修改生成增量上传包。
- 输出适合 Obsidian 阅读的 Markdown 文件。
- 维护 `.project-memory/state.json`，让后续运行知道应该走首次模式还是增量模式。
- 避免复制密钥、凭证、构建产物、依赖目录和 Git 内部文件。
- 提供 commit message 建议，但不会自动 push 到远程仓库。

## 仓库结构

```text
project-memory-sync/
  SKILL.md
  README.md
  .gitignore
  agents/
    openai.yaml
  references/
    packet-format.md
  scripts/
    project_memory_sync.py
```

## 安装

### Codex

把整个文件夹复制到：

```text
~/.codex/skills/project-memory-sync/
```

### Claude Code

把整个文件夹复制到：

```text
~/.claude/skills/project-memory-sync/
```

如果你的工具链支持项目级 Skill，也可以把它放在项目自己的 skills 目录里。

## 使用方式

你可以对 Codex 或 Claude Code 说：

```text
Use project-memory-sync to upload this project.
Use project-memory-sync to record this session.
Create initial project snapshot.
Create delta upload for this change.
Sync project progress to Obsidian.
```

Skill 会先检查 `.project-memory/state.json`：

- 如果不存在，执行首次上传。
- 如果存在且已经完成首次上传，执行增量上传。

## 辅助脚本

在项目根目录执行：

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault <你的-vault-路径> --mode auto
```

如果当前项目本身就是 vault 工作区：

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault . --mode auto
```

强制首次上传：

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault <你的-vault-路径> --mode initial
```

强制增量上传：

```powershell
python path/to/project-memory-sync/scripts/project_memory_sync.py --repo . --vault <你的-vault-路径> --mode delta
```

## 生成文件

首次上传会创建：

```text
20-Projects/<project-id>/00-project-brief.md
20-Projects/<project-id>/01-architecture.md
20-Projects/<project-id>/02-file-map.md
20-Projects/<project-id>/03-runbook.md
20-Projects/<project-id>/status.md
90-Agent/Project-Uploads/<project-id>/initial-YYYYMMDD-HHMM.md
.project-memory/state.json
```

增量上传会创建或更新：

```text
90-Agent/Project-Uploads/<project-id>/delta-YYYYMMDD-HHMM.md
20-Projects/<project-id>/progress-log.md
20-Projects/<project-id>/status.md
60-Tasks/open-tasks.md
.project-memory/state.json
```

## 安全边界

Skill 和辅助脚本会避免复制这些受保护内容：

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

如果受保护文件和项目进度有关，只应该记录路径和排除原因，不写入文件内容。

## 上传到 GitHub

新建一个 GitHub 仓库，然后执行：

```powershell
cd path/to/project-memory-sync
git init
git add SKILL.md README.md .gitignore agents references scripts
git commit -m "feat: add project memory sync skill"
git branch -M main
git remote add origin https://github.com/<你的用户名>/project-memory-sync.git
git push -u origin main
```

## 许可证

MIT License。详见 [LICENSE](LICENSE)。
