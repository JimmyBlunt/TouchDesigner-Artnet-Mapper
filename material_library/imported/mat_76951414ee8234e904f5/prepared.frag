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

uniform vec4 uMMParam000; // native input: speed
float speed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: reverse
bool reverse = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: bpmsync
bool bpmsync = uMMParam002.x > 0.5;
const int shape = 0;
#define shape_IS_Sin
uniform vec4 uMMParam004; // native input: size
float size = uMMParam004.x;
uniform vec4 uMMParam005; // native input: repeat
int repeat = int(round(uMMParam005.x));
uniform vec4 uMMParam006; // native input: posx
float posx = uMMParam006.x;
uniform vec4 uMMParam007; // native input: posy
float posy = uMMParam007.x;
uniform vec4 uMMParam008; // native input: foregroundColor
vec4 foregroundColor = uMMParam008;
uniform vec4 uMMParam009; // native input: backgroundColor
vec4 backgroundColor = uMMParam009;
uniform vec4 uMMParam010; // native input: brightness
float brightness = uMMParam010.x;
uniform vec4 uMMParam011; // native input: contrast
float contrast = uMMParam011.x;
float animation_time = uTDTime * (speed);






























#ifndef M_PI
  #define M_PI 3.1415926535897932384626433832795
#endif

float computeLuma(vec2 uv)
{
    
    float theta0 = animation_time * repeat;

    
    float value;
    #if defined(shape_IS_Out)
        
        value = (1/size) * mod(atan(uv.y,uv.x)*repeat/M_PI+theta0,2) / 2;
    #elif defined(shape_IS_In)
        
        value = (1/size) * (1 - mod(atan(uv.y,uv.x)*repeat/M_PI+theta0,2) / 2);
    #elif defined(shape_IS_Cut)
        
        value = smoothstep(0.99,1,1+sin(atan(uv.y,uv.x)*repeat+theta0*M_PI)+(1-2*size*(1/0.99)));
    #else
        
        value = (1/size) * (1+sin(atan(uv.y,uv.x)*repeat+theta0*M_PI))/2;
    #endif
    return 1 - value;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    if (size==0) return vec4(0,0,0,1);

    vec4 color = mix(backgroundColor, foregroundColor, clamp(computeLuma(texCoord-vec2(posx,posy)),0,1));

    
    color.rgb += vec3(brightness);

    
    color.rgb = mix(vec3(0.5), color.rgb, contrast);

    return color;
}



void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
