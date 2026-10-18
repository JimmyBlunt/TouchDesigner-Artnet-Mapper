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

uniform vec4 uMMParam000; // native input: seed1
float seed1 = uMMParam000.x;
uniform vec4 uMMParam001; // native input: seed2
float seed2 = uMMParam001.x;
uniform vec4 uMMParam002; // native input: scale
float scale = uMMParam002.x;
uniform vec4 uMMParam003; // native input: rate
float rate = uMMParam003.x;
uniform vec4 uMMParam004; // native input: zoom
float zoom = uMMParam004.x;
uniform vec4 uMMParam005; // native input: line
float line = uMMParam005.x;
uniform vec4 uMMParam006; // native input: flash
float flash = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mirror
bool mirror = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: color
bool color = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: cycle
float cycle = uMMParam009.x;

























































































#ifdef GL_ES

#endif

#define S(a, b, t) smoothstep(a, b, t)

float N1(float n) {
	return fract(sin(n) * 43758.5453123);
}

float N11(float p) {
	float fl = floor(p);
	float fc = fract(p);
	return mix(N1(fl), N1(fl + 1.0), fc);
} 

float N21(vec2 p) { return fract(sin(p.x * floor(seed1) + p.y * floor(seed2)) * floor(seed2+seed1)); }

vec2 N22(vec2 p) { return vec2(N21(p), N21(p + floor(seed2))); }

float L(vec2 p, vec2 a, vec2 b) {
	vec2 pa = p-a, ba = b-a;
	float t = clamp(dot(pa, ba)/dot(ba, ba), 0.0, 1.0);
	float d = length(pa - ba * t);
	float m = S(0.02, 0.0, d);
	d = length(a-b);
	float f = S(1.0, 0.8, d);
	m *= f;
	m += m*S(0.05, 0.06, abs(d - 0.5)) * 2.0;
	return m;
}

vec2 GetPos(vec2 p, vec2 o) {
	p += o;
	vec2 n = N22(p)*TIME*rate;
	p = sin(n) * line;
	return o+p;
}

float G(vec2 uv) {
	vec2 id = floor(uv);
	uv = fract(uv) - 0.5;
	vec2 g = GetPos(id, vec2(0));
	float m = 0.0;
	for(float y=-1.0; y<=1.0; y++) {
		for(float x=-1.0; x<=1.0; x++) {
			vec2 offs = vec2(x, y);
			vec2 p = GetPos(id, offs);
			m+=L(uv, g, p);
			vec2 a = p-uv;
			float f = 0.003/dot(a, a);
			f *= pow( sin(N21(id+offs) * 6.2831 + (flash*TIME)) * 0.4 + 0.6, flash);
			m += f;
		}
	}
	m += L(uv, GetPos(id, vec2(-1, 0)), GetPos(id, vec2(0, -1)));
	m += L(uv, GetPos(id, vec2(0, -1)), GetPos(id, vec2(1, 0)));
	m += L(uv, GetPos(id, vec2(1, 0)), GetPos(id, vec2(0, 1)));
	m += L(uv, GetPos(id, vec2(0, 1)), GetPos(id, vec2(-1, 0)));
	return m;
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = (2.25 - scale) * texCoord;
	if (mirror) { if(uv.x<0.0) uv.x = abs(uv.x); }
	float m = 0.0;
	vec3 col;
	for(float i=0.0; i<1.0; i+=0.2) {
		float z = fract(i+TIME*zoom);
		float s = mix(10.0, 0.5, z);
		float f = S(0.0, 0.4, z) * S(1.0, 0.8, z);
		m += G(uv * s + (N11(i)*100.0) * i) * f;
	}
	if (color) { col = 0.5 + sin(vec3(1.0, 0.5, 0.75)*TIME*cycle) * 0.5; }
	else col = vec3(1.0);
	col *= m; 
	return vec4( col, 1.0 );
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
