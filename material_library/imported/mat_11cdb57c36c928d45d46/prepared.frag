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

uniform vec4 uMMParam000; // native input: mat_nbCircles
int mat_nbCircles = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_radius
float mat_radius = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_blur
float mat_blur = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_pulseSize
float mat_pulseSize = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_pulseSpeed
float mat_pulseSpeed = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_amplitude
float mat_amplitude = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_color
vec4 mat_color = uMMParam007;
uniform vec4 uMMParam008; // native input: mat_brightness
float mat_brightness = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_hueOffset
float mat_hueOffset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_colorMode
bool mat_colorMode = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: mat_reverse
bool mat_reverse = uMMParam011.x > 0.5;
float mat_time = uTDTime * (mat_speed);
float mat_pulsetime = uTDTime * (mat_pulseSpeed);

























vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}


vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec4 materialColorForPixel(vec2 texCoord) {
    
    texCoord.y = 1.0 - texCoord.y;
    
    
    vec3 finalColor = vec3(0.0);
    
    
    vec3 baseColorHSV = rgb2hsv(mat_color.rgb);
    
    
    for (float i = 0.0; i < 100.0; i++) {
        if (i >= mat_nbCircles) break;
        
        
        float phase = i * 6.28 / mat_nbCircles;
        float posX = 0.5 + mat_amplitude * cos(mat_time + phase);
        float posY = 0.5 + mat_amplitude * sin(mat_time * 0.7 + phase);
        
        
        float animRadius = mat_radius + mat_pulseSize * sin(mat_pulsetime + phase);
        
        
        float dist = distance(texCoord, vec2(posX, posY));
        float blurFactor = max(0.001, mat_blur); 
        float circleValue = smoothstep(animRadius, animRadius - blurFactor, dist) * 0.5;
        
        
        if (mat_blur > 0.0) {
            circleValue = 0.5 * (1.0 - smoothstep(animRadius - blurFactor, animRadius + blurFactor, dist));
        }
        
        
        vec3 circleHSV = baseColorHSV;
        circleHSV.x = fract(circleHSV.x + i * pow(mat_hueOffset,3));
        vec3 circleRGB = hsv2rgb(circleHSV);
        
        
        finalColor += circleValue * mat_brightness * (mat_colorMode ? circleRGB : vec3(1.0));
    }
    
    
    finalColor = min(finalColor, vec3(1.0));
    
    return vec4(finalColor, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
