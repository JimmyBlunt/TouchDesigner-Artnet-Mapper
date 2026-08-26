// PixelblazeMapper Core Effects
// TouchDesigner GLSL TOP / GLSL 4.30 core.
// The effect functions intentionally use plain GLSL so they can be wrapped
// for MadMapper/ISF without depending on TouchDesigner nodes.

out vec4 fragColor;

uniform vec4 uParams0; // effect, time, scale, width
uniform vec4 uParams1; // coordinate mode, intensity, contrast, trail
uniform vec4 uParams2; // direction, rotation degrees, seed, transition
uniform vec4 uParams3; // panel columns, panel rows, hybrid mix, density
uniform vec4 uColorA;
uniform vec4 uColorB;

const float PI = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;

float hash11(float p)
{
    p = fract(p * 0.1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}

float hash21(vec2 p)
{
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p)
{
    float n = hash21(p);
    return vec2(n, hash11(n + 19.19));
}

float valueNoise(vec2 p)
{
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(hash21(i), hash21(i + vec2(1.0, 0.0)), u.x),
        mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), u.x),
        u.y
    );
}

float fbm(vec2 p)
{
    float sum = 0.0;
    float amp = 0.5;
    mat2 octaveRotation = mat2(0.80, 0.60, -0.60, 0.80);
    for (int i = 0; i < 5; ++i) {
        sum += amp * valueNoise(p);
        p = octaveRotation * p * 2.03 + 13.7;
        amp *= 0.5;
    }
    return sum;
}

vec2 rotateAroundCenter(vec2 uv, float angle)
{
    float c = cos(angle);
    float s = sin(angle);
    return mat2(c, -s, s, c) * (uv - 0.5) + 0.5;
}

vec2 coordinateSpace(vec2 uv)
{
    // The downstream per-index sampler owns coordinate selection because it
    // knows the real middle/upper/lower/rear panel ID.  A 2D material shader
    // cannot infer those physical boundaries from its render-canvas UV.
    return uv;
}

float wrappedDistance(float a, float b)
{
    float d = abs(a - b);
    return min(d, 1.0 - d);
}

float voronoiDistance(vec2 p)
{
    vec2 cell = floor(p);
    vec2 local = fract(p);
    float nearest = 10.0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            vec2 offset = vec2(float(x), float(y));
            vec2 point = hash22(cell + offset + uParams2.z * 17.0);
            point = 0.5 + 0.42 * sin(uParams0.y * 0.55 + TAU * point);
            nearest = min(nearest, length(offset + point - local));
        }
    }
    return nearest;
}

float fluidNoise(vec2 uv)
{
    vec2 p = uv * max(uParams0.z, 0.1);
    float t = uParams0.y * 0.18;
    vec2 q = vec2(fbm(p + vec2(0.0, t)), fbm(p + vec2(5.2, -t * 0.8)));
    vec2 r = vec2(
        fbm(p + 3.6 * q + vec2(1.7, 9.2) + t),
        fbm(p + 3.6 * q + vec2(8.3, 2.8) - t)
    );
    return fbm(p + 4.2 * r);
}

float blobby(vec2 uv)
{
    vec2 p = uv;
    float field = 0.0;
    float radius = mix(0.08, 0.28, clamp(uParams0.w, 0.0, 1.0));
    for (int i = 0; i < 7; ++i) {
        float fi = float(i);
        vec2 base = hash22(vec2(fi + uParams2.z * 13.0, fi * 2.17));
        vec2 center = 0.5 + 0.38 * sin(TAU * base + uParams0.y * vec2(0.21 + fi * 0.013, 0.17 + fi * 0.009));
        float d = length(p - center);
        field += (radius * radius) / max(d * d, 0.003);
    }
    return smoothstep(2.0, 4.5, field);
}

float spatialPulse(vec2 uv)
{
    float angle = uParams2.x * TAU;
    vec2 direction = vec2(cos(angle), sin(angle));
    float projected = dot(uv - 0.5, direction) + 0.5;
    float head = fract(uParams0.y * 0.22);
    float d = wrappedDistance(fract(projected), head);
    float width = mix(0.015, 0.30, clamp(uParams0.w, 0.0, 1.0));
    float core = exp(-pow(d / width, 2.0) * 4.0);
    float ripple = 0.5 + 0.5 * sin((projected - head) * TAU * max(uParams0.z, 1.0));
    return clamp(core + ripple * core * 0.35, 0.0, 1.0);
}

