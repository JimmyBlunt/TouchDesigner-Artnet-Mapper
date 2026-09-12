"""Offline audit only: TD fixture producer records do not prove visible frames."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path


def stats(values):
    values = sorted(values)
    if not values:
        return None
    def percentile(p):
        x = (len(values) - 1) * p
        a = int(x)
        b = min(a + 1, len(values) - 1)
        return values[a] + (values[b] - values[a]) * (x - a)
    return dict(count=len(values), minimum=values[0], mean=statistics.mean(values),
                median=percentile(.5), p95=percentile(.95), p99=percentile(.99),
                maximum=values[-1], population_stdev=statistics.pstdev(values))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    folder = args.run
    run = json.loads((folder / 'run.json').read_text(encoding='utf-8-sig'))
    rows = [json.loads(line) for line in (folder / 'submitted-frames.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    assert all(row['accepted'] for row in rows)
    assert all(b['time'] > a['time'] for a, b in zip(rows, rows[1:]))
    out = dict(schema=1, inputs={name: digest(folder / name) for name in ['run.json', 'submitted-frames.jsonl']},
               script_sha256=digest(Path(__file__)), logged_submissions=len(rows), phases=[],
               limitations=[
                   'Times are fixture step start before source cook/native pack/queue, not socket send timestamps.',
                   'accepted=true means native sender counter advanced; external worker may replace the batch.',
                   'Hold durations refer to logged producer identities, not electrical or optical LED hold durations.',
                   'Worker totals contain no per-ID or per-phase send trace; visible IDs/FPS require video.',
                   'An ID absent from this producer log could not be delivered by this fixture; an ID present may still be dropped downstream.',
                   'Temporary Script CHOP replaces effect source: arbitrary production effect render cost is outside scope.'
               ])
    for phase in run['phases']:
        if not phase['name'].startswith('measure_'):
            continue
        selected = [row for row in rows if row['phase'] == phase['name']]
        fps = phase['fps']
        expected = int(phase['duration_requested'] * fps)
        assert len(selected) == phase['submitted']
        assert all(row['id'] == int((row['time'] - phase['planned_start']) * fps) % 4096 for row in selected)
        assert all(b['id'] >= a['id'] for a, b in zip(selected, selected[1:]))
        groups = []
        for row in selected:
            if not groups or groups[-1]['id'] != row['id']:
                groups.append(dict(id=row['id'], first_time=row['time'], last_time=row['time'], submissions=1))
            else:
                groups[-1]['last_time'] = row['time']
                groups[-1]['submissions'] += 1
        for i, group in enumerate(groups):
            group['span_first_to_last_submission_ms'] = (group['last_time'] - group['first_time']) * 1000
            group['first_to_next_different_id_ms'] = ((groups[i + 1]['first_time'] - group['first_time']) * 1000
                                                    if i + 1 < len(groups) else None)
        present = {row['id'] for row in selected}
        missing = sorted(set(range(expected)) - present)
        intervals = [(b['time'] - a['time']) * 1000 for a, b in zip(selected, selected[1:])]
        holds = [g['first_to_next_different_id_ms'] for g in groups[:-1]]
        changes = [dict(previous_id=a['id'], next_id=b['id'], gap_size=b['id'] - a['id'] - 1,
                        previous_time=a['last_time'], next_time=b['first_time'],
                        between_submissions_ms=(b['first_time'] - a['last_time']) * 1000)
                   for a, b in zip(groups, groups[1:]) if b['id'] - a['id'] > 1]
        out['phases'].append(dict(name=phase['name'], planned_start=phase['planned_start'],
            planned_duration_seconds=phase['duration_requested'], content_fps_requested=fps,
            transport_fps_requested=run['transport_fps'], native_submissions=len(selected),
            native_submissions_per_planned_second=len(selected) / phase['duration_requested'],
            expected_id_count=expected, distinct_id_count=len(present),
            distinct_ids_per_planned_second=len(present) / phase['duration_requested'],
            repeated_id_submissions=len(selected) - len(present), first_id=selected[0]['id'], last_id=selected[-1]['id'],
            missing_ids=missing, internal_missing_ids=[x for x in missing if selected[0]['id'] < x < selected[-1]['id']],
            id_gap_events=changes, step_start_interarrival_ms=stats(intervals),
            first_submission_after_planned_id_boundary_ms=stats([(g['first_time'] - phase['planned_start'] - g['id'] / fps) * 1000 for g in groups]),
            producer_first_to_next_different_id_ms=stats(holds),
            producer_change_interval_minus_one_content_period_ms=stats([h - 1000 / fps for h in holds]),
            step_start_interarrival_over_1_content_period=sum(x > 1000 / fps for x in intervals),
            step_start_interarrival_over_2_content_periods=sum(x > 2000 / fps for x in intervals),
            id_submission_trace=groups))
    long_gaps = [dict(phase_before=a['phase'], phase_after=b['phase'], start=a['time'], end=b['time'],
                     duration_ms=(b['time'] - a['time']) * 1000)
                 for a, b in zip(rows, rows[1:]) if b['time'] - a['time'] > .09]
    out['global_step_start_gaps_over_90ms'] = long_gaps
    out['long_gap_start_spacing_seconds'] = stats([b['start'] - a['start'] for a, b in zip(long_gaps, long_gaps[1:])])
    out['long_gap_periodicity_note'] = 'Near-12.8-second repetition in producer records is observed, cause is not established by these logs.'
    native = run['sender_final']
    worker = run['worker_final']
    out['native_sender_final_telemetry'] = native['telemetry']
    out['worker_final'] = worker
    out['worker_accounting'] = dict(
        final_worker_submitted_equals_log=worker['submitted_batches'] == len(rows),
        native_send_count_equals_log=native['telemetry']['send_count'] == len(rows),
        packets_per_sent_batch=worker['sent_packets'] / worker['sent_batches'],
        submitted_minus_sent_minus_stale_minus_rejected=worker['submitted_batches'] - worker['sent_batches'] - worker['stale_batches'] - worker['rejected_batches'],
        note='One batch not classified as sent/stale/rejected at requested stop; do not label it a network loss.',
        native_transport_snapshot_lags_final_worker=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'sender-audit.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    compact = [{k: v for k, v in p.items() if k != 'id_submission_trace'} for p in out['phases']]
    print(json.dumps(compact, indent=2))


if __name__ == '__main__':
    main()
