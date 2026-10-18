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










































































#define pi acos(-1.)
#define tau (2.*pi)

float anim_time = mat_time;

vec2 rotate(vec2 a, float b)
{
    float c = cos(b);
    float s = sin(b);
    return vec2(
        a.x*c - a.y*s,
        a.x*s + a.y*c
    );
}

float sdbox2d(vec2 p, float r)
{
    p=abs(p);
    return max(p.x,p.y)-r;
}

vec2 boffset(vec2 p, float t)
{
    t*=pi*2.;
    return rotate(p+vec2(
        cos(t)*2.,
        -sin(t*3.)
    )*.15, sin(t)*(pi*2./3.));
}

float tick(float t)
{
    t = smoothstep(0.,1.,t);
    t = smoothstep(0.,1.,t);
    t = smoothstep(0.,1.,t);
    t = smoothstep(0.,1.,t);
    return t;
}

float pattern(float t)
{
    t=fract(t);
    return clamp(abs(t-.5)*-16.+7.5,-1.,1.)+1.;
    return tick(abs(t-.5)*2.);
}

float scene2(vec2 p, float angle)
{
    float t = ((angle/tau)/5.)*4.+anim_time*.25;

    float q = anim_time+angle;

    float r = .02 + pattern((angle/tau)*30.)*.02;

    float a = sdbox2d(boffset(p,t),r);
    float b = sdbox2d(boffset(p,t+1./5.),r);
    float c = sdbox2d(boffset(p,t+2./5.),r);
    float d = sdbox2d(boffset(p,t+3./5.),r);
    float e = sdbox2d(boffset(p,t+4./5.),r);
    return min(min(min(a,b),min(c,d)),e);
}

float scene(vec3 p)
{
    p.xz = mod(p.xz+2.,4.)-2.;

    float angle = atan(p.x,p.z);

    float q = .75;

    p.y += (angle/tau)*(q+q);

    p.y = mod(p.y+q,(q+q))-q;

    vec2 a = vec2(length(p.xz)-1., p.y);

    return scene2(a, angle);
}

vec4 materialColorForPixel(vec2 texCoord)
{

    vec4 out_color = vec4(0.25);

    vec2 uv = texCoord - vec2(0.5);

    uv *= 1.+length(uv)*.3;

    



    uv = abs(uv);
    uv=vec2(max(uv.x,uv.y),min(uv.x,uv.y)).yx;
    uv *= 2.5;

    uv *= mat_zoom;

    vec3 cam = vec3(0,0,-5);
    vec3 dir = normalize(vec3(uv, 2.5));

    cam.yz = rotate(cam.yz, pi/5.);
    dir.yz = rotate(dir.yz, pi/5.);

    cam.xz = rotate(cam.xz, pi/4.);
    dir.xz = rotate(dir.xz, pi/4.);

    cam.y += anim_time;

    float t =0.;
    float k = 0.;
    int iter=0;
    for(int i=0;i<100;++i)
    {
        k = scene(cam+dir*t)*.7;
        t+=k;
        iter=i;
        if (k < .001)break;
    }
    vec3 h = cam+dir*t;
    vec2 o = vec2(.002,0);
    vec3 n = normalize(vec3(
        scene(h+o.xyy)-scene(h-o.xyy),
        scene(h+o.yxy)-scene(h-o.yxy),
        scene(h+o.yyx)-scene(h-o.yyx)
    ));

    if (k < .001)
    {
        float iterFog = 1.-float(iter)/100.;
        iterFog = pow(iterFog, 3.);
        float light = max(n.y,0.);
        out_color.rgb += mix(vec3(.01,.01,.1), vec3(.1,.5,.5), iterFog);
        out_color.rgb += mix(vec3(0.), vec3(sin(anim_time),sin(anim_time+2.),sin(anim_time+4.))+1., light*iterFog);
    }
    else
    {
        out_color *= 0.;
    }

    out_color.rgb = vec3(pow(length(out_color.rgb)/sqrt(3.),2.));
    out_color.a = 1.0;

    return out_color;
}
    








void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
