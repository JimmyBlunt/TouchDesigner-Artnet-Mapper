"""Flash only the USB-identified ESP after checking its verified full backup."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

EXPECTED_MAC='e8:68:e7:0d:38:a4'
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'docs/performance-program-20260912/esp'

def main(label):
    backup=json.loads((REPORT/'backup-verification.json').read_text())
    if backup['mac']!=EXPECTED_MAC or not backup['two_independent_full_reads_identical']:
        raise RuntimeError('Verified backup metadata missing')
    for name in backup['private_backup_paths']:
        data=Path(name).read_bytes()
        if len(data)!=4194304 or hashlib.sha256(data).hexdigest()!=backup['sha256']:
            raise RuntimeError('A full backup does not match its recorded checksum')
    manifest=json.loads((REPORT/('build-'+label+'.json')).read_text())
    artifacts=Path(manifest['private_artifact_directory'])
    for name,meta in manifest['artifacts'].items():
        if hashlib.sha256((artifacts/name).read_bytes()).hexdigest()!=meta['sha256']:
            raise RuntimeError('Firmware artifact checksum mismatch')
    logpath=REPORT/('flash-'+label+'.log')
    if logpath.exists():raise RuntimeError('Flash log already exists; inspect the previous attempt')
    common=[sys.executable,'-m','esptool','--chip','esp32','--port','COM5','--baud','230400']
    preflight=subprocess.run(common+['--after','no_reset','read_mac'],capture_output=True,text=True,timeout=45)
    logpath.write_text(preflight.stdout+preflight.stderr)
    if preflight.returncode or ('MAC: '+EXPECTED_MAC) not in preflight.stdout:
        raise RuntimeError('COM5 identity does not match the authorized test ESP; flash aborted')
    args=common+['--before','no_reset','--after','hard_reset','write_flash',
                 '--flash_mode','dio','--flash_freq','40m','--flash_size','4MB']
    for name,offset in manifest['flash_offsets'].items():args.extend([offset,str(artifacts/name)])
    flashed=subprocess.run(args,capture_output=True,text=True,timeout=420)
    with logpath.open('a') as out:out.write(flashed.stdout+flashed.stderr)
    result={'label':label,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'mac':EXPECTED_MAC,'port':'COM5','returncode':flashed.returncode,
            'firmware_sha256':manifest['artifacts']['firmware.bin']['sha256'],
            'hash_verification_messages':flashed.stdout.count('Hash of data verified.'),
            'runtime_disarmed_verified':False,'log':str(logpath)}
    (REPORT/('flash-'+label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if flashed.returncode:raise RuntimeError('Flash failed; inspect log before any further action')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label',choices=['physical768-socket-v1','virtual1755-socket-v1','physical768-raw-v2','virtual1755-raw-v2'])
    main(parser.parse_args().label)
