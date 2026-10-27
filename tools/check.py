"""Offline checks for the standalone package and its declared evidence boundary."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'skills/ezbot-project-research/'
EXPECTED = {
    'AGENTS.md', '.gitignore', '.github/workflows/check.yml', 'README.md', 'LICENSE',
    'tools/check.py', 'tests/test_inspect_material.py', 'tests/test_package.py', 'tests/test_research.py',
    'evaluation/README.md', 'evaluation/observations-2026-10-28.json',
    'evaluation/topic-coverage.json', 'evaluation/automatic-research-2026-10-28.json',
    'evaluation/automatic-research-2026-10-28.md', 'release-manifest.json',
    PREFIX + 'SKILL.md', PREFIX + 'agents/openai.yaml',
    PREFIX + 'scripts/inspect_material.py', PREFIX + 'scripts/research.py',
    *{PREFIX + 'references/' + n for n in (
        'web-research.md', 'contract-research.md', 'participation.md',
        'report-format.md', 'case-index.md', 'question-cards.json',
        'agcid-cases.json', 'ecosystem-cases.json', 'source-catalog.json',
        'inventory.json', 'validation.md', 'case-studies.md', 'automatic-research.md')},
}
ARCHIVES = {
    # Filled from the first release; checked without reading their research bodies.
    'agcid-cases.json': '6600af7885fae2d254d5b59744cef026b6774daa471ee30729ce8fae54f89cb5',
    'ecosystem-cases.json': '9b207d1d405dcbf137515ad70c11f0d717a2f1b0b694a8171b966b897e30cbc9',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_cards(cards, sources):
    require(isinstance(cards, list) and len(cards) == 14, 'Expected 14 review topics')
    require(len({c['id'] for c in cards}) == len(cards), 'Duplicate topic ID')
    for card in cards:
        require(card.get('basis') == 'new_public_source_review', 'Topic has no new public basis')
        require(card.get('execution_tested') is False, 'Do not upgrade material review to execution')
        for field in ('questions', 'supported_points', 'limits', 'source_ids'):
            value = card.get(field)
            require(isinstance(value, list) and value and all(isinstance(s, str) and s.strip() for s in value), f'{card["id"]}: missing {field}')
        for source in card['source_ids']:
            require(source in sources, f'Unknown source: {source}')
            require(sources[source]['status'] in ('fetched', 'read_via_web'), f'Unread source: {source}')
        require(not re.search(r'0x[0-9a-fA-F]{40}', json.dumps(card)), 'Historical target address in general questions')


def check(root=ROOT):
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*')
             if p.is_file() and '.git' not in p.relative_to(root).parts
             and '__pycache__' not in p.parts}
    require(set(files) == EXPECTED, f'Unexpected/missing files: {set(files) ^ EXPECTED}')
    require(all(not p.is_symlink() for p in root.rglob('*') if '.git' not in p.parts), 'Symlink found')
    actual = {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in files.items() if n != 'release-manifest.json'}
    require(actual == json.loads(files['release-manifest.json'].read_text())['sha256'], 'Release hashes changed; review before updating manifest')
    for name, path in files.items():
        text = path.read_text()
        if name != 'tools/check.py':
            for pattern in (r'/Users/', r'127\.0\.0\.1', r'/api/mint/', r'gh[pousr]_[A-Za-z0-9]{20,}',
                            r'github_pat_[A-Za-z0-9_]{20,}', r'-----BEGIN .*PRIVATE KEY-----'):
                if name == 'tests/test_research.py' and pattern == r'127\.0\.0\.1':
                    continue  # Explicit synthetic private-network rejection test.
                require(not re.search(pattern, text), f'Private/runtime pattern in {name}')
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                linked = (path.parent / target.split('#')[0]).resolve()
                require(linked.is_relative_to(root.resolve()) and linked.exists(), f'Broken/outside link: {name}: {target}')
                if name.startswith(PREFIX):
                    require(linked.is_relative_to((root / PREFIX).resolve()), 'Installed skill must not depend on repo files')
    refs = root / PREFIX / 'references'
    for name, digest in ARCHIVES.items():
        require(hashlib.sha256((refs / name).read_bytes()).hexdigest() == digest, 'Historical archive was changed')
    src = json.loads((refs / 'source-catalog.json').read_text())['sources']
    require(len({s['id'] for s in src}) == len(src), 'Duplicate source ID')
    sources = {s['id']: s for s in src}
    for s in src:
        require(s['url'].startswith('https://') and s['retrieved_at'], 'Source URL/time missing')
        require(s['status'] in ('fetched', 'read_via_web', 'unavailable'), 'Unknown source status')
        if s['status'] == 'fetched':
            require(bool(re.fullmatch('[a-f0-9]{64}', s.get('sha256') or '')), 'Captured source missing digest')
        else:
            require(s['status'] != 'read_via_web' or s['sha256'] is None, 'Do not invent capture digest')
    cards = json.loads((refs / 'question-cards.json').read_text())['rules']
    validate_cards(cards, sources)
    coverage = json.loads((root / 'evaluation/topic-coverage.json').read_text())['topics']
    require({c['id'] for c in cards} == {c['id'] for c in coverage}, 'Coverage and topic IDs differ')
    for c in coverage:
        require(c['source_ids'] == next(r['source_ids'] for r in cards if r['id'] == c['id']), 'Coverage sources differ')
        require(c['execution_tested'] is False and c['cross_project_performance'] == 'not_measured', 'Unsupported performance claim')
    inventory = json.loads((refs / 'inventory.json').read_text())
    require(len(inventory['activities']) == inventory['historical_activities'] == 16, 'Activity inventory mismatch')
    require(len({a['family'] for a in inventory['activities']}) == inventory['historical_project_families'] == 15, 'Project inventory mismatch')
    require(inventory['legacy_reviewed_records']['verification'] == 'not_reconciled', '40 legacy records still need an itemized source list')
    entry = (root / PREFIX / 'SKILL.md').read_text()
    require(entry.startswith('---\nname: ezbot-project-research\ndescription: '), 'Invalid entry metadata')
    require('[TODO' not in entry, 'Unfinished entry')
    print(f'PASS: {len(files)} files; hashes, links, evidence metadata, 14 topics, inventory, archive preservation')


if __name__ == '__main__':
    try:
        check()
    except (ValueError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
