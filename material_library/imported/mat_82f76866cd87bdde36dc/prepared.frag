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
uniform vec4 uMMParam001; // native input: mat_char
float mat_char = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_over
float mat_over = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_invert
bool mat_invert = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_backgroundColor
vec4 mat_backgroundColor = uMMParam004;
uniform vec4 uMMParam005; // native input: mat_foregroundColor
vec4 mat_foregroundColor = uMMParam005;
float mat_time = uTDTime * (mat_speed);




















vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord *2. -1.;
    float len = length(uv);
    
 	for (int i = 0; i < 3; i++) {
            
        uv.x +=  sin(uv.y + mat_time * 0.6)*(0.2 + mat_char);
        uv.y +=  cos(uv.x + mat_time * 0.8 + cos(len * 3.0))*(0.4 + mat_char);
		len = length(vec2(uv.x, uv.y)); 
    }
    
	len = mix(min(1.,max(0.,len)), len, mat_over);

	vec3 col = mix(mat_backgroundColor.rgb,mat_foregroundColor.rgb,vec3(len));
	if(mat_invert)col = 1. - col;

	return vec4(col,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
