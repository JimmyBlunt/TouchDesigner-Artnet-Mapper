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
uniform vec4 uMMParam001; // native input: mat_reverse
bool mat_reverse = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: loops
float loops = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mirror
bool mirror = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: rotate
bool rotate = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: offset
bool offset = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: noise
bool noise = uMMParam006.x > 0.5;
float mat_animation_time = uTDTime * (mat_speed);

























































#define 	pi   	3.141592653589793 	
#define 	PALETTE vec3(.0, 1.4, 2.)+1.5


float w = 1;
float T = mat_animation_time;

mat2 mm2(in float a){float c = cos(a), s = sin(a);return mat2(c,-s,s,c);}

float tri(in float x){return abs(fract(x)-.5);}

vec2 tri2(in vec2 p){return vec2(tri(p.x+tri(p.y*2.)),tri(p.y+tri(p.x*2.)));}

mat2 m2 = mat2( 0.970,  0.242, -0.242,  0.970 );

float triangleNoise(in vec2 p) {
    float z=1.5;
    float z2=1.5;
	float rz = 0.;
    vec2 bp = p;
	for (float i=0.; i<=3.; i++ ) {
        vec2 dg = tri2(bp*2.)*.8;
        dg *= mm2(T*.3);
        p += dg/z2;
        bp *= 1.6;
        z2 *= .6;
		z *= 1.8;
		p *= 1.2;
        p*= m2;
        rz+= (tri(p.x+tri(p.y)))/z;
	}
	return rz;
}

vec4 materialColorForPixel(vec2 texCoord) {
 	vec2 p = texCoord*2.-1.;
    p*= 1.05;
    vec2 bp = p;
   	if (rotate) p *= mm2(T*.25);
    float lp = length(p);
    float id = floor(lp*loops+.5)/loops;
    if (offset) p *= mm2(id*11.);
    if (mirror) p.y = abs(p.y);
    vec2 plr = vec2(lp, atan(p.y, p.x));
    float rz = 1.-pow(abs(sin(plr.x*pi*loops))*1.25/pow(w,0.25),2.5);
    float enp = plr.y+sin((T+id*5.5))*1.52-1.5;
    rz *= smoothstep(0., 0.05, enp);
    rz *= smoothstep(0.,.022*w/plr.x, enp)*step(id,1.);
    if (mirror) rz *= smoothstep(-0.01,.02*w/plr.x,pi-plr.y);
    if (noise) rz *= (triangleNoise(p/(w*w))*0.9+0.4);
    vec3 col = (sin(PALETTE+id*5.+T)*0.5+0.5)*rz;
   	if (noise) col += smoothstep(.4,1.,rz)*0.15, col *= smoothstep(.2,1.,rz)+1.;
	else	col *= smoothstep(.8,1.15,rz)*.7+.8;
  
	return vec4(col,1.0);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
