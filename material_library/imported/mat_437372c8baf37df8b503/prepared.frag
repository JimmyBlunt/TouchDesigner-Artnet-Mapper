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
uniform vec4 uMMParam001; // native input: mat_min
float mat_min = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_show_curve
bool mat_show_curve = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_contrast
float mat_contrast = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_tint
vec4 mat_tint = uMMParam004;
uniform vec4 uMMParam005; // native input: mat_invert
bool mat_invert = uMMParam005.x > 0.5;
float mat_animation_time = uTDTime * (mat_speed);























float ecg(float x)
{   
   x = x - ceil(x/1.3 - 0.5)*1.3;   
   return 0.9*(exp((-pow(x + 1.4, 2.)) / (2.*0.02)) + exp((-pow(x - 1.4,2.)) / (2.*0.02))) + 
       (1. - abs(x / 0.1) - x)*exp((-pow(7.*x,2.)) / 2.);
}	
float plot(vec2 st, float pct,float w){
  return  smoothstep( pct-w, pct, st.y) - 
          smoothstep( pct, pct+w, st.y);
}

float line(float y,float axis,float width){
	return step(y-width/2,axis) - step(y+ width/2.,axis);
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord;

	float E = ecg(mat_animation_time )*0.666+0.333;

	E = mat_min + (1.-mat_min)*E;

	vec3 color = vec3(E);

	float P = plot(vec2(uv.x,1.-uv.y)*1.1-0.05, mat_min + (1.-mat_min)*(ecg(uv.x + mat_animation_time)*0.66+0.333), 0.01);

	color 		 = mix(color,vec3(1,0,0),P*float(mat_show_curve));

	float line_0 = line(0.02,uv.y*1.1-0.05,0.004);
	float line_1 = line(0.98,uv.y*1.1-0.05,0.004);
	float line_2 = line(0.5,uv.y*1.1-0.05,0.004);
	float l 		 = max(max(line_0,line_1),line_2);
	color 		 =  mix(color,vec3(0.,l,0)*0.25,l*float(mat_show_curve));

	
	color *= mat_tint.rgb;
	
	color = mix(color, vec3(1.0)-color,float(mat_invert));
		
	vec4 final_color = vec4(color,1.0);	
	return final_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
