"""Refresh published material repairs without selecting a different material."""
import json
from pathlib import Path
from audit_material_library import ROOT, td

SCRIPT = r'''
import json,importlib,hashlib
from pathlib import Path
from pixelblaze_mapper import show_pads
manager=show_pads._manager
if manager is None: raise RuntimeError('MK2 material manager is not running')
if manager.controller.snapshot().get('recording'): raise RuntimeError('Stop recording before refreshing materials')
lib=op('/project1/madmapper_library')
runtime=lib.op('runtime').module
def snapshot():
 active=runtime._active_item()
 adaptation,values=runtime._parameter_context(active)
 mapper=op('/project1/pixelblaze_mapper')
 return dict(active=active['id'],values=values,uv=hashlib.sha256(mapper.op('effect_panel_uv').text.encode()).hexdigest())
before=snapshot()
from pixelblaze_mapper import material_audio_runtime,material_texture_runtime,material_shader_repairs,material_generator_glsl,madmapper_td_adapter
for module in (material_audio_runtime,material_texture_runtime,material_shader_repairs,material_generator_glsl,madmapper_td_adapter): importlib.reload(module)
runtime._hover_context_cache.clear()
runtime._parameter_context_cache.clear()
if not runtime.refresh(reset_page=False): raise RuntimeError('Library refresh failed')
active=runtime._active_item()
validation=active.get('metadata',{}).get('_TD_VALIDATION',{})
if validation.get('adapter_version')!=madmapper_td_adapter.ADAPTER_VERSION: raise RuntimeError('Publish verified catalog before deployment')
adaptation,values=runtime._parameter_context(active)
preview=lib.op('live_preview')
runtime._configure_parameter_uniforms(preview,adaptation,values)
lib.op('preview_shader').text=adaptation.shader
preview.cook(force=True)
errors=runtime._compile_errors(preview)
if errors: raise RuntimeError(str(errors))
browser=op('/project1/material_browser/unified_runtime')
if browser is not None: browser.module.refresh(reset_page=False)
manager.refresh_catalog()
manager.update_surface()
after=snapshot()
if before!=after: raise RuntimeError('Active material, parameters or mapping changed during deployment: '+str((before,after)))
result=json.dumps(dict(before=before,after=after,adapter_version=madmapper_td_adapter.ADAPTER_VERSION,
 active_label=active['label'],mk2_materials=len(manager.catalog),mk2_status=manager.worker.status if manager.worker else None,
 errors=list(preview.errors())))
'''

if __name__=='__main__':
    report=td(SCRIPT)
    destination=ROOT/'docs/material-audit-20261013/deployment.json'
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
