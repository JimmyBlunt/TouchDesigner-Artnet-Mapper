"""Archive exact non-secret firmware artifacts and source for a measured build."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile

def main(label, profile):
    root=Path(__file__).resolve().parent
    private=Path(os.environ['LOCALAPPDATA'])/'CodexESP30'
    build=private/'build/esp32_testnode_mixed'
    report=root.parents[1]/'docs/performance-program-20260912/esp'
    target=report/('esp-firmware-'+label+'.zip')
    manifest_path=report/('build-'+label+'.json')
    if target.exists() or manifest_path.exists(): raise RuntimeError('Snapshot label already exists')
    source=[root/'platformio.ini',root/'src/main.cpp',root/'include/frame_assembler.h',root/'include/apa_frame.h',root/'README_DE.md']
    if any(p.stat().st_mtime>(build/'firmware.bin').stat().st_mtime for p in source if p.suffix in ('.cpp','.h')):
        raise RuntimeError('Source is newer than firmware; rebuild before snapshot')
    artifacts={name:build/name for name in ('firmware.bin','bootloader.bin','partitions.bin')}
    artifacts['boot_app0.bin']=private/'pio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin'
    manifest={'label':label,'compiled_panel_profile':profile,
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'platformio':'6.1.18','platform':'espressif32@6.10.0','fastled':'3.9.15',
        'board':'ESP32-D0WD rev1.0 /4MB /MAC e8:68:e7:0d:38:a4',
        'output_default':'disarmed; LED GPIO initialization deferred until ARM',
        'flash_offsets':{'bootloader.bin':'0x1000','partitions.bin':'0x8000','boot_app0.bin':'0xe000','firmware.bin':'0x10000'},
        'artifacts':{name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for name,p in artifacts.items()},
        'sources':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source}}
    saved=private/'artifacts'/label;saved.mkdir(parents=True,exist_ok=False)
    for name,p in artifacts.items():shutil.copy2(p,saved/name)
    shutil.copy2(build/'firmware.elf',saved/'firmware.elf')
    manifest['private_artifact_directory']=str(saved)
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,p in artifacts.items():archive.write(p,name)
        for p in source:archive.write(p,'source/'+str(p.relative_to(root)))
        archive.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip():raise RuntimeError('Archive integrity check failed')
    manifest['archive_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':str(manifest_path),'archive':str(target),'firmware':manifest['artifacts']['firmware.bin']},indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label',choices=['physical768-socket-v1','virtual1755-socket-v1','physical768-raw-v2','virtual1755-raw-v2'])
    parser.add_argument('--profile',type=int,choices=[768,1755],required=True)
    args=parser.parse_args();main(args.label,args.profile)
