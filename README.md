# World Cup Skill Template

Public, data-free Cursor Agent Skill template for answering World Cup and football knowledge questions from a local CSV knowledge base.

This repository contains only:

- Cursor Skill prompt and project rules
- CSV schema and retrieval guidance
- Local validation, merge, ID-check, gambling-keyword scan, and rate-limited fetch helper scripts
- Compliance notes and source-attribution guardrails

It intentionally does **not** include the private/full knowledge CSV files, entity table, task plan, generation seeds, review reports, scraped content, media assets, images, logos, audio, video, or official FIFA materials.

## What This Is

The Skill expects a user-maintained local `data/` directory with CSV files that match the schema in [`docs/csv-schema-design.md`](docs/csv-schema-design.md). At runtime, the Skill first checks gambling/betting refusal policy, then retrieves local CSV rows by question, aliases, keywords, and entities.

## What This Is Not

- Not an official FIFA, IFAB, federation, team, or broadcaster product
- Not endorsed by or affiliated with FIFA
- Not a source of betting, odds, wagering, lottery, or gambling advice
- Not a medical, legal, or commercial-rights advisory product
- Not a package of licensed World Cup data or official media

## Included Files

```text
.cursor/
  rules/                         # collection and script guardrails
  skills/world-cup/SKILL.md       # public Skill prompt
docs/
  csv-schema-design.md            # CSV schema
  data-collection-policy.md       # outbound request policy
  id-conventions.md               # ID and prohibited betting tokens
  skill-retrieval-guide.md        # retrieval flow
scripts/
  fetch_utils.py                  # >=1s rate-limited HTTP helper
  validate_knowledge.py           # CSV schema/content validator
  merge_batches.py                # local CSV merge helper
  scan_gambling_all.py            # prohibited-term scan
  check_ids_all.py                # ID/related_id consistency check
data/
  .gitkeep                        # placeholder only
```

## Quick Start

1. Clone this repository.
2. Add your own local CSV files under `data/` using the documented schema.
3. Open the folder in Cursor.
4. Ask football or World Cup questions in Agent mode.

Useful maintenance commands:

```bash
python3 scripts/validate_knowledge.py --all --strict
python3 scripts/scan_gambling_all.py
python3 scripts/check_ids_all.py
```

## Data And Compliance

Any data you add should be independently cleared for publication and use. Avoid copying protected articles, images, logos, mascots, songs, match footage, subtitles, transcripts, or proprietary databases. Facts and short factual statements are safer than expressive source text, but source terms still matter.

Outbound collection must respect robots.txt, source terms, copyright, and the project-wide minimum request interval of 1 second. Do not collect betting, odds, handicap, lottery, or wagering material.

See [`NOTICE`](NOTICE) and [`docs/data-collection-policy.md`](docs/data-collection-policy.md).

## License

Code and documentation in this repository are provided under the [Apache License 2.0](LICENSE), excluding third-party names, marks, and any data or content you may add locally.
