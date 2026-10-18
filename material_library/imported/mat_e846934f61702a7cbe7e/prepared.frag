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


#ifdef GL_ES

#endif

#define  PI 3.1415926535897932384626433832795
#define TAU 6.283185307179586476925286766559
mat2 rot(float a){return mat2(cos(a),sin(a),-sin(a),cos(a));}
float ease(float p){return(3.*p*p)-(2.*p*p*p);}
float ease(float p,float g){return(p<.5)?(.5*pow(2.*p,g)):(1.-.5*pow(2.*(1.-p),g));}
float c01(float x){return clamp(x,0.,1.);}
const int N=20;
float original(vec2 p){
    float t=fract(iTime/2.);

    float r=100.,d=16.,scal=1.3;

    float tt=ease(t,4.),O=0.;
    for(int a=2;a<=40;a++){
        vec2 p1=p*rot(PI*(float(a)+2.*tt)/float(N));
        p1*=pow(scal,float(a)+(12.*mod(tt,2.)));
        for(int i=0;i<N;i++){
            vec2 p2=p1*rot(TAU*(float(i)/float(N)));
            O+=1.-c01((length(p2-vec2(0,r))-(d/2.))*2.);
        }
    }
    return c01(O);
}
vec4 materialColorForPixel( vec2 texCoord ){
    
    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;

    return vec4(vec3(original(uv)),1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
