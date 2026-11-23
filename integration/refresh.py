#!/usr/bin/env python3
"""Refresh cached public sources once daily. Never requests paid APIs."""
import datetime,json,pathlib,urllib.request,urllib.parse,urllib.error,sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/Users/divjotai/Services/seonaut/private')
out={'updated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'start':'2026-10-24','end':'2026-11-20','sites':[]}
source=json.loads((root/'connected-metrics.json').read_text())
raw=source['results']
out['start']=source.get('start','2026-10-24')
out['end']=source.get('end','2026-11-20')
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 try:
  with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
 except Exception as e:return {'error':str(e)}
sites=[('Fraser Fix','fraserfixmechanical.com','plumber Surrey'),('Pick Card','pick-card.com','digital business card'),('Invites Cafe','invitescafe.com','digital wedding invitations'),('Enanto','enanto.com','web design Surrey'),('Mobillify','mobillify.com','invoice generator Canada')]
for i,(name,domain,keyword) in enumerate(sites):
 def data(n):return raw[n]['response'].get('data',{})
 s={'name':name,'domain':domain,'url':'https://www.'+domain,'keyword':keyword,'gsc':{'status':'Mobillify property is missing from the connected Search Console account. Add and verify sc-domain:mobillify.com.'} if i==4 else {'totals':data(i*3).get('rows',[]),'queries':data(i*3+1).get('rows',[]),'pages':data(i*3+2).get('rows',[])},'ga4':data(12+i),'bing':{'status':'Waiting for a free Bing Webmaster API key and verified site access.'},'pagespeed':{'status':'Waiting for a free PageSpeed API key. Keyless test returned quota exceeded.'}}
 # Suggestions fetched once per site per day. Cached on disk, never per page view.
 s['suggestions']=fetch('https://suggestqueries.google.com/complete/search?client=firefox&q='+urllib.parse.quote(keyword))
 out['sites'].append(s)
tmp=root/'overview.tmp';tmp.write_text(json.dumps(out));tmp.replace(root/'overview.json')
print('Updated five site snapshots')
