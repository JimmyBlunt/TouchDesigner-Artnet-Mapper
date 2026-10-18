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

uniform vec4 uMMParam000; // native input: mat_complexity
int mat_complexity = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_scale
float mat_scale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_speed
float mat_speed = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_reset
int mat_reset = int(round(uMMParam003.x));
float mat_iTime = uTDTime * (mat_speed);
















vec3 iResolution = vec3(RENDERSIZE, 1.);


#define TAU 6.2831853
mat2 rz2(float a){float c=cos(a),s=sin(a);return mat2(c,s,-s,c);}

float hlx(vec3 p){
    float m=TAU/5.;
    float t = mat_iTime;
    float a=mod(atan(p.y,p.x)-p.z*0.5+t,m)-.5*m;
    float l=length(p.xy);
    float r = .1+.2*(sin(abs(p.z*4.)+t*4.)*.5+.5);
    return length(vec2(a*l,length(p.xy)-(.5+abs(p.z)*2.)*(1.+sin(abs(p.z)-t*10.)*.5+.5)*0.2))-r;
}

vec3 hsv(vec3 c) {
    vec4 k=vec4(1.,2./3.,1./3.,3.);
    vec3 p=abs(fract(c.xxx+k.xyz)*6.-k.www);
    return c.z*mix(k.xxx,clamp(p-k.xxx,0.,1.),c.y);
}

float map(vec3 p){
    p.xy*=rz2(mat_iTime*.3+length(p)*.05);
    p.yz*=rz2(mat_iTime*.5);
    p.xz*=rz2(mat_iTime*.7);
    float d=min(min(hlx(p.xyz), hlx(p.yzx)),hlx(p.zxy))*(1.+sin(length(p*1.)-mat_iTime*4.)*0.8);
    vec3 n=normalize(sign(p));
    float d2=max(length(max(abs(p)-vec3(1.),0.)),dot(p,n)-2.3);
    return d;
}
float st(float x,float m){return floor(x*m)/m;}
vec4 materialColorForPixel(vec2 fragCoord)
{
    vec2 uv = fragCoord.xy-vec2(.5);
    vec3 ro=vec3(uv,sin(mat_iTime)*2.-20.*mat_scale*mat_scale),rd=vec3(uv,1.),mp=ro;
    float shade = 0.;
    int i = 0;
    float t = mat_iTime;
    for(;i<mat_complexity;++i){
        float md=map(mp);
        if(md<.01){
            break;
        }
        mp+=rd*md*(.25*50/mat_complexity);
    }
    float r=float(i)/50.;
    vec4 fragColor = vec4(hsv(vec3(st(length(mp)*.01-mat_iTime*0.2,6.),.8,1.)),1.);
    fragColor *= 1.-r*(1.-r)*-1.;
    fragColor *= length(mp-ro)*.02;
    fragColor = 1.-fragColor;
    if(length(mp)>20.)fragColor=vec4(0.);
	return fragColor;
}



void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
