"""Read-only Windows IPv4 enumeration, outside the TouchDesigner UI thread."""
import json
from ipaddress import IPv4Address
import subprocess
import threading

_lock = threading.Lock()
_busy = False
_result = None


def parse_interfaces(document):
    rows = json.loads(document)
    if rows is None:
        return []
    if isinstance(rows, dict):
        rows = [rows]
    result = []
    seen = set()
    for row in rows:
        address = str(IPv4Address(row['IPAddress']))
        if address in seen or address == '0.0.0.0':
            continue
        seen.add(address)
        result.append({'address':address, 'name':str(row['InterfaceAlias'])})
    return sorted(result, key=lambda item:(item['name'].casefold(),item['address']))


def refresh():
    global _busy, _result
    with _lock:
        if _busy:
            return
        _busy = True
        _result = None
    threading.Thread(target=_worker,daemon=True).start()


def _worker():
    global _busy, _result
    try:
        command = "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.AddressState -eq 'Preferred'} | Select-Object IPAddress,InterfaceAlias | ConvertTo-Json -Compress"
        process = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],
            capture_output=True, text=True, timeout=12, shell=False,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if process.returncode:
            raise RuntimeError('Windows interface query failed')
        value = {'interfaces':parse_interfaces(process.stdout or 'null'),'error':''}
    except Exception as error:
        value = {'interfaces':[],'error':str(error)}
    with _lock:
        _result = value
        _busy = False


def take_result():
    global _result
    with _lock:
        result,_result = _result,None
        return result
