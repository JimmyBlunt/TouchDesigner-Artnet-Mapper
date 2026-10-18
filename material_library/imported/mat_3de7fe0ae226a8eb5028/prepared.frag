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

uniform vec4 uMMParam000; // native input: resolution
float resolution = uMMParam000.x;
uniform vec4 uMMParam001; // native input: detail
float detail = uMMParam001.x;
uniform vec4 uMMParam002; // native input: red
float red = uMMParam002.x;
uniform vec4 uMMParam003; // native input: green
float green = uMMParam003.x;
uniform vec4 uMMParam004; // native input: blue
float blue = uMMParam004.x;
uniform vec4 uMMParam005; // native input: brightness
float brightness = uMMParam005.x;
uniform vec4 uMMParam006; // native input: movement
float movement = uMMParam006.x;




















vec4 materialColorForPixel( vec2 texCoord )
{
    vec2 uv =  (0.3 * texCoord.yx - 1);
    for(float i = movement * movement; i < resolution; i++){
    uv.y -= i * detail / i * 
    sin(uv.x * i * i + TIME * 0.3) * cos(uv.y * i * i + TIME * 0.3);
}
   vec3 col;
   col.r  = uv.y + red;   col.g = uv.y + green;   col.b = uv.y + blue;
   return vec4(col,brightness);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