float cometTails(vec2 uv)
{
    float angle = uParams2.x * TAU;
    vec2 p = rotateAroundCenter(uv, -angle);
    float value = 0.0;
    float trail = mix(0.03, 0.48, clamp(uParams1.w, 0.0, 1.0));
    for (int i = 0; i < 7; ++i) {
        float fi = float(i);
        vec2 rnd = hash22(vec2(fi + 4.0, uParams2.z * 31.0 + fi));
        float speed = mix(0.035, 0.12, rnd.x);
        float head = fract(rnd.x + uParams0.y * speed);
        float behind = mod(head - p.x + 1.0, 1.0);
        float cross = abs(p.y - rnd.y);
        float tailShape = exp(-behind / trail) * exp(-cross * cross / 0.0035);
        float headShape = exp(-behind * behind / 0.0015 - cross * cross / 0.0015);
        value += tailShape * 0.55 + headShape;
    }
    return clamp(value, 0.0, 1.0);
}

float arcs(vec2 uv)
{
    vec2 center = 0.5 + 0.16 * vec2(sin(uParams0.y * 0.21), cos(uParams0.y * 0.17));
    float radius = length(uv - center);
    float arcAngle = atan(uv.y - center.y, uv.x - center.x);
    float rings = 0.5 + 0.5 * sin(radius * max(uParams0.z, 1.0) * 28.0 - uParams0.y * 2.2);
    float gate = smoothstep(-0.35, 0.25, sin(arcAngle * 2.0 + uParams0.y * 0.3));
    float edge = mix(0.35, 0.75, clamp(uParams0.w, 0.0, 1.0));
    return smoothstep(edge, min(edge + 0.18, 0.98), rings) * gate;
}

float noisyBarcode(vec2 uv)
{
    float count = max(10.0, floor(max(uParams0.z, 1.0) * 14.0));
    float column = floor(uv.x * count + uParams0.y * 1.7);
    float band = floor(uv.y * 10.0 - uParams0.y * 0.8);
    float bar = hash21(vec2(column, floor(uParams0.y * 2.0) + uParams2.z * 19.0));
    float dropout = hash21(vec2(column * 0.37, band));
    float threshold = mix(0.25, 0.78, clamp(uParams0.w, 0.0, 1.0));
    return step(threshold, bar) * mix(0.25, 1.0, step(0.18, dropout));
}

float particles(vec2 uv)
{
    float value = 0.0;
    float density = clamp(uParams3.w, 0.25, 2.0);
    float trail = mix(0.01, 0.22, clamp(uParams1.w, 0.0, 1.0));
    for (int i = 0; i < 28; ++i) {
        float fi = float(i);
        vec2 rnd = hash22(vec2(fi + uParams2.z * 23.0, fi * 1.31));
        float activeParticle = step(fi, 14.0 * density);
        vec2 pos = vec2(rnd.x, fract(rnd.y + uParams0.y * mix(0.018, 0.075, hash11(fi + 5.0))));
        vec2 d = uv - pos;
        d.x = min(abs(d.x), 1.0 - abs(d.x));
        float head = exp(-dot(d, d) / 0.00085);
        float behind = mod(pos.y - uv.y + 1.0, 1.0);
        float tailShape = exp(-behind / trail) * exp(-d.x * d.x / 0.0012);
        value += activeParticle * (head + 0.35 * tailShape);
    }
    return clamp(value, 0.0, 1.0);
}

float badTV(vec2 uv)
{
    float frame = floor(uParams0.y * 24.0);
    float line = floor(uv.y * 150.0);
    float lineNoise = hash21(vec2(line, frame + uParams2.z * 41.0));
    float broadBand = hash21(vec2(floor(uv.y * 12.0), floor(frame * 0.17)));
    float snow = hash21(floor(uv * vec2(320.0, 180.0)) + frame);
    float scan = 0.72 + 0.28 * sin(uv.y * 720.0);
    float tear = step(0.88, broadBand) * (0.5 + 0.5 * sin((uv.x + lineNoise) * 60.0));
    return clamp((0.28 * snow + 0.72 * lineNoise) * scan + tear, 0.0, 1.0);
}

float plasma(vec2 uv)
{
    vec2 p = (uv - 0.5) * max(uParams0.z, 0.1);
    float t = uParams0.y * 0.65;
    float waves = sin(p.x * 2.1 + t);
    waves += sin(p.y * 2.7 - t * 1.17);
    waves += sin((p.x + p.y) * 1.8 + t * 0.73);
    waves += sin(length(p + vec2(sin(t * 0.3), cos(t * 0.27))) * 3.5 - t * 1.4);
    return 0.5 + 0.125 * waves;
}

