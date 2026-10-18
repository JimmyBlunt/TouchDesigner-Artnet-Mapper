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

uniform vec4 uMMParam000; // native input: mat_speed
float mat_speed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: range
float range = uMMParam001.x;
uniform vec4 uMMParam002; // native input: divergence
float divergence = uMMParam002.x;
uniform vec4 uMMParam003; // native input: iMouse
vec2 iMouse = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: iterations
int iterations = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: radius
float radius = uMMParam005.x;
float mat_time = uTDTime * (mat_speed);
































































const float fieldOfView = 1.5;
const float blend = 1.5;
const float balance = 1.5;
const float falloff = 1.9;

float random(vec2 p) { return fract(1e4 * sin(17.0 * p.x + p.y * 0.1) * (0.1 + abs(sin(p.y * 13.0 + p.x)))); }
mat2 rot(float a) { float c=cos(a),s=sin(a); return mat2(c,-s,s,c); }
float smoothmin (float a, float b, float r) { float h = clamp(.5+.5*(b-a)/r, 0., 1.); return mix(b, a, h)-r*h*(1.-h); }

vec3 look (vec3 eye, vec3 target, vec2 anchor, float fov) {
    vec3 forward = normalize(target-eye);
    vec3 right = normalize(cross(forward, vec3(0,1,0)));
    vec3 up = normalize(cross(right, forward));
    return normalize(forward * fov + right * anchor.x + up * anchor.y);
}

vec3 camera (vec3 eye) {
    vec2 mouse = iMouse/RENDERSIZE.xy*2.-1.;
    if (length(iMouse) > 0.0) {
        eye.yz *= rot(mouse.y*3.1415);
        eye.xz *= rot(mouse.x*3.1415);
    } else {
        eye.yz *= rot(-3.1415/4.);
        eye.xz *= rot(-3.1415/2.);
    }
    return eye;
}

float geometry (vec3 pos) {
    pos = camera(pos);
    float a = 1.0;
    float scene = 1.;
    float t = mat_time*0.2;
    float wave = 1.0+0.2*sin(t*8.-length(pos)*2.);
    t = floor(t)+pow(fract(t),.5);
    for (int i = iterations; i > 0; --i) {
        pos.xy *= rot(cos(t)*balance/a+a*2.+t);
        pos.zy *= rot(sin(t)*balance/a+a*2.+t);
        pos.zx *= rot(sin(t)*balance/a+a*2.+t);
        pos = abs(pos)-range*a*wave;
        scene = smoothmin(scene, length(pos)-radius*a, blend*a);
        a /= falloff;
    }
    return scene;
}

float raymarch ( vec3 eye, vec3 ray ) {
    float dither = random(ray.xy+fract(mat_time));
    float total = dither;
    const int count = 30;
    for (int index = count; index > 0; --index) {
        float dist = geometry(eye+ray*total);
        dist *= 0.9+.1*dither;
        total += dist;
        if (dist < 0.001 * total)
            return float(index)/float(count);
    }
    return 0.;
}

vec4 materialColorForPixel(vec2 texCoord) {
    vec2 uv = 2.0*(texCoord*RENDERSIZE.xy-0.5*RENDERSIZE.xy)/RENDERSIZE.y;
    
    vec3 eyeLeft = vec3(-divergence,0,5.);
    vec3 eyeRight = vec3(divergence,0,5.);
    vec3 rayLeft = look(eyeLeft, vec3(0), uv, fieldOfView);
    vec3 rayRight = look(eyeRight, vec3(0), uv, fieldOfView);
    
    float red = raymarch(eyeLeft, rayLeft);
    float cyan = raymarch(eyeRight, rayRight);
    
    return vec4(red, cyan, cyan, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
