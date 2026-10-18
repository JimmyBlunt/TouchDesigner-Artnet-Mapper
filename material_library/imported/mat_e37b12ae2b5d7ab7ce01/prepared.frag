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

uniform vec4 uMMParam000; // native input: distance
float distance = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_reverse
bool mat_reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_offset
float mat_offset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_strob
float mat_strob = uMMParam005.x;
float mat_time = uTDTime * (mat_speed);













































































#ifdef GL_ES

#endif

#ifndef PI
    #define PI 3.14159265359
#endif


float iTime = mat_time - mat_offset * 10;

vec2 rotate2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

vec4 materialColorForPixel(vec2 texCoord) {

    float t = iTime * 0.1;

    
    vec2 position = texCoord;



    position = rotate2D(position, PI);


    position -= vec2(0.5, 0.0);

    



     position /= -(position.y) + 0.8;

    
    


     position *= 20.0;

     

     position *= distance;
     vec2 horizon = position.xy;

         
      position.x =position.x+iTime*18.;


    vec3 color = vec3(2.-floor(1.+length(cos(position.xy)*2.0+2.*sin(iTime))));
         color *= horizon.y < 0.0 ? 0.0 : 1.0;
        horizon.y -= 5.+position.y;

        color += horizon.y > 0.0 ? 0.0 : 1.0;
        color *= pow(vec3(0.1, 0.7, 0.9), vec3(length(horizon.xy)) * 0.1);





    return vec4(color, 1.0 );

}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
