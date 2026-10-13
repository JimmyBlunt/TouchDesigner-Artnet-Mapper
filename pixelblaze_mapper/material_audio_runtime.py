"""Real-file waveform/FFT textures without speakers, microphone or fake audio.

File In CHOP decodes the configured track once; NumPy analyses windows of the
actual mono mix. Script TOP uploads SIZE x 1 float RGBA on demand. Waveform is
centred on 0.5 (ISF); FFT uses a 1024-sample Hann window, linear frequency bins and
peak aggregation when SIZE < 512. SIZE is clamped to MadMapper's 1..512 limit.

ADR uses attack/release exponential slew plus a decay peak tail, in seconds.
This is explicit compatibility behaviour: exact MadMapper FFT binning/ADR parity
has NOT been established. Deterministic audit seeks reset envelope history.
Source docs: derivative.ca/UserGuide/File_In_CHOP and /ScriptTOP%20Class;
github.com/madmappersoftware/MadMapper-Materials/blob/main/MaterialsDoc.md;
github.com/mrRay/ISF_Spec/blob/master/README.md.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import re

import numpy as np

CONFIG_PATH = Path(__file__).resolve().parents[1]/'config'/'material_audio.json'
OWNER_MARKER = 'pixelblaze_material_audio_v1'
FFT_SIZE = 1024
_decoded = {}  # Process-only cache; never store the music samples in a .toe.


def load_audio_config(config_path=None):
    path = Path(config_path) if config_path is not None else CONFIG_PATH
    try:
        config = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return dict(enabled=False, path=None, loop=True)
    if not isinstance(config, dict):
        raise ValueError('Audio configuration must be an object.')
    value = config.get('path')
    if not config.get('enabled', True) or not value:
        return dict(enabled=False, path=None, loop=bool(config.get('loop', True)))
    source = Path(value).expanduser()
    if not source.is_file():
        raise ValueError('Configured audio file does not exist: '+str(source))
    return dict(enabled=True, path=str(source.resolve()), loop=bool(config.get('loop', True)))


def configured_audio_path(config_path=None):
    """Explicit project-local source discovery for the offline adapter."""
    return load_audio_config(config_path)['path']


def resolve_setting(spec, key, default, parameters=None):
    value = spec.get(key, default)
    values = dict(spec.get('_parameter_values', {}))
    values.update(parameters or {})
    if isinstance(value, str):
        if value in values:
            value = values[value]
        else:
            try:
                value = float(value)
            except ValueError:
                raise ValueError('Unresolved audio %s parameter: %s' % (key, value)) from None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Audio %s must resolve to a finite numeric value.' % key)
    return float(value)


def audio_settings(spec, parameters=None):
    kind = str(spec.get('TYPE', '')).casefold()
    if kind not in ('audio', 'audiofft'):
        raise ValueError('Only real waveform/audioFFT textures are supported.')
    return dict(kind=kind, size=max(1, min(512, int(round(resolve_setting(spec, 'SIZE', 512, parameters))))),
                attack=max(0., resolve_setting(spec, 'ATTACK', 0., parameters)),
                decay=max(0., resolve_setting(spec, 'DECAY', 0., parameters)),
                release=max(0., resolve_setting(spec, 'RELEASE', 0., parameters)))


def sample_window(samples, rate, seconds, count=FFT_SIZE, loop=True):
    samples = np.asarray(samples, dtype=np.float32)
    if samples.ndim != 1 or not samples.size:
        raise ValueError('Audio decode must provide a nonempty mono signal.')
    if not math.isfinite(rate) or rate <= 0 or not math.isfinite(seconds):
        raise ValueError('Audio sample rate/time must be finite; rate must be positive.')
    start = int(math.floor(seconds*rate))
    indexes = start+np.arange(count, dtype=np.int64)
    if loop:
        output = samples[indexes % samples.size]
    else:
        output = np.zeros(count, dtype=np.float32)
        valid = (indexes >= 0) & (indexes < samples.size)
        output[valid] = samples[indexes[valid]]
    # Full decoded audio is validated once in _decode; avoid rescanning an
    # entire three-minute track every video frame for each material input.
    if not np.isfinite(output).all():
        raise ValueError('Audio window contains nonfinite samples.')
    return output


def analyse(samples, rate, seconds, spec, parameters=None):
    settings = audio_settings(spec, parameters)
    window = sample_window(samples, rate, seconds, loop=bool(spec.get('loop', True)))
    size = settings['size']
    if settings['kind'] == 'audio':
        # Real sampled waveform, represented around 0.5 per the ISF contract.
        values = np.interp(np.linspace(0, len(window)-1, size), np.arange(len(window)), window)
        values = np.clip(.5+.5*values, 0., 1.)
    else:
        hann = np.hanning(FFT_SIZE)
        magnitude = np.abs(np.fft.rfft(window*hann))[:512]*(2./hann.sum())
        values = np.asarray([np.max(band) for band in np.array_split(magnitude, size)])
        values = np.clip(values, 0., 1.)
    return values.astype(np.float32), settings


def smooth(values, previous, dt, settings):
    values = np.asarray(values, dtype=np.float32)
    if previous is None or np.shape(previous) != values.shape or dt < 0 or settings['kind'] != 'audiofft':
        return values.copy()
    previous = np.asarray(previous, dtype=np.float32)
    tau = np.where(values > previous, settings['attack'], settings['release'])
    factors = np.ones_like(values)
    nonzero = tau > 0
    factors[nonzero] = 1-np.exp(-max(0., dt)/tau[nonzero])
    output = previous+(values-previous)*factors
    if settings['decay'] > 0:
        output = np.maximum(output, previous*np.exp(-max(0., dt)/settings['decay']))
    return output.astype(np.float32)


def _decode(owner, path):
    source = Path(path)
    stat = source.stat()
    key = (str(source.resolve()), stat.st_mtime_ns, stat.st_size)
    if key in _decoded:
        return _decoded[key]
    from td import fileinCHOP
    decoder = owner.create(fileinCHOP, 'decode_file')
    try:
        decoder.par.file = str(source)
        decoder.par.timeslice = False
        decoder.cook(force=True)
        if decoder.errors():
            raise ValueError('Audio decode failed: '+str(decoder.errors()))
        raw = decoder.numpyArray()
        if raw is None or raw.ndim != 2 or not raw.shape[1]:
            raise ValueError('Audio decoder returned no samples.')
        mono = np.mean(raw, axis=0, dtype=np.float32)
        if not np.isfinite(mono).all():
            raise ValueError('Audio decoder returned nonfinite samples.')
        result = mono, float(decoder.rate)
        _decoded.clear()  # Bounded: keep the one selected track, not every import.
        _decoded[key] = result
        return result
    finally:
        decoder.destroy()


def _live_parameters(owner, spec):
    mapping = spec.get('_parameter_uniforms', {})
    if not mapping:
        return {}
    from td import op
    preview = op(owner.fetch('audio_preview_path'))
    if preview is None:
        raise ValueError('Audio texture preview no longer exists.')
    needed = {uniform: key for key, uniform in mapping.items()}
    values = {}
    for i in range(preview.par.vec.sequence.numBlocks):
        name = preview.par['vec%dname' % i].eval()
        if name in needed:
            values[needed[name]] = float(preview.par['vec%dvaluex' % i].eval())
    return values


def cook_audio_top(script_op, realtime_seconds):
    owner = script_op.parent()
    spec = owner.fetch('audio_spec')
    if owner.fetch('material_audio_owner') != OWNER_MARKER or not isinstance(spec, dict):
        raise ValueError('Unowned or unconfigured audio texture.')
    samples, rate = _decode(owner, spec['resolved_path'])
    forced = owner.fetch('audio_probe_time', None)
    seconds = float(forced if forced is not None else realtime_seconds-owner.fetch('audio_start_seconds', realtime_seconds))
    values, settings = analyse(samples, rate, seconds, spec, _live_parameters(owner, spec))
    previous = owner.fetch('audio_filter', None)
    last_time = owner.fetch('audio_last_time', seconds)
    values = smooth(values, previous, seconds-last_time, settings)
    owner.store('audio_filter', values)
    owner.store('audio_last_time', seconds)
    pixels = np.ones((1, len(values), 4), dtype=np.float32)
    pixels[0, :, :3] = values[:, None]
    script_op.copyNumpyArray(pixels)
    owner.store('audio_status', dict(source=spec['resolved_path'], rate=rate, samples=len(samples),
                duration=len(samples)/rate, position=seconds, loop=bool(spec.get('loop', True)),
                kind=settings['kind'], size=settings['size'], minimum=float(values.min()), maximum=float(values.max()),
                smoothing='Approximate ADR; exact MadMapper parity not verified'))


CALLBACKS = '''from pixelblaze_mapper.material_audio_runtime import cook_audio_top
def onCook(scriptOp):
    cook_audio_top(scriptOp, absTime.seconds)
def onGetCookLevel(scriptOp):
    return CookLevel.WHEN_USED
'''


def bind_audio_texture(preview, spec, index=0):
    """Return a same-network TOP; retain it and audio_component(TOP)."""
    from td import baseCOMP, textDAT, scriptTOP, selectTOP, absTime
    if type(index) is not int or index < 0:
        raise ValueError('Audio input index must be a nonnegative integer.')
    audio_settings(spec)
    source = Path(spec.get('resolved_path', ''))
    if not source.is_file():
        raise ValueError('A real configured audio file is required; no fallback source is generated.')
    name = preview.name+'_asset_'+str(index)+'_audio'
    if not re.fullmatch(r'[A-Za-z0-9_]+', name):
        raise ValueError('Unsafe audio component name.')
    parent = preview.parent()
    owner = parent.op(name)
    if owner is None:
        owner = parent.create(baseCOMP, name)
        owner.store('material_audio_owner', OWNER_MARKER)
    elif owner.fetch('material_audio_owner', None) != OWNER_MARKER:
        raise ValueError('Audio node name belongs to another component; refusing to overwrite it.')
    if preview.fetch('material_audio_source', None) != str(source):
        preview.store('material_audio_source', str(source))
        preview.store('material_audio_start_seconds', float(absTime.seconds))
    owner.store('audio_start_seconds', preview.fetch('material_audio_start_seconds'))
    previous_spec = owner.fetch('audio_spec', None)
    owner.store('audio_spec', deepcopy(spec))
    owner.store('audio_preview_path', preview.path)
    if previous_spec != spec:
        owner.store('audio_filter', None)
    callbacks = owner.op('callbacks')
    if callbacks is None:
        callbacks = owner.create(textDAT, 'callbacks')
    callbacks.text = CALLBACKS
    texture = owner.op('texture')
    if texture is None:
        texture = owner.create(scriptTOP, 'texture')
    texture.par.callbacks = callbacks.path
    texture.par.format = 'rgba32float'
    texture.viewer = False
    texture.cook(force=True)
    if texture.errors():
        raise ValueError('Audio texture failed: '+str(texture.errors()))
    # TOP wires cannot cross COMP network boundaries directly. A same-level
    # Select TOP explicitly exposes the owned inner Script TOP to the preview.
    output_name = name+'_out'
    output = parent.op(output_name)
    if output is None:
        output = parent.create(selectTOP, output_name)
        output.store('material_audio_component', name)
    elif output.fetch('material_audio_component', None) != name:
        raise ValueError('Audio output name is owned by another operator.')
    output.par.top = texture.path
    output.viewer = False
    output.cook(force=True)
    if output.errors():
        raise ValueError('Audio output reference failed: '+str(output.errors()))
    return output


def audio_component(output):
    """Resolve the owned COMP retained alongside an audio Select TOP."""
    name = output.fetch('material_audio_component', None)
    owner = output.parent().op(name) if name else None
    if owner is None or owner.fetch('material_audio_owner', None) != OWNER_MARKER:
        raise ValueError('Audio output has no owned analysis component.')
    return owner


def set_audio_probe_time(owner, seconds):
    """Seek only owned audio children; reset history for repeatable GPU audits."""
    if seconds is not None and (not isinstance(seconds, (int, float)) or not math.isfinite(seconds)):
        raise ValueError('Probe time must be finite or None (return to realtime).')
    count = 0
    children = list(owner.children)
    for node in children:
        if node.fetch('material_audio_owner', None) == OWNER_MARKER:
            node.store('audio_probe_time', seconds)
            node.store('audio_filter', None)
            texture = node.op('texture')
            if texture is not None:
                texture.cook(force=True)
                if texture.errors():
                    raise ValueError('Audio seek failed: '+str(texture.errors()))
            count += 1
        elif getattr(node, 'isCOMP', False):
            count += set_audio_probe_time(node, seconds)
    return count
