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
uniform vec4 uMMParam001; // native input: mat_force
float mat_force = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_complexity
int mat_complexity = int(round(uMMParam002.x));
uniform vec4 uMMParam003; // native input: mat_zoom
float mat_zoom = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_x
float mat_x = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_y
float mat_y = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_colour2
vec4 mat_colour2 = uMMParam006;
float mat_time = uTDTime * (mat_speed);



















#define PI 3.14159265359


vec2 rotate2D (vec2 _st, float _angle) {
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    return _st;
}

vec4 materialColorForPixel( vec2 p )
{
	p.x -= mat_x;
	p.y -= mat_y;
    p *= mat_zoom;

    float power = pow(mat_force/5.5, 3.);
    vec4 color = mat_colour2;
    float r = length(p)*1.;
    float w = 1.5;
    float time = -mat_time *1.5;
    float t = sin(r*3.0+time*PI*.35)*2.5/power;
    p *= t;
    p = rotate2D(p,(r*PI*0.8*mat_complexity-time*.6));
    color *= smoothstep(-w,.0,p.x)*smoothstep(w,.0,p.x);
    color *= distance(vec2(0.), vec2(cos(r*4.3+time*PI*0.25)));
    
	return color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
