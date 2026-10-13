"""Supplement the small default audit with square images at later times."""
import json
from pathlib import Path
from audit_material_library import ROOT, GPUProbe, adapter, load_catalog, td, quarantine_reason

IDS = ('mat_a6d6be3154c86c977fea','mat_8542a7bbfb2650ea5854','mat_9023587be44bdf837cc8',
       'mat_38ac1e34ded8229790b7','mat_2e490d5e1eb4eb713229')

def execute_square(script):
    if 'settings=json.loads' in script:
        script=script.replace("preview.par.resolutionw=96; preview.par.resolutionh=64",
                              "preview.par.resolutionw=256; preview.par.resolutionh=256")
        script=script.replace('(64,96,4)','(256,256,4)')
        script=script.replace("for phase in settings['times']:","for phase in (0.,8.,20.):")
    return td(script,timeout=60)

if __name__=='__main__':
    catalog=load_catalog(ROOT/'material_library/catalogs/madmapper-official-d7ff211.json')
    output=ROOT/'docs/material-audit-20261013/visual-recheck'
    probe=GPUProbe(output,execute=execute_square)
    results=[]
    try:
        for item in catalog.materials:
            if item.id not in IDS: continue
            if quarantine_reason(item): raise RuntimeError('Quarantined source: '+item.name)
            source=Path(item.source_path);root=Path(catalog.source_root)
            adaptation=adapter.adapt_material(source,library_roots=(root,root.parent,source.parent,source.parent.parent))
            if not adaptation.adaptable: raise RuntimeError('Unsupported source: '+item.name)
            evidence=probe.run(item,adaptation)
            results.append(dict(id=item.id,name=item.name,probe=evidence))
            print(item.name,[(s['time'],s['nonfinite_count']) for s in evidence.get('samples',[])],flush=True)
    finally: probe.close()
    (output/'results.json').write_text(json.dumps(dict(resolution=[256,256],times=[0,8,20],
        warning='Supplementary visual review; not substituted for the full audit.',results=results),indent=2),encoding='utf-8')
