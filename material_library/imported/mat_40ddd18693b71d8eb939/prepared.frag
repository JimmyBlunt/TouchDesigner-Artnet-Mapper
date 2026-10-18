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
uniform vec4 uMMParam001; // native input: mat_center
float mat_center = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_a
float mat_a = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_b
float mat_b = uMMParam003.x;
float mat_time = uTDTime * (mat_speed);


















float focusLine(vec2 uv,float a,float b)
{
    vec2 p=uv;
    float r = length(p);
 	r = mat_center * r - mat_center;
 	float aa = atan(uv.y, uv.x);
 	aa = abs(cos(a * aa + mat_time) + sin(b * aa + mat_time));
 	float d = aa - r;
 	return smoothstep(0.1, 0.4,clamp(d,0.0,1.0));
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord *2. -1;

 	float f = focusLine(uv,mat_a,mat_b);

	vec3 col = vec3(1.);
	col *= f;
	
	return vec4(col,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
