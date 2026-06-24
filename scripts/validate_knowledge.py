#!/usr/bin/env python3
"""
Validate World Cup knowledge CSV files against project schema and conventions.

Usage:
  python scripts/validate_knowledge.py data/knowledge_glossary.csv
  python scripts/validate_knowledge.py --all
  python scripts/validate_knowledge.py data/batches/T020_glossary.csv --known-ids data/knowledge_glossary.csv

Network: none (local structured data). Outbound HTTP must use fetch_utils.RateLimitedFetcher (>=1s/request); see docs/data-collection-policy.md and .cursor/rules/world-cup-data-collection.mdc."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema (must match data/knowledge_template.csv)
# ---------------------------------------------------------------------------

EXPECTED_COLUMNS = [
    "id",
    "category_l1",
    "category_l2",
    "category_l3",
    "scope",
    "priority",
    "question",
    "question_aliases",
    "answer_short",
    "answer_detail",
    "answer_format",
    "keywords",
    "tags",
    "entities",
    "related_ids",
    "difficulty",
    "era_start",
    "era_end",
    "region",
    "language",
    "fact_type",
    "confidence",
    "source_type",
    "source_ref",
    "content_flags",
    "updated_at",
]

REQUIRED_FIELDS = {
    "id",
    "category_l1",
    "category_l2",
    "scope",
    "question",
    "answer_short",
    "keywords",
    "language",
    "fact_type",
    "confidence",
    "updated_at",
}

SCOPES = {"world_cup", "football_general", "both"}
ANSWER_FORMATS = {"fact", "definition", "procedure", "comparison", "list", "timeline", ""}
DIFFICULTIES = {"入门", "进阶", "专业", ""}
FACT_TYPES = {"rule", "history", "record", "stat", "bio", "tactic", "culture", "term"}
CONFIDENCE_LEVELS = {"official", "verified", "common_knowledge"}
SOURCE_TYPES = {"FIFA", "IFAB", "historical_record", "media_archive", ""}
CONTENT_FLAGS = {
    "time_sensitive",
    "rule_change_2026",
    "deprecated",
    "needs_review",
}
LANGUAGES = {"zh-CN"}

CATEGORY_L1_TO_ABBR: dict[str, str] = {
    "规则与裁判": "RULE",
    "世界杯赛制与组织": "TFMT",
    "世界杯历史概览": "WHIS",
    "历届世界杯": "WCED",
    "国家队与地域": "NTEM",
    "球员与教练": "PLCO",
    "俱乐部与联赛": "CLUB",
    "战术与位置": "TACT",
    "术语与百科": "GLOS",
    "纪录与统计": "RECD",
    "裁判与纪律": "DISC",
    "场地装备与科技": "VTEC",
    "女子世界杯": "WWC",
    "足球文化与观赛": "CULT",
    "健康与训练": "HLTH",
}

ABBR_TO_L1 = {v: k for k, v in CATEGORY_L1_TO_ABBR.items()}

GAMBLING_KEYWORDS = [
    "彩票",
    "竞彩",
    "足彩",
    "体彩",
    "福彩",
    "博彩",
    "赌博",
    "赌球",
    "投注",
    "下注",
    "赔率",
    "盘口",
    "让球",
    "大小球",
    "亚盘",
    "欧赔",
    "水位",
    "串关",
    "稳赚",
    "必中",
    "庄家",
]

ID_PATTERN = re.compile(r"^WC-[A-Z0-9]{3,8}-\d{5}$")
KNOWLEDGE_ID_PATTERN = re.compile(r"^WC-[A-Z0-9]{3,8}-\d{5}$")
ENTITY_REF_PATTERN = re.compile(r"^[a-z_]+:[^|]+(?:\|[a-z_]+:[^|]+)*$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_PATTERN = re.compile(r"^\d{4}$")

ANSWER_SHORT_MAX_LEN = 120
ANSWER_DETAIL_MAX_LEN = 500
MIN_KEYWORDS = 3

GAMBLING_SCAN_FIELDS = ("question", "answer_short", "answer_detail", "keywords")


@dataclass
class ValidationIssue:
    level: str  # ERROR | WARN
    row: int | None
    field: str | None
    message: str


@dataclass
class ValidationResult:
    path: Path
    row_count: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "ERROR"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "WARN"]


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def add_issue(
    result: ValidationResult,
    level: str,
    row: int | None,
    field: str | None,
    message: str,
) -> None:
    result.issues.append(ValidationIssue(level, row, field, message))


def read_csv_rows(path: Path) -> tuple[list[str] | None, list[dict[str, str]], list[str]]:
    parse_errors: list[str] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return None, [], parse_errors
        rows: list[dict[str, str]] = []
        for line_num, row in enumerate(reader, start=2):
            if None in row:
                parse_errors.append(
                    f"line {line_num}: too many columns (extra: {row[None]!r})"
                )
            cleaned: dict[str, str] = {}
            for key, value in row.items():
                if key is None:
                    continue
                if isinstance(value, str):
                    cleaned[key] = value.strip()
                elif value is None:
                    cleaned[key] = ""
                else:
                    parse_errors.append(
                        f"line {line_num}: invalid cell type for column '{key}'"
                    )
                    cleaned[key] = str(value).strip()
            rows.append(cleaned)
        return list(reader.fieldnames), rows, parse_errors


def validate_header(result: ValidationResult, fieldnames: list[str] | None) -> bool:
    if fieldnames is None:
        add_issue(result, "ERROR", None, None, "missing or unreadable CSV header")
        return False
    if fieldnames != EXPECTED_COLUMNS:
        add_issue(
            result,
            "ERROR",
            None,
            None,
            f"column mismatch: expected {len(EXPECTED_COLUMNS)} columns in schema order, "
            f"got {len(fieldnames)}",
        )
        if set(fieldnames) != set(EXPECTED_COLUMNS):
            missing = set(EXPECTED_COLUMNS) - set(fieldnames)
            extra = set(fieldnames) - set(EXPECTED_COLUMNS)
            if missing:
                add_issue(result, "ERROR", None, None, f"missing columns: {sorted(missing)}")
            if extra:
                add_issue(result, "ERROR", None, None, f"unexpected columns: {sorted(extra)}")
        return False
    return True


def count_keywords(keywords: str) -> int:
    return len([k for k in re.split(r"[,，]", keywords) if k.strip()])


def contains_gambling(text: str) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for word in GAMBLING_KEYWORDS:
        if word in text or word.lower() in lower:
            hits.append(word)
    return hits


def validate_id_format(result: ValidationResult, row_num: int, row_id: str) -> str | None:
    if not row_id:
        return None
    if not ID_PATTERN.match(row_id):
        add_issue(
            result,
            "ERROR",
            row_num,
            "id",
            f"invalid id format '{row_id}', expected WC-{{ABBR}}-{{5 digits}}",
        )
        return None
    parts = row_id.split("-")
    return parts[1]


def validate_row(
    result: ValidationResult,
    row_num: int,
    row: dict[str, str],
    known_ids: set[str],
    file_ids: set[str],
) -> None:
    for field_name in REQUIRED_FIELDS:
        if not row.get(field_name, "").strip():
            add_issue(
                result,
                "ERROR",
                row_num,
                field_name,
                f"required field '{field_name}' is empty",
            )

    row_id = row.get("id", "")
    if row_id:
        if row_id in file_ids:
            add_issue(result, "ERROR", row_num, "id", f"duplicate id in file: {row_id}")
        file_ids.add(row_id)
        if row_id in known_ids:
            add_issue(result, "ERROR", row_num, "id", f"duplicate id across files: {row_id}")
        known_ids.add(row_id)

    abbr = validate_id_format(result, row_num, row_id)
    cat_l1 = row.get("category_l1", "")
    if abbr and cat_l1:
        expected_abbr = CATEGORY_L1_TO_ABBR.get(cat_l1)
        if expected_abbr is None:
            add_issue(
                result,
                "ERROR",
                row_num,
                "category_l1",
                f"unknown category_l1 '{cat_l1}'",
            )
        elif abbr != expected_abbr:
            add_issue(
                result,
                "ERROR",
                row_num,
                "id",
                f"id prefix '{abbr}' does not match category_l1 '{cat_l1}' (expected {expected_abbr})",
            )

    scope = row.get("scope", "")
    if scope and scope not in SCOPES:
        add_issue(result, "ERROR", row_num, "scope", f"invalid scope '{scope}'")

    priority = row.get("priority", "")
    if priority:
        if not priority.isdigit() or not (1 <= int(priority) <= 5):
            add_issue(
                result,
                "ERROR",
                row_num,
                "priority",
                f"priority must be 1-5, got '{priority}'",
            )

    answer_short = row.get("answer_short", "")
    if answer_short and len(answer_short) > ANSWER_SHORT_MAX_LEN:
        add_issue(
            result,
            "ERROR",
            row_num,
            "answer_short",
            f"exceeds {ANSWER_SHORT_MAX_LEN} chars (got {len(answer_short)})",
        )

    answer_detail = row.get("answer_detail", "")
    if answer_detail and len(answer_detail) > ANSWER_DETAIL_MAX_LEN:
        add_issue(
            result,
            "WARN",
            row_num,
            "answer_detail",
            f"exceeds {ANSWER_DETAIL_MAX_LEN} chars (got {len(answer_detail)})",
        )

    answer_format = row.get("answer_format", "")
    if answer_format and answer_format not in ANSWER_FORMATS - {""}:
        add_issue(result, "ERROR", row_num, "answer_format", f"invalid answer_format '{answer_format}'")

    keywords = row.get("keywords", "")
    if keywords and count_keywords(keywords) < MIN_KEYWORDS:
        add_issue(
            result,
            "ERROR",
            row_num,
            "keywords",
            f"need at least {MIN_KEYWORDS} keywords, got {count_keywords(keywords)}",
        )

    difficulty = row.get("difficulty", "")
    if difficulty and difficulty not in DIFFICULTIES - {""}:
        add_issue(result, "ERROR", row_num, "difficulty", f"invalid difficulty '{difficulty}'")

    entities = row.get("entities", "")
    if entities and not ENTITY_REF_PATTERN.match(entities):
        add_issue(
            result,
            "ERROR",
            row_num,
            "entities",
            f"invalid entities format '{entities}', expected type:name|type:name",
        )

    related = row.get("related_ids", "")
    if related:
        for ref_id in related.split(","):
            ref_id = ref_id.strip()
            if not ref_id:
                add_issue(result, "ERROR", row_num, "related_ids", "empty id in related_ids list")
            elif " " in related:
                add_issue(
                    result,
                    "ERROR",
                    row_num,
                    "related_ids",
                    "related_ids must be comma-separated without spaces",
                )
            elif not KNOWLEDGE_ID_PATTERN.match(ref_id):
                add_issue(
                    result,
                    "ERROR",
                    row_num,
                    "related_ids",
                    f"invalid related id '{ref_id}'",
                )

    for year_field in ("era_start", "era_end"):
        year_val = row.get(year_field, "")
        if year_val and not YEAR_PATTERN.match(year_val):
            add_issue(result, "ERROR", row_num, year_field, f"invalid year '{year_val}'")

    era_start = row.get("era_start", "")
    era_end = row.get("era_end", "")
    if era_start and era_end and int(era_start) > int(era_end):
        add_issue(result, "ERROR", row_num, "era_end", "era_end must be >= era_start")

    language = row.get("language", "")
    if language and language not in LANGUAGES:
        add_issue(result, "ERROR", row_num, "language", f"invalid language '{language}'")

    fact_type = row.get("fact_type", "")
    if fact_type and fact_type not in FACT_TYPES:
        add_issue(result, "ERROR", row_num, "fact_type", f"invalid fact_type '{fact_type}'")

    confidence = row.get("confidence", "")
    if confidence and confidence not in CONFIDENCE_LEVELS:
        add_issue(result, "ERROR", row_num, "confidence", f"invalid confidence '{confidence}'")

    source_type = row.get("source_type", "")
    if source_type and source_type not in SOURCE_TYPES - {""}:
        add_issue(result, "ERROR", row_num, "source_type", f"invalid source_type '{source_type}'")

    flags = row.get("content_flags", "")
    if flags:
        for flag in flags.split(","):
            flag = flag.strip()
            if flag and flag not in CONTENT_FLAGS:
                add_issue(
                    result,
                    "WARN",
                    row_num,
                    "content_flags",
                    f"unknown content_flag '{flag}'",
                )

    updated_at = row.get("updated_at", "")
    if updated_at:
        if not ISO_DATE_PATTERN.match(updated_at):
            add_issue(
                result,
                "ERROR",
                row_num,
                "updated_at",
                f"invalid date '{updated_at}', expected YYYY-MM-DD",
            )
        else:
            try:
                datetime.strptime(updated_at, "%Y-%m-%d")
            except ValueError:
                add_issue(result, "ERROR", row_num, "updated_at", f"invalid calendar date '{updated_at}'")

    for scan_field in GAMBLING_SCAN_FIELDS:
        text = row.get(scan_field, "")
        if not text:
            continue
        hits = contains_gambling(text)
        if hits:
            add_issue(
                result,
                "ERROR",
                row_num,
                scan_field,
                f"gambling keyword detected: {', '.join(sorted(set(hits)))}",
            )


def validate_file(path: Path, known_ids: set[str] | None = None) -> ValidationResult:
    result = ValidationResult(path=path)
    if not path.exists():
        add_issue(result, "ERROR", None, None, f"file not found: {path}")
        return result

    fieldnames, rows, parse_errors = read_csv_rows(path)
    for msg in parse_errors:
        add_issue(result, "ERROR", None, None, msg)
    if not validate_header(result, fieldnames):
        return result

    ids_in_file: set[str] = set()
    global_ids = known_ids if known_ids is not None else set()

    for idx, row in enumerate(rows, start=2):
        if not any(v.strip() for v in row.values()):
            continue
        result.row_count += 1
        validate_row(result, idx, row, global_ids, ids_in_file)

    return result


def discover_knowledge_files(data_dir: Path) -> list[Path]:
    """Batch/incremental knowledge CSVs (excludes merged knowledge_all.csv)."""
    patterns = [
        data_dir / "knowledge_*.csv",
        data_dir / "batches" / "*.csv",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(pattern.parent.glob(pattern.name)))
    return [
        f
        for f in files
        if f.name not in {"knowledge_template.csv", "knowledge_all.csv"}
    ]


def resolve_all_validation_targets(data_dir: Path) -> list[Path]:
    """--all: validate merged library when present; else all batch files."""
    all_csv = data_dir / "knowledge_all.csv"
    if all_csv.exists():
        return [all_csv]
    return discover_knowledge_files(data_dir)


def print_result(result: ValidationResult, verbose: bool) -> None:
    rel = result.path
    try:
        rel = result.path.relative_to(project_root())
    except ValueError:
        pass

    status = "PASS" if not result.errors else "FAIL"
    print(f"[{status}] {rel} — {result.row_count} row(s), {len(result.errors)} error(s), {len(result.warnings)} warning(s)")

    if verbose or result.errors or result.warnings:
        for issue in result.issues:
            loc = ""
            if issue.row is not None:
                loc = f"line {issue.row}"
            if issue.field:
                loc = f"{loc} ({issue.field})".strip()
            prefix = issue.level
            detail = f"  {prefix}: {loc}: {issue.message}" if loc else f"  {prefix}: {issue.message}"
            print(detail)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate World Cup knowledge CSV files.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="CSV file(s) to validate (default: --all if none given)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate merged data/knowledge_all.csv if present; else all batch knowledge_*.csv (excludes template and knowledge_all duplicates)",
    )
    parser.add_argument(
        "--batches",
        action="store_true",
        help="Validate all batch knowledge_*.csv under data/ (excludes knowledge_all.csv and template)",
    )
    parser.add_argument(
        "--known-ids",
        type=Path,
        action="append",
        default=[],
        help="Additional CSV files whose ids are treated as already reserved (cross-file dup check)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show warnings and details for passing files",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = project_root()
    data_dir = root / "data"

    targets: list[Path] = []
    if args.batches:
        targets = discover_knowledge_files(data_dir)
    elif args.all or not args.paths:
        targets = resolve_all_validation_targets(data_dir)
        if not targets:
            template = data_dir / "knowledge_template.csv"
            if template.exists():
                targets = [template]
    else:
        targets = [p if p.is_absolute() else root / p for p in args.paths]

    known_ids: set[str] = set()
    for extra in args.known_ids:
        extra_path = extra if extra.is_absolute() else root / extra
        _, rows, _ = read_csv_rows(extra_path)
        for row in rows:
            rid = row.get("id", "").strip()
            if rid:
                known_ids.add(rid)

    if not targets:
        print("SKIP: no local knowledge CSV files to validate")
        return 0

    global_known = set(known_ids)
    results: list[ValidationResult] = []
    for path in targets:
        res = validate_file(path, known_ids=global_known)
        results.append(res)
        print_result(res, args.verbose)

    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_rows = sum(r.row_count for r in results)

    print()
    print(f"Validated {len(results)} file(s), {total_rows} row(s) total.")
    print(f"Errors: {total_errors}, Warnings: {total_warnings}")

    if total_errors:
        return 1
    if args.strict and total_warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
