#!/usr/bin/env python3
import sys
from pathlib import Path

# ClearGlass Inc. - Marketing Agent Tool: SEO & Metadata Validator
print("Executing ClearGlass SEO Audit: Validating semantic architecture...")

html_files = list(Path('.').rglob('*.html'))
critical_failures = 0

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read().lower()
        if '<title>' not in content or '</title>' not in content:
            print(f"[FAIL] Missing <title> tag in {file}")
            critical_failures += 1
        if '<meta name="description"' not in content:
            print(f"[WARN] Missing meta description in {file}")

if critical_failures > 0:
    print(f"Audit Failed: {critical_failures} critical SEO violations detected.")
    sys.exit(1) # Halt the pipeline if structural SEO is missing
else:
    print("Audit Complete: Semantic architecture and metadata verified.")
    sys.exit(0)
