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

uniform vec4 uMMParam000; // native input: line_repeat2
int line_repeat2 = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: line_repeat
int line_repeat = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: line_thickness
float line_thickness = uMMParam002.x;
uniform vec4 uMMParam003; // native input: dash_length
float dash_length = uMMParam003.x;
uniform vec4 uMMParam004; // native input: line_rotation
float line_rotation = uMMParam004.x;
uniform vec4 uMMParam005; // native input: line_y
float line_y = uMMParam005.x;
uniform vec4 uMMParam006; // native input: scroll_speed
float scroll_speed = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_bpmsync
bool mat_bpmsync = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: col_spacing
float col_spacing = uMMParam008.x;
const int mat_shape = 0;
#define mat_shape_IS_Default
uniform vec4 uMMParam010; // native input: smoothness
float smoothness = uMMParam010.x;
uniform vec4 uMMParam011; // native input: symmetry
bool symmetry = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: polar_control
bool polar_control = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: reverse
bool reverse = uMMParam013.x > 0.5;
uniform vec4 uMMParam014; // native input: line_color
vec4 line_color = uMMParam014;
uniform vec4 uMMParam015; // native input: bg_color
vec4 bg_color = uMMParam015;
#ifndef M_PI
  #define M_PI 3.14159265358979323846
#endif
































vec4 materialColorForPixel(vec2 texCoord)
{
    vec2 uv = texCoord - 0.5;
    
    
    float angle = line_rotation * M_PI / 180.0;
    mat2 rot = mat2(cos(angle), -sin(angle),
                    sin(angle),  cos(angle));
    uv = rot * uv + 0.5;
    
    
    if (reverse) {
        uv.x = 1.0 - uv.x;
    }
    
    
    if (symmetry) {
        uv.x = abs(uv.x - 0.5) * 2.0;
    }
    
    
    float v;
    float cellIndex = floor(uv.y * float(line_repeat2));
    v = fract(uv.y * float(line_repeat2));

    
    float finalX;
    if (mat_shape == 0) { 
        float idealX = (line_repeat2 > 1) ? (cellIndex / (float(line_repeat2) - 1.0)) : 0.5;
        finalX = mix(0.5, idealX, col_spacing);
    } else if (mat_shape == 1) { 
        finalX = ((int(cellIndex) % 2 == 0) ? 1.0 : -1.0) * col_spacing;
    } else if (mat_shape == 2) { 
        finalX = sin((cellIndex / float(line_repeat2)) * M_PI) * col_spacing;
    }
    uv.x += finalX;

    
    if (polar_control) {
        float r = length(uv - 0.5);
        float theta = atan(uv.y - 0.5, uv.x - 0.5);
        uv.x = r;
        uv.y = theta / M_PI;
    }

    
    float bpm_factor = mat_bpmsync ? 2.0 : 1.0;
    if (scroll_speed > 0.0) {
        uv.x += TIME * scroll_speed * bpm_factor;
    }

    float smooth_factor = smoothness * 0.2;
    float vertical_alpha = 1.0 - smoothstep(line_thickness - smooth_factor, line_thickness + smooth_factor, abs(v - line_y));
    float dash_pattern = fract(uv.x * float(line_repeat));
    float edge = smooth_factor;
    float dash_alpha = 1.0 - smoothstep(dash_length - edge, dash_length, dash_pattern);
    float final_alpha = vertical_alpha * dash_alpha;
    return mix(bg_color, line_color, final_alpha);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
