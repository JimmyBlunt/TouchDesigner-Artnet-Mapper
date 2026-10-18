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

uniform vec4 uMMParam000; // native input: _Radius
float _Radius = uMMParam000.x;
uniform vec4 uMMParam001; // native input: _Radius2
float _Radius2 = uMMParam001.x;
uniform vec4 uMMParam002; // native input: _Intensity
float _Intensity = uMMParam002.x;
uniform vec4 uMMParam003; // native input: _Frequency
float _Frequency = uMMParam003.x;
uniform vec4 uMMParam004; // native input: spread
float spread = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_zoom
float mat_zoom = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_reverse
bool mat_reverse = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_speed
float mat_speed = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_offset
float mat_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_strob
float mat_strob = uMMParam010.x;
float mat_time = uTDTime * (mat_speed);














































































































#ifdef GL_ES

#endif




#define _Color vec3( 1.0,0.9, 0.4 );


#define _PulseSpeed 0.5



float mat_iTime = mat_time - mat_offset;


float mat_hash( float n ) { return fract(sin(n)*753.5453123); }


float mat_noise( in vec2 x )
{
    vec2 p = floor(x);
    vec2 f = fract(x);
    f = f*f*(3.0-2.0*f);

    float n = p.x + p.y*157.0;
    return mix(
                    mix( mat_hash(n+  0.0), mat_hash(n+  1.0),f.x),
                    mix( mat_hash(n+157.0), mat_hash(n+158.0),f.x),
            f.y);
}

float mat_fbm(vec2 p, vec3 a)
{
     float v = 0.0;
     v += mat_noise(p*a.x)*.5;
     v += mat_noise(p*a.y)*.25;
     v += mat_noise(p*a.z)*.125;
     return v;
}

vec3 WeirdCircle(vec2 uv, float radius, float thickness, float intensity, vec3 fbmOffset, float t2, vec3 color)
{
   float dist = length(uv);

    float aTan = atan(uv.y/uv.x);
    float t1 = intensity *sin(aTan * _Frequency + mat_iTime *t2) * 0.5 + 0.5 + mat_fbm(uv,fbmOffset) * spread; 
    float warp = mix(0.0, 0.5, t1);

    float effector = thickness*abs(0.003/((dist) - (radius + warp))); 

    return color * effector;

}


vec4 materialColorForPixel( vec2 texCoord )
{
    vec2 uv = texCoord * 2.0 - 1.0;

    uv *= mat_zoom;
    
    

    vec3 finalColor = vec3( 0.0 );

    
    

    finalColor += WeirdCircle(uv, _Radius, 1.0, _Intensity, vec3( 200, 100, 50),-10.0,vec3( 0.3, 0.5, 2.5 ));
    finalColor += WeirdCircle(uv, _Radius, 1.0, _Intensity, vec3( 90, 15, 1),1.0,vec3( 0.8,0.5, 0.0 ));


    finalColor += WeirdCircle(uv, _Radius2, 1.0, _Intensity , vec3(30, 6, 5),5.0, vec3( 2.3, 0.5, .5 ));
    finalColor += WeirdCircle(uv, _Radius2-0.04, 1.0, _Intensity * 2.0, vec3(100,100,100),4.0,vec3( 0.12, 0.15, 2.1 ));
    finalColor += WeirdCircle(uv, _Radius2-0.1, 0.1, _Intensity , vec3(200,200,200),4.0,vec3( 0.1, 0.1, 0.2 ));
    return vec4( finalColor, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
