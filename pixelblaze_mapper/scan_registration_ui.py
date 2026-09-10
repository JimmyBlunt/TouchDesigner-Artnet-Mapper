"""TouchDesigner review helper for explicit, undoable partial scan replacement."""
import json
from pathlib import Path

from .layout_scene import SceneError
from .scan_registration import prepare_registration, apply_registration
from .scan_result_review import compact_ids
from .scan_session import ScanSession

OWNER = '/project1/guided_scan'
LAYOUT = '/project1/layout_scene_editor'


def _fields(owner):
    from .build_scan_session_ui import field_text, parse_indices
    panel = owner.op('registration_panel')
    read = lambda name: field_text(panel.op(name + '/string'))
    return {'fit_source_ids': list(parse_indices(read('fit_ids'))),
            'check_source_ids': list(parse_indices(read('check_ids'))),
            'accepted_source_ids': list(parse_indices(read('accepted_ids'))),
            'max_error': float(read('max_error'))}


def summary(proposal):
    result = 'PASS: anchor deviations are within your limit' if proposal['passed'] else 'BLOCKED: anchor deviation exceeds your limit'
    errors = list(zip(proposal['fit_source_ids'], proposal['fit_errors'])) + list(zip(proposal['check_source_ids'], proposal['check_errors']))
    return ('%s\nFit RMS %.6g | independent check RMS %.6g | worst %.6g | limit %.6g\n'
            'Uniform scale %.6g | rotation %s | translation %s\n'
            'Replace %d LEDs: %s\nKeep other selected LEDs: %s. All fixed anchors stay unchanged.\n'
            'Anchor deviations: %s\nReview point comparison, then confirm one undoable draft edit.') % (
        result, proposal['fit_rms'], proposal['check_rms'], proposal['worst_error'], proposal['max_error'],
        proposal['transform']['scale'][0], ', '.join('%.3g' % v for v in proposal['transform']['rotation_degrees']),
        ', '.join('%.3g' % v for v in proposal['transform']['translation']),
        len(proposal['accepted_source_ids']), compact_ids(proposal['accepted_source_ids']),
        compact_ids(proposal['preserved_selected_source_ids']),
        ', '.join('%s: %.4g' % pair for pair in errors[:8]) + (' ...' if len(errors) > 8 else ''))


def _comparison(before, after, accepted):
    old = {led.source_index: point for led, point in before.scene.world_points()}
    new = {led.source_index: point for led, point in after.scene.world_points()}
    rows = ['source_id\told_x\told_y\told_z\tnew_x\tnew_y\tnew_z\tworld_displacement']
    for index in accepted:
        distance = sum((a-b)**2 for a, b in zip(old[index], new[index])) ** .5
        rows.append('\t'.join([str(index)] + ['%.9g' % v for v in (*old[index], *new[index], distance)]))
    return '\n'.join(rows)


def act(op, action, confirm=None):
    from . import layout_scene_td as layout
    owner = op(OWNER)
    panel = owner.op('registration_panel')
    try:
        if action == 'back':
            owner.op('review_panel').openViewer()
            return True
        if action == 'details':
            owner.op('registration_evidence').openViewer()
            return True
        if action == 'comparison':
            owner.op('registration_comparison').openViewer()
            return True
        value = owner.fetch('session', None)
        review = owner.fetch('result_review', None)
        if value is None or review is None:
            raise SceneError('Stage a Layout object and open its completed 3D result first')
        state = ScanSession.from_dict(value)
        editor = layout.editor(op(LAYOUT))
        if editor.preview is not None:
            raise SceneError('Finish or cancel the current Layout drag before registration')
        if action == 'open':
            from hashlib import sha256
            from .scan_workflow_ux import compact_indices
            key = (review['path'], review['sha256'], state.session_id,
                   sha256(json.dumps(value, sort_keys=True).encode()).hexdigest())
            if owner.fetch('registration_context', None) != list(key):
                lookup = {t.led_id: t.source_index for t in state.targets}
                anchors = [lookup[i] for i in state.anchor_ids if lookup[i] in review['ids']]
                accepted = [lookup[i] for i in state.selected_ids if lookup[i] in review['ids']]
                for name, ids in (('fit_ids', anchors[:-1]), ('check_ids', anchors[-1:]), ('accepted_ids', accepted)):
                    panel.op(name + '/string').text = compact_indices(ids)
                owner.store('registration_context', list(key))
                owner.store('registration_proposal', None)
                panel.op('summary').par.text = 'Calculate alignment to see fit and independent verification errors. Missing selected points are excluded from the proposed replacement; review the exact IDs.'
                owner.op('registration_evidence').text = ''
                owner.op('registration_comparison').text = ''
            panel.openViewer()
            if len(state.anchor_ids) < 4:
                panel.op('status').par.text = 'NEEDS ANCHORS: stage a partial scan with at least four fixed measured LEDs outside the replacement selection, then capture overlapping views. Three fit the alignment; one independently checks it.'
            else:
                panel.op('status').par.text = 'Source IDs refer to the staged scan. Confirm fixed fit/check anchors, replacement IDs and an appropriate maximum deviation.'
            return True
        fields = _fields(owner)
        if action == 'calculate':
            proposal = prepare_registration(editor.current, state, review, **fields)
            owner.store('registration_proposal', proposal)
            owner.op('registration_evidence').text = json.dumps(proposal, indent=2, allow_nan=False)
            panel.op('summary').par.text = summary(proposal)
            if proposal['passed']:
                after = apply_registration(editor.current, state, proposal)
                owner.op('registration_comparison').text = _comparison(editor.current, after, proposal['accepted_source_ids'])
            else:
                owner.op('registration_comparison').text = 'Blocked: improve anchors/views or review the deviation limit; no draft replacement prepared.'
            panel.op('status').par.text = 'Calculated only. Check the independent error and point comparison before replacing the listed LEDs.'
            return True
        if action == 'replace':
            proposal = owner.fetch('registration_proposal', None)
            if not proposal or any(proposal[key] != fields[key] for key in fields):
                raise SceneError('Inputs changed or no result was calculated; calculate and review alignment again')
            before = editor.current
            after = apply_registration(before, state, proposal)
            if confirm is None:
                raise SceneError('Explicit draft replacement confirmation is required')
            message = ('Replace ONLY source IDs %s in the current draft?\n'
                       '%d LEDs; independent check RMS %.6g; maximum deviation %.6g (limit %.6g).\n'
                       'Fixed anchors and all other LEDs keep their current coordinates and identities. '
                       'Original scans remain archived. Undo is available in Layout. Live output remains unchanged.') % (
                compact_ids(proposal['accepted_source_ids']), len(proposal['accepted_source_ids']),
                proposal['check_rms'], proposal['worst_error'], proposal['max_error'])
            if confirm(message) is not True:
                return False
            # Recheck mutable TD state and disk evidence after the modal review.
            if editor.current != before or owner.fetch('session', None) != value or _fields(owner) != fields:
                raise SceneError('Layout, session or inputs changed during confirmation; review again')
            after = apply_registration(editor.current, state, proposal)
            editor.commit(after)
            editor.select(proposal['object_id'])
            owner.store('registration_proposal', None)
            target = op(LAYOUT)
            from . import layout_fixture_td
            layout_fixture_td.action(target, 'view3d', None, None)
            layout.refresh(target)
            layout.frame_view(target, reset=True)
            layout.status(target, 'REGISTERED PARTIAL SCAN | %d draft LEDs replaced; anchors and other LEDs retained; Undo available' % len(proposal['accepted_source_ids']))
            target.op('ui_panel').openViewer()
            panel.op('status').par.text = 'Draft replacement complete. Original data and registration evidence are archived with the new scan. Undo in Layout.'
            return True
        raise SceneError('Unknown registration action')
    except Exception as error:
        panel.op('status').par.text = 'BLOCKED | ' + str(error)
        if action == 'open':
            panel.openViewer()
        return False


