"""Small read-only API clients. Credentials are loaded only from private files."""
import datetime,json,pathlib,time,urllib.request,urllib.parse,urllib.error
UTC=datetime.timezone.utc

def now(): return datetime.datetime.now(UTC).isoformat()
def request_json(url,timeout=45):
    req=urllib.request.Request(url,headers={'User-Agent':'SEOnaut-PrivateDashboard/1.0','Accept':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        # Never include the URL, error body or exception string: they may contain a key.
        return {'error':f'HTTP {e.code}','http_status':e.code}
    except Exception:
        return {'error':'Request failed or timed out'}

def private_key(config,field):
    f=config.get(field)
    if not f:return ''
    try:return pathlib.Path(f).read_text().strip()
    except OSError:return ''

class Sources:
    def __init__(self,root):
        self.root=pathlib.Path(root)
        try:self.config=json.loads((self.root/'sources.json').read_text())
        except FileNotFoundError:self.config={}
        try:self.cache=json.loads((self.root/'source-cache.json').read_text())
        except FileNotFoundError:self.cache={}
        self.last_call=0
        self.psi_limited=False
        self.bing_sites=None
    def paced(self,url):
        delay=3-(time.monotonic()-self.last_call)
        if delay>0:time.sleep(delay)
        result=request_json(url)
        self.last_call=time.monotonic()
        return result
    def cached(self,key,load):
        old=self.cache.get(key)
        if old:
            age=(datetime.datetime.now(UTC)-datetime.datetime.fromisoformat(old['attempted'])).total_seconds()
            if age<86400:return old['value']
        value=load()
        if value.get('error') and old and not old['value'].get('error'):
            value={**old['value'],'stale':True,'refresh_error':value['error']}
        self.cache[key]={'attempted':now(),'value':value}
        return value
    def pagespeed(self,url):
        result={}
        for strategy in ['mobile','desktop']:
            def load():
                if self.psi_limited:return {'error':'PageSpeed rate limited this refresh. Waiting for the next daily refresh or a free API key.','http_status':429}
                params=[('url',url),('strategy',strategy)]+[('category',c) for c in ['performance','accessibility','best-practices','seo']]
                key=private_key(self.config,'pagespeed_api_key_file')
                if key:params.append(('key',key))
                raw=self.paced('https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed?'+urllib.parse.urlencode(params))
                if raw.get('http_status')==429:self.psi_limited=True
                if raw.get('error'):return raw
                lhr=raw.get('lighthouseResult',{})
                if not lhr.get('categories'):return {'error':'PageSpeed returned no Lighthouse scores'}
                return {'fetched':now(),'scores':{k:round(v['score']*100) if v.get('score') is not None else None for k,v in lhr['categories'].items()},'field':raw.get('loadingExperience',{}),'lab':{k:{'value':v.get('numericValue'),'display':v.get('displayValue')} for k,v in lhr.get('audits',{}).items() if k in ['largest-contentful-paint','cumulative-layout-shift','total-blocking-time','first-contentful-paint']}}
            result[strategy]=self.cached('psi:'+url+':'+strategy,load)
        return result
    def bing(self,domain):
        key=private_key(self.config,'bing_api_key_file')
        if not key:return {'status':'Bing is not connected. Add the free Webmaster API key in private configuration.'}
        def api(method,params):
            return self.paced('https://ssl.bing.com/webmaster/api.svc/json/'+method+'?'+urllib.parse.urlencode({**params,'apikey':key}))
        if self.bing_sites is None:self.bing_sites=self.cached('bing:sites',lambda:api('GetSites',{}))
        if self.bing_sites.get('error'):return {'status':'Bing site discovery failed: '+self.bing_sites['error']}
        urls=[x.get('Url','') for x in self.bing_sites.get('d',[])]
        site=self.config.get('bing_sites',{}).get(domain) or next((u for u in urls if urllib.parse.urlparse(u).netloc.removeprefix('www.')==domain),None)
        if not site:return {'status':'This site is not present in the Bing API account. Import and verify it in Bing Webmaster Tools.'}
        out={'site':site,'fetched':now()}
        for name,method,params in [('queries','GetQueryStats',{}),('backlinks','GetLinkCounts',{'page':0}),('crawl','GetCrawlIssues',{})]:
            out[name]=self.cached('bing:'+site+':'+method,lambda method=method,params=params:api(method,{'siteUrl':site,**params}))
        return out
    def save(self):
        temp=self.root/'source-cache.tmp';temp.write_text(json.dumps(self.cache));temp.chmod(0o600);temp.replace(self.root/'source-cache.json')
