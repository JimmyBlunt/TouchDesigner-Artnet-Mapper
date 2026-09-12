"""Read-only source inspection: QuickTime timing tables and sparse decode checks."""
import hashlib
import json
import struct
from pathlib import Path
import cv2
import numpy as np

VIDEO = Path('E:/LED2.mov')
OUT = Path(__file__).resolve().parent

def boxes(data, base=0):
    p = 0
    while p + 8 <= len(data):
        size, kind = struct.unpack_from('>I4s', data, p)
        header = 8
        if size == 1:
            size = struct.unpack_from('>Q', data, p + 8)[0]
            header = 16
        elif size == 0:
            size = len(data) - p
        if size < header or p + size > len(data):
            break
        yield kind.decode('latin1'), data[p+header:p+size], base+p, size
        p += size

def read_tables(data, path='moov'):
    rows = []
    for kind, body, pos, size in boxes(data):
        name = path + '/' + kind
        row = {'path': name, 'size': size}
        if kind in ('trak', 'mdia', 'minf', 'stbl', 'edts', 'udta'):
            row['children'] = read_tables(body, name)
        elif kind in ('mvhd', 'mdhd'):
            v = body[0]
            off = 20 if v else 12
            scale = struct.unpack_from('>I', body, off)[0]
            dur = struct.unpack_from('>Q' if v else '>I', body, off+4)[0]
            row.update(timescale=scale, duration_ticks=dur, duration_seconds=dur/scale)
        elif kind == 'hdlr':
            row['handler'] = body[8:12].decode('latin1')
        elif kind in ('stts', 'ctts'):
            count = struct.unpack_from('>I', body, 4)[0]
            fmt = '>Ii' if kind == 'ctts' and body[0] else '>II'
            values = [list(struct.unpack_from(fmt, body, 8+i*8)) for i in range(count)]
            row.update(entry_count=count, entries=values)
        elif kind == 'elst':
            count = struct.unpack_from('>I', body, 4)[0]
            fmt = '>Qqhh' if body[0] else '>Iihh'
            step = struct.calcsize(fmt)
            row.update(entries=[list(struct.unpack_from(fmt, body, 8+i*step)) for i in range(count)])
        elif kind == 'meta':
            # QuickTime metadata uses indexed keys. Keep only camera/timing fields;
            # the embedded GPS location is irrelevant to this measurement.
            sub = {k:b for k,b,_,_ in boxes(body)}
            keys = []
            if 'keys' in sub:
                kb=sub['keys']; p=8
                for _ in range(struct.unpack_from('>I',kb,4)[0]):
                    n=struct.unpack_from('>I',kb,p)[0]
                    keys.append(kb[p+8:p+n].decode('utf8')); p+=n
            allowed={'com.apple.quicktime.make','com.apple.quicktime.model',
                     'com.apple.quicktime.software','com.apple.quicktime.creationdate',
                     'com.apple.quicktime.full-frame-rate-playback-intent'}
            values={}
            for ik, ib, _, _ in boxes(sub.get('ilst',b'')):
                index=int.from_bytes(ik.encode('latin1'),'big')-1
                if not 0<=index<len(keys) or keys[index] not in allowed:
                    continue
                for dk,db,_,_ in boxes(ib):
                    if dk=='data':
                        datatype=int.from_bytes(db[:4],'big')
                        values[keys[index]]=db[8:].decode('utf8') if datatype==1 else int.from_bytes(db[8:],'big')
            row['selected_metadata']=values
        elif kind == 'stsd':
            row['codec'] = body[12:16].decode('latin1')
        rows.append(row)
    return rows

OUT.mkdir(exist_ok=True)
top = []
moov = None
with VIDEO.open('rb') as f:
    while f.tell() < VIDEO.stat().st_size:
        start = f.tell()
        head = f.read(8)
        if len(head)<8:
            break
        size, kind = struct.unpack('>I4s', head)
        hs=8
        if size == 1:
            size=struct.unpack('>Q',f.read(8))[0]; hs=16
        if size == 0:
            size=VIDEO.stat().st_size-start
        top.append({'type':kind.decode('latin1'),'start':start,'size':size})
        if kind == b'moov':
            moov = f.read(size-hs)
        f.seek(start+size)
digest = hashlib.sha256()
with VIDEO.open('rb') as f:
    for chunk in iter(lambda:f.read(8*1024*1024),b''):
        digest.update(chunk)
cap = cv2.VideoCapture(str(VIDEO))
fps=cap.get(cv2.CAP_PROP_FPS)
count=cap.get(cv2.CAP_PROP_FRAME_COUNT)
duration=count/fps
samples=[]
tiles=[]
for seconds in [0,10,30,60,120,180,240,360,480,600,720,840,960,1080,1200,1320,1440,duration-0.2]:
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds*1000)
    ok,frame=cap.read()
    actual=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
    samples.append({'requested_seconds':seconds,'decoded':bool(ok),'actual_pts_seconds':actual})
    if ok:
        small=cv2.resize(frame,(180,320))
        cv2.putText(small,f'{actual:.2f}s',(4,18),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,255),1)
        tiles.append(small)
while len(tiles)%6:
    tiles.append(np.zeros((320,180,3),dtype=np.uint8))
cv2.imwrite(str(OUT/'sparse-contact-sheet.jpg'),np.vstack([np.hstack(tiles[i:i+6]) for i in range(0,len(tiles),6)]))
result={'video':str(VIDEO),'bytes':VIDEO.stat().st_size,'sha256':digest.hexdigest(),
        'opencv_version':cv2.__version__,'width':cap.get(3),'height':cap.get(4),'fps':fps,
        'frame_count':count,'duration_seconds':duration,'top_level_atoms':top,
        'movie_tables':read_tables(moov) if moov else None,'sparse_decode_samples':samples,
        'integrity_scope':'Atom extents, SHA-256 and sparse seeks incl. near EOF; not a complete video decode.'}
cap.release()
(OUT/'metadata.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ('movie_tables','sparse_decode_samples')},indent=2))
