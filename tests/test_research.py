import importlib.util
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/ezbot-project-research/scripts'
sys.path.insert(0, str(SCRIPTS))
import research as m

A='0x'+'1'*40
CODE='0x60016000'
ABI=[{'type':'function','name':'mint','inputs':[],'outputs':[],'stateMutability':'payable'},
     {'type':'function','name':'mintOpen','inputs':[],'outputs':[{'name':'','type':'bool'}],'stateMutability':'view'}]
SOURCE={'chainId':'56','address':A,'abi':ABI,'runtimeMatch':'match','runtimeBytecode':{'onchainBytecode':CODE},
        'proxyResolution':{'isProxy':False},'signatures':{'function':[{'signature':'mintOpen()','signatureHash4':'0x12345678'}]}}


class FakeFetcher:
    def __init__(self, source=None, chain='0x38', code=CODE, call='0x'+'0'*63+'1'):
        self.source = json.loads(json.dumps(SOURCE if source is None else source))
        self.chain=chain;self.code=code;self.call=call;self.calls=[]

    def request(self,url,payload=None):
        self.calls.append((url,payload))
        if payload is None:value=self.source
        else:
            method=payload['method']
            result={'eth_chainId':self.chain,'eth_getBlockByNumber':{'number':'0x10','hash':'0x'+'a'*64},'eth_getCode':self.code,'eth_call':self.call}[method]
            value={'id':1,'result':result}
        return {'status':'ok','text':json.dumps(value),'url':url,'sha256':'a'*64}


