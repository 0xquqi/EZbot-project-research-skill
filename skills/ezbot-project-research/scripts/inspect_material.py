#!/usr/bin/env python3
"""Extract reviewable hints from user-supplied material. Offline, stdlib only."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

MAX_BYTES = 2_000_000
ADDRESS = re.compile(r'(?<![a-zA-Z0-9])0x[0-9a-fA-F]{40}(?![a-zA-Z0-9])')
URL = re.compile(r'https?://[^\s<>"\x27)]+')


def web_url(value):
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ('http', 'https') and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


class Page(HTMLParser):
    def __init__(self, origin):
        super().__init__(convert_charrefs=True)
        self.origin = origin
        self.links = []
        self.scripts = []
        self.text = []
        self.inline_scripts = []
        self.hidden = []
        self.anchor = None

    def link(self, raw, kind):
        absolute = urljoin(self.origin, raw)
        if not web_url(absolute):
            return None
        item = {'url': absolute, 'kind': kind,
                'same_origin': urlsplit(absolute).netloc == urlsplit(self.origin).netloc}
        self.links.append(item)
        return item

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.anchor = self.link(a['href'], 'anchor')
        elif tag == 'link' and a.get('href') and a.get('rel') == 'alternate':
            self.link(a['href'], 'alternate')
        elif tag == 'script' and a.get('src'):
            absolute = urljoin(self.origin, a['src'])
            if web_url(absolute):
                self.scripts.append(absolute)
        if tag in ('script', 'style', 'noscript'):
            self.hidden.append(tag)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.anchor = None
        if tag in self.hidden:
            self.hidden.remove(tag)

    def handle_data(self, data):
        if 'script' in self.hidden:
            self.inline_scripts.append(data)
        if not self.hidden:
            clean = ' '.join(data.split())
            if clean:
                self.text.append(clean)
                if self.anchor is not None:
                    self.anchor['label'] = (self.anchor.get('label', '') + ' ' + clean).strip()


def abi_type(item):
    if not isinstance(item, dict):
        raise ValueError('ABI parameter must be an object')
    t = item.get('type')
    if not isinstance(t, str):
        raise ValueError('ABI parameter missing type')
    if t.startswith('tuple'):
        components = item.get('components')
        if not isinstance(components, list):
            raise ValueError('ABI tuple missing components')
        return '(' + ','.join(abi_type(c) for c in components) + ')' + t[5:]
    # Canonical aliases only, never change explicit widths.
    match = re.fullmatch(r'(uint|int)(\[.*\])?', t)
    return match[1] + '256' + (match[2] or '') if match else t


def describe_abi(abi):
    if not isinstance(abi, list):
        raise ValueError('ABI must be a JSON list')
    functions = []
    for f in abi:
        if not isinstance(f, dict) or f.get('type') != 'function':
            continue
        name = f.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', name):
            raise ValueError('Invalid ABI function name')
        inputs = f.get('inputs', [])
        if not isinstance(inputs, list):
            raise ValueError('Invalid ABI inputs')
        functions.append({'signature': name + '(' + ','.join(abi_type(i) for i in inputs) + ')',
                          'mutability': f.get('stateMutability', 'unknown'),
                          'semantics_confirmed': False})
    return functions


def inspect(raw, origin='', kind='auto', abi=None):
    if len(raw) > MAX_BYTES:
        raise ValueError('Material exceeds 2 MB; select a smaller relevant file')
    if origin and not web_url(origin):
        raise ValueError('Origin must be an HTTP(S) URL without credentials')
    value = raw.decode('utf-8-sig', errors='replace')
    if kind == 'auto':
        kind = 'html' if re.search(r'<(?:!doctype\s+html|html|head|body)\b', value[:2000], re.I) else 'text'
    page = Page(origin)
    if kind == 'html':
        page.feed(value)
        visible = '\n'.join(page.text)
    else:
        visible = value
        for url in dict.fromkeys(URL.findall(value)):
            page.link(url.rstrip('.,;'), 'text_url')
        # Markdown links may be relative to the supplied source URL.
        for target in re.findall(r'\]\(([^\s)]+)\)', value):
            page.link(target, 'markdown')
    candidates = []
    for match in ADDRESS.finditer(value):
        candidates.append({'address': match[0], 'offset': match.start(),
                           'context': value[max(0, match.start()-65):match.end()+65],
                           'role': 'unconfirmed'})
    output = {'schema_version': 1, 'input_sha256': hashlib.sha256(raw).hexdigest(),
              'origin': origin, 'format': kind, 'visible_text': visible,
              'links': page.links, 'scripts': list(dict.fromkeys(page.scripts)),
              'address_candidates': candidates,
              'requires_rendering_check': kind == 'html' and (bool(page.scripts) or len(visible.strip()) < 100),
              'participation_status': 'not_assessed',
              'limitations': ['Hints only: no fetch, script execution, chain read, price or eligibility determination.']}
    if abi is not None:
        output['abi_functions'] = describe_abi(abi)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--url', default='', help='Source URL for resolving links; no request is sent')
    parser.add_argument('--format', choices=['auto', 'html', 'text'], default='auto')
    parser.add_argument('--abi', type=Path, help='Explicit JSON ABI file; never extracted by running scripts')
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > MAX_BYTES:
            raise ValueError('Material exceeds 2 MB')
        abi = None
        if args.abi:
            if args.abi.stat().st_size > MAX_BYTES:
                raise ValueError('ABI exceeds 2 MB')
            abi = json.loads(args.abi.read_text())
        result = inspect(args.input.read_bytes(), args.url, args.format, abi)
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Cannot inspect material: {exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
