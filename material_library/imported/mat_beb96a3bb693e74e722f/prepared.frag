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
uniform vec4 uMMParam002; // native input: mat_offset
vec2 mat_offset = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: mat_brightness
float mat_brightness = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_contrast
float mat_contrast = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_tint
vec4 mat_tint = uMMParam005;
uniform vec4 uMMParam006; // native input: mat_invert
bool mat_invert = uMMParam006.x > 0.5;
float mat_animation_time = uTDTime * (mat_speed);


















	
float hash(float p){
    return fract(4768.1232345456 * sin(p));
}
#define EULER 2.7182818284590452353602874	
float wave(vec4 uv, vec4 emitter, float speed, float phase, float timeshift){
    float dst = distance(uv, emitter);
    return pow(EULER, sin(dst * phase - timeshift * speed)) / EULER;
}
vec4 wavedrag(vec4 uv, vec4 emitter){
    return normalize(uv - emitter);
}
float seedWaves = 0.0;
vec4 randWaves(){
    float x = hash(seedWaves);
    seedWaves += 1.0;
    float y = hash(seedWaves);
    seedWaves += 1.0;
    float z = hash(seedWaves);
    seedWaves += 1.0;
    float w = hash(seedWaves);
    seedWaves += 1.0;
    return vec4(x,y,z,w) * 2.0 - 1.0;
}
float getwaves5d(vec4 position, float dragmult, float timeshift){
    float iter = 0.0;
    float phase = 6.0;
    float speed = 2.0;
    float weight = 1.0;
    float w = 0.0;
    float ws = 0.0;
    for(int i=0;i<20;i++){
        vec4 p = randWaves() * 30.0;
        float res = wave(position, p, speed, phase, 0.0 + timeshift);
        float res2 = wave(position, p, speed, phase, 0.006 + timeshift);
        position -= wavedrag(position, p) * (res - res2) * weight * dragmult;
        w += res * weight;
        iter += 12.0;
        ws += weight;
        weight = mix(weight, 0.0, 0.2);
        phase *= 1.2;
        speed *= 1.02;
    }
    return w / ws;
}
vec3 polarToXyz(vec2 xy){
    xy *= vec2(2.0 *3.1415,  3.1415);
    float z = cos(xy.y);
    float x = cos(xy.x)*sin(xy.y);
    float y= sin(xy.x)*sin(xy.y);
    return normalize(vec3(x,y,z));
}
vec4 materialColorForPixel( vec2 texCoord )
{
	
	vec2 uv = texCoord;
	
	uv *= mat_scale;	
	float t = mat_animation_time;	
    vec3 color = vec3(1.0) * 
		getwaves5d(vec4(polarToXyz(uv), (mat_offset.x ) * 10.0), 10.0 + mat_offset.y * 10.0,t);
	
    color = mix(vec3(0.5), color, mat_contrast);
    
    color += vec3(mat_brightness);
	
	color *= mat_tint.rgb;
	
	color = mix(color, vec3(1.0)-color,float(mat_invert));		
	vec4 final_color = vec4(color,1.0);	
	return final_color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
