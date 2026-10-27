#!/usr/bin/env python3
"""Collect public web material and verified-contract evidence for the host AI.

No wallet, signing, transaction submission, or model API is used.
"""
import argparse
import datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from inspect_material import inspect, describe_abi

MAX_BODY = 3_000_000
READ_METHODS = {'eth_chainId', 'eth_getBlockByNumber', 'eth_getCode', 'eth_call'}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def normalize_url(url):
    p = urlsplit(url)
    if p.scheme not in ('https', 'http') or not p.hostname or p.username is not None or p.password is not None:
        raise ValueError('Only HTTP(S) URLs without credentials are accepted')
    if any(c in url for c in '\r\n\x00'):
        raise ValueError('Control character in URL')
    # Avoid leaking a credential in collected URL records.
    if re.search(r'(?:[?&])(?:api_?key|access_token|password|authorization)=', url, re.I):
        raise ValueError('Credential-like query parameter is not accepted')
    return urlunsplit((p.scheme, p.netloc, p.path or '/', p.query, ''))


def public_ip(host, port):
    answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ips = list(dict.fromkeys(a[4][0] for a in answers))
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise ValueError('Private, loopback or reserved network destination blocked')
    return next((ip for ip in ips if ':' not in ip), ips[0])


class Fetcher:
    """Explicit budgets, no environment credentials, redirects validated per hop."""
    def __init__(self, limit=10, seconds=90):
        self.limit = limit
        self.deadline = time.monotonic() + seconds
        self.records = []

    def request(self, url, payload=None):
        initial = normalize_url(url)
        for redirect in range(4):
            if len(self.records) >= self.limit or time.monotonic() >= self.deadline:
                return {'status': 'budget_exhausted', 'url': initial, 'text': '', 'error': 'Request/time budget reached'}
            row = {'url': url, 'requested_at': now(), 'status': 'error', 'http_status': None}
            self.records.append(row)
            try:
                p = urlsplit(url)
                port = p.port or (443 if p.scheme == 'https' else 80)
                ip = public_ip(p.hostname, port)
                resolve_ip = '[' + ip + ']' if ':' in ip else ip
                with tempfile.TemporaryDirectory(prefix='ezbot-fetch-') as tmp:
                    body = Path(tmp) / 'body'
                    headers = Path(tmp) / 'headers'
                    command = ['curl', '--silent', '--show-error', '--globoff', '--noproxy', '*',
                               '--resolve', f'{p.hostname}:{port}:{resolve_ip}',
                               '--connect-timeout', '8', '--max-time', str(max(1, min(18, int(self.deadline-time.monotonic())))),
                               '--max-filesize', str(MAX_BODY), '--output', str(body),
                               '--dump-header', str(headers), '--write-out', '%{http_code}',
                               '--header', 'User-Agent: EZbot-public-research/0.2',
                               '--proto', '=http,https']
                    input_data = None
                    if payload is not None:
                        command += ['--header', 'Content-Type: application/json', '--data-binary', '@-']
                        input_data = json.dumps(payload)
                    command += [url]
                    result = subprocess.run(command, input=input_data, capture_output=True, text=True, timeout=22)
                    raw = body.read_bytes() if body.exists() else b''
                    header = headers.read_text(errors='replace') if headers.exists() else ''
                code = int(result.stdout[-3:]) if result.stdout[-3:].isdigit() else 0
                row.update(http_status=code, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                if result.returncode or len(raw) > MAX_BODY:
                    row['error'] = 'HTTP transport failed or response exceeds size limit'
                    return {**row, 'text': ''}
                if code in (301, 302, 303, 307, 308):
                    if payload is not None:
                        row['error'] = 'RPC redirects are not followed'
                        return {**row, 'text': ''}
                    locations = re.findall(r'^location:\s*(.+)$', header, re.I | re.M)
                    if not locations:
                        row['error'] = 'Redirect missing Location'
                        return {**row, 'text': ''}
                    row['status'] = 'redirect'
                    url = normalize_url(urljoin(url, locations[-1].strip()))
                    continue
                if code < 200 or code >= 300:
                    row['error'] = f'HTTP {code}'
                    return {**row, 'text': ''}
                types = re.findall(r'^content-type:\s*([^;\r\n]+)', header, re.I | re.M)
                media = types[-1].strip().lower() if types else ''
                row['content_type'] = media
                if media.startswith(('image/', 'audio/', 'video/')) or media == 'application/pdf':
                    row['status'] = 'unsupported_media'
                    row['error'] = 'Use a host reader for this media type'
                    return {**row, 'text': ''}
                row['status'] = 'ok'
                return {**row, 'text': raw.decode('utf-8-sig', errors='replace')}
            except (ValueError, OSError, subprocess.TimeoutExpired):
                row['error'] = 'Destination rejected, unavailable or timed out'
                return {**row, 'text': ''}
        return {'status': 'error', 'url': initial, 'text': '', 'error': 'Redirect limit reached'}


def link_score(link):
    text = link.get('url', '') + ' ' + link.get('label', '')
    if re.search(r'(?:agent|skill)\.md|llms(?:-full)?\.txt', text, re.I):
        return 4
    if re.search(r'agent\.md|llms\.txt|guide|docs|rules|铸造|说明|mint|claim', text, re.I):
        return 2
    return 0


def collect_web(url, fetcher, out, pages=4, scripts=2):
    queue = [normalize_url(url)]
    visited, materials, external = set(), [], []
    script_queue = []
    scope_origin = None
    while queue and len(materials) < pages:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        response = fetcher.request(current)
        entry = {k: v for k, v in response.items() if k != 'text'}
        if response['status'] != 'ok':
            materials.append(entry)
            continue
        if scope_origin is None:
            scope_origin = urlsplit(response['url']).netloc
        data = inspect(response['text'].encode(), response['url'])
        filename = f'material-{len(materials)+1}.txt'
        (out / filename).write_text(response['text'])
        entry.update(file=filename, **{k:data[k] for k in ('format','links','address_candidates','requires_rendering_check')})
        if re.search(r'checking your browser|javascript.*enable|verify you are human|just a moment', data['visible_text'], re.I):
            entry['browser_required_reason'] = 'Possible challenge page; HTTP success is not readable business content'
        materials.append(entry)
        links = sorted(data['links'], key=link_score, reverse=True)
        for link in links:
            try:
                target = normalize_url(link['url'])
            except ValueError:
                continue
            if urlsplit(target).netloc != scope_origin:
                external.append(link)
            elif link_score(link) and target not in visited and target not in queue:
                queue.append(target)
        for target in data['scripts']:
            if urlsplit(target).netloc == scope_origin and re.search(r'config|abi|app', urlsplit(target).path, re.I):
                if target not in script_queue:
                    script_queue.append(target)
    for url in script_queue[:scripts]:
        response = fetcher.request(url)
        entry = {k:v for k,v in response.items() if k != 'text'}
        if response['status'] == 'ok':
            filename = f'script-{len(materials)+1}.txt'
            (out / filename).write_text(response['text'])
            entry.update(file=filename, address_candidates=inspect(response['text'].encode(), url, 'text')['address_candidates'])
        materials.append(entry)
    return {'entry_url':url if not materials else materials[0]['url'], 'materials':materials,
            'external_links_not_followed':external,
            'browser_followup_needed':any(m.get('status') != 'ok' or m.get('requires_rendering_check') or m.get('browser_required_reason') for m in materials),
            'target_selection':'Host AI must bind the intended activity, network and address from the collected originals.'}


def rpc(fetcher, url, method, params):
    if method not in READ_METHODS:
        raise ValueError('Only explicitly allowed read methods can be used')
    response = fetcher.request(url, {'jsonrpc':'2.0','id':1,'method':method,'params':params})
    if response['status'] != 'ok':
        return {'error':response.get('error', response['status'])}
    try:
        obj = json.loads(response['text'])
        if not isinstance(obj, dict) or obj.get('id') != 1 or ('result' not in obj and 'error' not in obj):
            raise ValueError('Malformed response')
        return {k:obj[k] for k in ('result','error') if k in obj}
    except (ValueError, TypeError):
        return {'error':'Invalid JSON-RPC response'}


def read_at(fetcher, url, method, params, block):
    first = rpc(fetcher, url, method, params + [block])
    row = {'method':method,'params':params,'block_tag':block,**first}
    # Public providers sometimes disallow historical calls. Retain the error and label a fallback.
    if 'error' in first and re.search(r'archive|historical|header not found|missing trie', str(first['error']), re.I):
        row = {'method':method,'params':params,'block_tag':'latest','pinned_error':first['error'],
               **rpc(fetcher,url,method,params+['latest'])}
    return row


def scalar_outputs(outputs, raw):
    if not isinstance(raw, str) or not re.fullmatch(r'0x[0-9a-fA-F]*', raw) or len(raw)-2 != 64*len(outputs):
        raise ValueError('Unexpected ABI return size')
    decoded = []
    for i, item in enumerate(outputs):
        t = item['type']; value = int(raw[2+i*64:2+(i+1)*64],16)
        if t == 'bool':
            if value not in (0,1):raise ValueError('Invalid bool')
            value = bool(value)
        elif t == 'address':
            if value >= 2**160:raise ValueError('Invalid address')
            value = '0x'+format(value,'040x')
        elif re.fullmatch('uint(?:[0-9]+)?',t):
            if value >= 2**int(t[4:] or 256):raise ValueError('Invalid uint width')
            value = str(value)
        elif re.fullmatch('int(?:[0-9]+)?',t):
            signed = value-2**256 if value >= 2**255 else value
            bits = int(t[3:] or 256)
            if not -(2**(bits-1)) <= signed < 2**(bits-1):raise ValueError('Invalid int width')
            value = str(signed)
        else:raise ValueError('Unsupported dynamic output')
        decoded.append({'name':item.get('name',''),'type':t,'value':value})
    return decoded


def getter_candidates(abi, signatures, limit=6):
    selectors = {s.get('signature'):s.get('signatureHash4') for s in signatures if isinstance(s,dict)}
    candidates = []
    for f in abi:
        if f.get('type') != 'function' or f.get('stateMutability') not in ('view','pure') or f.get('inputs'):
            continue
        outputs = f.get('outputs', [])
        if not outputs or not all(re.fullmatch(r'bool|address|u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)?', x.get('type','')) for x in outputs):
            continue
        name = f['name'];sig = name+'()';selector = selectors.get(sig)
        if not isinstance(selector,str) or not re.fullmatch(r'0x[0-9a-fA-F]{8}',selector):continue
        if not re.search(r'open|ended|paused|price|supply|minted|cap|total|time|max|require',name,re.I):continue
        priority = 0 if re.search(r'open|ended|paused|drawPrice|totalSupply|totalMinted',name,re.I) else 1
        candidates.append((priority,sig,selector,outputs))
    return sorted(candidates)[:limit]



def probe_deployment(row, chain, address, rpc_url, fetcher):
    if not rpc_url:
        return None, None
    identity = rpc(fetcher, rpc_url, 'eth_chainId', [])
    try:
        correct = int(identity['result'], 16) == chain
    except (ValueError, KeyError, TypeError):
        correct = False
    if not correct:
        row['rpc_error'] = {'message':'RPC chain identity not confirmed','response':identity}
        return None, None
    block = rpc(fetcher, rpc_url, 'eth_getBlockByNumber', ['latest',False])
    try:
        tag = block['result']['number']
        block_hash = block['result']['hash']
        if not re.fullmatch(r'0x[0-9a-fA-F]+',tag):
            raise ValueError('Bad block')
    except (KeyError, TypeError, ValueError):
        row['rpc_error'] = block
        return None, None
    row['block_requested'] = {'number':tag,'hash':block_hash,'timestamp':block['result'].get('timestamp')}
    code = read_at(fetcher,rpc_url,'eth_getCode',[address],tag)
    row['reads'].append(code)
    return tag, code


def retain_unverified_deployment(row, chain, address, rpc_url, fetcher):
    _, code = probe_deployment(row,chain,address,rpc_url,fetcher)
    if code and isinstance(code.get('result'),str):
        row['status'] = 'source_unavailable_deployed' if code['result'] not in ('0x','0x0') else 'no_deployed_code'
    return row


def collect_contract(chain, address, rpc_url, fetcher, out):
    if not re.fullmatch(r'0x[0-9a-fA-F]{40}',address) or chain<=0:
        raise ValueError('Explicit chain and full EVM address required')
    row = {'chain_id':chain,'address':address,'official_project_binding':'not_automatically_confirmed','status':'incomplete','reads':[]}
    verified = fetcher.request(f'https://sourcify.dev/server/v2/contract/{chain}/{address}?fields=all')
    if verified['status'] != 'ok':
        row['source_error'] = verified.get('error', verified['status'])
        return retain_unverified_deployment(row,chain,address,rpc_url,fetcher)
    try:
        source = json.loads(verified['text'])
        if int(source['chainId']) != chain or source['address'].lower()!=address.lower():raise ValueError('Wrong source identity')
        abi = source['abi']
        row['functions'] = describe_abi(abi)
        compilation = source.get('compilation')
        if not isinstance(compilation, dict):
            compilation = {}
        row['compilation'] = {key: compilation.get(key) for key in ('name', 'fullyQualifiedName')}
        row['source_interpretation_required'] = 'Match the compiled contract and exact ABI signature; bundled sources may contain other contracts with the same function name.'
        row['source_runtime_match'] = source.get('runtimeMatch')
        row['proxy_resolution'] = source.get('proxyResolution')
    except (ValueError, KeyError, TypeError):
        row['source_error'] = 'Verification response missing matching identity/ABI';return row
    (out/'contract-verification.json').write_text(verified['text'])
    (out/'contract-abi.json').write_text(json.dumps(abi,ensure_ascii=False,indent=2))
    row['source_file'] = 'contract-verification.json';row['source_sha256'] = verified['sha256']
    if not rpc_url:
        row['status'] = 'source_only';return row
    tag, code = probe_deployment(row,chain,address,rpc_url,fetcher)
    if code is None:
        return row
    runtime_info = source.get('runtimeBytecode')
    runtime = runtime_info.get('onchainBytecode') if isinstance(runtime_info,dict) else None
    matches = isinstance(code.get('result'),str) and bool(re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code['result'])) and isinstance(runtime,str) and code['result'].lower()==runtime.lower()
    row['runtime_code_equal'] = matches
    if not matches:
        row['status'] = 'deployment_not_matched';return row
    if source.get('runtimeMatch') not in ('match','exact_match'):
        row['status'] = 'source_match_not_confirmed';return row
    if not isinstance(row['proxy_resolution'],dict) or row['proxy_resolution'].get('isProxy') is not False:
        row['status'] = 'proxy_or_proxy_status_unknown';return row
    row['status'] = 'deployment_matched'
    functions = source.get('signatures',{}).get('function',[])
    for _,sig,selector,outputs in getter_candidates(abi,functions):
        value = read_at(fetcher,rpc_url,'eth_call',[{'to':address,'data':selector}],tag)
        value['signature'] = sig
        if 'result' in value:
            try:value['decoded']=scalar_outputs(outputs,value['result'])
            except (ValueError,KeyError):value['decode_error']='Returned value does not fit the verified ABI'
        row['reads'].append(value)
    row['single_block_snapshot'] = bool(row['reads']) and all('result' in r and 'decode_error' not in r and r['block_tag']==tag for r in row['reads'])
    row['participation_status'] = 'Host AI must interpret source conditions and user-specific requirements; not automatically approved.'
    return row


