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

uniform vec4 uMMParam000; // native input: mat_speed
float mat_speed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_scale
float mat_scale = uMMParam001.x;
float mat_time = uTDTime * (mat_speed);
#define texture_letters sTD2DInputs[0]



















float res = 1024.;
float text(vec2 fragCoord)
{
    vec2 uv = mod(fragCoord.xy, 16.)*.0625;
    vec2 block = fragCoord*.0625 - uv;
    uv = uv*.8+.1; 
    uv += floor(texture(texture_letters, block/vec2(res) + mat_time*.002).xy * 16.); 
    uv *= .0625; 
    uv.x = -uv.x; 
    return texture(texture_letters, uv).r;
}

vec3 rain(vec2 fragCoord)
{
	fragCoord.x -= mod(fragCoord.x, 16.);
    
    
    float offset=sin(fragCoord.x*15.);
    float speed=cos(fragCoord.x*3.)*.3+.7;
   
    float y = fract(fragCoord.y/res + mat_time*speed + offset);
    return vec3(.1,1,.35) / (y*20.);
}

vec4 materialColorForPixel( vec2 texCoord )
{
	res = 1024.*mat_scale;
	vec2 uv = texCoord.xy *res;
	uv.y = res - uv.y;
	return vec4(text(uv)*rain(uv),1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
