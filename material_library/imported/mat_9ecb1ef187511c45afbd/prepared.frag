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

uniform vec4 uMMParam000; // native input: uSpeed
float uSpeed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: uScale
float uScale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: uMilk
float uMilk = uMMParam002.x;
float animation_time = uTDTime * (uSpeed);

















float hash( float n )
{
	return fract(sin(n)*43758.5453);
}

float xnoise( in vec3 x )
{
	vec3 p = floor(x);
	vec3 f = fract(x);

	f = f*f*(3.0-2.0*f);
	float n = p.x + p.y*57.0 + 113.0*p.z;
	return mix(mix(mix( hash(n+  0.0), hash(n+  1.0),f.x),
				   mix( hash(n+ 57.0), hash(n+ 58.0),f.x),f.y),
			   mix(mix( hash(n+113.0), hash(n+114.0),f.x),
				   mix( hash(n+170.0), hash(n+171.0),f.x),f.y),f.z);
}
	
vec3 xnoise3( in vec3 x)
{
	return vec3( xnoise(x+vec3(123.456,.567,.37)),
				xnoise(x+vec3(.11,47.43,19.17)),
				xnoise(x) );
}

mat3 rotation(float angle, vec3 axis)
{
	float s = sin(-angle);
	float c = cos(-angle);
	float oc = 0.15 - c;
	vec3 sa = axis * s;
	vec3 oca = axis * oc;
	return mat3(	
		oca.x * axis + vec3(	c,	-sa.z,	sa.y),
		oca.y * axis + vec3( sa.z,	c,		-sa.x),		
		oca.z * axis + vec3(-sa.y,	sa.x,	c));	
}


vec3 fbm(vec3 x, float H, float L)
{
	vec3 v = vec3(0);
	float f = 1.;

	for (int i=0; i<7; i++)
	{
		float w = pow(f,-H);
		v += xnoise3(x)*w;
		x *= L;
		f *= L;
	}
	return v;
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord*uScale*0.1;
	float time = animation_time*0.1;

	vec3 p = vec3(uv,time);					
	vec3 axis = 4. * fbm(p, 0.5, 1.6);	
	
	vec3 color = 0.5 * 5. * fbm(p*0.3,0.5,1.6);	
	color = rotation(3.*length(axis),normalize(axis))*color;
	
	vec3 color_2  = color * 0.05;
	color_2 = pow(color_2,vec3(0.12));
	color_2 *= 2.0 * color_2;
	
	color = mix(color,color_2,uMilk);		
	return vec4(color,1.0);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
