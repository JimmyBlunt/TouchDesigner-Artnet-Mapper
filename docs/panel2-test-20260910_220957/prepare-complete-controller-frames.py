
import json
from pixelblaze_mapper import guided_scan_live as live,scan_capture
from pixelblaze_mapper.multi_controller import ControllerConfig,SegmentConfig,RouterConfig
from pixelblaze_mapper.scan_routing import create_snapshot
p=op(live.OWNER)
live.assert_outputs_off(op)
assert p.fetch('standalone_capture')['count']==738
assert p.fetch('standalone_capture')['universe']==122
brightness=live.scan_brightness(op)
controller=ControllerConfig('BACK_PANEL2_738_249','10.0.0.249','10.0.0.125',enabled=True,start_universe=120,color_order='RGB',brightness=brightness,rate=30,reserved_universes=7)
routing=RouterConfig((controller,),(SegmentConfig('panel2_only',0,738,controller.name,destination_start=340),),source_pixel_count=738)
snapshot=create_snapshot(routing,(0,170,340,510,737),brightness_cap=brightness)
old=p.fetch('capture_plan')
plan=scan_capture.prepare_capture(snapshot,old['camera'],old['workspace'],identity=old['identity'],scene_revision=old['scene_revision'])
assert [x.wire_universe for x in snapshot.targets]==[122,123,124,125,126]
assert [f.wire_universe for f in snapshot.packet_descriptors()]==list(range(120,127))
p.store('capture_plan',plan)
p.store('capture_signature',live._routing_signature(op))
p.op('worker_plan').text=json.dumps(plan,indent=2)
p.op('ui_panel/routing_summary').par.text='PANEL 2: 738 LEDs U122-126 | 5 TEST LEDs 6.2% | U120-121 BLACK for full controller frames'
result=json.dumps({'plan':plan,'previous_status':p.fetch('capture_status')})
