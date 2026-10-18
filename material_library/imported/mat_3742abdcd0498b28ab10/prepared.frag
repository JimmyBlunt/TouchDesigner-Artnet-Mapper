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

uniform vec4 uMMParam000; // native input: mat_grid_width
int mat_grid_width = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_angle_vars
int mat_angle_vars = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: mat_ambient_color
vec4 mat_ambient_color = uMMParam002;
uniform vec4 uMMParam003; // native input: mat_lightColor
vec4 mat_lightColor = uMMParam003;
uniform vec4 uMMParam004; // native input: mat_lightXY
vec2 mat_lightXY = uMMParam004.xy;
uniform vec4 uMMParam005; // native input: mat_lightZ
float mat_lightZ = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_lightAttenuation
float mat_lightAttenuation = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_spotLight
bool mat_spotLight = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_spotLightDir
vec2 mat_spotLightDir = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_spotLightCutoff
float mat_spotLightCutoff = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_spotLightExponent
float mat_spotLightExponent = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_brightness
float mat_brightness = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_contrast
float mat_contrast = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_invert
bool mat_invert = uMMParam013.x > 0.5;



























#define PI 3.1415926535897932384626433832795









bool pointInTriangle(vec2 P, vec2 A, vec2 B, vec2 C) {
    
    vec2 v0 = C - A;
    vec2 v1 = B - A;
    vec2 v2 = P - A;

    
    float dot00 = dot(v0,v0);
    float dot01 = dot(v0,v1);
    float dot02 = dot(v0,v2);
    float dot11 = dot(v1,v1);
    float dot12 = dot(v1,v2);

    
    float denom = dot00 * dot11 - dot01 * dot01;
    if (denom==0) return false;
    float invDenom = 1 / denom;
    float u = (dot11 * dot02 - dot01 * dot12) * invDenom;
    float v = (dot00 * dot12 - dot01 * dot02) * invDenom;

    
    return (u >= 0) && (v >= 0) && (u + v <= 1);
}

vec2 rotate2D(vec2 v, float a) {
    float s = sin(a);
    float c = cos(a);
    mat2 m = mat2(c, -s, s, c);
    return m * v;
}

vec4 materialColorForPixel( vec2 texCoord )
{
	texCoord.y = 1-texCoord.y;

	
	vec2 cell = vec2(int(texCoord.x * mat_grid_width),int(texCoord.y * mat_grid_width));
	vec2 posInCell = texCoord * mat_grid_width - cell;
    posInCell = vec2(0.5) + (posInCell-vec2(0.5))*sqrt(2);
    int cellId = int(cell.x + cell.y * mat_grid_width);
    int angleVariations = int(pow(2,mat_angle_vars));

    if (mat_angle_vars>0) {
        posInCell = vec2(0.5) + rotate2D(posInCell-vec2(0.5),(cellId%angleVariations) * 2*PI/angleVariations);
    }

    vec3 faceNormal;

	
	vec2 triangleP1 = vec2(0,0);
	vec2 triangleP2 = vec2(1,0);
	vec2 triangleP3 = vec2(0.5,1);
	vec2 pyramideCenter = vec2(0.5,0.5);

    
    if (pointInTriangle(posInCell,triangleP1,triangleP2,pyramideCenter)) {
        faceNormal = normalize(vec3(0,-0.5,0.5));
        
    }
    else if (pointInTriangle(posInCell,triangleP1,triangleP3,pyramideCenter)) {
        faceNormal = normalize(vec3(-0.5,0.25,0.5));
        
    }
    else if (pointInTriangle(posInCell,triangleP2,triangleP3,pyramideCenter)) {
        faceNormal = normalize(vec3(0.5,0.25,0.5));
        
    } else {
        return vec4(0,0,0,1);
    }
        
    if (mat_angle_vars>0) {
        faceNormal.xy = rotate2D(faceNormal.xy,-(cellId%angleVariations) * 2*PI/angleVariations);
    }

	vec3 color = vec3(1);

	
    color = mix(vec3(0.5), color, mat_contrast);
    
    color += vec3(mat_brightness);
	
	color *= mat_ambient_color.rgb;
	
	color = mix(color, vec3(1.0)-color,float(mat_invert));

	
	vec3 lightPos = vec3((vec2(1)+mat_lightXY)*0.5*mat_grid_width,mat_lightZ);
    vec3 vecToLight = lightPos-(vec3(texCoord * mat_grid_width,0));

    vec3 vecToLightNormalized = normalize(vecToLight);
    float lambertTerm = dot(faceNormal,vecToLightNormalized);
    if(lambertTerm > 0.0)
    {
        float lightDistance = length(vecToLight);
        float attenuation = min(1.0, 1.0 / (mat_lightAttenuation * lightDistance * lightDistance));

        if (mat_spotLight) {
            float clampedCosine = max(0.0, dot(-vecToLightNormalized, normalize(vec3(mat_spotLightDir-mat_lightXY,-1))));
            float maxCosine = cos(mat_spotLightCutoff);
            if (clampedCosine < maxCosine) 
                attenuation = 0.0;
            else
                attenuation = attenuation * pow(1.-((1.-clampedCosine) / (1.-maxCosine)), mat_spotLightExponent);
        }

        vec3 light_color = mat_lightColor.rgb * lambertTerm;
        color += light_color * attenuation;
    }

	return vec4(color,1.0);	
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
