"""Temporarily isolate output groups; restore exact runtime config in finally."""
import copy
import json
import sys
import time
import urllib.request
from controller_black_benchmark_20260912 import BASE, ROOT, get, run


def apply(value):
    req = urllib.request.Request(BASE + '/api/config', data=json.dumps(value).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=15))


def isolate(original, ids):
    value = copy.deepcopy(original)
    count, universes = 0, 0
    for output in value['outputs']:
        output['enabled'] = output['id'] in ids
        output['startPixel'] = count
        if output['enabled']:
            count += output['pixelCount']
            universes += (output['pixelCount'] + 169) // 170
    value.update(pixelCount=count, universeCount=universes)
    return value


if __name__ == '__main__':
    original = get('/api/config')
    folder = ROOT / 'docs/controller-performance-20260912'
    report = {'original': original, 'profiles': []}
    try:
        profiles = [
            ('external-five-outputs', {0,1,2,3,4}, [(15,0),(30,0),(15,.5),(30,.5),(15,1),(30,1)]),
            ('external-one-203', {0}, [(30,0),(30,.5)]),
            ('external-one-880', {2}, [(30,0),(30,.5),(30,1)]),
            ('external-three-a', {0,1,2}, [(30,.5),(30,1)]),
            ('external-two-b', {3,4}, [(30,.5),(30,1)]),
        ]
        for label, ids, cases in profiles:
            candidate = isolate(original, ids)
            result = apply(candidate)
            assert get('/api/config') == candidate, (label,result)
            report['profiles'].append({'label':label,'config':candidate})
            print('PROFILE '+label, flush=True)
            run(label, cases, duration=6)
    finally:
        apply(original)
        report['restored'] = get('/api/config') == original
        (folder/'profile-restoration.json').write_text(json.dumps(report,indent=2))
        assert report['restored'], 'Runtime configuration restoration failed'
        print('Original controller configuration restored',flush=True)
