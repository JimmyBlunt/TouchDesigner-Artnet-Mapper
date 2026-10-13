"""Reviewed repairs for pinned MadMapper sources with observed non-finite pixels.

This is not a general shader sanitizer. Both filename and normalized full-source
SHA256 must match a reviewed original; original files remain untouched. Changes
target individual undefined operations before they contaminate shading. No final
pixel replacement, NaN filtering, or blanket output clamping is performed.
GPU acceptance of these changes is separate from the offline regression tests.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceRepair:
    sha256: str
    reason: str
    replacements: tuple[tuple[str, str], ...]


# These guards alter only exactly singular denominators/zero-length normals.
# A small finite reciprocal at a bright singularity preserves the surrounding
# nonzero-domain calculation, unlike replacing contaminated output pixels.
_HELPERS = """
// Source-specific guards for reviewed singular operations.
float pbmRepairNonzero(float v) { return v == 0.0 ? 1e-6 : v; }
vec3 pbmRepairNonzero(vec3 v) { return vec3(pbmRepairNonzero(v.x), pbmRepairNonzero(v.y), pbmRepairNonzero(v.z)); }
vec3 pbmRepairNormal(vec3 v) { return dot(v,v) == 0.0 ? vec3(0.0) : normalize(v); }
vec2 pbmRepairNormal(vec2 v) { return dot(v,v) == 0.0 ? vec2(0.0) : normalize(v); }
"""

REPAIRS = {
    '_Tests.fs': SourceRepair(
        '7903f85496f5d8ac78b612523aef5e3365c8109cf38336411b361b5604a76328',
        'give the local arc implementation a distinct name before MadSDF expands its same-signature function', (
            ('arc(', 'pbmLocalArc('),
        )),
    '[recode]_Orbital_Wonky.fs': SourceRepair(
        'ddef4283698f6a20d6df313b116a15ddeaac38155b650fbd755f0fab348156df',
        'initialize the additive color accumulator and separate local noise values from their input names', (
            ('vec4 color;', 'vec4 color = vec4(0.0);'),
            ('vec2 noiseUV =', 'vec2 localNoiseUV ='),
            ('float noiseCircle =', 'float localNoiseCircle ='),
            ('float noiseStroke =', 'float localNoiseStroke ='),
            ('circle(noiseUV, circlesRadius) - noiseCircle', 'circle(localNoiseUV, circlesRadius) - localNoiseCircle'),
            ('circleDist, noiseStroke)', 'circleDist, localNoiseStroke)'),
            # noise() may be negative; GLSL pow has no negative-base domain,
            # including exponent 2. abs preserves the intended mathematical square.
            ('pow(noise(uv + mat_noise_time * 0.5 + i * noiseOffset * 0.1), 2)',
             'pow(abs(noise(uv + mat_noise_time * 0.5 + i * noiseOffset * 0.1)), 2)'),
        )),
    'Advanced Starfield.fs': SourceRepair(
        '37666ef87fa1996eba21f1bbf73976d8563e6c83abd94e653d861cf3102cf5a5',
        'remove self-shadowing colors; analytically cancel radDist in its ratio, including its zero limit', (
            ('vec3 tailColor = vec3(tailColor.rgb);', 'vec3 localTailColor = vec3(tailColor.rgb);'),
            ('vec3 nebulaColor = vec3(nebulaColor.rgb);', 'vec3 localNebulaColor = vec3(nebulaColor.rgb);'),
            ('float adist;', 'float radialRatio = distMode == 0 ? warp / pbmRepairNonzero(rad) : rad * warp;\n    float adist;'),
            ('adist = radDist / rad * warp;', 'adist = radDist * radialRatio;'),
            ('adist = radDist * rad * warp;', 'adist = radDist * radialRatio;'),
            ('mix(starColor, tailColor, adist / radDist)', 'mix(starColor, localTailColor, radialRatio)'),
            ('mix(color, nebulaColor,', 'mix(color, localNebulaColor,'),
            ('(2.2 / dist) * tailLengthAdjusted * adist / radDist / 50.0',
             '(2.2 / pbmRepairNonzero(dist)) * tailLengthAdjusted * radialRatio / 50.0'),
        )),
    'Burst.fs': SourceRepair(
        '463cfa28ca1969f5810911cd4db32adbaea9800ccba393aa1678174fe3fba150',
        'bound the exact frame-zero particle brightness singularity before blending', (
            ('explosionColour / fade', 'explosionColour / pbmRepairNonzero(fade)'),
        )),
    'Glass Candy.fs': SourceRepair(
        '510cfc0cf708017cdac87dfd311d2dcd55f5166fbb3817c61b605c5c0ddbdcb8',
        'handle zero surface gradients and roundoff below zero in diffuse square-root lighting', (
            ('return normalize(map(pos)-vec3(map(pos-noff.xyy), map(pos-noff.yxy), map(pos-noff.yyx)));',
             'return pbmRepairNormal(map(pos)-vec3(map(pos-noff.xyy), map(pos-noff.yxy), map(pos-noff.yyx)));'),
            ('pow(dot(normal, ray)*.5+.5, .5)', 'pow(max(dot(normal, ray)*.5+.5, 0.0), .5)'),
        )),
    'Glass Garden.fs': SourceRepair(
        '8b14f4e1b59b87abf6013ff01a9293eb64022c052c9395b5bacd3677d163e5e7',
        'omit the undefined zero-period grid layer and expand the fixed three-step coordinate loop to avoid GPU loop-carried length corruption', (
            ('for (float i = 0.; i < 3.; i++)', 'for (float i = 1.; i < 3.; i++)'),
            ('1.0 / abs(mod(st.xy, 0.732* i) * 10.)',
             '1.0 / vec2(pbmRepairNonzero(abs(mod(st.x, 0.732* i) * 10.)), pbmRepairNonzero(abs(mod(st.y, 0.732* i) * 10.)))'),
            # Preserve all three updates verbatim, including the length sample
            # BEFORE the last update. GPU probes found nonfinite loop-carried
            # len despite finite co; exact straight-line expansion fixes this.
            ('for (int i = 0; i < 3; i++) {\n'
             '        len = length(co);\n'
             '        co.x +=  sin(co.y + mat_time * 0.620)*0.;\n'
             '        co.y +=  cos(co.x + mat_time * 0.164)*0.1;\n'
             '    }',
             '\n    '.join(['len = length(co);\n'
                            '    co.x +=  sin(co.y + mat_time * 0.620)*0.;\n'
                            '    co.y +=  cos(co.x + mat_time * 0.164)*0.1;'] * 3)),
        )),
    'Holy Fractal.fs': SourceRepair(
        '152a750c438c4819ec1afc213702fd472e748600b1c718ce1cb63204cbdee235',
        'restrict radiance square root to its nonnegative domain', (
            ('sqrt(fc)', 'sqrt(max(fc, vec3(0.0)))'),
        )),
    'LEDWall.fs': SourceRepair(
        '81f98efba672c6d01d24c661f3a4614df2eadd0fdbb32df9742971a5f4bd8a0d',
        'bound exact sine-grid brightness singularities before multiplication by zero color channels', (
            ('/ abs(sin(PI * st.x) * sin(PI * st.y) * sin(PI * speed + random(floor(st.x )) + random(floor(st.y))))',
             '/ pbmRepairNonzero(abs(sin(PI * st.x) * sin(PI * st.y) * sin(PI * speed + random(floor(st.x )) + random(floor(st.y)))))'),
        )),
    'LEDWall2.fs': SourceRepair(
        '64b682ccb0fb16b7006d95a622e93ccc8c17b377c48a49066bf575d773acbb12',
        'bound exact sine-grid brightness singularities before multiplication by zero color channels', (
            ('/ abs(sin(PI * st.x) * sin(PI * st.y) * sin(PI * speed + floor(st.x ) + floor(st.y)))',
             '/ pbmRepairNonzero(abs(sin(PI * st.x) * sin(PI * st.y) * sin(PI * speed + floor(st.x ) + floor(st.y))))'),
        )),
    'Lignettes.fs': SourceRepair(
        '5e69769a1e0a08c3b2e5a871f8eef22a98db05ebfbf5ceb789b966e20ea71120',
        'handle the undefined normal of constant empty-space distance and the tunnel axis', (
            ('normalize(p.xz)', 'pbmRepairNormal(p.xz)'),
            ('return normalize(vec3(map(p+vec3(e,0,0))', 'return pbmRepairNormal(vec3(map(p+vec3(e,0,0))'),
        )),
    'Microcosm.fs': SourceRepair(
        '181c755d314491b9e0a85da2fd3fc9e22e1a543be0c148633f3ffab441dc1b78',
        'restrict cosine-derived radiance square roots to nonnegative values and handle zero dark-color normalization', (
            ('sqrt(out_color.rgb)', 'sqrt(max(out_color.rgb, vec3(0.0)))'),
            ('normalize(out_color.rgb)', 'pbmRepairNormal(out_color.rgb)'),
        )),
    'Noise Mold.fs': SourceRepair(
        'ec05af312e82d6a07d653162611082b163dfd71482e883cb151a733c7d42f335',
        'restrict the square root of overshooting interpolated noise to nonnegative radiance', (
            ('a = sqrt(a);', 'a = sqrt(max(a, 0.0));'),
        )),
    'Ocean Crystal.fs': SourceRepair(
        'bd07a21b5c4a8c31e56a821052324a1a7d641f7e11a460eb0ccaa2c5a68ca19e',
        'restrict fractional opacity power to nonnegative base and avoid unpremultiplication at zero alpha', (
            ('pow(-(pp.y-8.)*0.05,1.5)', 'pow(max(-(pp.y-8.)*0.05, 0.0),1.5)'),
            ('return fc/fc.a;', 'return fc.a == 0.0 ? vec4(0.0) : fc/fc.a;'),
        )),
    'Plasma_15.fs': SourceRepair(
        '2bff18be0435097966c28f8221bb6e0df679402009c0fa12da38c5daebab4648',
        'initialize the feedback length from the initial UV instead of reading an uninitialized value', (
            ('float len;', 'float len = length(uv);'),
        )),
    'Rainbow Ribbon.fs': SourceRepair(
        '5af12b6d2c820377c55fea456bfd211a38cf779e26f7dcfe90f6816749bc00ad',
        'bound the exact first-strand ID-zero reciprocal in coloring', (
            ('1./d.x', '1./pbmRepairNonzero(d.x)'),
        )),
    'Ripple Noise.fs': SourceRepair(
        '402adee879fbb7607d6b6a6a2400f21f61f7fd89113f4299a8978e04dc046d95',
        'bound reciprocal brightness where smoothstep deliberately returns exact zero', (
            ('color = light / color;', 'color = light / pbmRepairNonzero(color);'),
        )),
    'Spacetime Fracture.fs': SourceRepair(
        'd0d366f13652f7f881b7f56adb5b7f6699783edcdbc6e4e6c9dba4e803bfd7ff',
        'restrict fractional radiance powers after subtractive shape masks to nonnegative bases', (
            ('pow(col.x,1.5)', 'pow(max(col.x,0.0),1.5)'),
            ('pow(col.y,.9)', 'pow(max(col.y,0.0),.9)'),
            ('pow(col.z,3.5)', 'pow(max(col.z,0.0),3.5)'),
        )),
    'Sphere Lighting.fs': SourceRepair(
        '62782529ccd0eee3c60ed6af2cfad9d6ba287afb4b1b60c3a19773672e54bd96',
        'use the sphere equation directly, cover the outside disk, and restrict diffuse gamma to nonnegative illumination', (
            ('float sinAcosY = sin(acos(uv.y));\n    float zVal = sin(acos(uv.x/sinAcosY));\n    zVal = sqrt(1.-dot(uv.xy,U));',
             'float sphereDepth = 1.-dot(uv.xy,U);\n    if (sphereDepth < 0.0) return vec4(0.0);\n    float zVal = sqrt(sphereDepth);'),
            ('col = pow(col,vec3(2.2 / mat_power));', 'col = pow(max(col,vec3(0.0)),vec3(2.2 / mat_power));'),
        )),
    'Splotch Theory.fs': SourceRepair(
        'ce71059b78568a54ba7e037b7a57bbe100a8fd7f4308baceb68cde0ddd48c5b1',
        'sample the one-row waveform at its scalar horizontal coordinate and row center', (
            ('IMG_NORM_PIXEL(mat_audio, i)', 'IMG_NORM_PIXEL(mat_audio, vec2(i, 0.5))'),
        )),
    'warp.fs': SourceRepair(
        '4031fc1e9b37ca7f0a2c4be723a38d39c67a69a5af6b69975296b573bc63152e',
        'analytically cancel radDist in the starfield ratio, including its zero limit', (
            ('float adist = radDist / rad * warp;',
             'float radialRatio = warp / pbmRepairNonzero(rad);\n    float adist = radDist * radialRatio;'),
            ('(2.2 / dist) * cos(sin(TIME)) * adist / radDist / 50',
             '(2.2 / pbmRepairNonzero(dist)) * cos(sin(TIME)) * radialRatio / 50'),
        )),
}


def repair_source(path: str | Path, source: str) -> tuple[str, list[str]]:
    """Repair only a known complete original, before other adapter rewrites.

    Newline/BOM variations are accepted. Unknown/edited content is returned byte
    for byte unchanged. A second application is also unchanged and silent.
    """
    filename = str(path).replace('\\', '/').rsplit('/', 1)[-1]
    repair = REPAIRS.get(filename)
    if repair is None:
        return source, []
    normalized = source.lstrip('\ufeff').replace('\r\n', '\n').replace('\r', '\n')
    if hashlib.sha256(normalized.encode('utf-8')).hexdigest() != repair.sha256:
        return source, []
    if any(old not in normalized for old, _ in repair.replacements):
        # Fail closed if a reviewed literal and its source fingerprint disagree.
        return source, ['source repair skipped: expected expression absent in ' + filename]
    for old, new in repair.replacements:
        normalized = normalized.replace(old, new)
    if 'pbmRepair' in normalized:
        marker = normalized.find('*/') + 2
        normalized = normalized[:marker] + '\n' + _HELPERS + normalized[marker:]
    return normalized, ['source repair: %s: %s' % (filename, repair.reason)]
