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

uniform vec4 uMMParam000; // native input: line_width
float line_width = uMMParam000.x;
uniform vec4 uMMParam001; // native input: smoothness
float smoothness = uMMParam001.x;
uniform vec4 uMMParam002; // native input: speed
float speed = uMMParam002.x;
uniform vec4 uMMParam003; // native input: reverse
bool reverse = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: bpmsync
bool bpmsync = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: decay
float decay = uMMParam005.x;
uniform vec4 uMMParam006; // native input: release
float release = uMMParam006.x;
const int animation = 0;
#define animation_IS_Cross
uniform vec4 uMMParam008; // native input: cells_x
int cells_x = int(round(uMMParam008.x));
uniform vec4 uMMParam009; // native input: cells_y
int cells_y = int(round(uMMParam009.x));
uniform vec4 uMMParam010; // native input: offset
float offset = uMMParam010.x;
uniform vec4 uMMParam011; // native input: random_offset
bool random_offset = uMMParam011.x > 0.5;
float animation_time = uTDTime * (speed);


























float hash( vec2 p ) {
    return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);
}

vec4 materialColorForPixel(vec2 texCoord)
{
	if (line_width==0) return vec4(0,0,0,1);

	float pixelPos=mod(texCoord.x*cells_x,1);
	vec2 cellId = vec2(int(texCoord.x * cells_x), int(texCoord.y * cells_y));

    float normalizedCellId; 
    if (random_offset)
        normalizedCellId = hash(cellId * 0.5);
    else
        normalizedCellId = (cellId.x + cellId.y*cells_x) / (cells_x*cells_y); 

	float adjusted_bpm_pos = mod(animation_time - offset * normalizedCellId,1); 
	if (adjusted_bpm_pos < decay) {
		adjusted_bpm_pos = 1;
	} else {
		
		adjusted_bpm_pos = (adjusted_bpm_pos - decay) * 1 / (1 - decay);
		if (adjusted_bpm_pos < release) {
			adjusted_bpm_pos = 1 - adjusted_bpm_pos * 1 / release;
		} else {
			adjusted_bpm_pos = 0;
		}
	}

	float value;

	#if defined(animation_IS_Cross)
		value = smoothstep(line_width,line_width*(1-smoothness),abs(pixelPos-adjusted_bpm_pos));
		value += smoothstep(line_width,line_width*(1-smoothness),abs((1-pixelPos)-adjusted_bpm_pos));
	#elif defined(animation_IS_Centered_Filled)
		value = smoothstep(0,-smoothness,(2*abs(0.5-pixelPos)-adjusted_bpm_pos));
	#elif defined(animation_IS_Single)
		float dist = mod(abs(pixelPos-adjusted_bpm_pos),1);
		value = smoothstep(line_width,line_width*(1-smoothness),dist);
	#else 
		
		value = smoothstep(0,-smoothness,pixelPos-adjusted_bpm_pos);
	#endif

	return vec4(vec3(value),1);
}



void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
