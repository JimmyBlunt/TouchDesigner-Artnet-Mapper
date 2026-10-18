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


















































































float mat_iTime = mat_time - mat_offset * 10;

#define SURFACE_PRECISION 0.001




vec3 mat_permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

float mat_snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = mat_permute( mat_permute( i.y + vec3(0.0, i1.y, 1.0 ))
  + i.x + vec3(0.0, i1.x, 1.0 ));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
    dot(x12.zw,x12.zw)), 0.0);
  m = m*m ;
  m = m*m ;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return (130.0 * dot(m, g)+1.0)/2.0;
}

float mat_noise(vec2 p){
    float v = 0.0;
    float m = 0.0;
    for (int i =0 ; i< 5; i++)
    {
        float n = pow(2.0,float(i));
        float d = 1.0/n;
        m += d;
        v += mat_snoise(p * n) * d;
    }
    return v/m;
}

float surfaceFunction(vec2 pos)
{
    return sqrt(0.2-pow(pos.x,2.0)-pow(pos.y,2.0))*mat_noise(pos*1.0)*(sin(length(pos)*30.0-mat_iTime)+1.0)/2.0;
}

vec3 surfaceNormal(vec2 pos)
{
    vec2 off_a = vec2(SURFACE_PRECISION,0.0);
    vec2 off_b = vec2(0.0,SURFACE_PRECISION);
    vec3 n_0 = vec3(pos.x,pos.y,surfaceFunction(pos));
    vec3 n_a = vec3(pos.x+off_a.x,pos.y+off_a.y,surfaceFunction(pos+off_a));
    vec3 n_b = vec3(pos.x+off_b.x,pos.y+off_b.y,surfaceFunction(pos+off_b));
    return normalize(cross(n_a-n_0,n_b-n_0));
}

float surfaceOcclusion(vec2 pos)
{
    float depth_here = surfaceFunction(pos);

    float num = 0.0;
    float higher = 0.0;

    const int js = 3;

    for (int i = 0; i < 10; i++)
    {
        float radius = float(i+1)*0.01;
        float weight = 1.0 / float(i);

        for (int j = 0; j < js; j++)
        {
            float r = 3.141592*2.0*float(j)/float(js)+float(i);
            float s = surfaceFunction(vec2(cos(r),sin(r))*radius);

            higher += clamp((s-depth_here)/1.0,0.0,1.0);
            num++;
        }
    }

    return clamp(1.0-(higher/num),0.0,1.0);
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;

    vec2 pos = uv;

    

    vec4 ambientColor = vec4(0.3,0.0,0.0,0.0);

    vec3 lightDirection = normalize(vec3(-1.0,1.0,1.0));
    vec4 lightColor = vec4(1.0,0.0,0.0,1);
    vec4 specularColor = vec4(1,1,1,1);
    vec4 materialColor = vec4(1,1,1,1);

    vec3 surface = surfaceNormal(pos);

    float noisey = mat_noise(pos*5.0);

    float diffuse = max(0.0,dot(lightDirection,surface));
    float specular = pow(max(0.0,dot(normalize(reflect(lightDirection,surface)),normalize(vec3(-pos.x,-pos.y,-1.0)))),6.0);
    specular *= noisey;
    diffuse *= mat_noise(pos*2.0+mat_iTime/20.0);
    float occlusion = 1.0;

    



    vec4 outColor = ambientColor * occlusion;
    outColor = mix(outColor, lightColor, diffuse);
    
    outColor = mix(outColor, specularColor, specular);
    outColor *= materialColor;

        
        
    

    return outColor;


}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
