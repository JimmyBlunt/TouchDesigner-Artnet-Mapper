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
uniform vec4 uMMParam001; // native input: mat_morph
float mat_morph = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_mode
int mat_mode = int(round(uMMParam002.x));
uniform vec4 uMMParam003; // native input: mat_stroke_size
float mat_stroke_size = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_offset
vec2 mat_offset = uMMParam004.xy;
uniform vec4 uMMParam005; // native input: mat_brightness
float mat_brightness = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_contrast
float mat_contrast = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_tint
vec4 mat_tint = uMMParam007;
uniform vec4 uMMParam008; // native input: mat_invert
bool mat_invert = uMMParam008.x > 0.5;
float mat_animation_time = uTDTime * (mat_speed);























	
float rand( inout uint seed )
{
    
	seed = (seed << 13U) ^ seed;
    seed = seed * (seed * seed * 15731U + 789221U) + 1376312589U;
    uint seed2 = seed * seed;
    return float(seed2&0x7fffffffU)/float(0x7fffffffU);
}


float Polygon( vec2 uv, uint seed )
{
    float f = abs(uv.y-rand(seed)+.5)-rand(seed)-1.;
    f = max(f,abs(uv.x-rand(seed)+.5)-rand(seed)-.5);
    f = max(f,abs(dot(uv,vec2(1,1)/sqrt(2.))-rand(seed)+.5)-rand(seed)-1.);
    f = max(f,abs(dot(uv,vec2(1,-1)/sqrt(2.))-rand(seed)+.5)-rand(seed)-1.);
    return f;
}

float stroke(float v, float stroke_size)
{
	return (v>0 && v<stroke_size) ? -min(v,stroke_size-v) : 1;
}

vec4 materialColorForPixel( vec2 texCoord )
{
	
	vec2 uv = texCoord;
	
	uv += vec2(-mat_offset.x,mat_offset.y);
	
	
	vec3 color = vec3(0.);
	
    uint seed1 = 31713U + uint(mat_animation_time);
    uint seed2 = seed1+1U;

	float value;

	if (mat_morph>0) {
		float mixFactor = fract(mat_animation_time); 
		mixFactor = max(mixFactor-(1-mat_morph),0)*1/mat_morph;
		value = mix(Polygon(uv*5.+vec2(-2.5),seed1),Polygon(uv*5.+vec2(-2.5),seed2),mixFactor);
	} else {
		value = Polygon(uv*5.+vec2(-2.5),seed1);
	}

	if (mat_mode == 0) {
	    color.rgb = vec3(value);
	} else {
	    color.rgb = vec3(stroke(value,mat_stroke_size));
	}
		
	float bloom = .01;
    color.rgb = .5+.5*color.rgb/(bloom+abs(color.rgb));
	
	
    color = mix(vec3(0.5), color, mat_contrast);
    
    color += vec3(mat_brightness);
	
	color *= mat_tint.rgb;
	
	color = mix(color, vec3(1.0)-color,float(mat_invert));
		
	vec4 final_color = vec4(color,1.0);	
	return final_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
