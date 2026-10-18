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

const int solarized = 0;
#define solarized_IS_base03


















vec4 materialColorForPixel( vec2 texCoord )
{
vec4 color;
    #if defined(solarized_IS_base03)
        color = vec4 (  0./255,  43./255.,  54./255., 1);
    #elif defined(solarized_IS_base02)
        color = vec4 (  7./255,  54./255.,  66./255., 1);
    #elif defined(solarized_IS_base01)
        color = vec4 ( 88./255, 110./255., 117./255., 1);
    #elif defined(solarized_IS_base00)
        color = vec4 (101./255, 123./255., 131./255., 1);
    #elif defined(solarized_IS_base0)
        color = vec4 (131./255, 148./255., 150./255., 1);
    #elif defined(solarized_IS_base1)
        color = vec4 (147./255, 161./255., 161./255., 1);
    #elif defined(solarized_IS_base2)
        color = vec4 (238./255, 232./255., 213./255., 1);
    #elif defined(solarized_IS_base3)
        color = vec4 (253./255, 246./255., 227./255., 1);

    #elif defined(solarized_IS_yellow)
        color = vec4 (181./255, 137./255.,   0./255., 1);
    #elif defined(solarized_IS_orange)
        color = vec4 (203./255,  75./255.,  22./255., 1);
    #elif defined(solarized_IS_red)
        color = vec4 (220./255,  50./255.,  47./255., 1);
    #elif defined(solarized_IS_magenta)
        color = vec4 (211./255,  54./255., 130./255., 1);
    #elif defined(solarized_IS_violet)
        color = vec4 (108./255, 113./255., 196./255., 1);
    #elif defined(solarized_IS_blue)
        color = vec4 ( 38./255, 139./255., 210./255., 1);
    #elif defined(solarized_IS_cyan)
        color = vec4 ( 42./255, 161./255., 152./255., 1);
    #elif defined(solarized_IS_green)
        color = vec4 (133./255, 153./255.,   0./255., 1);
    #else
        color = vec4 (  0./255, 43./255., 54./255., 1);
    #endif
	return color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
