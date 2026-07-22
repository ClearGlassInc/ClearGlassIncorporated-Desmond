# Deployment

The current implementation is additive and safe to run locally.

Commands:

```bash
python -m pytest artemis/tests/test_growth_engine.py -q
python -m pytest artemis/tests -q
python -m http.server 8080 --directory apps/command-center
```

Production activation requires operator-owned CRM/ad/email accounts, reviewed privacy notices, approval workflow storage, environment secrets, and a deployment owner. Keep `CLEARGLASS_GROWTH_ENGINE_DISABLED=true` until controls are verified.
