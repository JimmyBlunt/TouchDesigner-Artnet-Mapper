// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION 6
// Prepared from a MadMapper material for TouchDesigner GLSL TOP.
out vec4 fragColor;
uniform vec4 uTDMaterial0; // phase, scale, width, frame zoom
uniform vec4 uTDMaterial1; // focus x, focus y, reserved, reserved
uniform vec4 uTDCoordinate; // mode, panel columns, panel rows, hybrid mix
#define uTDTime uTDMaterial0.x
#define TIME uTDTime
#define TIMEDELTA (1.0 / 60.0)
#define FRAMEINDEX int(uTDTime * 60.0)
#define RENDERSIZE uTDOutputInfo.res.zw
#define DATE vec4(0.0)
#define IMG_NORM_PIXEL(image, coord) texture(image, coord)
#define isf_FragNormCoord vUV.st
#define IMG_PIXEL(image, coord) texture(image, (coord) / vec2(textureSize(image, 0)))
#define IMG_SIZE(image) vec2(textureSize(image, 0))
#define texture2D texture

vec2 mapMadMapperUV(vec2 uv)
{
    vec2 focus = clamp(uTDMaterial1.xy, vec2(0.0), vec2(1.0));
    float zoom = clamp(uTDMaterial0.w, 0.25, 8.0);
    float scale = max(uTDMaterial0.y, 0.01) / 4.0;
    float width = clamp(uTDMaterial0.z, 0.01, 1.0);
    vec2 framed = focus + (uv - vec2(0.5)) / zoom;
    framed = focus + (framed - focus) * vec2(scale * (0.5 / width), scale);
    // True global/panel-local/hybrid selection happens in the downstream
    // per-LED sampler, where the physical panel ID is available.
    return framed;
}

uniform vec4 uMMParam000; // native input: mat_zoom
float mat_zoom = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_reverse
bool mat_reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_offset
float mat_offset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_strob
float mat_strob = uMMParam005.x;
float mat_time = uTDTime * (mat_speed);












































































#ifdef GL_ES

#endif



#define PI 3.14159265359

float iTime = mat_time - mat_offset * 10;


vec3 colorA = vec3(0.149, 0.141, 0.912);
vec3 colorB = vec3(1.000, 0.833, 0.224);

vec2 circle1(vec2 pt) {
    return vec2(abs(pt.x) + abs(pt.y), 0.8);
}

vec2 circle2(vec2 pt) {
    return vec2(length(pt), 0.4);
}

vec2 wave1(vec2 pt) {
    float r = length(pt);
    return vec2(0.5 * sin(r * 100.0) + 0.5, 0.5);
}

vec2 wave2(vec2 pt) {
    float r = abs(pt.x) + abs(pt.y);
    return vec2(0.5 * sin(r * 50.0) + 0.5, 0.5);
}

vec4 materialColorForPixel(vec2 texCoord) {

    

    vec2 pt = texCoord - vec2(0.5);
    pt *= mat_zoom;

    float t = iTime * 2.0;
    float idx = floor(mod(t, 4.0));

    vec2 f = vec2(0.0);
    vec2 g = vec2(0.0);
    float r = smoothstep(0.2, 0.8, mod(t, 1.0));

    if (idx == 0.0) {
        f = circle1(pt);
        g = circle2(pt);
    } else if (idx == 1.0) {
        f = circle2(pt);
        g = wave1(pt);
    } else if (idx == 2.0) {
        f = wave1(pt);
        g = wave2(pt);
    } else if (idx == 3.0) {
        f = wave2(pt);
        g = circle1(pt);
    }

    vec2 h = mix(f, g, r);
    float gray = step(h.x, h.y);

    vec3 color = mix(colorA, colorB, gray);

    return vec4(color, 1.0 );

}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
