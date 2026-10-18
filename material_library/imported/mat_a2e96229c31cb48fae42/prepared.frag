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

uniform vec4 uMMParam000; // native input: circle_size
float circle_size = uMMParam000.x;
uniform vec4 uMMParam001; // native input: circle_x
float circle_x = uMMParam001.x;
uniform vec4 uMMParam002; // native input: circle_y
float circle_y = uMMParam002.x;
uniform vec4 uMMParam003; // native input: smoothness
float smoothness = uMMParam003.x;
uniform vec4 uMMParam004; // native input: repeat_x
int repeat_x = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: repeat_y
int repeat_y = int(round(uMMParam005.x));
uniform vec4 uMMParam006; // native input: bpmsync
bool bpmsync = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: automovexactive
bool automovexactive = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: automovexsize
float automovexsize = uMMParam008.x;
uniform vec4 uMMParam009; // native input: automovexnoise
float automovexnoise = uMMParam009.x;
uniform vec4 uMMParam010; // native input: automovexspeed
float automovexspeed = uMMParam010.x;
uniform vec4 uMMParam011; // native input: automovexreverse
bool automovexreverse = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: automovexstrob
float automovexstrob = uMMParam012.x;
const int automovexshape = 0;
#define automovexshape_IS_Smooth
uniform vec4 uMMParam014; // native input: automoveyactive
bool automoveyactive = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: automoveysize
float automoveysize = uMMParam015.x;
uniform vec4 uMMParam016; // native input: automoveynoise
float automoveynoise = uMMParam016.x;
uniform vec4 uMMParam017; // native input: automoveyspeed
float automoveyspeed = uMMParam017.x;
uniform vec4 uMMParam018; // native input: automoveyreverse
bool automoveyreverse = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: automoveystrob
float automoveystrob = uMMParam019.x;
const int automoveyshape = 0;
#define automoveyshape_IS_Smooth
uniform vec4 uMMParam021; // native input: autolumaactive
bool autolumaactive = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: autolumasize
float autolumasize = uMMParam022.x;
uniform vec4 uMMParam023; // native input: autolumaspeed
float autolumaspeed = uMMParam023.x;
uniform vec4 uMMParam024; // native input: autolumareverse
bool autolumareverse = uMMParam024.x > 0.5;
uniform vec4 uMMParam025; // native input: autolumastrob
float autolumastrob = uMMParam025.x;
const int autolumashape = 0;
#define autolumashape_IS_Smooth
uniform vec4 uMMParam027; // native input: autoscaleactive
bool autoscaleactive = uMMParam027.x > 0.5;
uniform vec4 uMMParam028; // native input: autoscalesize
float autoscalesize = uMMParam028.x;
uniform vec4 uMMParam029; // native input: autoscalespeed
float autoscalespeed = uMMParam029.x;
uniform vec4 uMMParam030; // native input: autoscalereverse
bool autoscalereverse = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: autoscalestrob
float autoscalestrob = uMMParam031.x;
const int autoscaleshape = 0;
#define autoscaleshape_IS_Smooth
uniform vec4 uMMParam033; // native input: front_color
vec4 front_color = uMMParam033;
uniform vec4 uMMParam034; // native input: brightness
float brightness = uMMParam034.x;
uniform vec4 uMMParam035; // native input: contrast
float contrast = uMMParam035.x;
uniform vec4 uMMParam036; // native input: invert
bool invert = uMMParam036.x > 0.5;
float movex_position = uTDTime * (automovexspeed);
float movey_position = uTDTime * (automoveyspeed);
float luma_position = uTDTime * (autolumaspeed);
float scale_position = uTDTime * (autoscalespeed);
#define noiseLUT sTD2DInputs[0]
mat3 linePatternsMatrix;
float lumaValue;

#define M_PI 3.1415926535897932384626433832795

float fast_noise( float v ) {
    
    return IMG_NORM_PIXEL(noiseLUT,vec2(fract(v/20),1)).r * 2 - 1;
}

