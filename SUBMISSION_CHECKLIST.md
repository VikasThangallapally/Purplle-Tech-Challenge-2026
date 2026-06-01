SUBMISSION CHECKLIST
====================

Project structure
- pipeline/: detection/tracking/event modules
- analytics/: journey/funnel/store/POS analytics
- scripts/: runner scripts for validation and output generation
- dashboard/: Streamlit app (dashboard/app.py)
- outputs/: full pipeline outputs (NOT included in repo push)
- outputs_demo/: curated demo images for reviewers

Quick run commands
- Install: `pip install -e .`
- Run analytics: `python scripts/run_analytics.py`
- Run POS analytics: `python scripts/run_pos_analytics.py`
- Regenerate zone visuals: `python scripts/run_zone_events.py`
- Start dashboard: `streamlit run dashboard/app.py`

Streamlit Cloud install command
- Use this in Streamlit Cloud advanced settings:

```bash
pip install -r requirements-streamlit.txt
```

This keeps the Streamlit app lightweight and avoids installing the full API/ML stack that is not needed for the dashboard.

Deployment steps
1. Ensure `.env` is configured (use `.env.example` as template). Do NOT commit secrets.
2. Build container: `docker build -t retail-intel .`
3. Compose (local demo): `docker compose -f deployments/docker-compose.yml up --build`

Validation summary
- Confirmed: no raw videos, model weights, or venv folders are included in commits.
- Curated demo: `outputs_demo/` contains representative detection, tracking, zone, POS, and dashboard images for reviewer inspection.

Final git commands (example)
```bash
# set remote (replace with your repo)
git remote add origin https://github.com/VikasThangallapally/Purplle-Tech-Challenge-2026.git
git branch -M main
# stage curated/demo files and docs
git add outputs_demo/ README.md SUBMISSION_CHECKLIST.md .gitignore
git commit -m "chore(submission): add curated demo outputs and submission checklist"
# push (requires your credentials)
git push -u origin main
```

Notes
- If any model weight or video file is accidentally staged, run `git rm --cached <file>` and recommit before pushing.
- To remove large files from history, consider `git filter-repo` (careful — rewrite history).