class ResearchTests(unittest.TestCase):
    def test_only_read_methods(self):
        f=FakeFetcher()
        with self.assertRaises(ValueError):m.rpc(f,'https://example.org','eth_sendRawTransaction',[])
        self.assertEqual(f.calls,[])

    def test_network_url_boundary(self):
        for url in ['file:///etc/passwd','https://user:pass@example.org','https://example.org/?api_key=secret','https://example.org/\nheader']:
            with self.assertRaises(ValueError):m.normalize_url(url)
        self.assertEqual(m.normalize_url('https://example.org/mint#claim'),'https://example.org/mint')

    def test_private_and_mixed_dns_blocked(self):
        for ips in [('127.0.0.1',),('10.0.0.1',),('93.184.216.34','127.0.0.1')]:
            answers=[(socket.AF_INET,socket.SOCK_STREAM,0,'',(ip,443)) for ip in ips]
            with patch.object(m.socket,'getaddrinfo',return_value=answers):
                with self.assertRaises(ValueError):m.public_ip('example.org',443)

    def test_zero_budget_never_runs_transport(self):
        f=m.Fetcher(limit=0)
        with patch.object(m.subprocess,'run') as transport:
            self.assertEqual(f.request('https://example.org')['status'],'budget_exhausted')
            transport.assert_not_called()

    def test_rpc_wrong_chain_stops_before_code_or_calls(self):
        f=FakeFetcher(chain='0x1')
        with tempfile.TemporaryDirectory() as tmp:
            r=m.collect_contract(56,A,'https://example.org',f,Path(tmp))
        self.assertIn('rpc_error',r)
        self.assertEqual([p['method'] for _,p in f.calls if p],['eth_chainId'])

    def test_wrong_source_identity_stops_rpc(self):
        s=json.loads(json.dumps(SOURCE));s['address']='0x'+'2'*40;f=FakeFetcher(source=s)
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_contract(56,A,'https://example.org',f,Path(tmp))
        self.assertIn('source_error',r)
        self.assertFalse(any(p for _,p in f.calls))

    def test_code_mismatch_stops_getter_reads(self):
        f=FakeFetcher(code='0x6002')
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_contract(56,A,'https://example.org',f,Path(tmp))
        self.assertEqual(r['status'],'deployment_not_matched')
        self.assertFalse(any(p and p['method']=='eth_call' for _,p in f.calls))

    def test_matched_contract_reads_only_verified_scalar_view(self):
        f=FakeFetcher()
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_contract(56,A,'https://example.org',f,Path(tmp))
        self.assertEqual(r['status'],'deployment_matched')
        reads=[p for _,p in f.calls if p and p['method']=='eth_call']
        self.assertEqual(len(reads),1)
        self.assertEqual(reads[0]['params'][0]['data'],'0x12345678')
        self.assertEqual(r['reads'][-1]['decoded'][0]['value'],True)
        self.assertTrue(r['single_block_snapshot'])

    def test_proxy_not_read_as_simple_contract(self):
        s=json.loads(json.dumps(SOURCE));s['proxyResolution']={'isProxy':True};f=FakeFetcher(source=s)
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_contract(56,A,'https://example.org',f,Path(tmp))
        self.assertEqual(r['status'],'proxy_or_proxy_status_unknown')
        self.assertFalse(any(p and p['method']=='eth_call' for _,p in f.calls))

    def test_source_only_mode_does_not_imply_deployment_match(self):
        f=FakeFetcher()
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_contract(56,A,None,f,Path(tmp))
        self.assertEqual(r['status'],'source_only')
        self.assertNotIn('runtime_code_equal',r)

    def test_compiled_contract_identity_retained_with_exact_target_abi(self):
        source=json.loads(json.dumps(SOURCE))
        source['compilation']={'name':'TargetNFT','fullyQualifiedName':'Bundle.sol:TargetNFT'}
        source['sources']={'Bundle.sol':{'content':'contract Token { function mint(address to, uint amount) external {} } contract TargetNFT { function mint() external payable {} }'}}
        with tempfile.TemporaryDirectory() as tmp:
            r=m.collect_contract(56,A,None,FakeFetcher(source=source),Path(tmp))
        self.assertEqual(r['compilation']['name'],'TargetNFT')
        signatures=[f['signature'] for f in r['functions']]
        self.assertIn('mint()',signatures)
        self.assertNotIn('mint(address,uint256)',signatures)

    def test_archive_error_preserved_when_falling_back(self):
        class Archive:
            def request(self,url,payload):
                value={'id':1,'error':{'code':-32602,'message':'Archive requests require token'}} if payload['params'][-1]!='latest' else {'id':1,'result':'0x01'}
                return {'status':'ok','text':json.dumps(value)}
        r=m.read_at(Archive(),'https://example.org','eth_getCode',[A],'0x10')
        self.assertEqual(r['block_tag'],'latest');self.assertIn('pinned_error',r)

    def test_revert_is_not_retried_as_latest(self):
        class Revert:
            def __init__(self):self.n=0
            def request(self,url,payload):
                self.n+=1;return {'status':'ok','text':json.dumps({'id':1,'error':{'message':'execution reverted'}})}
        f=Revert();r=m.read_at(f,'https://example.org','eth_call',[{}],'0x10')
        self.assertEqual(f.n,1);self.assertEqual(r['block_tag'],'0x10')

    def test_missing_source_still_checks_deployment(self):
        class Missing(FakeFetcher):
            def request(self,url,payload=None):
                if payload is None:
                    return {'status':'error','error':'HTTP 404'}
                return super().request(url,payload)
        f=Missing()
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_contract(56,A,'https://example.org',f,Path(tmp))
        self.assertEqual(r['status'],'source_unavailable_deployed')
        self.assertEqual(r['source_error'],'HTTP 404')
        self.assertFalse(any(p and p['method']=='eth_call' for _,p in f.calls))

    def test_binary_document_not_presented_as_readable_text(self):
        def transport(command,**kwargs):
            Path(command[command.index('--dump-header')+1]).write_text('HTTP/1.1 200 OK\nContent-Type: application/pdf\n')
            Path(command[command.index('--output')+1]).write_bytes(b'%PDF-binary')
            from types import SimpleNamespace
            return SimpleNamespace(stdout='200',returncode=0)
        with patch.object(m,'public_ip',return_value='93.184.216.34'), patch.object(m.subprocess,'run',side_effect=transport):
            r=m.Fetcher().request('https://example.org/guide.pdf')
            self.assertEqual(r['status'],'unsupported_media')
            self.assertEqual(r['text'],'')

    def test_private_redirect_never_downloaded(self):
        def transport(command,**kwargs):
            Path(command[command.index('--dump-header')+1]).write_text('HTTP/1.1 302 Found\nLocation: http://localhost/secret\n')
            Path(command[command.index('--output')+1]).write_bytes(b'')
            from types import SimpleNamespace
            return SimpleNamespace(stdout='302',returncode=0)
        with patch.object(m,'public_ip',side_effect=['93.184.216.34',ValueError('blocked')]), patch.object(m.subprocess,'run',side_effect=transport) as process:
            r=m.Fetcher().request('https://example.org/')
            self.assertEqual(r['status'],'error')
            self.assertEqual(process.call_count,1)
            self.assertIn('--globoff',process.call_args.args[0])

    def test_scalar_size_bool_and_signed(self):
        self.assertEqual(m.scalar_outputs([{'type':'int8'}],'0x'+'f'*64)[0]['value'],'-1')
        self.assertEqual(m.scalar_outputs([{'type':'uint256'}],'0x'+format(10**24,'064x'))[0]['value'],str(10**24))
        for outputs,raw in [([{'type':'bool'}],'0x'+format(2,'064x')),([{'type':'uint8'}],'0x'+format(256,'064x')),([{'type':'string'}],'0x'+'0'*64),([{'type':'uint256'}],'0x')]:
            with self.assertRaises(ValueError):m.scalar_outputs(outputs,raw)

    def test_automatic_web_follows_guide_and_keeps_external_unfetched(self):
        class Web:
            def __init__(self):self.seen=[]
            def request(self,url):
                self.seen.append(url)
                body='<html><a href="agent.md">Guide</a><a href="https://other.org/claim">Claim</a><script src="config.js"></script></html>' if url.endswith('/') else 'Read source only'
                return {'status':'ok','url':url,'text':body}
        f=Web()
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_web('https://example.org/',f,Path(tmp))
        self.assertEqual(f.seen,['https://example.org/','https://example.org/agent.md','https://example.org/config.js'])
        self.assertTrue(r['external_links_not_followed'])

    def test_challenge_is_browser_followup_not_closed(self):
        class Web:
            def request(self,url):return {'status':'ok','url':url,'text':'<html>Checking your browser; enable JavaScript</html>'}
        with tempfile.TemporaryDirectory() as tmp:r=m.collect_web('https://example.org/',Web(),Path(tmp))
        self.assertTrue(r['browser_followup_needed'])
        self.assertNotIn('closed',r)

    def test_machine_readable_guide_precedes_translated_rules_with_page_budget(self):
        class Web:
            def __init__(self):self.seen=[]
            def request(self,url):
                self.seen.append(url)
                body='<html><a href="rules/">Rules</a><a href="zh/rules/">Rules</a><a href="zh-tw/rules/">Rules</a><a href="skill.md">Read the Skill</a></html>' if url.endswith('example.org/') else 'Original project rules'
                return {'status':'ok','url':url,'text':body}
        f=Web()
        with tempfile.TemporaryDirectory() as tmp:m.collect_web('https://example.org/',f,Path(tmp),pages=2)
        self.assertEqual(f.seen,['https://example.org/','https://example.org/skill.md'])


if __name__=='__main__':unittest.main()
