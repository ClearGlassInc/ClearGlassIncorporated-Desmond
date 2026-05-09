# shipprompt-starter

Opinionated MLOps + Prompt-Ops scaffold. Drop into any LLM-in-prod repo and
you have a signed prompt registry, a deploy CLI, a CI workflow with eval gates
and rollback, and a working audit checklist — all in under an hour.

This is the same scaffold installed during a paid **ShipPrompt 72-hour Sprint**.
You are welcome to use it for free under the MIT license. If you want it
embedded, hardened, evaluated, and tied to your CI in 72 hours, [book a
sprint](https://clearglassinc.github.io/shipprompt/).

## What you get

| File | Purpose |
|---|---|
| `cli/shipprompt.py` | Single-file Python CLI: `validate`, `diff`, `manifest`, `deploy`, `rollback`, `eval`. |
| `prompts/registry.example.yaml` | Canonical registry. Stable IDs, semver, immutable on publish. |
| `examples/deploy.yml` | GitHub Actions workflow with eval-gate, signed manifest, and rollback path. |

## Quickstart

```bash
# 1. Copy the scaffold into your repo (paths assume repo root)
cp -r shipprompt/starter/cli      ./shipprompt-cli
cp    shipprompt/starter/prompts/registry.example.yaml  prompts/registry.yaml
cp    shipprompt/starter/examples/deploy.yml            .github/workflows/shipprompt-deploy.yml

# 2. Author prompt body files referenced from registry.yaml
mkdir -p prompts/support
echo "Classify the following ticket..." > prompts/support/triage.classify.v1.2.0.txt

# 3. Validate locally
pip install pyyaml
python shipprompt-cli/shipprompt.py validate

# 4. Build a signed manifest
python shipprompt-cli/shipprompt.py manifest

# 5. Deploy to an environment
python shipprompt-cli/shipprompt.py deploy --env staging

# 6. If a deploy goes wrong
python shipprompt-cli/shipprompt.py rollback --env staging
```

## Mental model

```
prompts/registry.yaml          ← single source of truth (Git)
prompts/<id>/<version>.txt     ← prompt bodies (content-addressed)
deploy/manifests/<env>/        ← signed, versioned manifests
   ├── current.json            ← what is live
   └── previous.json           ← rollback target
```

Three rules:

1. **A `(prompt_id, version)` pair is immutable once it ships.** Bump the version
   to change the body. The CLI refuses to deploy if the registry and body
   disagree.
2. **The manifest is the only thing the runtime trusts.** Your inference workers
   read `current.json` for their environment. They do not read the registry
   directly, do not read Notion, do not read Slack.
3. **Rollback = restore previous manifest.** No magic, no migrations, no DB.

## Eval-gate

`shipprompt eval --suite regression` runs `evals/regression.yaml` and writes
`evals/regression.report.json`. The provided implementation is intentionally
minimal — wire it to your real harness (Promptfoo, LangSmith, custom). The
shape `(prompt_id, prompt_version, input) → assertions` does not change.

## Why this exists

LLM apps are in production *before* MLOps maturity caught up. SOC 2, ISO, and
the EU AI Act all require model + prompt lineage that most teams cannot
produce. Hiring a senior MLOps engineer is a 4-month, $220k/yr-loaded
commitment. A 72-hour sprint with this scaffold is a rounding error.

## License

MIT. Operated by [ClearGlass Inc.](https://clearglassinc.github.io/)
