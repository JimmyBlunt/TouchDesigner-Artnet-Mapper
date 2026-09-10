"""Archive an incomplete acquisition while binding only measured 3D points."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from .layout_scene import SceneError, Transform
from .layout_scene_adapter import LayoutDocument
from .scan_session import ScanSession

PREFIX = 'Partial acquisition evidence: '


def occupied_sources(document):
    """Include explicitly reserved missing slots of partial objects still present."""
    used={led.source_index for obj in document.scene.objects for led in obj.leds}
    scans={scan.scan_id:scan for scan in document.scene.scans}
    for obj in document.scene.objects:
        for scan_id in {led.scan_id for led in obj.leds}:
            scan=scans[scan_id]
            for warning in scan.warnings:
                if not warning.startswith(PREFIX):continue
                evidence=json.loads(warning[len(PREFIX):])
                expected=evidence['expected_source_indices']
                if (not isinstance(expected,list) or len(expected)>100000
                        or any(type(i) is not int or not 0<=i<100000 for i in expected)):
                    raise SceneError('Invalid reserved acquisition indices')
                offsets={led.source_index-led.scan_index for led in obj.leds if led.scan_id==scan_id}
                if len(offsets)!=1:
                    raise SceneError('Partial acquisition has ambiguous reserved source offsets')
                offset=next(iter(offsets))
                used.update(offset+i for i in expected)
    return used


def append_partial_reviewed(document, review, session, view_paths, *, source_offset, name,
                            transform=Transform()):
    from .scan_result_review import append_reviewed
    from .scan_coverage_visual import build_data
    if isinstance(session,dict):session=ScanSession.from_dict(session)
    if session.session_id!=review.get('session_id'):
        raise SceneError('Acquisition session differs from reviewed result')
    wanted=set(session.capture_ids)
    targets={t.source_index:t for t in session.targets if t.led_id in wanted}
    expected=set(targets)
    if not expected or max(expected)>=100000:
        raise SceneError('Expected acquisition range must fit 100000 scan slots')
    if type(source_offset) is not int or source_offset<0:
        raise SceneError('Global source offset must be a non-negative integer')
    paths=list(dict.fromkeys(str(Path(p).resolve(strict=True)) for p in view_paths))
    if not paths or len(paths)>64:raise SceneError('Select 1 to 64 original observations')
    files=sorted({str(file) for p in paths for file in
                  (Path(p),Path(p).parent/'capture.json',Path(p).parent/'result.json')})
    # Fingerprints surround validation so mutable input cannot silently change.
    def hashes():
        total=0
        result={}
        for p in files:
            with Path(p).open('rb') as stream:data=stream.read(16*1024*1024+1)
            total+=len(data)
            if len(data)>16*1024*1024 or total>32*1024*1024:
                raise SceneError('Observation evidence exceeds analysis limit')
            result[p]=sha256(data).hexdigest()
        return result
    before=hashes()
    data=build_data(paths,sorted(expected),review['path'],session=session)
    if hashes()!=before:raise SceneError('Observation files changed during acceptance')
    accepted=set(review['ids'])
    if (not accepted<=expected or data['reconstructed_count']!=len(accepted)):
        raise SceneError('Reviewed IDs differ from acquisition scope')
    if occupied_sources(document).intersection(source_offset+i for i in expected):
        raise SceneError('Expected acquisition range overlaps occupied or reserved source slots')
    updated=append_reviewed(document,review,source_offset=source_offset,name=name,transform=transform)
    obj=updated.scene.objects[-1]
    scan=next(s for s in updated.scene.scans if s.scan_id==obj.leds[0].scan_id)
    length=max(expected)+1
    points=scan.points+((0.,0.,0.),)*(length-len(scan.points))
    missing=tuple(i for i in range(length) if i not in accepted)
    never=set(data['never_seen_ids'])
    counts={point['id']:point['count'] for view in data['views'] for point in view['points']}
    if any(counts.get(i,0)<2 for i in accepted):
        raise SceneError('Reconstructed LEDs require at least two supporting selected views')
    metadata=[]
    for i in range(length):
        row=dict(scan.row_metadata[i]) if i<len(scan.row_metadata) else {}
        if set(row).intersection({'acquisition_source_index','draft_source_index','scan_status',
                                  'observation_count','occlusion','acquisition_led_id'}):
            raise SceneError('Acquisition metadata would overwrite original scan columns')
        status=('outside_requested_scope' if i not in expected else
                'reconstructed' if i in accepted else
                'missing_never_observed' if i in never else 'missing_not_reconstructed')
        row.update(acquisition_source_index=str(i),draft_source_index=str(source_offset+i),
                   scan_status=status,observation_count=str(counts.get(i,0)),occlusion='unknown')
        if i in targets:row['acquisition_led_id']=targets[i].led_id
        metadata.append(tuple(sorted(row.items())))
    evidence={'schema':'pixelblaze-partial-acquisition','version':1,'session':session.to_dict(),
              'expected_source_indices':sorted(expected),'accepted_source_indices':sorted(accepted),
              'missing_source_indices':sorted(expected-accepted),'never_observed':sorted(never),
              'observed_without_3d':sorted(expected-accepted-never),'source_offset':source_offset,
              'candidate_path':review['path'],'candidate_sha256':review['sha256'],
              'report_sha256':review['report_sha256'],'view_sha256':before,
              'occlusion':'unknown','coordinate_units':'arbitrary_sfm','registration_verified':False}
    archived=replace(scan,points=points,missing_indices=missing,row_metadata=tuple(metadata),
                     warnings=scan.warnings+(PREFIX+json.dumps(evidence,sort_keys=True),))
    bindings=tuple(replace(led,led_id=targets[led.scan_index].led_id,
                           local_index=targets[led.scan_index].local_index) for led in obj.leds)
    new_obj=replace(obj,leds=bindings)
    scene=replace(updated.scene,scans=tuple(archived if s.scan_id==scan.scan_id else s for s in updated.scene.scans),
                  objects=(*updated.scene.objects[:-1],new_obj))
    return LayoutDocument(scene,updated.routes)
