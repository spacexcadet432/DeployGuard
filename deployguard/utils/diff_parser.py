from __future__ import annotations

from typing import Any

from deployguard.models.schemas import DiffSummary


def parse_commit_diff_simplified(commit_json: dict[str, Any]) -> DiffSummary:
    """
    Simplify GitLab commit JSON into:
      {
        "files_changed": [...],
        "total_lines_changed": int
      }
    """
    stats = commit_json.get("stats") or {}
    additions = int(stats.get("additions") or 0)
    deletions = int(stats.get("deletions") or 0)
    total_lines_changed = additions + deletions

    files: list[str] = []
    changes = commit_json.get("changes") or []
    for ch in changes:
        if not isinstance(ch, dict):
            continue
        # GitLab "changes" items commonly include "new_path"
        path = ch.get("new_path") or ch.get("file_path") or ch.get("old_path")
        if isinstance(path, str) and path.strip():
            files.append(path.strip())

    # Deduplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            deduped.append(f)

    return DiffSummary(files_changed=deduped, total_lines_changed=total_lines_changed)

