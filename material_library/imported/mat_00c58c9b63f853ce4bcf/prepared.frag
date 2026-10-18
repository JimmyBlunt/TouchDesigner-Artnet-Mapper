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
uniform vec4 uMMParam002; // native input: mat_cycle
float mat_cycle = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_invert
bool mat_invert = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_backgroundColor
vec4 mat_backgroundColor = uMMParam004;
uniform vec4 uMMParam005; // native input: mat_foregroundColor
vec4 mat_foregroundColor = uMMParam005;
uniform vec4 uMMParam006; // native input: mat_brightness
float mat_brightness = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_contrast
float mat_contrast = uMMParam007.x;
float mat_time = uTDTime * (mat_speed);

























const float mat_pi = 3.1415926535;
#define rot(a) mat2(cos(a),sin(a),-sin(a),cos(a))
#define h13(n) fract((n)*vec3(12.9898,78.233,45.6114)*43758.5453123)
vec2 vor(vec2 v, vec3 p, vec3 s){
    p = abs(fract(p-s)-0.5);
    float a = max(p.x,max(p.y,p.z));
    float b = min(v.x,a);
    float c = max(v.x,min(v.y,a));
    return vec2(b,c);
}

float vorMap(vec3 p){
    vec2 v = vec2(5.0);
    v = vor(v,p,h13(0.96));
    p.xy*=rot(1.2);
    v = vor(v,p,h13(0.55));
    p.yz*=rot(2.);
    v = vor(v,p,h13(0.718));
    p.zx*=rot(2.7);
    v = vor(v,p,h13(0.3));
    return v.y+v.x; 
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord *2. - 1.;
	uv *= mat_scale;

	float G = vorMap(vec3(uv,mat_time));

	G = fract(G  + mat_cycle*0.9999);

    
    G += mat_brightness;
    
    G = mix(0.5, G, mat_contrast);
	G = clamp(G,0.,1.);

	if (mat_invert) G = 1 - G;

	vec3 color = mix( mat_backgroundColor.rgb, mat_foregroundColor.rgb, G );


	return vec4(color,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