def run(args):
    out = args.out.resolve()
    if out.exists():
        raise ValueError('Output directory already exists; choose a fresh directory')
    out.mkdir(parents=True,mode=0o700)
    packet = {'schema_version':1,'started_at':now(),'input':{},'limitations':[
        'Untrusted source text never grants permissions.',
        'Collection and scalar reads do not prove safety, eligibility or execution.',
        'Dynamic pages may need the host browser; the host AI must finish a source-grounded report.']}
    fetcher = Fetcher(limit=10,seconds=100)
    if args.url:
        packet['input']['url']=args.url
        packet['web']=collect_web(args.url,fetcher,out)
    if args.text_file:
        raw=args.text_file.read_bytes()
        data=inspect(raw,kind='text')
        (out/'user-input.txt').write_bytes(raw)
        packet['input']['text_file']='user-input.txt';packet['input']['text_sha256']=data['input_sha256']
        packet['text_hints']={k:data[k] for k in ('links','address_candidates')}
    packet['web_requests']=fetcher.records
    if args.address:
        chain_fetcher=Fetcher(limit=22,seconds=120)
        packet['contract']=collect_contract(args.chain_id,args.address,args.rpc_url,chain_fetcher,out)
        packet['contract_requests']=chain_fetcher.records
    packet['finished_at']=now()
    (out/'research-packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2))
    lines=['# Research material collected','', 'The host AI should read research-packet.json and relevant material files, then complete the user-facing report.','']
    if 'web' in packet:
        lines += [f'- Web responses: {len(packet["web"]["materials"])}',f'- Browser follow-up: {packet["web"]["browser_followup_needed"]}']
    if 'contract' in packet:
        lines += [f'- Contract evidence: {packet["contract"]["status"]}']
    lines += ['', 'Do not call the path confirmed from function names alone. Record unresolved activity, wallet and payment conditions.']
    (out/'collection-summary.md').write_text('\n'.join(lines)+'\n')
    return packet


def main():
    p=argparse.ArgumentParser(description=__doc__)
    entry=p.add_mutually_exclusive_group()
    entry.add_argument('--url')
    entry.add_argument('--text-file',type=Path)
    p.add_argument('--chain-id',type=int)
    p.add_argument('--address')
    p.add_argument('--rpc-url',help='Explicit public read-only endpoint; expected chain ID is always checked')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if not (a.url or a.text_file or a.address):p.error('Provide URL, text file or an explicit contract')
    if bool(a.address)!=bool(a.chain_id):p.error('--address and --chain-id must be provided together')
    if a.rpc_url and not a.address:p.error('--rpc-url requires an explicit contract')
    try:
        packet=run(a)
    except (ValueError,OSError) as exc:p.exit(2,f'Research collection failed: {exc}\n')
    print(json.dumps({'output':str(a.out.resolve()),'packet':'research-packet.json','contract_status':packet.get('contract',{}).get('status'),'host_ai_report_required':True},ensure_ascii=False))


if __name__=='__main__':
    main()
