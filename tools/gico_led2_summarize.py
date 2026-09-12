"""Summarize recorded decoder decisions; never fill optical gaps from sender IDs."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.gico_camera_benchmark import summarize
BASE=ROOT/'measurements/gico-td-camera-001-video-review';OPT=BASE/'optical'
FILES=[('extraction','measure_15','measure_15'),('extraction-25','measure_25','measure_25'),
       ('extraction-30','measure_30_slow','measure_30'),('extraction-30','measure_30_end','measure_30')]

def runs(rows):
 result=[]
 for row in rows:
  if result and row['id'] is not None and result[-1]['id']==row['id']:
   result[-1]['count']+=1;result[-1]['last']=row['time']
  else:result.append({'id':row['id'],'first':row['time'],'last':row['time'],'count':1})
 return result

def main():
 audit=json.loads((BASE/'sender-audit/sender-audit.json').read_text())
 phases={p['name']:p for p in audit['phases']};cases=[]
 for directory,name,phase in FILES:
  path=OPT/directory/(name+'.npz')
  if not path.exists() or not path.with_suffix('.json').exists():continue
  info=json.loads(path.with_suffix('.json').read_text());raw=np.load(path);stats=raw['stats']
  variants={};idsets={}
  for kind,col in (('direct_crc',4),('including_bounded_erasures',5)):
   rows=[{'time':float(s[1]),'id':int(s[col]) if s[col]>=0 else None} for s in stats]
   groups=runs(rows); ids=set(r['id'] for r in rows if r['id'] is not None)
   stable=set(r['id'] for r in groups if r['id'] is not None and r['count']>=2)
   idsets[kind]=ids
   intervals=[];previous=None
   for r in groups:
    if r['id'] is None or r['count']<2:continue
    if previous and r['id']!=previous['id']:intervals.append((r['first']-previous['first'])*1000)
    if previous is None or r['id']!=previous['id']:previous=r
   variants[kind]={'single_frame':summarize(rows,info['requested_fps'],min_stable=1),
      'two_consecutive_frames':summarize(rows,info['requested_fps'],min_stable=2),
      'global_unique_ids':len(ids),'global_ids_seen_twice_consecutively':len(stable),
      'ids':sorted(ids),'ids_seen_twice_consecutively':sorted(stable),
      'observed_change_intervals_ms':{'median':float(np.median(intervals)) if intervals else None,
        'p95':float(np.percentile(intervals,95)) if intervals else None,'max':max(intervals,default=None)},
      'longest_consecutive_same_id_observation_ms':max(((r['last']-r['first'])*1000 for r in groups if r['id'] is not None),default=0)}
  visible=idsets['including_bounded_erasures'];submitted={r['id'] for r in phases[phase]['id_submission_trace']}
  interior=set(range(min(visible),max(visible)+1)) if visible else set()
  comparison={'optical_id_range':[min(visible),max(visible)] if visible else None,
      'optical_ids_absent_from_producer':sorted(visible-submitted),
      'ids_unobserved_optically_in_interior':sorted(interior-visible),
      'already_absent_before_worker':sorted((interior-visible)-submitted),
      'submitted_but_unobserved_optically':sorted((interior-visible)&submitted),
      'visible_ids_with_direct_crc':len(idsets['direct_crc']),
      'visible_ids_only_with_bounded_erasures':len(visible-idsets['direct_crc'])}
  direct_anchors=[]
  for target in (1450.2,1455.,1460.,1465.,1470.):
   valid=stats[(stats[:,4]>=0)&(np.abs(stats[:,0]-target)<.5)]
   if len(valid):
    s=valid[np.argmin(np.abs(valid[:,0]-target))];direct_anchors.append({'video_s':float(s[0]),'id':int(s[4])})
  cases.append({'window':name,'phase':phase,'fps_requested':info['requested_fps'],'real_duration_seconds':info['real_duration'],
       'video_start':info['video_start'],'video_end':info['video_end'],'time_basis':info['time_basis'],
       'classification_counts':info['reasons'],'variants':variants,'producer_comparison':comparison,
       'direct_tail_anchors':direct_anchors,'input_npz_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 report={'video':'E:/LED2.mov','video_sha256':'8f65f06de4c2fa991e8aed9c2f332006d3e87edaaa1524c7e4aad988cb5d64b3',
       'model_sha256':hashlib.sha256((OPT/'model.npz').read_bytes()).hexdigest(),'cases':cases,
       'notes':['Primary slow-motion count requires two consecutive valid camera samples.',
                'One-frame results and direct/recovered evidence are separate.',
                'Observed frame changes are not electrical refreshes.',
                'Float32 scores are diagnostic; stored decoded decisions were made using float64.',
                'Missing optical IDs are not automatically controller or network losses.']}
 (OPT/'comparison.json').write_text(json.dumps(report,indent=2))
 print(json.dumps([{'window':c['window'],'direct_fps':c['variants']['direct_crc']['two_consecutive_frames']['observed_unique_fps_estimate'],
   'bounded_fps':c['variants']['including_bounded_erasures']['two_consecutive_frames']['observed_unique_fps_estimate'],
   'single_fps':c['variants']['including_bounded_erasures']['single_frame']['observed_unique_fps_estimate'],
   'unique':c['variants']['including_bounded_erasures']['global_unique_ids'],
   'compare':{k:(len(v) if isinstance(v,list) and k!='optical_id_range' else v) for k,v in c['producer_comparison'].items()}} for c in cases],indent=2))

if __name__=='__main__':main()
