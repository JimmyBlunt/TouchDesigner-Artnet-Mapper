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

uniform vec4 uMMParam000; // native input: mat_outline
float mat_outline = uMMParam000.x;
uniform vec4 uMMParam001; // native input: adjust
float adjust = uMMParam001.x;
uniform vec4 uMMParam002; // native input: speed
float speed = uMMParam002.x;
uniform vec4 uMMParam003; // native input: bpmsync
bool bpmsync = uMMParam003.x > 0.5;
float animation_time = uTDTime * (speed);



















































#define M_PI 3.1415926535897932384626433832795
#define SMOOTH(r,R) (1.0-smoothstep(R-1.0,R+1.0, r))

vec4 materialColorForPixel(vec2 texCoord)
{
    vec2 uv = texCoord;
    uv = (uv * vec2(1,adjust)) + vec2(0,(1.0-adjust)/2.0);

    
    vec2 st = uv;    
    vec2 bl = smoothstep(vec2(mat_outline/2),vec2(mat_outline/2 + 0.005),st); 
    float pct = bl.x * bl.y;

    
    vec2 tr = smoothstep(vec2(mat_outline/2),vec2(mat_outline/2 + 0.005),1.0-st);
    pct *= tr.x * tr.y;

	if (pct > 0) return vec4(0,0,0,1);
	
    
    vec2 vecFromCenter = texCoord-vec2(0.5,0.5);
    float angle = 2*M_PI+atan(vecFromCenter.y,vecFromCenter.x);
    float animAngle = 2*M_PI*fract(animation_time);
	float angleDist = mod(4*M_PI+(angle-animAngle),2*M_PI);
    float luma = 0.5 + 0.5 * sin(angleDist);

    return vec4(vec3(luma),1);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
