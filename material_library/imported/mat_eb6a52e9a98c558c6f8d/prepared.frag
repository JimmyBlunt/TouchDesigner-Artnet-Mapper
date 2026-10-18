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

uniform vec4 uMMParam000; // native input: mat_backgroundColor
vec4 mat_backgroundColor = uMMParam000;
uniform vec4 uMMParam001; // native input: mat_foregroundColor
vec4 mat_foregroundColor = uMMParam001;














vec3 oklab_mix(vec3 lin1, vec3 lin2, float a)
{
    
    const mat3 kCONEtoLMS = mat3(                
         0.4121656120,  0.2118591070,  0.0883097947,
         0.5362752080,  0.6807189584,  0.2818474174,
         0.0514575653,  0.1074065790,  0.6302613616);
    const mat3 kLMStoCONE = mat3(
         4.0767245293, -1.2681437731, -0.0041119885,
        -3.3072168827,  2.6093323231, -0.7034763098,
         0.2307590544, -0.3411344290,  1.7068625689);
                    
    
    vec3 lms1 = pow( kCONEtoLMS*lin1, vec3(1.0/3.0) );
    vec3 lms2 = pow( kCONEtoLMS*lin2, vec3(1.0/3.0) );
    
    vec3 lms = mix( lms1, lms2, a );
    
    lms *= 1.0+0.2*a*(1.0-a);
    
    return kLMStoCONE*(lms*lms*lms);
}

vec3 linear_from_srgb(vec3 rgb)
{
    return pow(rgb, vec3(2.2));
}
vec3 srgb_from_linear(vec3 lin)
{
    return pow(lin, vec3(1.0/2.2));
}

vec4 materialColorForPixel( vec2 texCoord )
{
	float  m = texCoord.x;
	vec3 col1 = oklab_mix(mat_backgroundColor.rgb,mat_foregroundColor.rgb,m);
	vec3 col2 = mix(mat_backgroundColor.rgb,mat_foregroundColor.rgb,m);

	vec3 col = col1;


	if(texCoord.y < 0.5)col = col2;


	return vec4(col,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
