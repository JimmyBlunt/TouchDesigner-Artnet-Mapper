"""Run run(op, td) inside TouchDesigner; isolated GPU/LED parity acceptance."""
from uuid import uuid4


def run(resolve, tdmodule):
    import numpy as np
    from pixelblaze_mapper.integrate_live_show import TRANSITION_SHADER
    from pixelblaze_mapper.show_renderer import render_frame, TRANSITION_INFO
    root = resolve('/project1').create(tdmodule.baseCOMP, 'overlap_test_'+uuid4().hex[:8])
    results = []
    try:
        colors = ((.8, .2, .1), (.1, .4, .9))
        sources = []
        for index, color in enumerate(colors):
            top = root.create(tdmodule.constantTOP, 'color_'+str(index))
            top.par.resolutionw, top.par.resolutionh = 4, 4
            for component, value in zip('rgb', color):
                getattr(top.par, 'color'+component).val = value
            sources.append(top)
        shader = root.create(tdmodule.textDAT, 'shader')
        shader.text = TRANSITION_SHADER
        mixer = root.create(tdmodule.glslTOP, 'mixer')
        mixer.par.pixeldat = shader.path
        mixer.par.outputresolution = 'custom'
        mixer.par.resolutionw, mixer.par.resolutionh = 4, 4
        for index, source in enumerate(sources):
            mixer.inputConnectors[index].connect(source)
        mixer.par.vec.sequence.numBlocks = 5
        def uniform(index, name, values):
            getattr(mixer.par, 'vec%dname' % index).val = name
            for suffix, value in zip('xyzw', values):
                getattr(mixer.par, 'vec%dvalue%s' % (index, suffix)).val = value
        uniform(2, 'uOverlapMode', (1, 0, 0, 0))
        for mode in ('crossfade', 'cut', 'fade_black', 'wipe', 'wipe_left', 'wipe_up', 'wipe_down'):
            number = next(i for i, item in enumerate(TRANSITION_INFO) if item[0] == mode)
            for gain_a, gain_b, brightness_a, brightness_b, blackout, tone in (
                (1, 0, .8, .3, False, None), (.5, .5, .8, .3, False, None),
                (0, 1, .8, .3, False, None), (1, 1, .8, .3, False, None),
                (.2, .3, .8, .3, False, (.7, 1.3)), (.5, .5, .8, .3, True, None)):
                uniform(0, 'uTransition', (number, .4, .9, int(blackout)))
                uniform(1, 'uOverlap', (gain_a, gain_b, brightness_a, brightness_b))
                uniform(3, 'uSlotToneA', (*tone, 1, 0) if tone else (1, 1, 0, 0))
                uniform(4, 'uSlotToneB', (1, 1, 0, 0))
                mixer.cook(force=True)
                assert not mixer.errors(), mixer.errors()
                actual = mixer.numpyArray(delayed=False)[1, 1, :3]
                # Read quantized input pixels rather than ideal decimal colors.
                a, b = [source.numpyArray(delayed=False)[1, 1, :3] for source in sources]
                expected = np.asarray(render_frame([[float(c)*255] for c in a], [[float(c)*255] for c in b],
                    u=[.375], v=[.375], transition=mode, output_b_mix=.4,
                    brightness=.9, blackout=blackout, targets_a=['all'], targets_b=['all'], source_groups=['middle'],
                    timing_mode='overlap', slot_a_gain=gain_a, slot_b_gain=gain_b,
                    slot_a_brightness=brightness_a, slot_b_brightness=brightness_b,
                    slot_a_tone=tone))[:, 0]/255
                error = float(np.max(np.abs(actual-expected)))
                assert np.isfinite(actual).all() and error < .009, (mode, actual.tolist(), expected.tolist(), error)
                results.append(dict(mode=mode, gains=[gain_a, gain_b], blackout=blackout, max_error=error))
        return dict(passed=True, cases=len(results), maximum_error=max(item['max_error'] for item in results), results=results)
    finally:
        root.destroy()
