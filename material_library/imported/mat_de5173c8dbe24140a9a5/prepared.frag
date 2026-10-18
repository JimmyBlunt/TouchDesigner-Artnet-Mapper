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

uniform vec4 uMMParam000; // native input: scale
float scale = uMMParam000.x;
uniform vec4 uMMParam001; // native input: speed
float speed = uMMParam001.x;
uniform vec4 uMMParam002; // native input: reverse
bool reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: foregroundColor
vec4 foregroundColor = uMMParam003;
uniform vec4 uMMParam004; // native input: brightness
float brightness = uMMParam004.x;
uniform vec4 uMMParam005; // native input: contrast
float contrast = uMMParam005.x;
float animation_time = uTDTime * (speed);























float range(float val, float mi, float ma) {
    return val * (ma - mi) + mi;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec2 p = vec2(0.5,0.5) + (texCoord-vec2(0.5,0.5)) * scale;
    float t = animation_time;
    
    
    float x = p.x;
    float y = p.y;
    
    float mov0 = x+y+cos(sin(t)*2.0)*100.+sin(x/100.)*1000.;
    float mov1 = -y / 0.5 +  t;
    float mov2 = -x / 0.82;
    
    float c1 = abs(sin(mov1+t)/2.+mov2/2.-mov1-mov2+t);
    float c2 = abs(sin(c1+sin(mov0/1000.+t)+sin(y/40.+t)+sin((x+y)/100.)*3.));
    float c3 = abs(sin(c2+cos(mov1+mov2+c2)+cos(mov2)+sin(x/1000.)));
    
    float value = -1 + 2 * (range(c2, 0.55, 0.65) + range(c3, 0.5, 0.55) + range(c3, 1., 0.75)) / 3;
    vec3 color = foregroundColor.rgb * value;

     
    color = mix(vec3(0.5), color, contrast);

    
    color += vec3(brightness);

    return vec4(color,1.0);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