float fire(vec2 uv)
{
    float scale = max(uParams0.z, 0.1);
    float t = uParams0.y * 0.55;
    vec2 p = vec2(uv.x * scale, uv.y * scale * 0.72);
    float coarse = fbm(p + vec2(0.0, -t));
    float detail = fbm(p * 2.15 + vec2(coarse * 2.4, -t * 1.63));
    float flame = (1.10 - uv.y) + coarse * 0.48 + detail * 0.30;
    float edge = mix(0.62, 1.02, clamp(uParams0.w, 0.0, 1.0));
    return smoothstep(edge - 0.28, edge + 0.20, flame);
}

float aurora(vec2 uv)
{
    float scale = max(uParams0.z, 0.1);
    float t = uParams0.y * 0.24;
    float warp = fbm(vec2(uv.x * scale * 0.72 + t, uv.y * 1.4));
    float curtain = 0.5 + 0.16 * sin(uv.x * scale * 2.8 + t * 2.3 + warp * 5.0);
    float width = mix(0.035, 0.20, clamp(uParams0.w, 0.0, 1.0));
    float ribbon = exp(-pow(abs(uv.y - curtain) / width, 1.45));
    float rays = 0.58 + 0.42 * pow(0.5 + 0.5 * sin(uv.x * scale * 14.0 + warp * 7.0), 2.0);
    return clamp(ribbon * rays + ribbon * ribbon * 0.35, 0.0, 1.0);
}

float oceanWaves(vec2 uv)
{
    float scale = max(uParams0.z, 0.1);
    float t = uParams0.y * 0.42;
    float distortion = fbm(uv * vec2(scale * 0.7, scale * 1.3) + vec2(t * 0.28, -t * 0.16));
    float phase = uv.y * scale * TAU + sin(uv.x * scale * 3.1 + t) * 1.25;
    phase += distortion * 4.0 - t * 2.2;
    float crest = 0.5 + 0.5 * sin(phase);
    float sharpness = mix(1.2, 5.0, clamp(uParams0.w, 0.0, 1.0));
    return pow(clamp(crest, 0.0, 1.0), sharpness);
}

float rippleRings(vec2 uv)
{
    float value = 0.0;
    float scale = max(uParams0.z, 0.1);
    float width = mix(0.015, 0.11, clamp(uParams0.w, 0.0, 1.0));
    for (int i = 0; i < 3; ++i) {
        float fi = float(i);
        vec2 center = 0.18 + 0.64 * hash22(vec2(fi + uParams2.z * 11.0, fi * 7.31));
        float radius = fract(uParams0.y * (0.10 + fi * 0.018) + fi * 0.37);
        float d = abs(fract(length(uv - center) * scale * 0.42) - radius);
        d = min(d, 1.0 - d);
        value += exp(-d * d / max(width * width, 0.0001));
    }
    return clamp(value, 0.0, 1.0);
}

float kaleidoscope(vec2 uv)
{
    vec2 p = uv - 0.5;
    float segments = max(3.0, floor(max(uParams0.z, 1.0)));
    float angle = atan(p.y, p.x) + uParams0.y * 0.18;
    float wedge = TAU / segments;
    angle = abs(mod(angle + 0.5 * wedge, wedge) - 0.5 * wedge);
    vec2 folded = vec2(cos(angle), sin(angle)) * length(p) * max(uParams0.z, 1.0);
    float pattern = fbm(folded * 2.8 + vec2(uParams0.y * 0.12, -uParams0.y * 0.09));
    pattern += 0.35 * sin(folded.x * 8.0 - folded.y * 5.0 + uParams0.y);
    return clamp(pattern, 0.0, 1.0);
}

float tunnel(vec2 uv)
{
    vec2 p = uv - 0.5;
    float radius = max(length(p), 0.012);
    float angle = atan(p.y, p.x) / TAU;
    float depth = 0.18 / radius + uParams0.y * 0.18;
    float scale = max(uParams0.z, 1.0);
    float rings = 0.5 + 0.5 * sin(depth * scale * TAU);
    float spokes = 0.5 + 0.5 * sin((angle * floor(scale + 3.0) + depth * 0.13) * TAU);
    float width = mix(0.25, 0.78, clamp(uParams0.w, 0.0, 1.0));
    return smoothstep(width, min(width + 0.18, 0.98), rings * 0.72 + spokes * 0.28);
}

