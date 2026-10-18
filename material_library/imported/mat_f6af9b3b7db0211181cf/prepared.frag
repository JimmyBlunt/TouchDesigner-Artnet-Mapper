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

float iTime = mat_time - mat_offset * 10;



float map(float value, float beforeMin, float beforeMax, float afterMin, float afterMax) {
    return afterMin + (afterMax - afterMin) * ((value - beforeMin) / (beforeMax - beforeMin));
}

float box(vec2 _st, vec2 _size){
    _size = vec2(0.5) - _size * 0.5;  
    vec2 uv = step(_size, _st);
    uv *= step(_size, vec2(1.0) - _st);
    return uv.x * uv.y;
}

float exposeInOut(float t) {
    if (t == 0.0) {
        return 0.0;

    } else if (t == 1.0) {
        return 1.0;

    } else if ((t /= 0.5) < 1.0) {
        return 0.5 * pow(2.0, 10.0 * (t - 1.0));

    } else {
        return 0.5 * (-pow(2.0, -10.0 * --t) + 2.0);
    }
}

float ease(float t) {
    return exposeInOut(t);
}

mat2 rotate2d(float _angle){
    return mat2(cos(_angle), -sin(_angle),  sin(_angle), cos(_angle));
}

vec4 materialColorForPixel( vec2 texCoord ) {
    

    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;

    uv *= rotate2d(iTime * 0.2);

    vec2 scaledUv = uv * 10.0;
    vec2 repeatedUv = fract(scaledUv);

    float len = length(uv);
    float s = sin((iTime + len) * 10.0);
    float  r = 0.4 * s;

    float b = box(repeatedUv, vec2(r));
    vec3 color = vec3(b ,0.0, 0.1);

    if (b >= 1.0) {
        float t = map(sin(floor(iTime * 5.0) + ease(fract(iTime * 5.0))), -1.0, 1.0, 0.3, 1.0);
        color = vec3(0.5, t * 0.5, t);
    }
    return vec4(color, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
