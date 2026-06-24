# Data Directory

This public repository intentionally does not include knowledge data.

Add your own local CSV files here when using the Skill privately:

- `knowledge_all.csv`
- `knowledge_*.csv`
- `entities.csv`
- `refusal_policy.csv`

These files are ignored by Git in this public template. Validate local data before use:

```bash
python3 scripts/validate_knowledge.py --all --strict
python3 scripts/scan_gambling_all.py
python3 scripts/check_ids_all.py
```