float matrixRain(vec2 uv)
{
    float columns = max(6.0, floor(max(uParams0.z, 1.0) * 2.5));
    float column = floor(uv.x * columns);
    float rnd = hash11(column + uParams2.z * 37.0);
    float speed = mix(0.10, 0.34, rnd);
    float head = fract(rnd * 3.7 - uParams0.y * speed);
    float behind = mod(uv.y - head + 1.0, 1.0);
    float trail = mix(0.08, 0.55, clamp(uParams1.w, 0.0, 1.0));
    float glyphRow = floor(uv.y * columns * 1.4);
    float glyph = step(0.36, hash21(vec2(column, glyphRow + floor(uParams0.y * 7.0))));
    float headGlow = exp(-behind * behind / 0.0018);
    return clamp(glyph * exp(-behind / trail) * 0.78 + headGlow, 0.0, 1.0);
}

float twinkleSparkle(vec2 uv)
{
    float grid = max(4.0, floor(max(uParams0.z, 1.0) * 2.0));
    vec2 cell = floor(uv * grid);
    vec2 local = fract(uv * grid) - 0.5;
    float rnd = hash21(cell + uParams2.z * 29.0);
    float density = clamp(uParams3.w, 0.25, 2.0);
    float sparkEnabled = step(1.0 - 0.12 * density, rnd);
    float phase = fract(uParams0.y * mix(0.18, 0.75, rnd) + rnd * 9.0);
    float pulse = pow(0.5 + 0.5 * sin(phase * TAU), 7.0);
    float size = mix(0.06, 0.25, clamp(uParams0.w, 0.0, 1.0));
    float star = exp(-abs(local.x * local.y) / max(size * size * 0.18, 0.0001));
    star *= exp(-length(local) / max(size, 0.01));
    return clamp(sparkEnabled * pulse * star * 2.0, 0.0, 1.0);
}

float scanner(vec2 uv)
{
    float angle = uParams2.x * TAU;
    vec2 direction = vec2(cos(angle), sin(angle));
    float projected = dot(uv - 0.5, direction) + 0.5;
    float head = 0.5 + 0.5 * sin(uParams0.y * 0.72);
    float delta = projected - head;
    float width = mix(0.008, 0.12, clamp(uParams0.w, 0.0, 1.0));
    float core = exp(-delta * delta / max(width * width, 0.00001));
    float trailSide = step(0.0, -delta);
    float trail = trailSide * exp(delta / mix(0.04, 0.52, clamp(uParams1.w, 0.0, 1.0)));
    return clamp(core + trail * 0.42, 0.0, 1.0);
}

// Stateless approximation: layered domain-warped bands evoke a Gray-Scott
// field while remaining portable to hosts without feedback buffers.
float reactionDiffusion(vec2 uv)
{
    float scale = max(uParams0.z, 0.1);
    vec2 p = uv * scale;
    float t = uParams0.y * 0.08;
    vec2 warp = vec2(fbm(p * 0.55 + vec2(t, 3.1)), fbm(p * 0.55 + vec2(7.4, -t)));
    float fieldA = fbm(p + (warp - 0.5) * 4.2);
    float fieldB = fbm(p * 1.75 - (warp - 0.5) * 2.8 + vec2(-t, t));
    float bands = abs(fieldA - fieldB);
    float threshold = mix(0.055, 0.28, clamp(uParams0.w, 0.0, 1.0));
    return 1.0 - smoothstep(threshold, threshold + 0.10, bands);
}

float geometricGridMorph(vec2 uv)
{
    float scale = max(uParams0.z, 1.0);
    vec2 grid = fract(uv * scale) - 0.5;
    float phase = 0.5 + 0.5 * sin(uParams0.y * 0.52);
    float squareDistance = max(abs(grid.x), abs(grid.y));
    float circleDistance = length(grid) * 0.82;
    float shapeDistance = mix(squareDistance, circleDistance, phase);
    float radius = mix(0.16, 0.43, clamp(uParams0.w, 0.0, 1.0));
    float edgeWidth = max(fwidth(shapeDistance) * 2.0, 0.008);
    float outline = 1.0 - smoothstep(edgeWidth, edgeWidth * 2.5, abs(shapeDistance - radius));
    float checker = step(0.5, hash21(floor(uv * scale) + floor(uParams0.y * 0.22)));
    return outline * mix(0.42, 1.0, checker);
}

vec3 colorize(float value)
{
    float contrast = max(uParams1.z, 0.01);
    float shaped = clamp((value - 0.5) * contrast + 0.5, 0.0, 1.0);
    return mix(uColorB.rgb, uColorA.rgb, shaped) * max(uParams1.y, 0.0);
}

