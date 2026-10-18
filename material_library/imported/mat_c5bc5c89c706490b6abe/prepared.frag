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



float PI = 3.1415926535;
float sections = 3.0;

float atan2(in float y, in float x) {
    return x == 0.0 ? sign(y) * PI / 2.0 : atan(y, x);
}

bool belongs(float iTime, vec2 uv, float near, float far) {
    near += sin(uv.x - iTime * 8.0) / 50.0;
    far += cos(uv.y - iTime * 8.0) / 50.0;
    vec2 center = vec2(0.5, 0.5) * mat_zoom;
    vec2 xy = uv - center;

    float dist = distance(xy, vec2(0.0, 0.0));
    float angle = mod(atan2(xy.y, xy.x) + iTime * 2.5 + sin(iTime * 4.0) / 1.0, PI * 2.0);
    float oddity = mod(angle / (2.0 * PI) * sections * 2.0, 2.0);
    if (dist > near && dist < far && floor(mod(oddity, 2.0)) == 0.0) {
        return true;
    } else {
        return false;
    }
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    
    

    vec2 UV = fragCoord;

    UV *= mat_zoom;

    

    if (belongs(iTime, UV, 0.2, 0.25) || belongs(iTime + 0.5, UV, 0.3, 0.35) || belongs(iTime + 1.0, UV, 0.4, 0.45)) {
        fragColor = vec4(1.0, 1.0, 1.0, 1.0);
    } else {
        fragColor = vec4(0.0, 0.0, 0.0, 0.0);
    }
}



vec4 materialColorForPixel(vec2 texCoord)
{
    
    
    vec4 color = vec4(0);
    mainImage(color, texCoord);
    return color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
