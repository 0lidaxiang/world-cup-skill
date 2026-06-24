# Public Repository Agent Guide

This repository is the public, data-free Skill/tooling template. Keep it safe to publish.

## Must Not Add

- Full knowledge CSV files, entity tables, task exports, review reports, or generated seed banks
- Images, logos, event emblems, mascot artwork, audio, video, lyrics, subtitles, transcripts, match footage, or copied article text
- Betting, odds, lottery, handicap, wagering, or gambling material
- Secrets, API keys, cookies, credentials, personal data, or private notes

## Allowed

- Cursor Skill prompts and project rules
- Generic validation, merge, ID-check, gambling-scan, and rate-limited fetch scripts
- Schema, retrieval, and compliance documentation
- Empty placeholder directories and small synthetic examples with no third-party expressive content

## Network Policy

All outbound requests must be serial and separated by at least 1 second. Python network code must use `scripts/fetch_utils.py` and never set `min_interval_sec < 1.0`.

## Publication Check

Before committing, run:

```bash
find data -type f ! -name ".gitkeep" ! -name "README.md" -print
find . -type d -name "__pycache__" -print
rg -n "彩票|竞彩|足彩|体彩|福彩|博彩|赌博|赌球|投注|下注|赔率|盘口|让球|大小球|亚盘|欧赔|水位|串关|稳赚|必中|庄家" .
```

Only commit if the first two commands return nothing and the third only matches policy/guardrail documentation.
