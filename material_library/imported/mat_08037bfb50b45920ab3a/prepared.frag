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

uniform vec4 uMMParam000; // native input: scale
float scale = uMMParam000.x;
uniform vec4 uMMParam001; // native input: speed
float speed = uMMParam001.x;
uniform vec4 uMMParam002; // native input: reverse
bool reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: foregroundColor
vec4 foregroundColor = uMMParam003;
uniform vec4 uMMParam004; // native input: brightness
float brightness = uMMParam004.x;
uniform vec4 uMMParam005; // native input: contrast
float contrast = uMMParam005.x;
float animation_time = uTDTime * (speed);



















vec2 hash( vec2 p )                       
{
  p = vec2(dot(p,vec2(127.1,311.7)),
           dot(p,vec2(269.5,183.3)));
  return -1. + 2.*fract(sin(p+20.)*53758.5453123);
}


float dunes_noise( in vec2 x )
{
  vec2 p = floor(x);
  vec2 f = fract(x);
  f = f*f*(3.0-2.0*f);
  vec2 uv = (p+vec2(37.0,17.0)) + f;
  vec2 rg = hash( uv/256.0 ).yx;
  return 0.5*mix( rg.x, rg.y, 0.5 );
}


#define GABOR_BLOBS_NB 10       
#define GABOR_BLOBS_SIZE 0.25   
                                

float rnd(int i, int j)
{
  return dunes_noise(vec2(i, j));
}

float DuneStripes (vec2 uv, float d, float freq, float time)
{
  float hv = 0.;
  for (int i=0; i<GABOR_BLOBS_NB; i++) 
  {
    vec2 pos = vec2(rnd(i,0), rnd(i,1));
    vec2 dir = (.15+d)*vec2(rnd(i,2),rnd(i,3)) - d;
    hv += GABOR_BLOBS_SIZE * sin(dot(uv-pos, freq*dir) * 6. + time);
  }
  return hv;
}

vec4 materialColorForPixel(vec2 texCoord)
{
  vec2 uv = vec2(0.5,0.5) + (texCoord-vec2(0.5,0.5)) * scale;
  float h = DuneStripes(uv, -.5, 10, - 3.5*animation_time);
  vec3 color = foregroundColor.rgb * clamp(h, 0.0, 1.0);

  
  color = mix(vec3(0.5), color, contrast);

  
  color += vec3(brightness);

  return vec4(color,1);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
