import json,pathlib,tempfile,unittest
from unittest.mock import patch
from sources import Sources

class SourcesTest(unittest.TestCase):
    def test_bing_without_key_makes_no_request(self):
        with tempfile.TemporaryDirectory() as root,patch('sources.request_json') as network:
            result=Sources(root).bing('example.com')
            self.assertIn('not connected',result['status']);network.assert_not_called()
    def test_pagespeed_scores_and_cache(self):
        with tempfile.TemporaryDirectory() as root,patch('sources.time.sleep'),patch('sources.request_json',return_value={'lighthouseResult':{'categories':{'performance':{'score':.87}},'audits':{}}}) as network:
            client=Sources(root);first=client.pagespeed('https://example.com');client.save()
            again=Sources(root).pagespeed('https://example.com')
            self.assertEqual(first,again);self.assertEqual(first['mobile']['scores']['performance'],87);self.assertEqual(network.call_count,2)
    def test_rate_limit_stops_following_network_calls(self):
        with tempfile.TemporaryDirectory() as root,patch('sources.request_json',return_value={'error':'HTTP 429','http_status':429}) as network:
            client=Sources(root);client.pagespeed('https://example.com');client.pagespeed('https://second.example')
            self.assertEqual(network.call_count,1)
    def test_bing_uses_verified_site_and_required_methods(self):
        with tempfile.TemporaryDirectory() as root:
            root=pathlib.Path(root);(root/'key').write_text('test-key');(root/'sources.json').write_text(json.dumps({'bing_api_key_file':str(root/'key')}))
            with patch.object(Sources,'paced',side_effect=[{'d':[{'Url':'https://www.example.com/'}]},{'d':[]},{'d':[]},{'d':[]}]) as network:
                result=Sources(root).bing('example.com')
                self.assertEqual(result['site'],'https://www.example.com/');self.assertIn('queries',result);self.assertIn('backlinks',result);self.assertIn('crawl',result);self.assertEqual(network.call_count,4)
if __name__=='__main__':unittest.main()
