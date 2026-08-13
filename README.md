# UAS Detection & Awareness Platform (UAS-DAP)

This package provides **detection, tracking, classification, alerting, reporting, and incident workflow** for Uncrewed Aerial Systems (UAS) events.

## Scope / Safety
This platform is built for **lawful monitoring and situational awareness**. It **does not** include any features that disable, jam, intercept, or otherwise harm aircraft/UAS.

## Quick Start (Windows / PowerShell)
1. Run the deployment script:
   - `deploy\Deploy-UAS-DAP.ps1`
2. Start the local API:
   - `python .\software\00_UAS_Detection_Awareness_Platform.py --db data\uas_dap.sqlite serve --port 8080 --token <YOUR_TOKEN>`

## Quick Start (Manual)
```bash
python 00_UAS_Detection_Awareness_Platform.py demo
python 00_UAS_Detection_Awareness_Platform.py init-db
python 00_UAS_Detection_Awareness_Platform.py report
python 00_UAS_Detection_Awareness_Platform.py export --out export/uas_export.json
python 00_UAS_Detection_Awareness_Platform.py serve --host 127.0.0.1 --port 8080 --token YOUR_TOKEN
```

## HTTP API
- `GET /health`
- `GET /detections`
- `POST /detections` (requires header `X-API-Token`)
- `GET /responses`
- `POST /responses` (requires header `X-API-Token`)

## Sale & Compliance Docs
See the `docs/` folder for:
- Sales Agreement
- Purchase Order
- NDA
- Warranty Agreement
- Service Level Agreement
- EULA
- Maintenance Contract
- Compliance Acknowledgment
- Technical Specification Sheet (detection/awareness scope)

All are **templates** and should be reviewed by qualified legal counsel for your jurisdiction and use case.
