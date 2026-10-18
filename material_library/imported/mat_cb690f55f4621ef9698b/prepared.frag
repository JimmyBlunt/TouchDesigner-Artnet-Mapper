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
uniform vec4 uMMParam002; // native input: mat_edge
bool mat_edge = uMMParam002.x > 0.5;



















float pow1d5(float a) { return a * sqrt(a); }

float hash21(vec2 co) {
  return fract(sin(dot(co.xy, vec2(1.9898, 7.233))) * 45758.5433);
}

float hash(vec2 uv) {

	return pow1d5(hash21(uv));
}

float edgeMin(float dx, vec2 da, vec2 db) {
  return min(min((1. - dx) * db.y, da.x), da.y);
}



vec2 trinoise(vec2 uv) {
  const float sq = sqrt(3. / 2.);
  uv.x *= sq;
  uv.y -= .5 * uv.x;
  vec2 d = fract(uv);
  uv -= d;

  bool c = dot(d, vec2(1)) > 1.;

  vec2 dd = 1. - d;
  vec2 da = c ? dd : d, db = c ? d : dd;

  float nn = hash(uv + float(c));
  float n2 = hash(uv + vec2(1, 0));
  float n3 = hash(uv + vec2(0, 1));

  float nmid = mix(n2, n3, d.y);
  float ns = mix(nn, c ? n2 : n3, da.y);
  float dx = da.x / db.y;
  return vec2(mix(ns, nmid, dx), edgeMin(dx, da, db));
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord *2.-1.;
	uv *= mat_scale;

	
	vec2 n = trinoise(uv);

	if(mat_edge) return vec4(n,0.,1.);

	return vec4(n.x,n.x,n.x,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
