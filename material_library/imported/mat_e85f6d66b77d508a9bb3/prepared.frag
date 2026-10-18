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

uniform vec4 uMMParam000; // native input: mat_zoom
float mat_zoom = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_reverse
bool mat_reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_offset
float mat_offset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_strob
float mat_strob = uMMParam005.x;
float mat_time = uTDTime * (mat_speed);














































































#ifdef GL_ES

#endif

float iTime = mat_time - mat_offset*10;



#define PI 3.141592653589793
#define TWO_PI  6.283


float backOut(float t) {
    float f = 1.0 - t;
    return 1.0 - (pow(f, 3.0) - f * sin(f * PI));
}

vec2 random(vec2 p) {
    return fract(sin(vec2(dot(p,vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)))) * 43758.5453);
}

mat2 rotate2d(float _angle){
    return mat2(cos(_angle), -sin(_angle),  sin(_angle), cos(_angle));
}

float map(float value, float beforeMin, float beforeMax, float afterMin, float afterMax) {
    return afterMin + (afterMax - afterMin) * ((value - beforeMin) / (beforeMax - beforeMin));
}

float obliqueLine(vec2 uv){
    return step(0.6, fract((uv.x + uv.y + iTime * 0.8) * 4.0));
}

vec4 materialColorForPixel( vec2 texCoord ) {
    
    vec2 uv = texCoord - vec2(0.5);

    uv *= 2. * mat_zoom;
    vec2 scaledUv = uv * 8.0;

    scaledUv -= 0.5;
    scaledUv *= rotate2d(iTime * 0.2);
    scaledUv += 0.5;

    vec2 i_st = floor(scaledUv);
    vec2 f_st = fract(scaledUv);

    float m_dist = 1.0;

    
    

    float t = iTime;
    float speed = (floor(t) + backOut(fract(t)));



    for (int j = -1; j <= 1; j++) {
        for (int i = -1; i <= 1; i++) {
            
            vec2 neighbor = vec2(float(i), float(j));

            
            vec2 offset = random(i_st + neighbor);

            
            offset = vec2(
                map(sin(speed + TWO_PI * offset).x, -1.0, 1.0, 0.0, 1.0),
                map(sin(speed + TWO_PI * offset).y, -1.0, 1.0, 0.0, 1.0)
            );

            
            vec2 pos = neighbor + offset - f_st;

            
            float dist = length(pos);

            
            m_dist = min(m_dist, m_dist * dist);
        }
    }

    float cell = 1.0 - step(0.1, m_dist);

    vec3 color = vec3(0.05);
    color += cell;

    color.r *= obliqueLine(uv * 4.0);
    color.g *= obliqueLine(uv * 8.0);

    return vec4(color, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
