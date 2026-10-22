import json,re,collections as C
d=json.load(open('data/afdc_dcfast_raw.json'));S=d['fuel_stations']
print('total_results',d['total_results'],'records',len(S))
print('countries',C.Counter(s.get('country') for s in S))
S=[s for s in S if s.get('country') in (None,'US')]
f=lambda s:(s.get('ev_pricing') or '').strip()
print('stations',len(S),'dc ports',sum(s.get('ev_dc_fast_num') or 0 for s in S))
print('status',C.Counter(s['status_code'] for s in S))
print('dc ports by status',{k:sum(s.get('ev_dc_fast_num') or 0 for s in S if s['status_code']==k) for k in 'ETP'})
E=[s for s in S if s['status_code']=='E']
for lab,g in (('all',S),('E only',E)):print('fill',lab,f"{sum(1 for s in g if f(s))}/{len(g)} = {100*sum(1 for s in g if f(s))/len(g):.1f}%")
num=re.compile(r'\$\s*\.?\d|\d+(\.\d+)?\s*(¢|cents?)|\d\.\d+\s*(/|per)\s*(kwh|min)',re.I)
print('\nnetwork top15: stations, fill%, numeric% of all')
for n,c in C.Counter(s.get('ev_network') for s in S).most_common(15):
  g=[s for s in S if s.get('ev_network')==n];fl=sum(1 for s in g if f(s));nm=sum(1 for s in g if num.search(f(s)))
  print(f"{n:30} {c:6} {100*fl/c:5.1f}% {100*nm/c:5.1f}%")
P=[f(s) for s in S if f(s)];N=[p for p in P if num.search(p)]
print(f'\nfilled {len(P)} numeric {len(N)} ({100*len(N)/len(P):.1f}%) vague {len(P)-len(N)}')
print('top vague',C.Counter(p for p in P if not num.search(p)).most_common(8))
import random;random.seed(1)
print('samples:');[print(' -',repr(p[:140])) for p in random.sample(sorted(set(N)),9)+random.sample(sorted(set(P)-set(N)),6)]
print('\nstates')
for st,c in C.Counter(s['state'] for s in S).most_common(10):
  g=[s for s in S if s['state']==st];print(st,c,f"{100*sum(1 for s in g if f(s))/c:.1f}% fill {100*sum(1 for s in g if num.search(f(s)))/c:.1f}% numeric")
print('\nfreshness (E stations)')
for k in ('date_last_confirmed','updated_at','open_date','expected_date'):
  v=sorted((s.get(k) or '')[:10] for s in E if s.get(k));print(k,'present',len(v),'/',len(E),'min',v[:1],'median',v[len(v)//2:len(v)//2+1],'max',v[-1:])
v=[(s.get('date_last_confirmed') or '')[:7] for s in E];print('confirmed by month top',C.Counter(v).most_common(8))
from datetime import date
def age(s):
  x=s.get('date_last_confirmed');return None if not x else (date(2026,10,22)-date.fromisoformat(x[:10])).days
a=[age(s) for s in E];print('confirmed <=30d',sum(1 for x in a if x is not None and x<=30),'<=90d',sum(1 for x in a if x is not None and x<=90),'>365d',sum(1 for x in a if x is not None and x>365),'missing',a.count(None))
print('T stations with status reason fields sample keys:',[k for k in S[0] if 'status' in k or 'date' in k or 'updated' in k])
