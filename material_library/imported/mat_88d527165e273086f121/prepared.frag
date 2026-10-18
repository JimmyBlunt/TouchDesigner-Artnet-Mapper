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
uniform vec4 uMMParam001; // native input: mat_scale
float mat_scale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_complex
float mat_complex = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_offset
vec2 mat_offset = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: mat_brightness
float mat_brightness = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_contrast
float mat_contrast = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_tint
vec4 mat_tint = uMMParam006;
uniform vec4 uMMParam007; // native input: mat_invert
bool mat_invert = uMMParam007.x > 0.5;
float mat_animation_time = uTDTime * (mat_speed);






















vec4 materialColorForPixel( vec2 texCoord )
{
	
	vec2 uv = texCoord;
	
	uv *= mat_scale;
	uv += vec2(-mat_offset.x,mat_offset.y);
		
	vec2 R = vec2(1024.),
         r = ( (uv*1024.) - .5 * R ) /R.y,
         q = (uv*1024.) / R-.5;
	
	float t = mat_animation_time,
          k = 1.;
	
    t+=sin(t);
	
	vec4 o = vec4(0.);
	vec3 a;
	float complex = mat_complex;
	complex = 1./complex;
    for(float i = 1.;i>0.;i-=complex) {
        a = (vec3(-.03,0.,.03)+i)*(k=-k);
        for(int x=0;x<3;++x)
            if(sin(8.*length(r-(cos(vec2(a[x]+t*.4,a[x]+t*.7))*i)))<0.)
                o[x]=1.-o[x];
            }
    o -= .1*fract(sin(dot(r*t,r+t))*1e5);
    o *= 1.-dot(q,q*1.4);

		
	
	vec3 color = o.rgb;	
	
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
