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









































































vec3 iResolution = vec3(RENDERSIZE, 1.);
float iTime = TIME;



vec4 materialColorForPixel( vec2 texCoord ) {

    float adj_time = mat_time - mat_offset*4;

    vec2 uv = texCoord;

    uv *= 200;

    uv *= mat_zoom;

    vec2 R = iResolution.xy,
         U = uv = (uv-R/2.)/R.y * 6. *  1.73/2.;          

    U *= mat2(1,-1./1.73, 0,2./1.73);                     
    vec3 g = vec3(U, 1.-U.x-U.y), g2,                     
         id = floor(g);                                   

    g = fract(g);                                         
    g2 = abs(2.*g-1.);                                    

    U = id.xy * mat2(1,.5, 0,1.73/2.);
    float l00 = length(U-uv),                    
          l10 = length(U+vec2(1,0)-uv),
          l01 = length(U+vec2(.5,1.73/2.)-uv),
          l11 = length(U+vec2(1.5,1.73/2.)-uv),
            l = min(min(l00, l10), min( l01, l11)); 
    vec2 C = U+ ( l==l00 ? vec2(0) : l==l10 ? vec2(1,0) : l==l01 ? vec2(.5,1.73/2.) : vec2(1.5,1.73/2.) );

    return sin(length(40.*l-2.*adj_time)) +vec4(0) - vec4(0);
}




void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
