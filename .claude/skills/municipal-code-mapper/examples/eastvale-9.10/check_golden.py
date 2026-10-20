"""Validate the golden files: schemas, verbatim quotes, coverage, reference integrity, orphan/patch consistency.

Run:  python3 -I check_golden.py   (needs the jsonschema package)
Phase 2 replaces this with scripts/validate.py.
"""
import json,sys,glob,os,re
from jsonschema import Draft202012Validator
import pathlib
ex=str(pathlib.Path(__file__).resolve().parent)
base=str(pathlib.Path(ex).parent.parent); g=ex+'/golden/'
L=lambda p: json.load(open(p))
def val(schema,data,name):
    errs=list(Draft202012Validator(L(base+'/schemas/'+schema)).iter_errors(data))
    for e in errs[:5]: print('SCHEMA',name,list(e.absolute_path),e.message[:150])
    return not errs
ok=True
prov=L(g+'provisions.json'); acts=L(g+'actors.json'); pre=L(g+'actions.pre-resolution.json'); fro=L(g+'actions.frozen.json'); orp=L(g+'orphans.json'); dep=L(g+'dependencies.json')
for s,d,n in [('provision.schema.json',prov,'provisions'),('actor.schema.json',acts,'actors'),('action.schema.json',pre,'pre'),('action.schema.json',fro,'frozen'),('orphan.schema.json',orp,'orphans'),('dependency.schema.json',dep,'deps')]:
    ok&=val(s,d,n)
src=re.sub(r'\s+',' ',open(ex+'/source.md').read())
pd={p['id']:p for p in prov}
actor_ids={a['id'] for a in acts}
for name,recs in (('pre',pre),('frozen',fro)):
    ids={r['id'] for r in recs}
    for r in recs:
        for pid in r['provision_refs']:
            if pid not in pd: print('BAD provision ref',r['id'],pid); ok=False
        if r['source_quote'] not in pd[r['provision_refs'][0]]['text']: print('QUOTE not in provision',r['id']); ok=False
        if re.sub(r'\s+',' ',r['source_quote']) not in src: print('QUOTE not in source',r['id']); ok=False
        for k in ('actor','counterparty'):
            if r[k] and r[k]['id'] not in actor_ids: print('unknown actor',r['id'],r[k]['id']); ok=False
        s=r['signal']
        if s.get('ref') and s['ref'] not in ids: print('bad signal ref',r['id']); ok=False
        for c in r['conflict_with']:
            if c not in ids: print('bad conflict ref',r['id'],c); ok=False
        if (r['status']=='orphan')!=bool(r['orphan_flags']) and r['status']!='known_gap': print('status/flags mismatch',name,r['id'],r['status'],r['orphan_flags']); ok=False
        if r['signal']['type']=='unknown' and 'O-SIG' not in r['orphan_flags'] and not (r.get('duplicate_of') or r.get('superseded_by')): print('unknown signal without O-SIG',r['id']); ok=False
        if r['actor'] is None and 'O-ACT' not in r['orphan_flags']: print('no actor without O-ACT',r['id']); ok=False
# coverage invariant
for p in prov:
    if p['class']!='reserved' and not p['record_ids'] and not p['attaches_to']: print('UNCOVERED',p['id']); ok=False
    for rid in p['record_ids']:
        if rid not in {r['id'] for r in pre}: print('bad record id',p['id'],rid); ok=False
# graph integrity
ids={r['id'] for r in fro}
for e in dep['edges']:
    for end in (e['from'],e['to']):
        if end not in ids and not end.startswith('external:'): print('dangling edge end',e['id'],end); ok=False
    if e['from'] not in dep['nodes'] or e['to'] not in dep['nodes']: print('node missing',e['id']); ok=False
# orphans vs pre-resolution flags
pre_flags={(c,r['id']) for r in pre for c in r['orphan_flags']}
orp_flags={(o['code'],rid) for o in orp for rid in o['records']}
if pre_flags!=orp_flags: print('FLAG MISMATCH',pre_flags^orp_flags); ok=False
# patches reproduce frozen
import copy
test={r['id']:copy.deepcopy(r) for r in pre}
for o in orp:
    for rid,p in o['resolution']['patch'].items(): test[rid].update(p)
for rid,r in test.items():
    f={x['id']:x for x in fro}[rid]
    for k in r:
        if k in ('resolution_note','orphan_flags','status'): continue
        if r[k]!=f[k]: print('PATCH MISMATCH',rid,k); ok=False
print('provisions',len(prov),'pre',len(pre),'frozen',len(fro),'orphans',len(orp),'edges',len(dep['edges']))
print('ALL CHECKS PASSED' if ok else 'FAILURES')
sys.exit(0 if ok else 1)
