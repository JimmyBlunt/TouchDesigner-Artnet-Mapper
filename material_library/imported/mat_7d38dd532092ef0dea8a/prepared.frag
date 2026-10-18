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
uniform vec4 uMMParam006; // native input: I_MAX
float I_MAX = uMMParam006.x;
uniform vec4 uMMParam007; // native input: background_on
bool background_on = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: FAR
float FAR = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mod_a
float mod_a = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mod_b
float mod_b = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mod_c
float mod_c = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mod_d
float mod_d = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mod_e
float mod_e = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mod_f
float mod_f = uMMParam014.x;
float mat_time = uTDTime * (mat_speed);





































































































vec2    march(vec3 pos, vec3 dir);
vec3    camera(vec2 uv);
void    rotate(inout vec2 v, float angle);

float   t;          
vec3    ret_col;    
vec3    h;          

float iTime = mat_time - mat_offset * 10;


#define E           0.00001












vec3 blackbody(float Temp)
{
    vec3 col = vec3(255.);
    col.x = 56100000. * pow(Temp,(-3. / 2.)) + 148.;
    col.y = 100.04 * log(Temp) - 623.6;
    if (Temp > 6500.) col.y = 35200000. * pow(Temp,(-3. / 2.)) + 184.;
    col.z = 194.18 * log(Temp) - 1448.6;
    col = clamp(col, 0., 255.)/255.;
    if (Temp < 1000.) col *= Temp/1000.;
    return col;
}





float   scene(vec3 p)
{
    float   var;
    float   mind = 1e5;
    p.z += 10.;

    rotate(p.xz, 1.57-.5*iTime );
    rotate(p.yz, 1.57-.5*iTime );
    var = atan(p.x,p.y);
    vec2 q = vec2( ( length(p.xy) )-6.,p.z);
    rotate(q, var*.25+iTime*2.*0.);
    vec2 oq = q ;
    q = abs(q)-2.5;
    if (oq.x < q.x && oq.y > q.y)
        rotate(q, ( (var*1.)+iTime*0.)*3.14+iTime*0.);
    else
        rotate(q, ( .28-(var*1.)+iTime*0.)*3.14+iTime*0.);
    float   oldvar = var;
    ret_col = 1.-vec3(.350, .2, .3);
    mind = length(q)+.5+mod_a*1.05*(length(fract(mod_d*q*.5*(3.+3.*sin(oldvar*1. - iTime*2.)) )-.5)-1.215);
    h -= vec3(-3.20,.20,1.0)*vec3(1.)*mod_b*.0025/(.051+(mind-sin(oldvar*1. - iTime*2. + 3.14)*.125 )*(mind-sin(oldvar*1. - iTime*2. + 3.14)*.125 ) );
    h -= vec3(1.20,-.50,-.50)*mod_c*vec3(1.)*.025/(.501+(mind-sin(oldvar*1. - iTime*2.)*.5 )*(mind-sin(oldvar*1. - iTime*2.)*.5 ) );
    h += vec3(.25, .4, .5)*.0025/(.021+mind*mind);

    return (mind);
}

vec2    march(vec3 pos, vec3 dir)
{
    vec2    dist = vec2(0.0, 0.0);
    vec3    p = vec3(0.0, 0.0, 0.0);
    vec2    s = vec2(0.0, 0.0);

    float far = FAR;

    
    
    

        for (float i = -1.; i < I_MAX; ++i)
        {
            p = pos + dir * dist.y;
            dist.x = scene(p);
            dist.y += dist.x*.2; 
            


            if (log(dist.y*dist.y/dist.x/1e5) > .0 || dist.x < E || (background_on && dist.y > FAR))
            {
                break;
            }
            s.x++;
    }
    s.y = dist.y;
    return (s);
}



void rotate(inout vec2 v, float angle)
{
    v = vec2(cos(angle)*v.x+sin(angle)*v.y,-sin(angle)*v.x+cos(angle)*v.y);
}

vec3    camera(vec2 uv)
{
    float       fov = 1.;
    vec3        forw  = vec3(0.0, 0.0, -1.0);
    vec3        right = vec3(1.0, 0.0, 0.0);
    vec3        up    = vec3(0.0, 1.0, 0.0);

    return (normalize((uv.x) * right + (uv.y) * up + fov * forw));
}

vec4 materialColorForPixel( vec2 texCoord ) {

    t  = iTime*.125;
    vec3    col = vec3(0., 0., 0.);

    vec2 uv  = texCoord - vec2(0.5);

    uv *= mat_zoom;

    vec3    dir = camera(uv);
    vec3    pos = vec3(.0, .0, 0.0);
    pos.z = mod_e*4.5+1.5*sin(t*10.);
    h*=0.;
    vec2    inter = (march(pos, dir));
    col.xyz = ret_col*(1.-inter.x*.0125);
    col += h * .4 * mod_f;
    return vec4(col,1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
