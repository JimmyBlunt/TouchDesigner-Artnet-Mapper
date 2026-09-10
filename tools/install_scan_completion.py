"""Install completed scan controls and dormant apply adapter; outputs stay off."""
import json
from pathlib import Path
from tools.audit_20260907_capture import td
from tools.install_scan_workflow_ux import ROOT,install_script

def script():
    value=install_script(ROOT).replace("'scan_library', 'scan_result_review'", "'scan_library', 'scan_library_ui', 'scan_registration', 'scan_registration_ui', 'scan_ui_style', 'scan_result_review'")
    return value + r'''
installation=json.loads(result)
from pixelblaze_mapper import build_layout_apply, preview_color_bulk
importlib.reload(build_layout_apply);importlib.reload(preview_color_bulk)
path=root/'pixelblaze_mapper/build_layout_apply.py'
scope=dict(globals(),__file__=str(path),__name__='completion_apply')
exec(compile(path.read_text(),str(path),'exec'),scope,scope);scope['build']()
preview=op('/project1/pixelblaze_mapper/preview3d/instance_data_callbacks')
preview.text=preview_color_bulk.ensure_bulk_source(preview.text)
installation['after']=snapshot()
installation['checks']['no_operator_errors']=not installation['after']['errors']
result=json.dumps(installation)
'''

if __name__=='__main__':
    result=td(script())
    (ROOT/'docs/completion-20260910/final-ui-install.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result['checks'],indent=2))
    assert all(result['checks'].values())
