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
uniform vec4 uMMParam002; // native input: mat_invert
bool mat_invert = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_backgroundColor
vec4 mat_backgroundColor = uMMParam003;
uniform vec4 uMMParam004; // native input: mat_foregroundColor
vec4 mat_foregroundColor = uMMParam004;
uniform vec4 uMMParam005; // native input: mat_brightness
float mat_brightness = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_contrast
float mat_contrast = uMMParam006.x;
float mat_time = uTDTime * (mat_speed);



























#define PI 3.14159265358979

float hash( in vec3 p ) 
{
    return fract(sin(p.x*15.32758341+p.y*39.786792357+p.z*59.4583127+7.5312) * 43758.236237153)-.5;
}

vec3 hash3( in vec3 p )
{
    return vec3(hash(p),hash(p+1.5),hash(p+2.5));
}

float gavoronoi3b(in vec3 p)
{    
    vec3 ip = floor(p);
    vec3 fp = fract(p);
    float f = 2.*PI;																																										;
    float v = .8;
    float va = 0.0;
    float wt = 0.0;
    for (int i=-1; i<=1; i++) 
	for (int j=-1; j<=1; j++)
    for (int k=-1; k<=1; k++)     
	{		
        vec3 o = vec3(i, j, k)-.5;       		
        vec3 pp = fp +o  - v*hash3(ip - o);
        float d = length(pp);
        float w = exp(-d*4.);
        wt +=w;
        va +=sin(sqrt(d)*f)*w;
	}    
    return va/wt;
}

float fbmabs( vec3 p ) {
	
	float f=1.2;
   
	float r = 0.0;	
    for(int i = 0;i<5;i++){	
		r += abs(gavoronoi3b( p*f ))/f;       
	    f *=2.3;
	}
	return r/2.;
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord * 2. -1.;
	uv *= mat_scale;
	float n = fbmabs(vec3(uv,mat_time));

    n += mat_brightness;
    n = mix(0.5, n, mat_contrast);

	if (mat_invert) n = 1 - n;

	vec3 color = mix( mat_backgroundColor.rgb, mat_foregroundColor.rgb, n );
	return vec4(color,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
