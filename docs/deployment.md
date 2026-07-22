# Deployment

## Local commands

```bash
python -m pytest tests/test_clearglass_growth_engine.py -q
python -m http.server 8080
```

Open `http://localhost:8080/apps/command-center/index.html` for the static command centre.

## Environment

Copy `.env.example` and set runtime secrets in the deployment environment only. Default mode is dry run.
