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

uniform vec4 uMMParam000; // native input: color
vec4 color = uMMParam000;
uniform vec4 uMMParam001; // native input: mat_zoom
float mat_zoom = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_reverse
bool mat_reverse = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_speed
float mat_speed = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_offset
float mat_offset = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_strob
float mat_strob = uMMParam006.x;
uniform vec4 uMMParam007; // native input: rot_center
vec2 rot_center = uMMParam007.xy;
uniform vec4 uMMParam008; // native input: rot_separate
bool rot_separate = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: rot_bpm_sync
bool rot_bpm_sync = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: rot_reverse
bool rot_reverse = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: rot_speed
float rot_speed = uMMParam011.x;
uniform vec4 uMMParam012; // native input: rot_offset
float rot_offset = uMMParam012.x;
uniform vec4 uMMParam013; // native input: rot_strob
float rot_strob = uMMParam013.x;
float mat_time = uTDTime * (mat_speed);
float rot_time = uTDTime * (rot_speed);





















































































































































vec3 iResolution = vec3(RENDERSIZE, 1.);
float iTime = mat_time - mat_offset;

float rotTime;


#define SIZE 100.
#define PI 3.14159265359
#define PI2 1.570796326795



mat2 rot(float a)
{
    return mat2(cos(a),-sin(a),
                sin(a),cos(a));
}
float in_out_cubic(float t)
{
    t *= 2.;
    if (t < 1.) return .5*t*t*t;
    t-=2.;
    return .5*(t*t*t+2.);
}
vec4 mainImage(vec2 uv_orig)
{
    

    if (rot_separate) {
        rotTime = rot_time - rot_offset;

    } else {
        rotTime = iTime;
    }

    vec2 R2 = iResolution.xy - rot_center;

    float t = fract(iTime / 2.),
         t3 = step(abs(mod(iTime, 4.) - 2.), 1.),
         t4 = 1. - t3,
   halfdiag = sqrt(2.)/2.,
        pad = .5-halfdiag;

    vec2 uv = uv_orig - rot_center;

    uv *= 1000 * mat_zoom;

#ifndef HORIZONTAL
    t = in_out_cubic(t);
    

    uv = uv * rot(-rotTime/5.);
#else
    uv.y += sin(t*PI)*pad*SIZE/2.;
    uv.x += t*-halfdiag*SIZE;
    uv.x -= halfdiag*SIZE*floor(iTime/2.);
#endif

    uv = fract(uv / SIZE + t4 / 2.);
    uv = (1.-pad-pad-.6/SIZE)*uv+pad;
    uv = (uv - .5) * rot(t*PI2);
    uv =
#ifdef HORIZONTAL
        
        
        step(0.,
#else
        smoothstep(0.,2./SIZE,
#endif
                              .5-abs(uv));

    
    vec4 fragColor = color*mix(t4,t3,uv.x*uv.y);
    return fragColor;
}





















vec4 materialColorForPixel( vec2 texCoord ) {
    return mainImage(texCoord);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
