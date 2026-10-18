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
uniform vec4 uMMParam001; // native input: bpmsync
bool bpmsync = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_zoom
float mat_zoom = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_rotation
float mat_rotation = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_twist
float mat_twist = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_iterations
float mat_iterations = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_offset
float mat_offset = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_linesOffset
float mat_linesOffset = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_fade
float mat_fade = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_stripes
bool mat_stripes = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: mat_invert
bool mat_invert = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: mat_backgroundColor
vec4 mat_backgroundColor = uMMParam011;
uniform vec4 uMMParam012; // native input: mat_foregroundColor
vec4 mat_foregroundColor = uMMParam012;
uniform vec4 uMMParam013; // native input: mat_brightness
float mat_brightness = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_contrast
float mat_contrast = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_pos
vec2 mat_pos = uMMParam015.xy;
float mat_time = uTDTime * (mat_speed);





























const float PI = 3.14159265;

vec2 rotate(vec2 v, float a) {
	float sinA = sin(a);
	float cosA = cos(a);
	return vec2(v.x * cosA - v.y * sinA, v.y * cosA + v.x * sinA); 	
}

float square(vec2 uv, float d) {
	return max(abs(uv.x), abs(uv.y)) - d;	
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord;
	uv -= vec2(mat_pos);

	uv *= mat_zoom;
	
	uv = rotate(uv, mat_rotation * PI);
	
	float blurAmount = -5.0 / RENDERSIZE.y * (mat_zoom * 0.5);
    
	float time = mat_time;
	time = mod(time, 1.0);
	time += mat_twist;
	
	float G = 0.0;
	for (int i = 0; i < 60; i++) {
		
		float n = float(i);
		float size = 1.0 - n / mat_iterations;
		float rotateAmount = (n * 0.5 + 0.25) * PI * 2.0; 
		G = mix(G, 1.0, smoothstep(0.0, blurAmount, square(rotate(uv, -rotateAmount * time), size)));
		
		float blackOffset = mix(mat_linesOffset / 4.0, mat_linesOffset / 2.0, n / (mat_iterations * mat_offset)) / (mat_iterations * mat_offset);
		G = mix(G, 0.0, smoothstep(0.0, blurAmount, square(rotate( uv, -(rotateAmount + PI / 2.0) * time), size - blackOffset)));
    	
    	
    	if (mat_stripes) {
		G = (G * -1.0 + 1.0) * mat_fade;
       	} else {
			G = G * mat_fade;
       	}
	}

	
	G += mat_brightness;
    
    G = mix(0.5, G, mat_contrast);
	G = clamp(G,0., 1.);

	if (mat_invert) G = 1 - G;

	vec4 color = mix( mat_backgroundColor, mat_foregroundColor, G );

	return color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
