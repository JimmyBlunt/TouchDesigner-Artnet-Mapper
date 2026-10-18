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

uniform vec4 uMMParam000; // native input: mat_audio_level
float mat_audio_level = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_animspeed
float mat_animspeed = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_scale
float mat_scale = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_squirl
float mat_squirl = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_distance
float mat_distance = uMMParam004.x;
float anim_position = uTDTime * (mat_animspeed);
#define spectrum sTD2DInputs[0]



















vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = 2*mat_scale*mat_scale*(texCoord-vec2(0.5));
	vec2 spec = vec2(IMG_NORM_PIXEL(spectrum,vec2(0.17,0)).r,IMG_NORM_PIXEL(spectrum,vec2(0.83,0)).r) * mat_audio_level * mat_audio_level;
	float col = 0.0;
	for (float i=0; i<30; i++) {
		uv.x += sin(i*mat_distance*mat_distance + spec.x * 30*fract(anim_position) + anim_position + uv.y*mat_squirl) * spec.y;
		col += abs(.066/uv.x) * spec.y;
	}
	return vec4(col,col,col,1);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
