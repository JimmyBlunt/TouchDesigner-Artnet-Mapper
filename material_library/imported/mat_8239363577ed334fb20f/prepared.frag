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



#define PI 3.14159265358
#define TWO_PI 6.28318530718


vec3 colorA = vec3(0.149, 0.141, 0.912);
vec3 colorB = vec3(1.000, 0.833, 0.224);

vec3 rgb2hsb( in vec3 c ){
    vec4 K = vec4(0.0, -1.0 / .0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz),
                 vec4(c.gb, K.xy),
                 step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r),
                 vec4(c.r, p.yzx),
                 step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)),
                d / (q.x + e),
                q.x);
}



vec3 hsb2rgb( in vec3 c ){
    vec3 rgb = clamp(abs(mod(c.x*6.0+vec3(0.0,4.0,2.0),
                             6.0)-3.0)-1.0,
                     0.0,
                     1.0 );
    rgb = rgb*rgb*(3.0-2.0*rgb);
    return c.z * mix(vec3(1.0), rgb, c.y);
}


vec2 coord(in vec2 p) {
    p = p / RENDERSIZE.xy;
    
    if (RENDERSIZE.x > RENDERSIZE.y) {
        p.x *= RENDERSIZE.x / RENDERSIZE.y;
        p.x += (RENDERSIZE.y - RENDERSIZE.x) / RENDERSIZE.y / 2.0;
    } else {
        p.y *= RENDERSIZE.y / RENDERSIZE.x;
        p.y += (RENDERSIZE.x - RENDERSIZE.y) / RENDERSIZE.x / 2.0;
    }
    
    p -= 0.5;
    p *= vec2(-1.0, 1.0);
    return p;
}





mat2 rot(in float angle) {
    return mat2(cos(angle), -sin(angle),
                sin(angle),  cos(angle));
}

float wave(in vec2 pt, in float f, in float v) {
    float r = length(pt);
    float a = atan(pt.y, pt.x);
    return sin(r * TWO_PI * f - v * iTime);
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;

    vec2 st = uv;

    
    float rx = 1.0;
    
    
    


    vec2 pt = st;

    float f = 10.0 * abs(sin(0.1 * iTime));
    float v = 10.0;
    float g = wave(pt, f, v);

    for (float k = 0.0; k < 8.0; k++) {
        float t = PI / 4.0 * k;
        vec2 offset = 0.5 * vec2(cos(t), sin(t));
        g += wave(pt + offset, f, v);
    }

    g *= 0.5;
    g = step(g, 0.0);

    vec3 rgb = mix(colorA, colorB, g);

    return vec4(rgb, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
