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

uniform vec4 uMMParam000; // native input: mat_thickness
float mat_thickness = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_amplitude
float mat_amplitude = uMMParam001.x;
const float mat_release = 0.2;
const bool mat_show_peaks = false;
#define mat_show_peaks_IS_false
const float mat_peaks_decay = 0.4;
uniform vec4 uMMParam005; // native input: mat_peaks_color
vec4 mat_peaks_color = uMMParam005;
#define spectrum_512_decay sTD2DInputs[0]
#define spectrum_512 sTD2DInputs[1]









































































vec4 materialColorForPixel(vec2 texCoord)
{
	texCoord.y = 1-texCoord.y;
	
    vec4 finalColor = vec4(vec3(0),1);
	float thickness = pow(mat_thickness,3);

    float posY = IMG_NORM_PIXEL(spectrum_512,vec2(texCoord.x,0)).r * mat_amplitude * mat_amplitude;
	float dist = abs(posY-texCoord.y);
	if (dist < thickness) {
		finalColor.rgb = vec3(1-dist/(thickness));
	}

    #if defined(mat_show_peaks_IS_true)
        float posY_decay = IMG_NORM_PIXEL(spectrum_512_decay,vec2(texCoord.x,0)).r * mat_amplitude * mat_amplitude;
		float dist_decay = abs(posY_decay-texCoord.y);
        if (dist_decay<thickness) {
			finalColor += mat_peaks_color * (1-dist_decay/(thickness));
        }
    #endif

    return finalColor;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
