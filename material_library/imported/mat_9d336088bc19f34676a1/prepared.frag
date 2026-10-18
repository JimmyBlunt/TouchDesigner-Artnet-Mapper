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
uniform vec4 uMMParam001; // native input: mat_count
float mat_count = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_height
float mat_height = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_ribbon
float mat_ribbon = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_stroke
float mat_stroke = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_activity
float mat_activity = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_frac
float mat_frac = uMMParam006.x;






















#define COUNT mat_count
#define COL_BLACK vec3(23,20,38) / 255.0 

#define SF 1./min(RENDERSIZE.x,RENDERSIZE.y)
#define SS(l,s) smoothstep(SF,-SF,l-s)
#define hue(h) clamp( abs( fract(h + vec4(3,2,1,0)/3.) * 6. - 3.) -1. , 0., 1.)


#define MOD3 vec3(1,.2,1)

vec3 hash33(vec3 p3)
{
	p3 = fract(p3 * MOD3);
    p3 += dot(p3, p3.yxz+19.19);
    return -1.0 + 2.0 * fract(vec3((p3.x + p3.y)*p3.z, (p3.x+p3.z)*p3.y, (p3.y+p3.z)*p3.x));
}

float simplex_noise(vec3 p)
{
    const float K1 = 0.333333333;
    const float K2 = 0.166666667;
    
    vec3 i = floor(p + (p.x + p.y + p.z) * K1);
    vec3 d0 = p - (i - (i.x + i.y + i.z) * K2);
        
    vec3 e = step(vec3(0.0), d0 - d0.yzx);
	vec3 i1 = e * (1.0 - e.zxy);
	vec3 i2 = 1.0 - e.zxy * (1.0 - e);
    
    vec3 d1 = d0 - (i1 - 1.0 * K2);
    vec3 d2 = d0 - (i2 - 2.0 * K2);
    vec3 d3 = d0 - (1.0 - 3.0 * K2);
    
    vec4 h = max(0.6 - vec4(dot(d0, d0), dot(d1, d1), dot(d2, d2), dot(d3, d3)), 0);
    vec4 n = h * h * h * h * vec4(dot(d0, hash33(i)), dot(d1, hash33(i + i1)), dot(d2, hash33(i + i2)), dot(d3, hash33(i + 1)));
    
 	return dot(vec4(mat_height), n);
}

vec4 materialColorForPixel( vec2 texCoord ) {

  
    vec2 uv = texCoord.xy;
    
    float m = mat_frac;
    float t = TIME * mat_speed;
    vec3 col;
    for(float i=COUNT; i>=0.; i-=1.){
        float edge = simplex_noise(vec3(uv * vec2(3, 0.) + vec2(0, t + i*mat_ribbon), 1.))*mat_activity + (.5/COUNT)*i + .1;
        float mi = SS(edge, uv.y) - SS(edge + mat_stroke, uv.y);        
        m *= SS(edge, uv.y);
        m += mi;        
        
        if(mi > 0){
        	col = (1-hue(i/COUNT).rgb);
        }        
    }           
    
   col = mix(COL_BLACK, col, m);

    
    return vec4(col,1.0);
}









void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
