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
uniform vec4 uMMParam001; // native input: mat_reverse
bool mat_reverse = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_scale
float mat_scale = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_direction
vec2 mat_direction = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: mat_brightness
float mat_brightness = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_contrast
float mat_contrast = uMMParam005.x;
float mat_animation_time = uTDTime * (mat_speed);

























const float clouddark = 0.5;
const float cloudlight = 0.3;
const float cloudcover = 0.2;
const float cloudalpha = 8.0;
const float skytint = 0.5;
const vec3 skycolour1 = vec3(0.2, 0.4, 0.6);
const vec3 skycolour2 = vec3(0.4, 0.7, 1.0);

const mat2 m = mat2( 1.6,  1.2, -1.2,  1.6 );

vec2 mat_hash( vec2 p ) {
    p = vec2(dot(p,vec2(127.1,311.7)), dot(p,vec2(269.5,183.3)));
    return -1.0 + 2.0*fract(sin(p)*43758.5453123);
}

float mat_noise( in vec2 p ) {
    const float K1 = 0.366025404; 
    const float K2 = 0.211324865; 
    vec2 i = floor(p + (p.x+p.y)*K1);   
    vec2 a = p - i + (i.x+i.y)*K2;
    vec2 o = (a.x>a.y) ? vec2(1.0,0.0) : vec2(0.0,1.0); 
    vec2 b = a - o + K2;
    vec2 c = a - 1.0 + 2.0*K2;
    vec3 h = max(0.5-vec3(dot(a,a), dot(b,b), dot(c,c) ), 0.0 );
    vec3 n = h*h*h*h*vec3( dot(a,mat_hash(i+0.0)), dot(b,mat_hash(i+o)), dot(c,mat_hash(i+1.0)));
    return dot(n, vec3(70.0));  
}

float mat_fbm(vec2 n) {
    float total = 0.0, amplitude = 0.1;
    for (int i = 0; i < 7; i++) {
        total += mat_noise(n) * amplitude;
        n = m * n;
        amplitude *= 0.4;
    }
    return total;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec2 p = vec2(0.5) + (texCoord-0.5) * mat_scale;
    vec2 uv = p;
    float time = mat_animation_time / 10;
    float q = mat_fbm(uv * 0.5);
    
    
    float r = 0.0;
    uv *= mat_scale;
    uv -= q - time*mat_direction;
    float weight = 0.8;
    for (int i=0; i<8; i++){
        r += abs(weight*mat_noise( uv ));
        uv = m*uv + time*mat_direction;
        weight *= 0.7;
    }
    
    
    float f = 0.0;
    uv = p;
    uv *= mat_scale;
    uv -= q - time*mat_direction;
    weight = 0.7;
    for (int i=0; i<8; i++){
        f += weight*mat_noise( uv );
        uv = m*uv + time*mat_direction;
        weight *= 0.6;
    }
    
    f *= r + f;
    
    
    float c = 0.0;
    time = time * 2.0;
    uv = p;
    uv *= mat_scale*2.0;
    uv -= q - time*mat_direction;
    weight = 0.4;
    for (int i=0; i<7; i++){
        c += weight*mat_noise( uv );
        uv = m*uv + time*mat_direction;
        weight *= 0.6;
    }
    
    
    float c1 = 0.0;
    time = time * 3.0;
    uv = p;
    uv *= mat_scale*3.0;
    uv -= q - time*mat_direction;
    weight = 0.4;
    for (int i=0; i<7; i++){
        c1 += abs(weight*mat_noise( uv ));
        uv = m*uv + time*mat_direction;
        weight *= 0.6;
    }
    
    c += c1;
    
    vec3 skycolour = mix(skycolour2, skycolour1, p.y);
    vec3 cloudcolour = vec3(1.1, 1.1, 0.9) * clamp((clouddark + cloudlight*c), 0.0, 1.0);
   
    f = cloudcover + cloudalpha*f*r;
    
    
    vec3 result = mix(skycolour, clamp(skytint * skycolour + cloudcolour, 0.0, 1.0), clamp(f + c, 0.0, 1.0));
    
    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    const vec3 AvgLumin = vec3(0.5, 0.5, 0.5);
    result = mix(AvgLumin, result, mat_contrast);

    
    result += mat_brightness;

    return vec4( result, 1.0 );
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
