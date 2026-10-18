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
















































































float iTime = mat_time - mat_offset * 10;





 
 
 

 mat2 r2d(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
 }

 
 
 void mo(inout vec2 p, vec2 d) {
    p.x = abs(p.x) - d.x;
    p.y = abs(p.y) - d.y;
    if (p.y > p.x)p = p.yx;
 }

 
 float re(float p, float d) {
    return mod(p - d * .5, d) - d * .5;
 }

 
 void amod(inout vec2 p, float d) {
    float a = re(atan(p.x, p.y), d);
    p = vec2(cos(a), sin(a)) * length(p);
 }

 
 
 float cube(vec3 p, vec3 b) {
    b = abs(p) - b;
    return min(max(b.x, max(b.y, b.z)), 0.) + length(max(b, 0.));
 }

 float g = 0.;
 float de(vec3 p) {
    float t = iTime * 1.;
    float s = (t*.1 + sin(t)*.1)*2.5;
    p.xz *= r2d(s);
     

    amod(p.xz, 6.28 / 4.);
    mo(p.xz, vec2(2.7));

    vec3 q = p;
    q.xz *= r2d(q.y*.7 + iTime * 4.);
    amod(q.xz, 6.28 / 9.);
    q.x = abs(q.x) - 2.4;
    float c = cube(q, vec3(.1, 1e6, .1));

    q = p;
    mo(q.xz, vec2(.3));
    q.x = abs(q.x) - 2.;
    float cyl = length(q.xz) - .05;

    p.xz *= r2d(p.y*.3 + iTime * 1.);
    float d = cube(p, vec3(.9, 1e6, .9));
    d = min(d, cyl);
    d = min(d, c);
    g += .01 / (.01 + d * d);
    return d;
 }

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;

    vec3 ro = vec3(0, -iTime * 6., -0);
    vec3 rd = normalize(vec3(uv, .4 - length(uv))); 

    vec3 p;
    float t = 0., ri;
    for (float i = 0.; i < 1.; i += .01) {
        ri = i;
        p = ro + rd * t;
        float d = de(p);
        
        d = max(abs(d), .02);
        t += d * .2;
    }

    vec3 c = mix(vec3(.9, .8, .6), vec3(.1, .1, .2), sin(uv.x*2.) + ri);
    c.r += sin(iTime)*.3;
    c += g * .03; 
    c = mix(c, vec3(.1, .1, .12), 1. - exp(-.07*t*t)); 

    return vec4(c, 1);





}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
