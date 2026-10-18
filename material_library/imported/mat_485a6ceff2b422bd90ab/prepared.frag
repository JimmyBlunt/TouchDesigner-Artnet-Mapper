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

#define NumberOfParticles 64
#define Pi 3.141592

vec3 palette(float x)
{
    return vec3(
        sin(x*2.0*Pi)+1.5,
        sin((x+1.0/3.0)*2.0*Pi)+1.5,
        sin((x+2.0/3.0)*2.0*Pi)+1.5
    )/2.5;
}

float starline(vec2 relpos,float confradius,float filmsize)
{
    if(abs(relpos.y)>confradius) return 0.0;
    float y=relpos.y/confradius;
    float d=abs(relpos.x/filmsize);
    return sqrt(1.0-y*y)/(0.0001+d*d)*0.00001;
}

float star(vec2 relpos,float confradius,float filmsize)
{
    vec2 rotpos=mat2(cos(Pi/3.0),-sin(Pi/3.0),sin(Pi/3.0),cos(Pi/3.0))*relpos;
    vec2 rotpos2=mat2(cos(Pi/3.0),sin(Pi/3.0),-sin(Pi/3.0),cos(Pi/3.0))*relpos;
    return starline(relpos,confradius,filmsize)+
        starline(rotpos,confradius,filmsize)+
        starline(rotpos2,confradius,filmsize);
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 screenpos = texCoord - vec2(0.5);

    screenpos *= mat_zoom;

    float focaldistance=0.5+sin(iTime*0.05)*0.013;
    float focallength=0.100;
    float filmsize=0.036;
    float minconf=filmsize/1000.0;
    float lensradius=focallength/1.0;

    float filmdistance=1.0/(1.0/focallength-1.0/focaldistance);

    vec3 c=vec3(0.0);
    for(int i=0;i<NumberOfParticles;i++)
    {
        float t=float(i)/float(NumberOfParticles);
        float a=t*2.0*Pi+iTime*0.1;

        vec3 pos=vec3(sin(a)+2.0*sin(2.0*a),cos(a)-2.0*cos(2.0*a),-sin(3.0*a))*0.01;

        float a1=0.1*iTime;
        pos.xz*=mat2(cos(a1),-sin(a1),sin(a1),cos(a1));
        
        

        pos.z+=0.5;

        float intensity=0.0000002;

        vec2 filmpos=pos.xy/pos.z*filmdistance;
        float confradius=lensradius*filmdistance*abs(1.0/focaldistance-1.0/pos.z)+minconf;

        float diffusedintensity=intensity/(confradius*confradius);

        vec3 colour=palette(t);

        vec2 relpos=filmpos-screenpos/2.0*filmsize;
        if(length(relpos)<confradius) c+=colour*diffusedintensity;

        c+=colour*diffusedintensity*star(relpos,confradius,filmsize);
    }

    return vec4(pow(c,vec3(1.0/2.2)),1.0);




}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
