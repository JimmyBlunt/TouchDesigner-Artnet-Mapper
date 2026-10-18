"""MK2-owned desktop windows; TouchDesigner operations stay on the main thread."""
import json
from pathlib import Path
from time import monotonic


MATERIAL = '/project1/madmapper_player_controls/ui_panel'
SHOW_CONTROL = '/project1/show_control/control_panel'
SHOW_PREVIEW = '/project1/show_control/show_preview_out'
ROOT = '/project1/mk2_windows'


def monitor_pair(monitors, config):
    available = list(monitors)
    if not available:
        raise RuntimeError('Kein Bildschirm verfügbar.')
    primary = next((m for m in available if m.isPrimary), available[0])
    # Saved display names survive normal monitor enumeration order changes.
    sequencer = next((m for m in available if m.displayName == config.get('sequencer_monitor')), None)
    if sequencer is None:
        sequencer = next((m for m in available if 'HP Z24i' in m.description), None)
    if sequencer is None:
        sequencer = next((m for m in available if not m.isPrimary), primary)
    workspace = next((m for m in available if m.displayName == config.get('workspace_monitor')
                      and m.index != sequencer.index), None)
    if workspace is None:
        workspace = next((m for m in available if m.index != sequencer.index), sequencer)
    return sequencer, workspace


def browser_rect(monitor, monitors):
    primary = next((m for m in monitors if m.isPrimary), monitors[0])
    # TD uses bottom-up coordinates; Win32 uses primary-monitor top-left.
    return dict(x=int(monitor.left), y=int(primary.top-monitor.top),
                width=int(monitor.width), height=max(200, int(monitor.height)-48))


class WindowDirector:
    def __init__(self, resolve, tdmodule=None, *, sequencer=None, preview=None, clock=monotonic):
        self.resolve = resolve
        self.td = tdmodule or __import__('td')
        self.clock = clock
        self.project_dir = Path(self.td.project.folder)
        self.path = self.project_dir/'config'/'mk2_windows.json'
        self.config = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}
        if not isinstance(self.config, dict) or self.config.get('show_view', 'control') not in ('control', 'preview'):
            raise ValueError('Ungültige MK2-Fensterkonfiguration.')
        if sequencer is None:
            from .mk2_sequencer_window import SequencerWindow
            sequencer = SequencerWindow(self.project_dir)
        self.sequencer = sequencer
        self.preview = preview
        self.mode = None
        self.screen = None
        self.pending = None
        self.pending_since = 0
        self.shown_id = None
        self.loaded_id = None
        self.error = ''

    def _root(self):
        root = self.resolve(ROOT)
        return root if root is not None else self.resolve('/project1').create(self.td.baseCOMP, 'mk2_windows')

    def _close(self, role):
        window = self.resolve(ROOT+'/'+role)
        if window is not None and window.isOpen:
            window.par.winclose.pulse()

    def _open(self, role, target, monitor, title):
        content = self.resolve(target)
        if content is None:
            raise RuntimeError('Fensterinhalt fehlt: '+target)
        root = self._root()
        window = root.op(role)
        if window is None:
            window = root.create(self.td.windowCOMP, role)
        width = min(int(getattr(content, 'width', 1180)), int(monitor.width)-40)
        height = min(int(getattr(content, 'height', 800)), int(monitor.height)-80)
        if target == SHOW_PREVIEW:
            width, height = int(monitor.width)-80, int(monitor.height)-120
        values = dict(winop=target, title=title, justifyoffsetto='specifydisplay',
                      display=monitor.index, justifyh='center', justifyv='center',
                      winoffsetx=0, winoffsety=0, dpiscaling='native', size='custom',
                      winw=max(200, width), winh=max(200, height), borders=True,
                      bordersinsize=False, alwaysontop=False, interact=True,
                      ignoretaskbar=False, cursorvisible='alwaysvisible', closeescape=True)
        changed = any(str(getattr(window.par, key).eval()) != str(value) for key, value in values.items())
        if changed and window.isOpen:
            window.par.winclose.pulse()
        for key, value in values.items():
            getattr(window.par, key).val = value
        window.par.winopen.pulse()
        return window

    def show_mode(self, mode):
        if mode not in ('material', 'show'):
            raise ValueError('Unbekannter Fenstermodus.')
        sequencer, workspace = monitor_pair(self.td.monitors, self.config)
        self.mode, self.screen = mode, 'home'
        self.pending = self.loaded_id = self.shown_id = None
        if mode == 'material':
            self.sequencer.hide()
            self._close('show')
            self._open('material', MATERIAL, workspace, 'MK2 Material Player')
        else:
            self._close('material')
            target = SHOW_PREVIEW if self.config.get('show_view') == 'preview' else SHOW_CONTROL
            self._open('show', target, workspace, 'MK2 Show')
            # Bridge normally already exists; do not launch an unrelated browser.
            from . import show_timeline_ui
            if getattr(self.td, '__name__', '') == 'td':
                show_timeline_ui.launch(open_browser=False)
            self.sequencer.show(browser_rect(sequencer, list(self.td.monitors)))
        self.error = ''

    def _preview(self, item):
        self._root()
        if self.preview is None:
            from .mk2_material_preview import MaterialPreview
            self.preview = MaterialPreview(self.resolve, self.td)
        target = self.preview.select(item['id'], item)
        _, workspace = monitor_pair(self.td.monitors, self.config)
        self._open('material', target, workspace, 'MK2 Materialauswahl')
        self.shown_id = item['id']
        self.pending = None

    def material_loaded(self, identifier):
        if self.mode != 'material':
            return
        _, workspace = monitor_pair(self.td.monitors, self.config)
        self._open('material', MATERIAL, workspace, 'MK2 Material Player')
        self.loaded_id = identifier
        self.pending = None

    def observe(self, view, images):
        """Debounce selection previews; never compile for every wheel detent."""
        self.mode = view['mode']
        previous, self.screen = self.screen, view['screen']
        if self.mode != 'material':
            self.pending = None
            return
        if self.screen == 'browse':
            items = view.get('browse_items', [])
            if not items:
                self.pending = None
                return
            item = dict(items[min(view['browse_index'], len(items)-1)])
            item['preview_path'] = images.get(item.get('image'))
            if previous not in ('browse', 'categories', 'browse_assign', 'confirm_overwrite'):
                self.loaded_id = None
                self._preview(item)
            elif item['id'] not in (self.shown_id, self.loaded_id):
                if self.pending is None or self.pending['id'] != item['id']:
                    self.pending, self.pending_since = item, self.clock()
                elif self.clock()-self.pending_since >= .3:
                    self._preview(item)
            else:
                self.pending = None
        elif self.screen == 'home' and previous in ('browse', 'categories', 'browse_assign', 'confirm_overwrite'):
            self.pending = None
            _, workspace = monitor_pair(self.td.monitors, self.config)
            self._open('material', MATERIAL, workspace, 'MK2 Material Player')

    def status(self):
        return dict(mode=self.mode, error=self.error or self.sequencer.error,
                    sequencer=self.sequencer.status, selected_preview=self.shown_id)
