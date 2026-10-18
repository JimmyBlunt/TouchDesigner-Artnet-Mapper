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
uniform vec4 uMMParam002; // native input: mat_octaves
float mat_octaves = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_power
float mat_power = uMMParam003.x;
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
























#define DO_ROTATE         true  
#define BOXFILTER_SAMPLES 2.0
#define PPI                3.14159265359





vec2 hash22(vec2 p)
{

    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx+33.33);
    return fract((p3.xx+p3.yz)*p3.zy);
}


float gainf(float x, float k) 
{
    
    k = k < 0.5 ? 2.*k : 1./(1.-(k-0.5)*2.);
    float a = 0.5*pow(2.0*((x<0.5)?x:1.0-x), k);
    return (x<0.5)?a:1.0-a;
}


vec2 rot_golden(vec2 pos,vec2 uv)
{
    
    float sine   = -0.67549029078724183023998;
    float cosine = -0.73736888126104662389070;
    mat2 rot = mat2(cosine, -sine, sine, cosine);
    uv -= pos; 
    uv = rot * uv  ;
    return uv + pos;
}


float gradnoise_random(vec2 uv)
{
    vec2 p = floor(uv),
        f = (fract(uv));
    
    vec2 u = f*f*f*(6.0*f*f - 15.0*f +10.0);  
    
    float dot1, dot2, dot3, dot4;
    
    dot1 = dot(2.*(hash22(p)) - 1.0, f);
    dot2 = dot(2.*(hash22(p + vec2(1., 0.)))-1.0 , f - vec2(1.,0.));
    dot3 = dot(2.*(hash22(p + vec2(0., 1.)))-1.0, f - vec2(0.,1.));
    dot4 = dot(2.*(hash22(p + vec2(1., 1.)))-1.0, f - vec2(1.,1.));
   
    float m1, m2;
    
    m1 = mix(dot1, dot2, u.x);
    m2 = mix(dot3, dot4, u.x);
    
    return mix(m1, m2, u.y);
}


float gradnoise_circular(vec2 uv, float power)
{
    vec2 p = floor(uv),
        f = (fract(uv));
    
    vec2 u = f*f*f*(6.0*f*f - 15.0*f +10.0);
    
    float dot1, dot2, dot3, dot4;
    
    vec2 hash00, hash10, hash01, hash11;
    vec2 grad00, grad10, grad01, grad11;
  
    hash00 = hash22(p);
    hash01 = hash22(p + vec2(0., 1.));
    hash10 = hash22(p + vec2(1., 0.));
    hash11 = hash22(p + vec2(1., 1.));

    
    
    
    
    
    
    
    
 	
    grad00 = vec2(sin(hash00.x * PPI * 2. + mat_animation_time), cos(hash00.x * PPI * 2. + mat_animation_time)) * (pow(hash00.y, power));
    grad01 = vec2(sin(hash01.x * PPI * 2. + mat_animation_time), cos(hash01.x * PPI * 2. + mat_animation_time)) * (pow(hash01.y, power));
    grad10 = vec2(sin(hash10.x * PPI * 2. + mat_animation_time), cos(hash10.x * PPI * 2. + mat_animation_time)) * (pow(hash10.y, power));
    grad11 = vec2(sin(hash11.x * PPI * 2. + mat_animation_time), cos(hash11.x * PPI * 2. + mat_animation_time)) * (pow(hash11.y, power));
    
    dot1 = dot(grad00, f);
    dot2 = dot(grad10, f - vec2(1.,0.));
    dot3 = dot(grad01, f - vec2(0.,1.));
    dot4 = dot(grad11, f - vec2(1.,1.));
  
  
    float m1, m2;
    
    m1 = mix(dot1, dot2, u.x);
    m2 = mix(dot3, dot4, u.x);
   
   
    return mix(m1, m2, u.y);
}

vec2 calc_pos_width(float pos, float width)
{
    float low, high;
    
    low = pos - width/2.0;
    high = pos + width/2.0;
    return clamp(vec2(low, high), vec2(0.0), vec2(1.0));
}

float oct_gained_gradnoise(vec2 uv, float octaves, float roughness, float octscale, float power)
{
    float a = 0.;
    float intensity = 1.;
    float oct_intensity = 1.0; 
    float total_scale = 0.0;
    float remap;

    float contrast = 0.999;
    float gain = .00111;

    for(float i = 0.; i < octaves; i++)
    {
        float gradnoise_lookup = gradnoise_circular(uv, power)*1.75;
        
        remap = gradnoise_lookup;
        remap = gainf((gradnoise_lookup*.5 + .5), gain);
        remap = ((remap - 0.5) * 2.); 
        
		total_scale += oct_intensity;
        a += remap* oct_intensity;
        oct_intensity*= roughness; 
        
        if(DO_ROTATE)
        	uv = rot_golden(vec2(11.1231, 11.1231), uv) * octscale;
        else
        	uv = uv * octscale;
    }
    
	
    a = (a/(1.0 -contrast)) ;
    a= clamp(a/total_scale, -1., 1.0);
    return a; 
}	

vec4 materialColorForPixel( vec2 texCoord )
{
	
	vec2 uv = texCoord;
	uv = uv*2.-1.;
	
	uv *= mat_scale*0.1;
	uv += vec2(-mat_offset.x,mat_offset.y)*0.1;
	
    int octaves = int(ceil(mat_octaves * 10.));
    float power = mat_power * 6.+.1;
    float roughness = 1.1; 
    
    
    
    float octscale = 2.0; 
    float final_value;
    
    final_value = oct_gained_gradnoise(uv * 2., float(octaves), roughness, octscale, power);
    
    final_value = final_value *0.5+0.5;
	
	
	vec3 color = vec3(final_value);

	
	
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
