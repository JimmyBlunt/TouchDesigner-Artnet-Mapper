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

uniform vec4 uMMParam000; // native input: frequency_x
int frequency_x = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: frequency_y
int frequency_y = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: width_x
float width_x = uMMParam002.x;
uniform vec4 uMMParam003; // native input: width_y
float width_y = uMMParam003.x;
uniform vec4 uMMParam004; // native input: speed_x
float speed_x = uMMParam004.x;
uniform vec4 uMMParam005; // native input: speed_y
float speed_y = uMMParam005.x;
uniform vec4 uMMParam006; // native input: Smooth
float Smooth = uMMParam006.x;
float animation_time_x = uTDTime * (speed_x);
float animation_time_y = uTDTime * (speed_y);















































































#define M_PI 3.1415926535897932384626433832795

vec4 materialColorForPixel(vec2 texCoord)
{
    float Sx = 0.9999 - Smooth*pow(width_x/10,2);
    float Sy = 0.9999 - Smooth*pow(width_y/10,2); 
    float x = smoothstep(Sx,1.0,width_x*sin(frequency_x*2*M_PI*(texCoord.x + animation_time_x/2)));
    float y = smoothstep(Sy,1.0,width_y*sin(frequency_y*2*M_PI*(texCoord.y + animation_time_y/2)));

    vec3 color = vec3(x+y,x+y,x+y);

    return vec4(color,1);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
