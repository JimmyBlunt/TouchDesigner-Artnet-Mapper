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

uniform vec4 uMMParam000; // native input: frame_on
int frame_on = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: frame_off
int frame_off = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: backgroundColor
vec4 backgroundColor = uMMParam002;
uniform vec4 uMMParam003; // native input: foregroundColor
vec4 foregroundColor = uMMParam003;
#define PI 3.1415926535897932384626433832795

void materialVsFunc(vec2 uv) {
}
















vec4 materialColorForPixel(vec2 texCoord)
{
  
  
  

  float amount = mod(FRAMEINDEX, frame_on + frame_off);
  amount = step(amount, frame_on);
  
  
	vec4 backColor = backgroundColor;
	vec4 frontColor = foregroundColor;
	return mix(backColor,frontColor,amount);
}


void main()
{
    materialVsFunc(vec2(0.0));

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
