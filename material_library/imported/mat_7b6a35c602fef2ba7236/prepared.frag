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
















































































float iTime = mat_time - mat_offset * 10;


vec2 hash(vec2 p)
{
    mat2 m = mat2(  13.85, 47.77,
                    99.41, 88.48
                );

    return fract(sin(m*p) * 46738.29);
}

float voronoi(vec2 p)
{
    vec2 g = floor(p);
    vec2 f = fract(p);

    float distanceToClosestFeaturePoint = 1.0;
    for(int y = -1; y <= 1; y++)
    {
        for(int x = -1; x <= 1; x++)
        {
            vec2 latticePoint = vec2(x, y);
            float currentDistance = distance(latticePoint + hash(g+latticePoint), f);
        
            distanceToClosestFeaturePoint = min(distanceToClosestFeaturePoint, currentDistance);
        }
    }

    return distanceToClosestFeaturePoint;
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;



    float r = voronoi( uv*2.0) * 5.50;
    float xWaves = smoothstep(0.1,1.0,sin(uv.x*2.0+iTime)*2.0);
    float yWaves = smoothstep(0.1,1.0,sin(uv.x*3.0+iTime*2.0)*2.0);
    float f = fract(uv.x*1.0+iTime);
    float t =voronoi( uv*8.0+iTime) * 1.50;
    vec3 c = sin(clamp(r*t/f*3.1415,0.0,20.0))*vec3(0.5,1.0,01.85);
    vec3 c1 = sin(1.0-clamp(r*1.25*3.1415,4.0,14.0))*xWaves*vec3(0.85,1.0,01.85);
    vec3 c2 = sin(1.0-clamp(r*1.25*3.1415,4.0,10.0))*yWaves*vec3(0.0,0.8,01.05);

        vec3 finalColor = vec3(c);
    return vec4(finalColor, 1.0 );

}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
