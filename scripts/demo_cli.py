from __future__ import annotations
import argparse
import json
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parents[1]
SCENARIOS = {
    'roster': 'roster_missing_credits.json',
    'merchant': 'merchant_decline.json',
    'cutoff': 'order_cutoff_change.json',
    'invoice': 'invoice_needs_clarification.json',
    'dietary': 'dietary_preference_timing.json',
    'refund': 'refund_balance_novel.json',
}

parser = argparse.ArgumentParser(description='Run ClientOps Desk demo requests against the local API.')
parser.add_argument('--scenario', choices=SCENARIOS, default='roster')
parser.add_argument('--url', default='http://localhost:8000/analyze')
args = parser.parse_args()

payload = json.loads((BASE / 'data' / 'sample_requests' / SCENARIOS[args.scenario]).read_text(encoding='utf-8'))
response = requests.post(args.url, json=payload, timeout=30)
response.raise_for_status()
print(json.dumps(response.json(), indent=2))
