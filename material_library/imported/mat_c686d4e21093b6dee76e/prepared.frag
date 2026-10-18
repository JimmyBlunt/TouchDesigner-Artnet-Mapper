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
uniform vec4 uMMParam002; // native input: mat_turb
bool mat_turb = uMMParam002.x > 0.5;
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






















#define rot(a) mat2(cos(a),-sin(a),sin(a),cos(a))
#define pi acos(-1.)
#define pmod(p,a) mod(p - 0.5*(a),(a)) - 0.5*(a)

mat3 getOrthogonalBasis(vec3 direction){
    direction = normalize(direction);
    vec3 right = normalize(cross(vec3(0,1,0),direction));
    vec3 up = normalize(cross(direction, right));
    return mat3(right,up,direction);
}
float cyclicNoise(vec3 p, bool turbulent, float time){
    float noise = 0.;
    
    p.yz *= rot(0.5);
    float amp = 1.;
    float gain = 0.9 + sin(p.z*0.2)*0.2;
    const float lacunarity = 1.6;
    const int octaves = 5;
    
    const float warp = 2.2;    
    float warpTrk = 1.5 ;
    const float warpTrkGain = .2;
    
    vec3 seed = vec3(-4,-2.,0.5);
    mat3 rotMatrix = getOrthogonalBasis(seed);
    
    for(int i = 0; i < octaves; i++){
        
        p += sin(p.zxy*warpTrk + vec3(0,-time*2.,0) - 2.*warpTrk)*warp; 
        noise += sin(dot(cos(p), sin(p.zxy + vec3(0,time*0.3,0))))*amp;
    
        p *= rotMatrix;
        p *= lacunarity;
        
        warpTrk *= warpTrkGain;
        amp *= gain;
    }
    
    if(turbulent){
        return 1. - abs(noise)*0.5;
    
    }{
        return (noise*0.25 + 0.5);

    }
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord *2. -1.;
	float n = cyclicNoise(vec3(uv*mat_scale,mat_time),mat_turb, 0.);

   
    n += mat_brightness;
    
    n = mix(0.5, n, mat_contrast);
	n = clamp(n,0.,1.);
	if (mat_invert) n = 1 - n;

	vec3 color = mix( mat_backgroundColor.rgb, mat_foregroundColor.rgb, n );
	return vec4(color,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
