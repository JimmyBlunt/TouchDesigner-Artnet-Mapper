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

const vec3 color_inside = vec3(0, 0, 0);
const vec3 color_outside = vec3(1, 1, 1);
const vec3 color_strip = vec3(1, 0, 0);


const float ANIMATION_SPEED = 1.0;
const float GRADIENT_FACTOR = 80.0;
const float DARKENING_FACTOR = 2.0;
const float PI = 3.1415926535897932384626433832795;

float cycleTime() {
    return mod(iTime * ANIMATION_SPEED, 1.0);
}

float radiusTranslation(float x) {
    return 1.0 / x;
}

float timeTranslation() {
    return cycleTime() * 2.0 * PI;
}

float mixFunction(float x) {
    return sin(radiusTranslation(x) + timeTranslation());
}

vec3 sharpMix(vec3 a, vec3 b, float x, float gf) {
    return mix(a, b, clamp(x * gf - gf / 2.0, 0.0, 1.0));
}

float gf(float radius) {
    return radius * GRADIENT_FACTOR;
}

vec3 color(float radius) {
    return sharpMix(color_inside, color_outside, mixFunction(radius), gf(radius)) * clamp(sqrt(radius * DARKENING_FACTOR), 0.0, 1.0);
}

vec4 materialColorForPixel( vec2 texCoord ) {
    
    

    vec2 pos = texCoord - vec2(0.5);
    pos *= mat_zoom;
    float radius = sqrt(pos.x * pos.x + pos.y * pos.y);

    return vec4(color(radius), 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
