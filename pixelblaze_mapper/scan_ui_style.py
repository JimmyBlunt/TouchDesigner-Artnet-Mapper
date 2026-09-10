"""Consistent native scan actions with readable click-through captions."""
from .scan_library_ui import style_button


def install(owner):
    primary = {'btn_prepare', 'btn_arm', 'btn_offline', 'btn_offline_start',
               'btn_offline_result', 'btn_review_add', 'btn_stage_capture',
               'btn_discover_views', 'btn_registration'}
    for name in ('ui_panel', 'review_panel', 'new_capture_panel'):
        panel = owner.op(name)
        if panel is None:
            continue
        for node in panel.children:
            if node.type != 'button':
                continue
            style_button(node, 'primary' if node.name in primary else 'secondary')
            if node.name in ('btn_stop', 'btn_offline_stop'):
                node.par.colorr, node.par.colorg, node.par.colorb = .8, .16, .15
