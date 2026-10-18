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

uniform vec4 uMMParam000; // native input: speed
float speed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: reverse
bool reverse = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: scale
float scale = uMMParam002.x;
uniform vec4 uMMParam003; // native input: brightness
float brightness = uMMParam003.x;
uniform vec4 uMMParam004; // native input: contrast
float contrast = uMMParam004.x;
float animation_time = uTDTime * (speed);


















#define MAX_ITER 20

vec4 materialColorForPixel(vec2 texCoord)
{
    vec2 uv = vec2(0.5,0.5) + abs(texCoord-vec2(0.5,0)) * scale;
	vec2 uv2 = vec2(0.5,0.5) + cos(texCoord-vec2(0.5,0.5)) * scale;
	
    vec2 p =  uv * 8.0 - vec2(20.0);
    vec2 i = p;
    
	vec2 w = uv2 * 8.0 - vec2(20.0); 
	
	float c = 1.0;
    float inten = .08;

    for (int n = 0; n < MAX_ITER; n++)
    {
        float t = animation_time * (1.0 - (3.0 / float(n+1)));

        i = ( cos(w+p)+p)+ vec2(fract(t - i.x) + sin(t + i.y),  
        sin(t - i.y) + cos(t + i.x));
    
        c += 1.0/length(vec2(p.x / (fract(i.x+t)/inten),
        p.y / (cos(i.y+t)/inten)));
    }

    c /= float(MAX_ITER);
    c = 1.5 - sqrt(c);

    float value = 0.1 / (1.0 - (c + 0.05));
    value += brightness;
    value = mix(0.5, value, contrast);
	
	
	

    return vec4(vec3(value),1);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
