#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / 'README.md').read_text(encoding='utf-8')
required_assets = [
    'assets/header-satar-v2.svg',
    'assets/control-deck-v2.svg',
    'assets/energy-divider-v2.svg',
    'assets/footer-satar-v2.svg',
    'assets/generated/metrics.svg',
    'assets/generated/isocalendar.svg',
    'assets/generated/skyline.gif',
    'assets/generated/pacman-contribution-graph.svg',
    'assets/generated/pacman-contribution-graph-dark.svg',
]
missing = []
for rel in required_assets:
    if rel not in README and 'generated/' not in rel:
        missing.append(f'README does not reference {rel}')
    if not (ROOT / rel).exists():
        missing.append(f'Missing file: {rel}')
svg_paths = list((ROOT / 'assets').rglob('*.svg'))
for svg in svg_paths:
    try:
        ET.fromstring(svg.read_text(encoding='utf-8'))
    except Exception as exc:
        missing.append(f'Invalid SVG XML: {svg.relative_to(ROOT)} -> {exc}')
if '<script' in README.lower():
    missing.append('README should not include script tags for GitHub compatibility.')
if not re.search(r'Full Futuristic Gaming', README, flags=re.I):
    missing.append('README theme marker not found.')
if missing:
    print('PROFILE VALIDATION FAILED:')
    for item in missing:
        print('-', item)
    sys.exit(1)
print(f'Validated {len(svg_paths)} SVG assets and README references successfully.')
