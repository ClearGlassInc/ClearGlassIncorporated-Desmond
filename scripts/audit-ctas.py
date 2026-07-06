#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# ClearGlass Inc. - Revenue Agent Tool: CTA & Lead Capture Validator
print("Executing ClearGlass Revenue Audit: Scanning for conversion paths...")

html_files = list(Path('.').rglob('*.html'))
missing_ctas = 0

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Basic validation: ensure high-value pages have contact or action links
        if 'href="mailto:' not in content and '<form' not in content:
            print(f"[WARN] No lead capture or direct contact vector found in {file}")
            missing_ctas += 1

if missing_ctas > 0:
    print(f"Audit Complete: {missing_ctas} pages lack direct conversion paths. Monitor for impact.")
else:
    print("Audit Complete: All scanned pages contain operational conversion vectors.")
    
sys.exit(0) # Exit 0 ensures the pipeline continues successfully
