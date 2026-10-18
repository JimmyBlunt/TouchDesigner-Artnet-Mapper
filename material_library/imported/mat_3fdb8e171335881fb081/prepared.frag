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
uniform vec4 uMMParam001; // native input: inputA
float inputA = uMMParam001.x;
uniform vec4 uMMParam002; // native input: inputF
float inputF = uMMParam002.x;
uniform vec4 uMMParam003; // native input: timeScale
float timeScale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: timeOffset
float timeOffset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: slide
vec2 slide = uMMParam005.xy;
uniform vec4 uMMParam006; // native input: slidePos
float slidePos = uMMParam006.x;
float mat_animation_time = uTDTime * (mat_speed);



































































#ifdef GL_ES

#endif



vec2 rotate(vec2 p, float a)
{
	return vec2(p.x * cos(a) - p.y * sin(a), p.x * sin(a) + p.y * cos(a));
}


float rand1(float n)
{
    return fract(sin(n) * 58.5453123);
}


vec2 rand2(in vec2 p)
{
	return fract(vec2(sin(p.x * 591.32 + p.y * 154.077 + mat_animation_time), cos(p.x * 391.32 + p.y * 49.077 + mat_animation_time)));
}


float noiseF(float p)
{
	float fl = floor(p);
	float fc = fract(p);
	return mix(rand1(fl), rand1(fl + 1.0), fc);
}


float voronoi(in vec2 x)
{
	vec2 p = floor(x);
	vec2 f = fract(x);
	
	vec2 res = vec2(8.0);
	for(int j = -1; j <= 1; j ++)
	{
		for(int i = -1; i <= 1; i ++)
		{
			vec2 b = vec2(i, j);
			vec2 r = vec2(b) - f + rand2(p + b);
			
			
			float d = max(abs(r.x), abs(r.y));
			
			if(d < res.x)
			{
				res.y = res.x;
				res.x = d;
			}
			else if(d < res.y)
			{
				res.y = d;
			}
		}
	}
	return res.y - res.x;
}




vec4 materialColorForPixel(vec2 texCoord)
{
	float flicker = noiseF(mat_animation_time * timeScale) * (1.0-timeOffset) + timeOffset;
	vec2 uv = texCoord;
	uv = (uv - 0.5) * 2.0;
	vec2 suv = uv;
	
	
	float v = 0.0;
	
	
	
	
	
	
	
	
	uv += slide*slidePos;
	
	
	
	float a = inputA, f = inputF;
	
	for(int i = 0; i < 3; i ++) 
	{	
		float v1 = voronoi(uv * f + 1.0);
		float v2 = 0.0;
		
		
		if(i > 0)
		{
			
			v2 = voronoi(uv * f * 0.5 + 50.0 + mat_animation_time);
			
			float va = 0.0, vb = 0.0;
			va = 1.0 - smoothstep(0.0, 0.1, v1);
			vb = 1.0 - smoothstep(0.0, 0.08, v2);
			v += a * pow(va * (0.5 + vb), 2.0);
		}
		
		
		v1 = 1.0 - smoothstep(0.0, 0.3, v1);
		
		
		v2 = a * (noiseF(v1 * 10.0 + 0.1));
		
		
		if(i == 0)
			v += v2*flicker;
		else
			v += v2;
		
		f *= inputF;
		a *= inputA;
	}

	
	v *= exp(-0.6 * length(suv)) * 1.2;
	
	
	
	
	
	vec3 cexp = vec3(3.0, 2.0, 4.0) * 1.3;

	vec3 col = vec3(pow(v, cexp.x), pow(v, cexp.y), pow(v, cexp.z)) * 1.0;
	
	return vec4(col, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
