"""Offline release checks; no application or wallet dependencies."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/ezbot-project-research'
EXPECTED = {
    '.gitignore', '.github/workflows/check.yml', 'README.md', 'LICENSE',
    'tools/check.py', 'release-manifest.json',
    'skills/ezbot-project-research/SKILL.md',
    'skills/ezbot-project-research/agents/openai.yaml',
    *{'skills/ezbot-project-research/references/' + name for name in (
        'web-research.md', 'contract-research.md', 'participation.md',
        'report-format.md', 'case-index.md', 'question-cards.json',
        'agcid-cases.json', 'ecosystem-cases.json')},
}


def check():
    files = {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob('*')
             if p.is_file() and '.git' not in p.relative_to(ROOT).parts
             and '__pycache__' not in p.parts}
    assert set(files) == EXPECTED, f'Unexpected/missing files: {set(files) ^ EXPECTED}'
    assert all(not p.is_symlink() for p in ROOT.rglob('*') if '.git' not in p.parts), 'Symlink found'
    manifest = json.loads(files['release-manifest.json'].read_text())
    actual = {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in files.items()
              if n != 'release-manifest.json'}
    assert actual == manifest['sha256'], 'Release file hashes changed; review before updating manifest'
    for name, path in files.items():
        text = path.read_text()
        if name != 'tools/check.py':
            for pattern in (r'/Users/', r'127\.0\.0\.1', r'/api/mint/', r'gh[pousr]_[A-Za-z0-9]{20,}',
                            r'github_pat_[A-Za-z0-9_]{20,}', r'-----BEGIN .*PRIVATE KEY-----'):
                assert not re.search(pattern, text), f'Private/runtime pattern in {name}'
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                linked = (path.parent / target.split('#')[0]).resolve()
                assert linked.is_relative_to(ROOT) and linked.exists(), f'Broken/outside link: {name}: {target}'
    refs = SKILL / 'references'
    base = json.loads((refs / 'agcid-cases.json').read_text())
    ecosystem = json.loads((refs / 'ecosystem-cases.json').read_text())
    cards = json.loads((refs / 'question-cards.json').read_text())['rules']
    assert len(base['cases']) == 5 and len(base['reports']) == 3
    assert any(c['id'] == 'ptah-relic' and c.get('learning_report') for c in base['cases'])
    assert len(ecosystem['cases']) == 10 and len(cards) == 14
    assert len({c['id'] for c in cards}) == len(cards)
    for card in cards:
        assert set(card) == {'id', 'name', 'keywords', 'questions'}, 'Historical parameters leaked into question cards'
        assert card['questions'] and all(isinstance(q, str) and q.strip() for q in card['questions'])
        assert not re.search(r'0x[0-9a-fA-F]{40}', json.dumps(card)), 'Address in question cards'
    entry = (SKILL / 'SKILL.md').read_text()
    assert entry.startswith('---\nname: ezbot-project-research\ndescription: ')
    assert '[TODO' not in entry
    print(f'PASS: {len(files)} release files; links, hashes, case inventory, question boundaries and pattern scan')


if __name__ == '__main__':
    check()
