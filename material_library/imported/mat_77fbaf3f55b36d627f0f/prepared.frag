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
uniform vec4 uMMParam001; // native input: mat_reverse
bool mat_reverse = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: grid
vec2 grid = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: density
float density = uMMParam003.x;
uniform vec4 uMMParam004; // native input: seed1
float seed1 = uMMParam004.x;
uniform vec4 uMMParam005; // native input: seed2
float seed2 = uMMParam005.x;
uniform vec4 uMMParam006; // native input: seed3
float seed3 = uMMParam006.x;
uniform vec4 uMMParam007; // native input: offset1
float offset1 = uMMParam007.x;
uniform vec4 uMMParam008; // native input: offset2
float offset2 = uMMParam008.x;
float mat_animation_time = uTDTime * (mat_speed);






















































































 
float ranf(in float x) {
    return fract(sin(x)*1e4);
}

float rant(in vec2 st) { 
    return fract(sin(dot(st.xy, vec2(seed1,seed2)))*seed3);
}

float pattern(vec2 st, vec2 v, float t) {
    vec2 p = floor(st+v);
    return step(t, rant(100.+p*.000001)+ranf(p.x)*0.5 );
}

vec4 materialColorForPixel(vec2 texCoord) {
    vec2 st = texCoord;
    st *= grid;
    
    vec2 ipos = floor(st);  
    vec2 fpos = fract(st);  
    vec2 vel = vec2(mat_animation_time*max(grid.x,grid.y)); 
    vel *= vec2(-1.,0.0) * ranf(1.0+ipos.y); 
    vec2 off1 = vec2(offset1,0.);
    vec2 off2 = vec2(offset2,0.);
    vec3 color = vec3(0.);
    color.r = pattern(st+off1,vel,0.5+density/1024);
    color.g = pattern(st,vel,0.5+density/1024);
    color.b = pattern(st-off2,vel,0.5+density/1024); 
    color *= step(0.2,fpos.y);

    return vec4(color,1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
