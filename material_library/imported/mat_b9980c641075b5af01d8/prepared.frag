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
uniform vec4 uMMParam001; // native input: shape_type
int shape_type = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: mat_centerX
float mat_centerX = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_centerY
float mat_centerY = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_rotation
float mat_rotation = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_use_random_center
bool mat_use_random_center = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_ringWidth
float mat_ringWidth = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_gradient_width
float mat_gradient_width = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_color_count
int mat_color_count = int(round(uMMParam008.x));
uniform vec4 uMMParam009; // native input: mat_colour1
vec4 mat_colour1 = uMMParam009;
uniform vec4 uMMParam010; // native input: mat_colour2
vec4 mat_colour2 = uMMParam010;
uniform vec4 uMMParam011; // native input: mat_colour3
vec4 mat_colour3 = uMMParam011;
uniform vec4 uMMParam012; // native input: mat_colour4
vec4 mat_colour4 = uMMParam012;
float mat_time = uTDTime * (mat_speed);


























vec4 pickColour(float ringIndex) {

    vec4 selectedColor;
    if (ringIndex < 1.0) {
        selectedColor = mat_colour1;
    } else if (ringIndex < 2.0) {
        selectedColor = mat_colour2;
    } else if (ringIndex < 3.0 && mat_color_count > 2) {
        selectedColor = mat_colour3;
    } else {
        selectedColor = mat_colour4;
    }
	return selectedColor;
}
vec4 materialColorForPixel( vec2 uv )
{
    
    vec2 center;
    if (mat_use_random_center) {
        
        float seed = floor(mat_time * 0.5); 
        center = vec2(
            fract(sin(seed) * 43758.5453123) * 2.0 - 1.0, 
            fract(sin(seed * 1.324) * 43758.5453123) * 2.0 - 1.0 
        );
    } else {
        
        center = vec2(mat_centerX, mat_centerY);
    }

    
    vec2 offsetUV = uv - center;

	
	float rads = mat_rotation / 360.0 * 2 * 3.14159;
    float cosAngle = cos(rads);
    float sinAngle = sin(rads);
    vec2 rotatedUV = vec2(
        offsetUV.x * cosAngle - offsetUV.y * sinAngle,
        offsetUV.x * sinAngle + offsetUV.y * cosAngle
    );

	offsetUV = rotatedUV;

    
    float growth = mat_time * 0.5;

    
    float dist;

    
    if (shape_type == 0) {
        
        dist = length(offsetUV);
    } else if (shape_type == 1) {
        
        dist = abs(offsetUV.x) + abs(offsetUV.y);
    } else if (shape_type == 2) {
        
        dist = max(abs(offsetUV.x), abs(offsetUV.y));
    } else if (shape_type == 3) {
        
        float angle = atan(offsetUV.y, offsetUV.x);
        float starFactor = sin(angle * 5.0 + mat_time * 2.0) * 0.2 + 1.0;
        dist = length(offsetUV) * starFactor;
    } else if (shape_type == 4) {
        
        dist = abs(offsetUV.x);
    } else if (shape_type == 5) {
        
        float chevronWidth = 0.3;
        float chevronAngle = abs(offsetUV.x) + abs(offsetUV.y / chevronWidth);
        dist = chevronAngle;
    } else {
        
        dist = length(offsetUV);
    }

    
    float ringWidth = mat_ringWidth;
    float ringIndex = mod(floor((dist - growth) / ringWidth), float(mat_color_count));
	float gradient_width = mat_gradient_width * ringWidth;

    
  	float ringPosition = mod(dist - growth, ringWidth);
    float gradientFactor = smoothstep(0.0, gradient_width, ringPosition) * (1.0 - smoothstep(ringWidth - gradient_width, ringWidth, ringPosition));

			
    
    vec4 innerColor = pickColour(mod(ringIndex, float(mat_color_count)));
    vec4 outerColor = pickColour(mod(ringIndex + 1.0, float(mat_color_count)));

	vec4 color = mix(innerColor, outerColor, gradientFactor);


    
    return color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
