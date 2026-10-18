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

uniform vec4 uMMParam000; // native input: bpmsync
bool bpmsync = uMMParam000.x > 0.5;
uniform vec4 uMMParam001; // native input: mat_reverse
bool mat_reverse = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: speed
float speed = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_offset
float mat_offset = uMMParam003.x;
uniform vec4 uMMParam004; // native input: decay
float decay = uMMParam004.x;
uniform vec4 uMMParam005; // native input: release
float release = uMMParam005.x;
uniform vec4 uMMParam006; // native input: shape
int shape = int(round(uMMParam006.x));
uniform vec4 uMMParam007; // native input: cut
bool cut = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: cut_threshold
float cut_threshold = uMMParam008.x;
uniform vec4 uMMParam009; // native input: backgroundColor
vec4 backgroundColor = uMMParam009;
uniform vec4 uMMParam010; // native input: foregroundColor
vec4 foregroundColor = uMMParam010;
uniform vec4 uMMParam011; // native input: brightness
float brightness = uMMParam011.x;
float strob_position = uTDTime * (speed);































#define PI 3.1415926535897932384626433832795

vec4 materialColorForPixel(vec2 texCoord)
{


	vec4 backColor = vec4(backgroundColor.rgb * brightness, backgroundColor.a);
	vec4 frontColor = vec4(foregroundColor.rgb * brightness, foregroundColor.a);


    float adjusted_bpm_pos = mod(strob_position + mat_offset,1); 
    if (adjusted_bpm_pos < decay) {
        adjusted_bpm_pos = 1;
    } else {
        
        adjusted_bpm_pos = (adjusted_bpm_pos - decay) * 1 / (1 - decay);
        if (adjusted_bpm_pos < release) {
            adjusted_bpm_pos = 1 - adjusted_bpm_pos * 1 / release;
        } else {
            adjusted_bpm_pos = 0;
        }
    }

    if (shape == 0) { 
        adjusted_bpm_pos = adjusted_bpm_pos;
    } else if (shape == 1) { 
        adjusted_bpm_pos = 1-adjusted_bpm_pos;
    } else { 
        adjusted_bpm_pos = (1+sin((-0.25+adjusted_bpm_pos)*2*PI))/2;
    }

    if (cut) {

        if (adjusted_bpm_pos > cut_threshold) {
            adjusted_bpm_pos = 1.;
        } else {
            adjusted_bpm_pos = 0.;
        }


    }


	return mix(backColor,frontColor,adjusted_bpm_pos);
}



void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
