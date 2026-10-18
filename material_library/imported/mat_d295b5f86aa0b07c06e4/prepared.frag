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

uniform vec4 uMMParam000; // native input: mirror
bool mirror = uMMParam000.x > 0.5;
uniform vec4 uMMParam001; // native input: pattern
bool pattern = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: iteration
float iteration = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_reverse
bool mat_reverse = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: radius
float radius = uMMParam005.x;
uniform vec4 uMMParam006; // native input: centerRadius
float centerRadius = uMMParam006.x;
uniform vec4 uMMParam007; // native input: lineThickness
float lineThickness = uMMParam007.x;
uniform vec4 uMMParam008; // native input: smoothEdge
float smoothEdge = uMMParam008.x;
uniform vec4 uMMParam009; // native input: yOffset
float yOffset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: xOffset
float xOffset = uMMParam010.x;
uniform vec4 uMMParam011; // native input: startValue
float startValue = uMMParam011.x;
uniform vec4 uMMParam012; // native input: endValue
float endValue = uMMParam012.x;
uniform vec4 uMMParam013; // native input: rotate
float rotate = uMMParam013.x;
uniform vec4 uMMParam014; // native input: pos
vec2 pos = uMMParam014.xy;
float mat_anim_time = uTDTime * (mat_speed);
























































































































#define NB 35.
#define MODE1
#define PI 3.14159265358979323846

float circle(vec2 center , float radius,float thickness,float la,float ha)
{
	float f = length(center);
	
	float a = atan(center.y,center.x) ;
	return(smoothstep(f,f+0.01,radius) * smoothstep(radius - thickness,radius - thickness+0.01,f) * step(la,a) *smoothstep(a-smoothEdge,a+smoothEdge,ha));
}

float cable(vec2 p,float dx,float dy,float r,float thick,float la,float ha)
{
	p.x-= dx;
	p.y -= dy;
	return (circle(p,r,thick,la,ha));
}


vec2 rot(vec2 uv,float a){
	return vec2(uv.x*cos(a)-uv.y*sin(a),uv.y*cos(a)+uv.x*sin(a));
}

vec4 materialColorForPixel(vec2 texCoord)
{
	
	vec2 uv = texCoord;
	uv -= vec2(pos - 0.5);

	vec2 p = -1. + 2. * uv;
	
	p=rot(p,rotate * PI);

	
	
	vec2 ap = vec2(0.0);
	if (mirror){
		ap = p * vec2(1.,-1.);
	} else {
		ap = p * vec2(-1.,-1.);
	}



	float f = 0.;
	for(float i = 0.; i < NB; ++i)
	{
		if (i > iteration) break;
		
		if (pattern) f *= -1.; 
		
		float divi = i/iteration * centerRadius;
		f += cable(p,xOffset,yOffset,radius - divi,lineThickness,0.,(sin(mat_anim_time - divi*5.)*startValue+endValue) * 3.14);
		f += cable(ap,xOffset,yOffset,radius - divi,lineThickness,0.,(sin(mat_anim_time - divi*5.)*startValue+endValue) * 3.14);
	}
	vec3 col = mix(vec3(0.,0.,0.),vec3(1.,1.,1.),f);
	
	return vec4(col,1.0);
}



void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
