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

uniform vec4 uMMParam000; // native input: lines
float lines = uMMParam000.x;
uniform vec4 uMMParam001; // native input: linesStartOffset
float linesStartOffset = uMMParam001.x;
uniform vec4 uMMParam002; // native input: amp
float amp = uMMParam002.x;
uniform vec4 uMMParam003; // native input: glow
float glow = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mod1
float mod1 = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mod2
float mod2 = uMMParam005.x;
uniform vec4 uMMParam006; // native input: twisted
float twisted = uMMParam006.x;
uniform vec4 uMMParam007; // native input: zoom
float zoom = uMMParam007.x;
uniform vec4 uMMParam008; // native input: rotateCanvas
float rotateCanvas = uMMParam008.x;
uniform vec4 uMMParam009; // native input: scroll
float scroll = uMMParam009.x;
uniform vec4 uMMParam010; // native input: pos
vec2 pos = uMMParam010.xy;
uniform vec4 uMMParam011; // native input: mat_auto_scroll_active
bool mat_auto_scroll_active = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_auto_scroll_speed
float mat_auto_scroll_speed = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam013.x > 0.5;
float mat_auto_scroll_time = uTDTime * (mat_auto_scroll_speed);














































































































#define PI 3.14159265359
#define TWO_PI 6.28318530718

mat2 rotate2d(float _angle){
    return mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle));
}

vec4 materialColorForPixel(vec2 texCoord)
{
	vec2 uv = texCoord;
	uv -= vec2(pos.x,1-pos.y);
	uv *= zoom; 
	uv = rotate2d(rotateCanvas*-TWO_PI) * uv; 
	
	float scrollValue = scroll;
	if (mat_auto_scroll_active) scrollValue += fract(mat_auto_scroll_time);
	
	
	vec3 wave_color = vec3(0.0);
	
	float wave_width = 0.01;
	
	
	for(float i = 0.0; i < 200.0; i++) {
		if (i > lines) break;
		
		uv = rotate2d(twisted*-TWO_PI) * uv; 
		
		uv.y +=  sin(sin(uv.x + i*mod1 + (scrollValue * TWO_PI) ) * amp + (mod2 * PI));

		
		if(lines * linesStartOffset - 1.0 <= i) {
			wave_width = abs(1.0 / (50.0 * uv.y * glow));
			wave_color += vec3(wave_width, wave_width, wave_width);
		}
	}
	
	return vec4(wave_color, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