def install(ns):
    """Build an independent review panel, never calculate or commit on install."""
    import td
    from .scan_library_ui import style_button
    scope = dict(ns, __name__='scan_registration_helpers')
    path = Path(__file__).resolve().parent / 'build_gico_port_config_ui.py'
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)
    node, panel, text, field, button, click = (scope[k] for k in ('_node', '_panel', '_text', '_field', '_button', '_click'))
    owner = ns['op'](OWNER)
    review = owner.op('review_panel')
    advanced = review.op('btn_review_advanced')
    if advanced is not None:
        advanced.par.w = 465
        style_button(advanced)
    entry = button(review, 'btn_registration', 'ALIGN / PARTIAL REPLACE', 515, 375, 465)
    style_button(entry, 'primary')
    command = "__import__('pixelblaze_mapper.scan_registration_ui',fromlist=['act']).act(op, %r%s)"
    click(owner, 'click_registration_open', entry, command % ('open', ''))
    p = panel(node(owner, ns.get('containerCOMP', td.containerCOMP), 'registration_panel'), 0, 0, 1040, 790, 10)
    p.viewer = True
    text(p, 'title', 'ALIGN KNOWN LED IDs / REPLACE SELECTED DRAFT POINTS', 20, 735, 1000, 40, 19)
    text(p, 'help', '1 Choose fixed anchors: at least 3 across a surface, plus a separate verification LED.\n2 Enter the maximum acceptable deviation in the target object coordinate units.\n3 Calculate, review independent errors and point comparison, then replace the listed draft LEDs.', 20, 640, 1000, 88, 13)
    for name, label, default, y in (
        ('fit_ids', 'FIT ANCHOR SOURCE IDs (fixed LEDs from the staged scan)', '', 583),
        ('check_ids', 'INDEPENDENT CHECK SOURCE IDs (fixed LEDs excluded from the fit)', '', 519),
        ('accepted_ids', 'REPLACE THESE SOURCE IDs ONLY (reconstructed selected LEDs)', '', 455),
        ('max_error', 'MAXIMUM FIT / CHECK DEVIATION (original object coordinate units)', '0.01', 391)):
        text(p, name + '_label', label, 20, y + 32, 1000, 27, 11)
        previous = p.op(name + '/string')
        field(p, name, previous.text if previous is not None else default, 20, y, 1000)
    text(p, 'summary', 'Calculate alignment to review errors. No nearest-point matching or automatic replacement.', 20, 160, 1000, 210, 12)
    text(p, 'status', 'Draft only. Three fit anchors and an independent check anchor are required; all remain unchanged.', 20, 70, 1000, 75, 12)
    for name, label, x, width in (('calculate', 'CALCULATE', 20, 170), ('comparison', 'COMPARE POINTS', 205, 195),
                                  ('details', 'EVIDENCE', 415, 150), ('replace', 'REPLACE IN DRAFT', 580, 260), ('back', 'BACK', 855, 165)):
        control = button(p, 'btn_' + name, label, x, 20, width)
        style_button(control, 'replace' if name == 'replace' else 'primary' if name == 'calculate' else 'secondary')
        confirmation = ", lambda message: ui.messageBox('Replace reviewed draft LEDs?', message, buttons=['Cancel', 'Replace draft']) == 1" if name == 'replace' else ''
        click(owner, 'click_registration_' + name, control, command % (name, confirmation))
    for name in ('registration_evidence', 'registration_comparison'):
        node(owner, ns.get('textDAT', td.textDAT), name)
    return {'panel': p.path, 'draft_changed': False, 'output_started': False}
