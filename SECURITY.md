# Security Guidelines

## Never Commit These Files

| File | Reason |
|------|--------|
| `.env` | Contains database password |
| `logs/*.log` | May contain SQL queries with data |
| `data/*.csv` | Raw data files (large + potential PII) |
| `.dbeaver/` | DBeaver stores connection passwords here |
| `.vscode/settings.json` | May contain DB connection profiles |
| `__pycache__/` | Compiled code with potential strings |

## If You Accidentally Committed Secrets

1. **Change password immediately:**
   ```sql
   ALTER USER your_user WITH PASSWORD 'new_secure_password';
   ```

2. **Remove from Git history:**
   ```bash
   git filter-branch --force --index-filter \
   "git rm --cached --ignore-unmatch .env" \
   --prune-empty --tag-name-filter cat -- --all
   ```

3. **Force push:**
   ```bash
   git push origin --force --all
   ```

## How This Project Handles Security

- All credentials read from `.env` via `python-dotenv`
- `.env.example` provides template without real values
- `.gitignore` excludes sensitive files
- No hardcoded passwords in source code
