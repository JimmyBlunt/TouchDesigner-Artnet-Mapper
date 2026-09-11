"""Prepare Panel 4 for the user's orientation review, without active output changes."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.layout_scene_adapter import load_document_json, document_json
from pixelblaze_mapper.scan_result_review import inspect_result
from pixelblaze_mapper.scan_partial_acceptance import append_partial_reviewed
from pixelblaze_mapper.layout_remove_leds import prepare as remove_leds
from place_panel4_20260911 import prepare as place

OUT=ROOT/'docs/panel4-integration-20260911'


def main():
    saved=json.loads((OUT/'reconstruction-and-draft.json').read_text(encoding='utf-8'))
    captured=json.loads((OUT/'scan-state-before.json').read_text(encoding='utf-8'))
    original=load_document_json(saved['document'])
    review=inspect_result(saved['status'])
    assert review['count']==809 and review['missing_observed_ids']==[45]
    views=[p.strip() for p in captured['fields']['views'].split('|')]
    assert len(views)==3 and all('_repaired' in p for p in views)
    updated=append_partial_reviewed(original,review,saved['session'],views,
        source_offset=5362,name='Panel 4 | Ausrichtung ausstehend')
    updated,placement=place(updated)
    panel=updated.scene.objects[-1]
    template=updated.scene.object('33ef5c9a-877d-5d46-a359-13632f057db5')
    wanted=set(range(1696,1952))
    bindings=[b for b in template.leds if b.source_index in wanted]
    assert {b.source_index for b in bindings}==wanted
    updated,removed=remove_leds(updated,template.object_id,[b.local_index for b in bindings])
    assert {b.source_index for b in removed}==wanted
    assert updated.routes==original.routes
    before={b.source_index:(b,p) for b,p in original.scene.world_points()}
    after={b.source_index:(b,p) for b,p in updated.scene.world_points()}
    assert set(before)-set(after)==wanted
    assert all(after[i]==v for i,v in before.items() if i not in wanted)
    assert set(after)-set(before)==set(range(5362,6172))-{5407}
    assert updated.scene.scans[:-1]==original.scene.scans
    report={'panel_id':panel.object_id,'source_offset':5362,'reserved_source_range':[5362,6171],
        'measured_leds':809,'expected_leds':810,'missing_local_ids':[45],
        'missing_global_sources':[5407],'placement':placement,
        'retired_template_sources':[1696,1951],'retired_template_count':256,
        'other_objects_unchanged':True,'routes_unchanged':True,'active_applied':False,
        'orientation_user_confirmed':False}
    (OUT/'draft-prepared.json').write_text(document_json(updated),encoding='utf-8')
    (OUT/'draft-plan.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
