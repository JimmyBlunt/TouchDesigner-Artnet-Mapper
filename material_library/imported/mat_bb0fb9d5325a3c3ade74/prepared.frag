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

uniform vec4 uMMParam000; // native input: horizon
vec2 horizon = uMMParam000.xy;
uniform vec4 uMMParam001; // native input: grid
vec2 grid = uMMParam001.xy;
uniform vec4 uMMParam002; // native input: zoom
float zoom = uMMParam002.x;
uniform vec4 uMMParam003; // native input: fog
float fog = uMMParam003.x;
uniform vec4 uMMParam004; // native input: tint
float tint = uMMParam004.x;





























































#ifdef GL_ES

#endif

vec4 materialColorForPixel(vec2 texCoord) {
	vec2 position = texCoord;

	float y = position.y - horizon.y;
	float yy = abs(y);
	if (y > 0.5) {
		return vec4(0.25);
	} 
	
	y /= (horizon.y) ;
	
	float z = 1.0 / yy;
	float x = (position.x - 0.5) / yy;
	float color = 0.01;
	if (sin(z * 8.0 + TIME* zoom) > grid.y) {
		color += 0.3;
	} else {
	}
	if (sin(x * 40.0 + TIME *  - horizon.x * 100.0) > grid.x) {
		color += 0.3;
	} else {
	}
	vec4 result = vec4( vec3( color * (7.0 - tint), color * (tint + 1.0), sin( color + TIME / 2.0 ) * 0.85 ), 6.0 );

	if (yy < 0.99) {
		result *= (yy*(5.0-fog));
	}

  return result;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
