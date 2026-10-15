"""Isolated real timeline HTTP backend for browser acceptance; never touches TD."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.test_show_timeline import FakeHost
from pixelblaze_mapper.show_timeline_ui import Bridge

host = FakeHost()
bridge = Bridge(host, port=0)
bridge.start()
bridge.port = bridge.server.server_address[1]
print(json.dumps(dict(url=f'http://127.0.0.1:{bridge.port}/')), flush=True)
while True:
    bridge.tick()
    time.sleep(.01)