mat3 makeTransformMatrix()
{
    
    mat3 linePatternsMatrix = mat3(1,0,-0.5-circle_x,
                              0,1,-0.5-circle_y,
                              0,0,1);

	
    if (automovexactive) {
      float translateX=circle_x;
      translateX += automovexnoise * fast_noise(movex_position);

      #if defined(automovexshape_IS_Smooth)
        translateX += automovexsize * sin(movex_position*2*M_PI) / 2;
      #elif defined automovexshape_IS_In
        translateX += automovexsize * (0.5-mod(movex_position,1));
      #elif defined automovexshape_IS_Out
        translateX += automovexsize * (-0.5+mod(movex_position,1));
      #elif defined automovexshape_IS_Linear
        translateX += automovexsize * (0.5-abs(mod(movex_position*2+1,2)-1));
      #else 
        translateX += automovexsize * (0.5-step(0.5,mod(movex_position,1)));
      #endif

      linePatternsMatrix *= mat3(1,0,fract(translateX),
                                 0,1,0,
                                 0,0,1);
    }

    if (automoveyactive) {
      float translateY=circle_y;
      translateY += automoveynoise * fast_noise(movey_position+0.5);

      #if defined(automoveyshape_IS_Smooth)
        translateY += automoveysize * cos(movey_position*2*M_PI) / 2;
      #elif defined automoveyshape_IS_In
        translateY += automoveysize * (0.5-mod(movey_position,1));
      #elif defined automoveyshape_IS_Out
        translateY += automoveysize * (-0.5+mod(movey_position,1));
      #elif defined automoveyshape_IS_Linear
        translateY += automoveysize * (0.5-abs(mod(movey_position*2+1,2)-1));
      #else 
        translateY += automoveysize * (0.5-step(0.5,mod(movey_position,1)));
      #endif

      linePatternsMatrix *= mat3(1,0,0,
                                 0,1,translateY,
                                 0,0,1);
    }

    
    if (autoscaleactive) {
      float scale;
      #if defined(autoscaleshape_IS_Smooth)
        scale = autoscalesize * (1+sin(scale_position*2*M_PI))/2;
      #elif defined(autoscaleshape_IS_In)
        scale = autoscalesize * (mod(scale_position,1));
      #elif defined(autoscaleshape_IS_Out)
        scale = autoscalesize * (1-mod(scale_position,1));
      #elif defined(autoscaleshape_IS_Linear)
        scale = autoscalesize * (-1+abs(mod(scale_position*2+1,2)-1));
      #else 
        scale = autoscalesize * step(0.5,mod(scale_position,1));
      #endif
      scale = 0.5/(1-scale + 0.00000001);
      linePatternsMatrix *= mat3(scale,0,0,
                                 0,scale,0,
                                 0,0,1);
    }

    return linePatternsMatrix;
}

void materialVsFunc(vec2 uv) {
    if (autolumaactive) {
      
      #if defined(autolumashape_IS_Smooth)
        lumaValue = autolumasize * (1+sin(luma_position*2*M_PI))/2;
      #elif defined(autolumashape_IS_In)
        lumaValue = autolumasize * (mod(luma_position,1));
      #elif defined(autolumashape_IS_Out)
        lumaValue = autolumasize * (1-mod(luma_position,1));
      #elif defined(autolumashape_IS_Linear)
        lumaValue = autolumasize * (-1+abs(mod(luma_position*2+1,2)-1));
      #else 
        lumaValue = autolumasize * step(0.5,mod(luma_position,1));
      #endif
    } else {
      lumaValue = 1;
    }

    linePatternsMatrix=makeTransformMatrix();
}












































































vec4 materialColorForPixel(vec2 texCoord)
{
    
    float finalSmoothness = smoothness;
    float halfFinalWidth = circle_size/2;
    float value = 0;

	for (int x=-1; x<=1; x++) {
		for (int y=-1; y<=1; y++) {
			vec2 uv = (vec3(fract(vec2(repeat_x,repeat_y)*texCoord)+vec2(x,y),1) * linePatternsMatrix).xy;
			float dist=length(uv);
			if (dist>0)
			  value=max(value,1-smoothstep(halfFinalWidth-finalSmoothness,halfFinalWidth,dist));
			else
			  value=max(value,1-smoothstep(-halfFinalWidth+finalSmoothness,-halfFinalWidth,dist));
		}
	}

    value *= lumaValue;

    vec3 col =value*front_color.rgb;

    
    col.rgb = mix(vec3(0.5), col.rgb, contrast);

    
    col.rgb += vec3(brightness);

    if (invert)
      return vec4(1-value*col,1);
    else
      return vec4(value*col,1);
}


void main()
{
    materialVsFunc(vec2(0.0));

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
