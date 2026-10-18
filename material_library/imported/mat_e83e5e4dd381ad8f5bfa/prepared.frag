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
uniform vec4 uMMParam002; // native input: mat_cA
vec4 mat_cA = uMMParam002;
uniform vec4 uMMParam003; // native input: mat_cB
vec4 mat_cB = uMMParam003;
float mat_time = uTDTime * (mat_speed);
#define mat_tex_noise sTD2DInputs[0]
#define mat_tex_panther sTD2DInputs[1]





















#define fma(a,b,c) (a*b+c)
vec2 rotate( in vec2 p, in float angle )
{
	vec2 cossin = vec2(cos(angle), sin(angle));
	return( vec2(fma(p.x, cossin.x, p.y * cossin.y), fma(p.x, -cossin.y, p.y * cossin.x)) );
}

vec4 materialColorForPixel( vec2 texCoord )
{

	vec2 uv = texCoord *2.-1.;
	uv *= mat_scale;

    vec2 p = rotate(uv, texture(mat_tex_noise, uv).r - 0.5f) * 0.1f;
    float tex = texture(mat_tex_panther, rotate((uv + p) * 0.125f, mat_time * 0.1f), 0.0f).r;
    
    vec3 T = vec3(uv, abs(sin(tex * 3.14 + mat_time)));
  	vec3 G = exp2(-1.618*T*T);         
    float N = G.x*G.y*G.z;
	float C = (1.0f - N) * N;
	C = pow(C + 0.7,3.2);
	
	vec3 col = mix(mat_cA.rgb,mat_cB.rgb, vec3(C));
	return vec4(col,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
