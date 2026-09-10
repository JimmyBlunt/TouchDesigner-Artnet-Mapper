"""Retire only the old upper-right 16x16 template from the 3D draft.

Scan archival data and the 680 real Panel 2 binding identities remain unchanged.
Removing template bindings is reversible with the normal Layout Undo action.
No active mapping or controller routing is changed by this preparation.
"""
from dataclasses import replace
from pixelblaze_mapper.layout_scene import SceneError


def prepare(document):
    scene=document.scene
    template=scene.object('33ef5c9a-877d-5d46-a359-13632f057db5')
    panel=scene.object('eeb92daf-cb0b-4ddf-952b-d3c49897b0f9')
    wanted=set(range(1184,1440))
    removed=tuple(b for b in template.leds if b.source_index in wanted)
    if {b.source_index for b in removed}!=wanted:
        raise SceneError('Upper-right template changed or was already retired; inspect the draft')
    if len(panel.leds)!=680 or {b.source_index for b in panel.leds}&wanted:
        raise SceneError('Panel 2 identity or source allocation changed')
    positions={b.source_index:p for b,p in scene.world_points()}
    points=[positions[i] for i in sorted(wanted)]
    lo=tuple(min(p[a] for p in points) for a in range(3))
    hi=tuple(max(p[a] for p in points) for a in range(3))
    if (any(abs(a-b)>1e-9 for a,b in zip(lo,(.815625,1.,.315625)))
            or any(abs(a-b)>1e-9 for a,b in zip(hi,(.984375,1.,.484375)))):
        raise SceneError('These sources no longer represent the upper-right template')
    cleaned=replace(template,leds=tuple(b for b in template.leds if b.source_index not in wanted))
    updated=replace(document,scene=replace(scene,objects=tuple(cleaned if o.object_id==template.object_id else o for o in scene.objects)))
    before={b.led_id:(b,p) for b,p in scene.world_points()}
    after={b.led_id:(b,p) for b,p in updated.scene.world_points()}
    assert set(before)-set(after)=={b.led_id for b in removed}
    assert all(before[key]==value for key,value in after.items())
    assert updated.scene.scans==scene.scans and updated.routes==document.routes
    assert updated.scene.object(panel.object_id)==panel
    return updated,{'removed_template_count':len(removed),'removed_sources':sorted(wanted),
        'removed_led_ids':[b.led_id for b in removed],'removed_bounds':[lo,hi],
        'remaining_template_count':len(cleaned.leds),'remaining_draft_led_count':len(after),
        'panel2_led_count':len(panel.leds),'other_points_and_ids_unchanged':True,
        'raw_scans_unchanged':True,'active_applied':False}
