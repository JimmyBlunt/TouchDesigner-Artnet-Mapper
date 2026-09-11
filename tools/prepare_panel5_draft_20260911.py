"""Accept every measured Panel 5 point, reserving missing slots for later scans."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.layout_scene_adapter import load_document_json,document_json
from pixelblaze_mapper.scan_result_review import inspect_result
from pixelblaze_mapper.scan_partial_acceptance import append_partial_reviewed
from pixelblaze_mapper.layout_remove_leds import prepare as remove_leds
from place_panel5_20260911 import prepare as place

OUT=ROOT/'docs/panel5-integration-20260911'
MISSING={123,197,231,234,235,243,244,252,253,261,270}


def main():
    saved=json.loads((OUT/'before.json').read_text(encoding='utf-8'))
    original=load_document_json(saved['document'])
    review=inspect_result(saved['status'])
    assert review['count']==341 and set(review['ids'])==set(range(352))-MISSING
    paths=[p.strip() for p in saved['fields']['views'].split('|')]
    assert len(paths)==4 and all('panel5_352' in p for p in paths)
    updated=append_partial_reviewed(original,review,saved['session'],paths,
        source_offset=6172,name='Panel 5 | Ausrichtung ausstehend')
    updated,placement=place(updated)
    panel=updated.scene.objects[-1]
    template=updated.scene.object('33ef5c9a-877d-5d46-a359-13632f057db5')
    wanted=set(range(2464,2720))
    bindings=[b for b in template.leds if b.source_index in wanted]
    assert {b.source_index for b in bindings}==wanted
    updated,removed=remove_leds(updated,template.object_id,[b.local_index for b in bindings])
    assert {b.source_index for b in removed}==wanted
    before={b.source_index:(b,p) for b,p in original.scene.world_points()}
    after={b.source_index:(b,p) for b,p in updated.scene.world_points()}
    assert set(before)-set(after)==wanted
    assert all(after[i]==v for i,v in before.items() if i not in wanted)
    assert set(after)-set(before)=={6172+i for i in range(352) if i not in MISSING}
    assert updated.scene.scans[:-1]==original.scene.scans and updated.routes==original.routes
    assert {0,351}<={b.local_index for b in panel.leds}
    report={'panel_id':panel.object_id,'expected_leds':352,'measured_leds':341,
        'missing_local_ids':sorted(MISSING),'missing_global_sources':[6172+i for i in sorted(MISSING)],
        'reserved_sources':[6172,6523],'placement':placement,
        'retired_template_sources':[2464,2719],'retired_template_count':256,
        'other_points_and_routes_unchanged':True,'active_applied':False,
        'orientation_user_confirmed':False}
    (OUT/'draft-prepared.json').write_text(document_json(updated),encoding='utf-8')
    (OUT/'draft-plan.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
