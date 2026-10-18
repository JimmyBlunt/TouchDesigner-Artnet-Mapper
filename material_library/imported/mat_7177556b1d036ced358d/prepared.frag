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

uniform vec4 uMMParam000; // native input: mat_shape
int mat_shape = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_speed
float mat_speed = uMMParam001.x;
uniform vec4 uMMParam002; // native input: bpmsync
bool bpmsync = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_zoom
float mat_zoom = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_rotate
float mat_rotate = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_twist
float mat_twist = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_tunnel
float mat_tunnel = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_thickness
float mat_thickness = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_amplitude
float mat_amplitude = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_frequency
float mat_frequency = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_band
float mat_band = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_pos
vec2 mat_pos = uMMParam011.xy;
uniform vec4 uMMParam012; // native input: mat_invert
bool mat_invert = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_backgroundColor
vec4 mat_backgroundColor = uMMParam013;
uniform vec4 uMMParam014; // native input: mat_foregroundColor
vec4 mat_foregroundColor = uMMParam014;
uniform vec4 uMMParam015; // native input: mat_brightness
float mat_brightness = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_contrast
float mat_contrast = uMMParam016.x;
float mat_time = uTDTime * (mat_speed);

































const float PI = 3.14159265359;
const float TWO_PI = 6.28318530718;

float electro(vec2 uv, float d, float f, float o, float a, float b)
{
    
    float theta = atan(uv.y,uv.x);
    
	float amp = smoothstep(0.0, 1.0, (sin(theta + mat_time * PI)*0.5+0.5)-b)*a;
	float phase = d + sin(theta * f + o + mat_time * PI) * amp;
    
    return sin(clamp(phase, 0.0, PI*2.0) + PI/2.0) + 1.0005;
}

mat2 rotate2d(float _angle){
    return mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle));
}

vec4 materialColorForPixel( vec2 texCoord )
{
   const float radius = 0.1;
    
	vec2 uv = texCoord;
	uv -= vec2(mat_pos);

	uv = rotate2d(PI) * uv; 
       
	uv = rotate2d(mat_rotate * -TWO_PI) * uv;
	uv *= mat_zoom;
   
	float grey = 0.0;
	float alpha = 1.0;

	for(int i = 0; i < 20; i++) {
	
   		float d = 0.0;
		
		
		if (mat_shape == 0) {
			float root2 = sqrt(2.0);
			d = dot(uv, vec2(0.0,-1.0));
    			d = max(d, dot(uv, vec2(-root2,1.0)));
    			d = max(d, dot(uv, vec2( root2,1.0)));
		}
		
		
		if (mat_shape == 1) {
	    		d = max(abs(uv).x, abs(uv).y);
		}

		grey += 1.0 - smoothstep(0.0, mat_thickness, electro(uv, d/radius, mat_frequency, 0.0 * PI, mat_amplitude, mat_band));
    		grey += 1.0 - smoothstep(0.0, mat_thickness, electro(uv, d/radius, mat_frequency, 0.5 * PI, mat_amplitude, mat_band));
    		grey += 1.0 - smoothstep(0.0, mat_thickness, electro(uv, d/radius, mat_frequency, 1.0 * PI, mat_amplitude, mat_band));
   	
    	
	    	
	    	uv *= mat_tunnel;
	    	
	    	
	    	uv = rotate2d(mat_twist * -TWO_PI) * uv;
   	}

	
	grey += mat_brightness;

    
    grey = mix(0.5, grey, mat_contrast);
	grey = clamp(grey, 0., 1.);

	if (mat_invert) grey = 1 - grey;

	vec4 color = mix( mat_backgroundColor, mat_foregroundColor, grey );
   	
	return color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
