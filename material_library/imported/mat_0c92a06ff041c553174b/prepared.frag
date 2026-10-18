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

uniform vec4 uMMParam000; // native input: lineScale
float lineScale = uMMParam000.x;
uniform vec4 uMMParam001; // native input: harmonic
float harmonic = uMMParam001.x;
uniform vec4 uMMParam002; // native input: lineOffsetSpeed
float lineOffsetSpeed = uMMParam002.x;
uniform vec4 uMMParam003; // native input: brightness
float brightness = uMMParam003.x;
uniform vec4 uMMParam004; // native input: contrast
float contrast = uMMParam004.x;
uniform vec4 uMMParam005; // native input: contrastShift
float contrastShift = uMMParam005.x;
uniform vec4 uMMParam006; // native input: randomMultiply
float randomMultiply = uMMParam006.x;
uniform vec4 uMMParam007; // native input: randomAmt
vec2 randomAmt = uMMParam007.xy;
uniform vec4 uMMParam008; // native input: origin
vec2 origin = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: xyStretch
vec2 xyStretch = uMMParam009.xy;
uniform vec4 uMMParam010; // native input: xyNoiseFactor
vec2 xyNoiseFactor = uMMParam010.xy;



































































































































#ifdef GL_ES

#endif


float mat_random (in vec2 st) { 
    return fract(sin(dot(st.xy,
                         vec2(randomAmt.x,randomAmt.y))) 
                * randomMultiply);
}



float mat_noise(vec2 st) {

    vec2 i = floor(st);
	vec2 f = fract(st);


    vec2 u = f*f*(3.0-2.0*f);
    return mix( mix( mat_random( i + vec2(0.0,0.0) ), 
                     mat_random( i + vec2(1.0,0.0) ), u.x),
                mix( mat_random( i + vec2(0.0,1.0) ), 
                     mat_random( i + vec2(1.0,1.0) ), u.x), u.y);
}


mat2 mat_rotate2d(float angle){
    return mat2(cos(angle *xyNoiseFactor.x),-sin(angle),
                sin(angle * xyNoiseFactor.y),cos(angle));
}


float mat_lines(in vec2 pos, float b){
    float scale = lineScale;
    pos *= scale;
    return smoothstep(0.0,
                    .5+b*.5,
                    abs((sin(pos.x*3.1415)+b*2.0))* brightness);
}


vec4 materialColorForPixel(vec2 texCoord) {
    vec2 st = texCoord.xy;
    st -= vec2(origin);

    vec2 pos = st.yx*vec2(xyStretch);

    float pattern = pos.x;

    
    pos = mat_rotate2d( mat_noise(pos) ) * pos * harmonic + (TIME * lineOffsetSpeed);
    
    
    pattern = mat_lines(pos,0.5);
    
    
	pattern += smoothstep(0.0+contrast+contrastShift,1.0-contrast+contrastShift, pattern);

    return vec4(vec3(pattern),1.0);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
