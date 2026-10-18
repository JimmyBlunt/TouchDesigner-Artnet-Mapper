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

uniform vec4 uMMParam000; // native input: mouse
vec2 mouse = uMMParam000.xy;
uniform vec4 uMMParam001; // native input: mat_zoom
float mat_zoom = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_reverse
bool mat_reverse = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_speed
float mat_speed = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_offset
float mat_offset = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_strob
float mat_strob = uMMParam006.x;
float mat_time = uTDTime * (mat_speed);


























































































#ifdef GL_ES

#endif

float iTime = mat_time - mat_offset * 10;




float circle(vec2 st, float size, float w, float s){
    s/=10.0;
    float c = smoothstep(size-s,size+s,length(st*(1.0+w)))-smoothstep(size-s,size+s,length(st*(1.0-w)));
    c*=cos(atan(st.x,st.y)*10.0*mouse.x+iTime*mouse.y*10.0);
    return c;
}

mat2 Rot(float a){
    a*=0.0174533;
    return mat2(cos(a),-sin(a),sin(a),cos(a));
}
vec4 materialColorForPixel(vec2 texCoord) {

    
    vec2 p = texCoord;

    vec2 p1 = p;
    if(p1.x>0.5){
        p1.x=1.0-p1.x;
        
    }
    if(p1.y>0.5){
        p1.y=1.0-p1.y;
        
    }
    p=mix(p,p1,0.0);
    p-=0.5;
    

    p *= mat_zoom;

    float s = 0.051;
    float w = 0.025;
    float c = 1.0;
    float c1 = 0.0;
    float cTmp = 0.0;



    for(int i = 0; i<3;i++){
        for(int j = 0; j<5;j++){
            float t = iTime*15.0*float(i);
            cTmp = circle(p*Rot(120.0*float(i)+iTime*25.0)+vec2(0.0,float(j)*0.05),float(9-j)*0.05,w,s);
            c *= 1.0-cTmp;
            c1 += cTmp;
        }
    }
    c = 1.0-c;
    
    float anim = sin(length(p)*10.0+iTime)*0.5+0.5;
    vec4 col = vec4(mix(vec3(1.0,0.0,0.0)*2.5-anim,vec3(1.0,0.95,0.0)*1.50+anim,c)*clamp(c,0.0,1.0),1.0);
    return col;

}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
