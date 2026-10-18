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

uniform vec4 uMMParam000; // native input: mat_scale
float mat_scale = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_stroke
float mat_stroke = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_stroke_inner
float mat_stroke_inner = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
float mat_time = uTDTime * (mat_speed);

















#define PI 3.141592
#define TAU 6.283185

float fillSpiritDeck(float x, float size)
{
    return 1.-step(size, x);
}

float polySDFSpiritDeck(vec2 st, int V)
{
    
    float a = atan(st.x, st.y) + PI;
    float r = length(st);
    float v = TAU/float(V);
    return cos(floor(.5+a/v)*v-a)*r;
}

vec4 materialColorForPixel( vec2 texCoord )
{

  	vec2 uv = texCoord - .5;
    uv /= mat_scale;
    
    float t = mat_time *.1;
    vec2 rng = vec2(3., 10.);
    
    int poly = int((sin(t *TAU ) * .5 + .5) * (rng.y-rng.x) + rng.x);

    float d1 = polySDFSpiritDeck(uv, poly);
    vec2 domain = vec2(uv.x, -uv.y);
    float d2 = polySDFSpiritDeck(domain, poly);

    vec3 col = vec3(0.);
    col += fillSpiritDeck(d1, .7) * fillSpiritDeck(fract(d1 * cos(t*PI * 2.) * 8.), mat_stroke);
    col -= fillSpiritDeck(d2, .6) * fillSpiritDeck(fract(d2 * sin(t*PI * 2.) * 8.), mat_stroke_inner);
    
    return vec4(col,1.0);
	
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
