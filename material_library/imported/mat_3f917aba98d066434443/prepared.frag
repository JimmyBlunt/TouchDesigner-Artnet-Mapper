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












































































float pbmRepairNonzero(float v) { return v == 0.0 ? 1e-6 : v; }
vec3 pbmRepairNonzero(vec3 v) { return vec3(pbmRepairNonzero(v.x), pbmRepairNonzero(v.y), pbmRepairNonzero(v.z)); }
vec3 pbmRepairNormal(vec3 v) { return dot(v,v) == 0.0 ? vec3(0.0) : normalize(v); }
vec2 pbmRepairNormal(vec2 v) { return dot(v,v) == 0.0 ? vec2(0.0) : normalize(v); }






#ifdef GL_ES

#endif

float iTime = mat_time - mat_offset;

const float PI = 3.14159;
const float N = 90.0;

float random(float n) {
    return fract(abs(sin(n * 55.753) * 367.34));
}

vec4 materialColorForPixel( vec2 texCoord ){
    

    vec2 st = texCoord - vec2(0.5);

    st *= 8.0;

    st *= 2.0 * mat_zoom;

    float brightness = 0.0;
    vec3 baseColor = vec3(0.0, 0.1, 0.3);
    float speed = mat_time * 1.0;

    for (float i = 0.0;  i < N;  i++) {
        brightness += 0.002 / pbmRepairNonzero(abs(sin(PI * st.x) * sin(PI * st.y) * sin(PI * speed + random(floor(st.x )) + random(floor(st.y)))));
    }

    return vec4(baseColor * brightness, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
