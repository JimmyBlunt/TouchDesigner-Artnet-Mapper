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

uniform vec4 uMMParam000; // native input: thickness
float thickness = uMMParam000.x;
uniform vec4 uMMParam001; // native input: size
float size = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_zoom
float mat_zoom = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_reverse
bool mat_reverse = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: mat_speed
float mat_speed = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_offset
float mat_offset = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_strob
float mat_strob = uMMParam007.x;
float mat_time = uTDTime * (mat_speed);




























































































#ifdef GL_ES

#endif

float iTime = mat_time - mat_offset;



float rectangle(vec4 borders, vec2 coords){
    vec4 coordVals = vec4(coords.x, 1. - coords.x, 1. - coords.y, coords.y);
    vec4 vals = step(borders, coordVals);
    float val = (vals.x * vals.y * vals.z * vals.w);

    return val;
}

float rectangleOutline(vec4 borders, vec2 coords, float thickness){
    vec4 realBorders = vec4(borders.x  + thickness, borders.y + thickness,
                            borders.z + thickness, borders.w + thickness);

    return abs(rectangle(borders, coords) * (rectangle(realBorders, coords) - 1.));
}

vec2 tile(vec2 coords, float zoom, bool brick){ 
    coords *= zoom;
    float t = iTime * .5;
    if (brick){
        if( fract(t)>0.5 ){
            if (fract( coords.y * 0.5) > 0.5){
                coords.x += fract(t)*2.0;
            } else {
                coords.x -= fract(t)*2.0;
            }
        } else {
            if (fract( coords.x * 0.5) > 0.5){
                coords.y += fract(t)*2.0;
            } else {
                coords.y -= fract(t)*2.0;
            }
        }
    }
    return fract(coords);
}
vec2 rotate2D(vec2 coords, float angle){ 
    coords -= 0.500;
    coords =  mat2(cos(angle),-sin(angle),
                sin(angle),cos(angle)) * coords;
    coords += 0.5;
    return coords;
}


vec4 materialColorForPixel( vec2 texCoord ) {
    

    vec2 st = texCoord;

    st *= mat_zoom;

    st = tile(st, 5., true);
    st = rotate2D(st, iTime);

    float t = abs(sin(iTime));
    float c = rectangleOutline(vec4(size), st, thickness);

    return vec4(c, c, c, 1.0);

    
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
