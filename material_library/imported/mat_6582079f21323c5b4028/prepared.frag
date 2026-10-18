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

uniform vec4 uMMParam000; // native input: mat_definition
int mat_definition = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_speed
float mat_speed = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_attack
float mat_attack = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_decay
float mat_decay = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_release
float mat_release = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_bpmsync
bool mat_bpmsync = uMMParam005.x > 0.5;
float mat_animation_time = uTDTime * (mat_speed);




















float valueAtPos(float pos)
{
	float value = 0;
	if (pos < mat_attack) {
		value = pos / mat_attack;
	} else if (pos < mat_attack + mat_decay) {
		value = 1;
	} else if (pos < mat_attack + mat_decay+ mat_release) {
		value = pow(1 - (pos-(mat_attack + mat_decay)) / mat_release,2);
	}
	return value;
}

#define H_CELL_COUNT 32
#define V_CELL_COUNT 8
#define LINES_SIZE (1/32.)

vec4 materialColorForPixel(vec2 texCoord)
{
	texCoord.x += LINES_SIZE/H_CELL_COUNT;
	texCoord.y += LINES_SIZE/(2*V_CELL_COUNT);

	float value = 0;
	if (abs(fract(texCoord.x*H_CELL_COUNT)-LINES_SIZE/2)<(LINES_SIZE/2)) {
		value += 1 - abs(fract(texCoord.x*H_CELL_COUNT)-LINES_SIZE/2)/(LINES_SIZE/2);
	}
	if (abs(fract(texCoord.y*2*V_CELL_COUNT)-LINES_SIZE/2)<(LINES_SIZE/2)) {
		value = max(value, 1 - abs(fract(texCoord.y*2*V_CELL_COUNT)-LINES_SIZE/2)/(LINES_SIZE/2));
	}

	int cellY = 1+int(texCoord.y * V_CELL_COUNT);
	bool isCurveCell = fract(texCoord.y * V_CELL_COUNT) > 0.5;
	if (!isCurveCell) {
		texCoord.x = int(texCoord.x*mat_definition) / float(mat_definition);
	}
	texCoord.x = fract(texCoord.x + mat_animation_time);
	float pos = fract(texCoord.x*cellY);
	
	if (isCurveCell) {
		float yPosInCurveCell = (1 - 2 * (fract(texCoord.y * 8)-0.5)) * 1.1;

		float value1 = valueAtPos(pos-1.0/800);
		float value2 = valueAtPos(pos+1.0/800);

        float minY = min(value1,value2);
        float maxY = max(value1,value2)+20.0/800;

        value += (yPosInCurveCell>=minY&&yPosInCurveCell<=maxY)?1:0;

    		return vec4(vec3(value), 1);
	}  else {
		float value1 = valueAtPos(pos);
		float value2 = valueAtPos(pos+0.9/mat_definition);
		value += (value1+value2)/2;
    		return vec4(vec3(value), 1);
	}
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
