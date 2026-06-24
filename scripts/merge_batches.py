#!/usr/bin/env python3
"""
Merge batch knowledge CSV files into main category files or knowledge_all.csv.

Usage:
  # Merge one batch into its target category file
  python scripts/merge_batches.py data/batches/T020_glossary.csv

  # Merge batch, specifying target explicitly
  python scripts/merge_batches.py data/batches/T020_glossary.csv -o data/knowledge_glossary.csv

  # Merge all pending batches under data/batches/
  python scripts/merge_batches.py --all-batches

  # Build full library from all knowledge_*.csv
  python scripts/merge_batches.py --build-all

  # Preview without writing
  python scripts/merge_batches.py data/batches/T020_glossary.csv --dry-run

Network: none (local structured data). Outbound HTTP must use fetch_utils.RateLimitedFetcher (>=1s/request); see docs/data-collection-policy.md and .cursor/rules/world-cup-data-collection.mdc."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_knowledge import EXPECTED_COLUMNS, discover_knowledge_files, project_root

SLUG_TO_TARGET: dict[str, str] = {
    "rules": "knowledge_rules.csv",
    "tournament_format": "knowledge_tournament_format.csv",
    "wc_history": "knowledge_wc_history.csv",
    "wc_editions": "knowledge_wc_editions.csv",
    "national_teams": "knowledge_national_teams.csv",
    "players_coaches": "knowledge_players_coaches.csv",
    "clubs_leagues": "knowledge_clubs_leagues.csv",
    "tactics": "knowledge_tactics.csv",
    "glossary": "knowledge_glossary.csv",
    "records_stats": "knowledge_records_stats.csv",
    "discipline": "knowledge_discipline.csv",
    "venues_tech": "knowledge_venues_tech.csv",
    "womens_wc": "knowledge_womens_wc.csv",
    "culture": "knowledge_culture.csv",
    "health_training": "knowledge_health_training.csv",
}

BATCH_SLUG_PATTERN = re.compile(
    r"(?:^|_)(rules|tournament_format|wc_history|wc_editions|national_teams|"
    r"players_coaches|clubs_leagues|tactics|glossary|records_stats|discipline|"
    r"venues_tech|womens_wc|culture|health_training)(?:\.csv|$)",
    re.IGNORECASE,
)


@dataclass
class MergeStats:
    target: Path
    existing: int = 0
    incoming: int = 0
    added: int = 0
    skipped: int = 0
    replaced: int = 0
    messages: list[str] = field(default_factory=list)


def read_data_rows(path: Path) -> tuple[list[str] | None, list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return None, []
        if list(reader.fieldnames) != EXPECTED_COLUMNS:
            raise ValueError(f"{path}: column header does not match schema")
        rows: list[dict[str, str]] = []
        for row in reader:
            cleaned = {col: (row.get(col) or "").strip() for col in EXPECTED_COLUMNS}
            if any(cleaned.values()):
                rows.append(cleaned)
        return list(reader.fieldnames), rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def infer_slug_from_batch(path: Path) -> str | None:
    name = path.stem.lower()
    match = BATCH_SLUG_PATTERN.search(name)
    if match:
        return match.group(1).lower()
    if name.startswith("knowledge_"):
        slug = name[len("knowledge_") :]
        if slug in SLUG_TO_TARGET:
            return slug
    return None


def target_for_batch(batch_path: Path, output: Path | None, data_dir: Path) -> Path:
    if output is not None:
        return output if output.is_absolute() else project_root() / output
    slug = infer_slug_from_batch(batch_path)
    if slug is None:
        raise ValueError(
            f"cannot infer target from batch filename '{batch_path.name}'; "
            "use -o/--output to specify"
        )
    filename = SLUG_TO_TARGET[slug]
    return data_dir / filename


def run_validate(paths: list[Path], known_ids: list[Path] | None = None) -> None:
    root = project_root()
    cmd = [sys.executable, str(root / "scripts" / "validate_knowledge.py")]
    for p in paths:
        cmd.append(str(p.relative_to(root) if p.is_relative_to(root) else p))
    for kid in known_ids or []:
        cmd.extend(["--known-ids", str(kid.relative_to(root) if kid.is_relative_to(root) else kid)])
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(result.returncode)


def merge_rows(
    target_path: Path,
    batch_path: Path,
    on_duplicate: str,
    dry_run: bool,
) -> MergeStats:
    stats = MergeStats(target=target_path)

    if target_path.exists():
        _, existing_rows = read_data_rows(target_path)
    else:
        existing_rows = []

    _, incoming_rows = read_data_rows(batch_path)
    stats.existing = len(existing_rows)
    stats.incoming = len(incoming_rows)

    index: dict[str, int] = {}
    merged: list[dict[str, str]] = []
    for row in existing_rows:
        rid = row.get("id", "")
        if rid:
            index[rid] = len(merged)
        merged.append(row)

    for row in incoming_rows:
        rid = row.get("id", "")
        if not rid:
            stats.skipped += 1
            stats.messages.append(f"skip row without id from {batch_path.name}")
            continue
        if rid in index:
            if on_duplicate == "skip":
                stats.skipped += 1
                stats.messages.append(f"skip duplicate id {rid}")
                continue
            if on_duplicate == "error":
                raise ValueError(f"duplicate id '{rid}' when merging {batch_path} -> {target_path}")
            # replace
            merged[index[rid]] = row
            stats.replaced += 1
            continue
        index[rid] = len(merged)
        merged.append(row)
        stats.added += 1

    if dry_run:
        stats.messages.append("dry-run: no files written")
        return stats

    write_rows(target_path, merged)
    return stats


def archive_batch(batch_path: Path, archive_dir: Path) -> Path:
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = archive_dir / f"{batch_path.stem}_{ts}{batch_path.suffix}"
    shutil.move(str(batch_path), str(dest))
    return dest


def print_stats(stats: MergeStats) -> None:
    rel = stats.target
    try:
        rel = stats.target.relative_to(project_root())
    except ValueError:
        pass
    print(
        f"  -> {rel}: existing={stats.existing}, incoming={stats.incoming}, "
        f"added={stats.added}, replaced={stats.replaced}, skipped={stats.skipped}"
    )
    for msg in stats.messages:
        print(f"     {msg}")


def discover_batch_files(batches_dir: Path) -> list[Path]:
    if not batches_dir.exists():
        return []
    files = sorted(batches_dir.glob("*.csv"))
    archive = batches_dir / "archive"
    return [f for f in files if f.parent == batches_dir]


def build_knowledge_all(data_dir: Path, dry_run: bool) -> MergeStats:
    target = data_dir / "knowledge_all.csv"
    stats = MergeStats(target=target)
    sources = [
        f
        for f in discover_knowledge_files(data_dir)
        if f.name != "knowledge_all.csv" and f.name != "knowledge_template.csv"
    ]
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for src in sources:
        if not src.exists():
            continue
        _, rows = read_data_rows(src)
        stats.existing += len(rows)
        for row in rows:
            rid = row.get("id", "")
            if not rid:
                stats.skipped += 1
                continue
            if rid in seen:
                stats.skipped += 1
                stats.messages.append(f"skip duplicate id {rid} from {src.name}")
                continue
            seen.add(rid)
            merged.append(row)
            stats.added += 1
    stats.incoming = stats.added
    if dry_run:
        stats.messages.append("dry-run: knowledge_all.csv not written")
        return stats
    write_rows(target, merged)
    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge batch CSV files into knowledge library.")
    parser.add_argument(
        "batches",
        nargs="*",
        type=Path,
        help="Batch CSV file(s) to merge",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Target knowledge CSV (default: infer from batch filename slug)",
    )
    parser.add_argument(
        "--all-batches",
        action="store_true",
        help="Merge every CSV in data/batches/ (excluding archive/)",
    )
    parser.add_argument(
        "--build-all",
        action="store_true",
        help="Combine all data/knowledge_*.csv into data/knowledge_all.csv",
    )
    parser.add_argument(
        "--on-duplicate",
        choices=("skip", "error", "replace"),
        default="error",
        help="How to handle duplicate ids (default: error)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show merge plan without writing files",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip pre-merge validation (not recommended)",
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Move merged batch files to data/batches/archive/",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = project_root()
    data_dir = root / "data"
    batches_dir = data_dir / "batches"
    archive_dir = batches_dir / "archive"

    if args.build_all:
        if not args.skip_validate:
            sources = [
                f
                for f in discover_knowledge_files(data_dir)
                if f.name not in {"knowledge_all.csv", "knowledge_template.csv"} and f.exists()
            ]
            if sources:
                print("Validating source files before building knowledge_all.csv ...")
                run_validate(sources)
        print("Building data/knowledge_all.csv ...")
        stats = build_knowledge_all(data_dir, args.dry_run)
        print_stats(stats)
        total = stats.added
        print(f"\nDone. knowledge_all.csv rows: {total}")
        return 0

    batch_paths: list[Path] = []
    if args.all_batches:
        batch_paths = discover_batch_files(batches_dir)
    else:
        batch_paths = [p if p.is_absolute() else root / p for p in args.batches]

    if not batch_paths:
        print("No batch files specified.", file=sys.stderr)
        return 1

    merged_batches: list[Path] = []
    for batch_path in batch_paths:
        if not batch_path.exists():
            print(f"Batch not found: {batch_path}", file=sys.stderr)
            return 1

        target_path = target_for_batch(batch_path, args.output, data_dir)
        known = [target_path] if target_path.exists() else []

        if not args.skip_validate:
            print(f"Validating {batch_path.relative_to(root) if batch_path.is_relative_to(root) else batch_path} ...")
            run_validate([batch_path], known_ids=known)

        print(f"Merging {batch_path.name} -> {target_path.name} ...")
        stats = merge_rows(target_path, batch_path, args.on_duplicate, args.dry_run)
        print_stats(stats)

        if not args.dry_run:
            merged_batches.append(batch_path)

    if args.archive and merged_batches and not args.dry_run:
        for batch_path in merged_batches:
            dest = archive_batch(batch_path, archive_dir)
            rel = dest.relative_to(root)
            print(f"Archived {batch_path.name} -> {rel}")

    print(f"\nMerged {len(batch_paths)} batch file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
