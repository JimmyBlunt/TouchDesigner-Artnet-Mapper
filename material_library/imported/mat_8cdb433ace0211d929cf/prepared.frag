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
uniform vec4 uMMParam001; // native input: mat_shift
vec2 mat_shift = uMMParam001.xy;
uniform vec4 uMMParam002; // native input: direction
vec2 direction = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_reverse
bool mat_reverse = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: mat_speed
float mat_speed = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_offset
float mat_offset = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_strob
float mat_strob = uMMParam007.x;
float mat_time = uTDTime * (mat_speed);






























































































#ifdef GL_ES

#endif

float iTime = mat_time - mat_offset * 10;




vec4 materialColorForPixel(vec2 texCoord)
{
    vec3 c1 = vec3(1.0, 1.0, 0.0);
    vec3 cb = vec3(0.0);
    vec3 c3 = vec3(0.25, 1.0, 1.0);

    

    

    vec2 new_center = mat_shift;
    new_center.x = 1. - new_center.x;

    vec2 uv = 4. * mat_zoom * (texCoord - vec2(0.5)) - iTime * direction + vec2(0.5) + new_center;

    

    vec2 b = 8.0 * fract(uv);
    int x = int(b.x);
    int y = int(b.y);

    vec3 g = cb;

    if (y == 0)
    {
        g = x == 3 || x == 5 ? c1 : cb;
    }
    else if (y == 1)
    {
        g = x == 0 ? cb : x == 5 ? c1 : c3;
    }
    else if (y==2 || y==6)
    {
        g = x == 0 || x == 2 || x == 4 || x == 6 ? cb : (x == 1 || x == 7) ? c3 : c1;
    }
    else if (y == 3)
    {
        g = x==4 ? cb : x==7 ? c3 : c1;
    }
    else if (y == 4)
    {
        g = x==1||x==7 ? c3 : cb;
    }
    else if (y == 5)
    {
        g = x==4 ? cb : x==1 ? c3 : c1;
    }
    else if (y == 7)
    {
        g = x == 0 ? cb : x == 3 ? c1 : c3;
    }

    float sh = 0.0;
    vec3 d = 0.8 * g;

    if (y==3&&x==6 || y==5&&x==0 || y==1&&x==4 || y==7&&x==2)
    {
        g = mix(g, d, smoothstep(sh, 1.0, fract(b.x)));
    }
    else if (y==3&&x==0 || y==5&&x==2 || y==1&&x==6 || y==7&&x==4)
    {
        g = mix(g, d, smoothstep(1.0-sh, 0.0, fract(b.x)));
    }
    else if (y==0&&x==3 || y==6&&x==5 || y==2&&x==1 || y==4&&x==7)
    {
        g = mix(g, d, smoothstep(sh, 1.0, fract(b.y)));
    }
    else if (y==2&&x==3 || y==0&&x==5 || y==4&&x==1 || y==6&&x==7)
    {
        g = mix(g, d, smoothstep(1.0-sh, 0.0, fract(b.y)));
    }


    return vec4(g, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