void main()
{
    vec2 sourceUV = vUV.st;
    vec2 uv = coordinateSpace(sourceUV);
    uv = rotateAroundCenter(uv, radians(uParams2.y));

    int effect = int(floor(uParams0.x + 0.5));
    float value = 0.0;
    vec3 color = vec3(0.0);

    if (effect == 0) {
        color = uColorA.rgb * max(uParams1.y, 0.0);
    } else if (effect == 1) {
        float direction = dot(uv - 0.5, vec2(cos(uParams2.x * TAU), sin(uParams2.x * TAU)));
        value = 0.5 + 0.5 * sin(direction * max(uParams0.z, 0.1) * TAU - uParams0.y);
        color = colorize(value);
    } else if (effect == 2) {
        float stripe = fract((uv.x + uv.y) * max(uParams0.z, 0.1) - uParams0.y * 0.18);
        float edge = max(fwidth(stripe) * 1.5, 0.002);
        value = 1.0 - smoothstep(clamp(uParams0.w, 0.01, 0.99) - edge, clamp(uParams0.w, 0.01, 0.99) + edge, stripe);
        color = colorize(value);
    } else if (effect == 3) {
        value = fluidNoise(uv);
        color = colorize(value);
    } else if (effect == 4) {
        float d = voronoiDistance(uv * max(uParams0.z, 0.1));
        value = 1.0 - smoothstep(mix(0.12, 0.48, clamp(uParams0.w, 0.0, 1.0)), 0.75, d);
        color = colorize(value);
    } else if (effect == 5) {
        value = blobby(uv);
        color = colorize(value);
    } else if (effect == 6) {
        value = spatialPulse(uv);
        color = colorize(value);
    } else if (effect == 7) {
        value = cometTails(uv);
        color = colorize(value);
    } else if (effect == 8) {
        value = arcs(uv);
        color = colorize(value);
    } else if (effect == 9) {
        value = noisyBarcode(uv);
        color = colorize(value);
    } else if (effect == 10) {
        value = particles(uv);
        color = colorize(value);
    } else if (effect == 11) {
        value = badTV(uv);
        float chroma = hash21(vec2(floor(uv.y * 90.0), floor(uParams0.y * 18.0)));
        color = colorize(value) * mix(vec3(0.65, 1.0, 1.25), vec3(1.3, 0.65, 1.0), chroma);
    } else if (effect == 12) {
        vec3 source = texture(sTD2DInputs[0], sourceUV).rgb;
        float dissolve = fbm(uv * max(uParams0.z, 0.1) + vec2(uParams0.y * 0.08, -uParams0.y * 0.05));
        float progress = clamp(uParams2.w, 0.0, 1.0);
        float mask = smoothstep(progress - 0.12, progress + 0.12, 1.0 - dissolve);
        vec3 target = colorize(fluidNoise(uv));
        color = mix(source, target, mask) * max(uParams1.y, 0.0);
    } else if (effect == 13) {
        value = plasma(uv);
        color = colorize(value);
    } else if (effect == 14) {
        value = fire(uv);
        color = mix(uColorB.rgb * 0.18, uColorA.rgb, value) * value * max(uParams1.y, 0.0);
    } else if (effect == 15) {
        value = aurora(uv);
        color = colorize(value) * (0.42 + 0.85 * value);
    } else if (effect == 16) {
        value = oceanWaves(uv);
        color = colorize(value);
    } else if (effect == 17) {
        value = rippleRings(uv);
        color = colorize(value);
    } else if (effect == 18) {
        value = kaleidoscope(uv);
        color = colorize(value);
    } else if (effect == 19) {
        value = tunnel(uv);
        color = colorize(value);
    } else if (effect == 20) {
        value = matrixRain(uv);
        color = mix(uColorB.rgb * 0.08, uColorA.rgb, value) * value * max(uParams1.y, 0.0);
    } else if (effect == 21) {
        value = twinkleSparkle(uv);
        color = colorize(value);
    } else if (effect == 22) {
        value = scanner(uv);
        color = colorize(value);
    } else if (effect == 23) {
        value = reactionDiffusion(uv);
        color = colorize(value);
    } else if (effect == 24) {
        value = geometricGridMorph(uv);
        color = colorize(value);
    } else {
        color = vec3(0.0);
    }

    fragColor = TDOutputSwizzle(vec4(max(color, vec3(0.0)), 1.0));
}
