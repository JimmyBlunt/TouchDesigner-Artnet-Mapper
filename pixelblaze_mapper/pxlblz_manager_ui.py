"""Idempotent menu entries for the external PXLBLZ installation manager."""
from pathlib import Path
import json
import shutil
import subprocess
import urllib.request
import webbrowser
import threading
import time

ROOT = Path(__file__).resolve().parents[1] / 'tools' / 'pxlblz_manager'
URL = 'http://127.0.0.1:9990/'

def launch(open_browser=True):
    # Never wait for a TD-dependent HTTP action on TouchDesigner's main thread.
    try:
        with urllib.request.urlopen(URL+'api/state', timeout=0.5) as response:
            response.read()
    except OSError:
        node = shutil.which('node') or r'C:\Program Files\nodejs\node.exe'
        with open(ROOT/'service.log', 'ab') as out, open(ROOT/'service-error.log', 'ab') as err:
            subprocess.Popen([node, str(ROOT/'service.mjs')], cwd=str(ROOT),
                stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
    if open_browser:
        def show_when_ready():
            for _ in range(30):
                try:
                    with urllib.request.urlopen(URL+'api/state', timeout=0.5):
                        webbrowser.open(URL)
                        return
                except OSError:
                    time.sleep(0.2)
        threading.Thread(target=show_when_ready,daemon=True).start()
    return URL

def install():
    from pixelblaze_mapper.build_layout_scene_ui import _node, _panel, _set
    import td
    installed=[]
    for panel_path, x, y, width in [
        ('/project1/layout_scene_editor/ui_panel', 890, 915, 210),
        ('/project1/pixelblaze_mapper/ui/canvas', 1050, 750, 195)]:
        panel=td.op(panel_path)
        if panel is None:
            continue
        if 'layout_scene_editor' in panel_path:
            _set(panel.op('title'), 'w', 850)
        else:
            _set(panel.op('subtitle'), 'w', 475)
            _set(panel.op('subtitle'), 'text', 'MAP IMPORT / EXPORT  |  Gesamtanlage: PXLBLZ / ART-NET')
        button=_panel(_node(panel, td.buttonCOMP, 'btn_pxlblz_manager'), x,y,width,32,50)
        for key,value in [('label','PXLBLZ / ART-NET'),('buttontype','momentary'),('fontsize',12),
                          ('bgcolorr',.04),('bgcolorg',.32),('bgcolorb',.29)]:
            _set(button,key,value)
        callback=_node(panel,td.panelexecuteDAT,'click_pxlblz_manager')
        callback.par.active=False
        callback.par.panels=button.path
        callback.par.fromop=button.path
        callback.par.panelvalue='lselect'
        callback.par.offtoon=True
        callback.par.ontooff=False
        callback.par.valuechange=False
        _set(callback,'whileon',False)
        _set(callback,'whileoff',False)
        callback.text="def onOffToOn(panelValue):\n    from pixelblaze_mapper.pxlblz_manager_ui import launch\n    launch()\n    return\n"
        callback.par.active=True
        installed.append(button.path)
    return installed
