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
uniform vec4 uMMParam001; // native input: u_var1
float u_var1 = uMMParam001.x;
uniform vec4 uMMParam002; // native input: u_var2
float u_var2 = uMMParam002.x;
uniform vec4 uMMParam003; // native input: u_var6
float u_var6 = uMMParam003.x;
uniform vec4 uMMParam004; // native input: u_nonLinearTime
float u_nonLinearTime = uMMParam004.x;
uniform vec4 uMMParam005; // native input: u_randomFactor
float u_randomFactor = uMMParam005.x;
uniform vec4 uMMParam006; // native input: u_var3
float u_var3 = uMMParam006.x;
uniform vec4 uMMParam007; // native input: u_var4
float u_var4 = uMMParam007.x;
uniform vec4 uMMParam008; // native input: u_var5
float u_var5 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_mapToPalette
bool mat_mapToPalette = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: u_paletteSize
int u_paletteSize = int(round(uMMParam010.x));
uniform vec4 uMMParam011; // native input: mat_balance
float mat_balance = uMMParam011.x;
uniform vec4 uMMParam012; // native input: u_paletteColor1
vec4 u_paletteColor1 = uMMParam012;
uniform vec4 uMMParam013; // native input: u_paletteColor2
vec4 u_paletteColor2 = uMMParam013;
uniform vec4 uMMParam014; // native input: u_paletteColor3
vec4 u_paletteColor3 = uMMParam014;
uniform vec4 uMMParam015; // native input: u_paletteColor4
vec4 u_paletteColor4 = uMMParam015;
float mat_time = uTDTime * (mat_speed);






























float fractal(vec2 p, float time, float var1, float var2) {
    float scale = 2.0 + var1;
    float offset = var2;
    float result = 0.0;
    for (int i = 0; i < 6; i++) {
        p = abs(p) / dot(p, p) - offset;
        result += sin(p.x * scale + time) + cos(p.y * scale + time);
    }
    return result;
}


vec4 mapToPalette(float value, vec4 color1, vec4 color2, vec4 color3, vec4 color4, int paletteSize, float balance) {
    float adjustedValue = value;
    if (paletteSize == 2) {
        adjustedValue = mix(value, 0.5, balance);
        return mix(color1, color2, adjustedValue);
    } else if (paletteSize == 3) {
        if (value < 0.5) {
            adjustedValue = mix(value * 2.0, 0.5, balance);
            return mix(color1, color2, adjustedValue);
        } else {
            adjustedValue = mix((value - 0.5) * 2.0, 0.5, balance);
            return mix(color2, color3, adjustedValue);
        }
    } else if (paletteSize == 4) {
        if (value < 0.33) {
            adjustedValue = mix(value * 3.0, 0.5, balance);
            return mix(color1, color2, adjustedValue);
        } else if (value < 0.66) {
            adjustedValue = mix((value - 0.33) * 3.0, 0.5, balance);
            return mix(color2, color3, adjustedValue);
        } else {
            adjustedValue = mix((value - 0.66) * 3.0, 0.5, balance);
            return mix(color3, color4, adjustedValue);
        }
    }
    return color1; 
}

vec4 materialColorForPixel( vec2 uv )
{
	
	float randomOffset = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453) * u_randomFactor;
    float time = mat_time * u_var6;
    time = time + u_nonLinearTime * sin(time + randomOffset); 

    
    float fractalValue = fractal(uv, time, u_var1, u_var2);

	vec4 color;
	if(mat_mapToPalette) {
		
    	float normalizedValue = fractalValue * 0.5 + 0.5;
    	normalizedValue = clamp(normalizedValue, 0.0, 1.0);

    	
    	color = mapToPalette(normalizedValue, u_paletteColor1, u_paletteColor2, u_paletteColor3, u_paletteColor4, u_paletteSize, mat_balance);
	} else {
    	
    	color = vec4(
        	0.5 + 0.5 * cos(fractalValue + u_var3),
        	0.5 + 0.5 * sin(fractalValue + u_var4),
        	0.5 + 0.5 * cos(fractalValue + u_var5),
			1.0
    	);
	}

    
	return color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
