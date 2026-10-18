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

uniform vec4 uMMParam000; // native input: amplitude
float amplitude = uMMParam000.x;
uniform vec4 uMMParam001; // native input: div_x
int div_x = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: div_y
int div_y = int(round(uMMParam002.x));
uniform vec4 uMMParam003; // native input: sep_width
float sep_width = uMMParam003.x;
const int color_mode = 0;
#define color_mode_IS_Gray
uniform vec4 uMMParam005; // native input: hue
float hue = uMMParam005.x;
uniform vec4 uMMParam006; // native input: hue_offset
float hue_offset = uMMParam006.x;
const bool show_peaks = false;
#define show_peaks_IS_false
uniform vec4 uMMParam008; // native input: peaks_size
float peaks_size = uMMParam008.x;
uniform vec4 uMMParam009; // native input: peaks_color
vec4 peaks_color = uMMParam009;
#define hue_texture sTD2DInputs[0]
#define white_texture sTD2DInputs[1]
#define spectrum_16_decay sTD2DInputs[2]
#define spectrum_16 sTD2DInputs[3]











































































































vec4 materialColorForPixel(vec2 texCoord)
{
    texCoord.y = 1-texCoord.y;

    if (fract(sep_width/2+texCoord.x*div_x)<sep_width) return vec4(0,0,0,1);
    if (fract(sep_width/2+texCoord.y*div_y)<sep_width) return vec4(0,0,0,1);

    float quantizedX = int(texCoord.x*div_x)/float(div_x);
    float quantizedY = int(texCoord.y*div_y)/float(div_y);

    float index = (int(quantizedX*IMG_SIZE(spectrum_16).x)) / IMG_SIZE(spectrum_16).x;
    float posY = IMG_NORM_PIXEL(spectrum_16,vec2(index,0)).r * amplitude * amplitude - 0.1;

    float value = posY-quantizedY;
    value = step(0,value);

    vec4 finalColor;

    #if defined(color_mode_IS_Mad_EQ)
        finalColor = vec4(IMG_NORM_PIXEL(hue_texture,vec2(0.5/div_x + hue + hue_offset*quantizedX, 1-(1.0/div_y)-quantizedY*div_y/(div_y+1.0))).rgb*step(0.01,value), 1);
    #else 
        finalColor = vec4(IMG_NORM_PIXEL(white_texture,vec2(0.5/div_x + hue + hue_offset*quantizedX, 1-(1.0/div_y)-quantizedY*div_y/(div_y+1.0))).rgb*step(0.01,value), 1);
    #endif

    #if defined(show_peaks_IS_true)
        float posY_decay = IMG_NORM_PIXEL(spectrum_16_decay,vec2(index,0)).r * amplitude * amplitude;
        float value_decay = posY_decay-quantizedY;
        if (value_decay>0.0 && value_decay<1.0/div_y && fract(texCoord.y*div_y)<peaks_size) {
            finalColor = peaks_color;
        }
    #endif

    return finalColor;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
