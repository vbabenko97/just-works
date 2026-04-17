#!/usr/bin/env python3
"""Inventory a repository and surface structural smells for cleanup planning."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".idea",
    ".vscode",
    ".next",
    ".turbo",
    ".cache",
    "coverage",
}

KEY_REPO_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    ".gitignore",
]

KEY_DIRS = [
    "src",
    "tests",
    "docs",
    "scripts",
    "config",
    "configs",
    "notebooks",
    "examples",
    ".github",
]

LIKELY_ARTIFACT_DIR_NAMES = {
    "artifacts",
    "outputs",
    "output",
    "checkpoints",
    "models",
    "runs",
    "results",
    "tmp",
    "temp",
    "cache",
    "logs",
    "data",
}

LANGUAGE_HINTS = {
    ".py": "python",
    ".ipynb": "jupyter",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".scala": "scala",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c-family",
    ".hpp": "cpp",
    ".tf": "terraform",
    ".sh": "shell",
    ".sql": "sql",
    ".r": "r",
}

ML_MARKERS = {
    "notebooks",
    "configs",
    "checkpoints",
    "wandb",
    "mlruns",
    "data",
}

MONOREPO_MARKERS = {"apps", "packages", "services", "libs"}


@dataclass
class RepoInventory:
    root: str
    top_level_entries: list[str]
    top_level_file_count: int
    top_level_dir_count: int
    file_count: int
    dir_count: int
    largest_files: list[dict[str, object]]
    common_extensions: list[list[object]]
    language_hints: list[list[object]]
    present_key_files: list[str]
    missing_key_files: list[str]
    present_key_dirs: list[str]
    top_level_smells: list[str]
    likely_artifact_dirs: list[str]
    repo_archetype_guess: str
    notes: list[str]


def iter_paths(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        current = Path(current_root)
        for dirname in dirnames:
            yield current / dirname
        for filename in filenames:
            yield current / filename


def guess_repo_archetype(root: Path, ext_counter: Counter[str]) -> str:
    top_names = {p.name for p in root.iterdir()}
    if top_names & MONOREPO_MARKERS:
        return "monorepo"
    if top_names & ML_MARKERS or ext_counter[".ipynb"] > 0:
        return "ml-or-research"
    if any(name in top_names for name in {"infra", "terraform", "environments", "deploy"}) or ext_counter[".tf"] > 0:
        return "infra-or-platform"
    if any(name in top_names for name in {"src", "app", "server", "service"}):
        return "application-or-service"
    if any(name in top_names for name in {"lib", "package", "packages", "examples"}):
        return "library-or-sdk"
    return "mixed-or-transitional"


def analyze_repo(root: Path) -> RepoInventory:
    file_count = 0
    dir_count = 0
    ext_counter: Counter[str] = Counter()
    lang_counter: Counter[str] = Counter()
    largest_files: list[tuple[int, Path]] = []
    top_level_smells: list[str] = []
    notes: list[str] = []
    likely_artifact_dirs: list[str] = []

    for path in iter_paths(root):
        relative = path.relative_to(root)
        if path.is_dir():
            dir_count += 1
            if relative.parts and relative.parts[0] == path.name and path.name.lower() in LIKELY_ARTIFACT_DIR_NAMES:
                likely_artifact_dirs.append(path.name)
            continue

        file_count += 1
        ext = path.suffix.lower()
        if ext:
            ext_counter[ext] += 1
            if ext in LANGUAGE_HINTS:
                lang_counter[LANGUAGE_HINTS[ext]] += 1

        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        largest_files.append((size, path))

    largest_files.sort(reverse=True, key=lambda item: item[0])
    largest_files_payload = [
        {
            "path": str(path.relative_to(root)),
            "bytes": size,
        }
        for size, path in largest_files[:10]
    ]

    top_level_entries = sorted([p.name for p in root.iterdir() if p.name not in IGNORED_DIRS])
    top_level_files = [p.name for p in root.iterdir() if p.is_file()]
    top_level_dirs = [p.name for p in root.iterdir() if p.is_dir() and p.name not in IGNORED_DIRS]

    if len(top_level_entries) > 15:
        top_level_smells.append("crowded root directory")
    if len(top_level_files) > 8:
        top_level_smells.append("too many top-level files")
    if any(name.endswith((".png", ".jpg", ".jpeg", ".pdf", ".csv")) for name in top_level_files):
        top_level_smells.append("non-code assets or exports stored at the root")
    if any(name in {"notes.md", "todo.md", "scratch.md"} for name in map(str.lower, top_level_files)):
        top_level_smells.append("scratch or personal notes committed at the root")
    if any(name.lower() in {"data", "outputs", "artifacts", "checkpoints"} for name in top_level_dirs):
        top_level_smells.append("artifact or dataset directories mixed into the root")
    if "README.md" not in top_level_entries and "README.md" not in top_level_files:
        notes.append("missing README.md reduces discoverability")
    if ".github" not in top_level_dirs:
        notes.append("missing .github may indicate absent CI or templates")

    present_key_files = [name for name in KEY_REPO_FILES if (root / name).exists()]
    missing_key_files = [name for name in KEY_REPO_FILES if not (root / name).exists()]
    present_key_dirs = [name for name in KEY_DIRS if (root / name).exists()]

    return RepoInventory(
        root=str(root.resolve()),
        top_level_entries=top_level_entries,
        top_level_file_count=len(top_level_files),
        top_level_dir_count=len(top_level_dirs),
        file_count=file_count,
        dir_count=dir_count,
        largest_files=largest_files_payload,
        common_extensions=[[ext, count] for ext, count in ext_counter.most_common(15)],
        language_hints=[[lang, count] for lang, count in lang_counter.most_common()],
        present_key_files=present_key_files,
        missing_key_files=missing_key_files,
        present_key_dirs=present_key_dirs,
        top_level_smells=sorted(set(top_level_smells)),
        likely_artifact_dirs=sorted(set(likely_artifact_dirs)),
        repo_archetype_guess=guess_repo_archetype(root, ext_counter),
        notes=notes,
    )


def format_markdown(inventory: RepoInventory) -> str:
    lines = [
        f"# Repo inventory for `{inventory.root}`",
        "",
        f"- Archetype guess: **{inventory.repo_archetype_guess}**",
        f"- Files scanned: **{inventory.file_count}**",
        f"- Directories scanned: **{inventory.dir_count}**",
        f"- Top-level files: **{inventory.top_level_file_count}**",
        f"- Top-level directories: **{inventory.top_level_dir_count}**",
        "",
        "## Top-level entries",
        "",
    ]
    lines.extend([f"- `{entry}`" for entry in inventory.top_level_entries] or ["- none"])
    lines.extend(["", "## Structural smells", ""])
    lines.extend([f"- {smell}" for smell in inventory.top_level_smells] or ["- none detected"])
    lines.extend(["", "## Missing key files", ""])
    lines.extend([f"- `{name}`" for name in inventory.missing_key_files] or ["- none"])
    lines.extend(["", "## Present key directories", ""])
    lines.extend([f"- `{name}`" for name in inventory.present_key_dirs] or ["- none"])
    lines.extend(["", "## Language hints", ""])
    lines.extend([f"- {lang}: {count}" for lang, count in inventory.language_hints] or ["- none"])
    lines.extend(["", "## Largest files", ""])
    lines.extend([
        f"- `{item['path']}` ({item['bytes']} bytes)"
        for item in inventory.largest_files
    ] or ["- none"])
    lines.extend(["", "## Notes", ""])
    lines.extend([f"- {note}" for note in inventory.notes] or ["- none"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Path to the repository root")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"Path does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Path is not a directory: {root}")

    inventory = analyze_repo(root)
    if args.format == "json":
        print(json.dumps(asdict(inventory), indent=2))
    else:
        print(format_markdown(inventory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
