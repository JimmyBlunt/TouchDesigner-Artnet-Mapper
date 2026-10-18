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

uniform vec4 uMMParam000; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam000.x > 0.5;
uniform vec4 uMMParam001; // native input: mat_scale
float mat_scale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_rotate
float mat_rotate = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: mat_shift_scale
float mat_shift_scale = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_shift_type
int mat_shift_type = int(round(uMMParam005.x));
uniform vec4 uMMParam006; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_size
float mat_size = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_texture
float mat_texture = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_inside
float mat_inside = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_glow
float mat_glow = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_cycle1
float mat_cycle1 = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_cycle2
float mat_cycle2 = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_iterations1
int mat_iterations1 = int(round(uMMParam014.x));
uniform vec4 uMMParam015; // native input: mat_iterations2
int mat_iterations2 = int(round(uMMParam015.x));
uniform vec4 uMMParam016; // native input: mat_a1_speed
float mat_a1_speed = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_a1_offset
float mat_a1_offset = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_a1_strob
float mat_a1_strob = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam022.x));
uniform vec4 uMMParam023; // native input: mat_cam
vec2 mat_cam = uMMParam023.xy;
uniform vec4 uMMParam024; // native input: mat_cam_scale
float mat_cam_scale = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_a2_animate
bool mat_a2_animate = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_a2_speed
float mat_a2_speed = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam027.x > 0.5;
uniform vec4 uMMParam028; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam028.x > 0.5;
uniform vec4 uMMParam029; // native input: mat_a2_offset
float mat_a2_offset = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_a2_strob
float mat_a2_strob = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_a2_restart
int mat_a2_restart = int(round(uMMParam032.x));
uniform vec4 uMMParam033; // native input: mat_sky
float mat_sky = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_brightness
float mat_brightness = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_contrast
float mat_contrast = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_saturation
float mat_saturation = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_hue_shift
float mat_hue_shift = uMMParam037.x;
uniform vec4 uMMParam038; // native input: mat_invert
bool mat_invert = uMMParam038.x > 0.5;
uniform vec4 uMMParam039; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam039.x > 0.5;
uniform vec4 uMMParam040; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam041.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);

// BEGIN MadCommon.glsl
/*
MadCommon Glsl Library

Copyright (c) 2016, Garage Cube, All rights reserved.
Copyright (c) 2016, Simon Geilfus, All rights reserved.

Portions of code from Romain Dura see corresponding licence

Redistribution and use in source and binary forms, with or without modification, are permitted provided that
the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and
 the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
 the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
*/

//! Constants
#define PI 3.1415926535897932384626433832795

//! Returns the luminance of a RGB color
float luma( vec3 color );

//! Returns the luminance of a RGB color
float luminance( vec3 color );

//! Luminance based rgb8/linear conversion
vec3 linearToRgb( vec3 color, vec3 range );

//! Luminance based rgb8/linear conversion
vec3 rgbToLinear( vec3 color, vec3 range );

//! Contrast, saturation, brightness, For all settings: 1.0 = 100% 0.5=50% 1.5 = 150%
vec3 applyContrastSaturationBrightness( vec3 color, float contrast, float saturation, float brightness );

//! Returns HSV values for RGB input color
vec3 rgb2hsv( vec3 color );

//! Returns RGB values for HSV input color
vec3 hsv2rgb( vec3 color );

//! Returns the Hue value for RGB input color
float rgb2hue( vec3 color );

//! Usefull shortcuts
#define saturate(x) clamp( x, 0.0, 1.0 )
#define lerp(x,y,t) mix( x, y, t )

// Implementation

// Luminance
float luma( vec3 color )
{
    // Rec 709 Coefficients
    return dot( color, vec3( 0.2126729, 0.7151522, 0.0721750 ) );
}
float luminance( vec3 color )
{
    return dot( color, vec3( 0.299, 0.587, 0.114 ) );
}

// Luminance based rgb8/linear conversion
vec3 linearToRgb( vec3 color, vec3 range )
{
    return ( color ) / ( vec3( 1.0 ) - vec3( luminance( color ) ) / range );
}

vec3 rgbToLinear( vec3 color, vec3 range )
{
    return ( color ) / ( vec3( 1.0 ) + vec3( luminance( color ) ) / range );
}

// RGB <-> HSV Conversion functions
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    //vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    //vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    vec4 p = c.g < c.b ? vec4(c.bg, K.wz) : vec4(c.gb, K.xy);
    vec4 q = c.r < p.x ? vec4(p.xyw, c.r) : vec4(c.r, p.yzx);
    
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float rgb2hue(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return abs(q.z + (q.w - q.y) / (6.0 * d + e));
}

/*
** Copyright (c) 2012, Romain Dura romain@shazbits.com
** 
** Permission to use, copy, modify, and/or distribute this software for any 
** purpose with or without fee is hereby granted, provided that the above 
** copyright notice and this permission notice appear in all copies.
** 
** THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES 
** WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF 
** MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY 
** SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES 
** WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN 
** ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR 
** IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/


/*
** Contrast, saturation, brightness
** Code of this function is from TGM's shader pack
** http://irrlicht.sourceforge.net/phpBB2/viewtopic.php?t=21057
*/

// For all settings: 1.0 = 100% 0.5=50% 1.5 = 150%
vec3 applyContrastSaturationBrightness( vec3 color, float contrast, float saturation, float brightness )
{
    // Increase or decrease theese values to adjust r, g and b color channels seperately
    const float AvgLumR = 0.5;
    const float AvgLumG = 0.5;
    const float AvgLumB = 0.5;
    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    
    vec3 AvgLumin = vec3(AvgLumR, AvgLumG, AvgLumB);
    vec3 brtColor = color * brightness;
    vec3 intensity = vec3(dot(brtColor, LumCoeff));
    vec3 satColor = mix( intensity, brtColor, saturation );
    vec3 conColor = mix( AvgLumin, satColor, contrast );
    return conColor;
}
// END MadCommon.glsl

float mat_a1_time = (mat_a1_time_source - mat_a1_offset * 8. * mat_a1_offset_scale) * 4.;
float mat_a2_time = (mat_a2_time_source - mat_a2_offset * 8. * mat_a2_offset_scale) * 0.05;

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
}

vec2 flipX(vec2 coord, float multiplier) {
    
    
    vec2 new_coord = coord * multiplier;
    new_coord += vec2(0.5);
    new_coord.x = 1.-new_coord.x;
    new_coord -= vec2(0.5);
    return new_coord;
}

vec2 flipY(vec2 coord, float multiplier) {
    
    
    vec2 new_coord = coord * multiplier;
    new_coord += vec2(0.5);
    new_coord.y = 1.-new_coord.y;
    new_coord -= vec2(0.5);
    return new_coord;
}

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

vec2 mirrorUV(vec2 uv) {
    uv += vec2(0.5);
    if (mat_mirror_x) {
        if (uv.x > 0.5)   {
            uv.x = 1.0-uv.x;
        }
    }
    if (mat_mirror_y) {
        if (uv.y > 0.5) {
            uv.y = 1.0-uv.y;
        }
    }
    uv -= vec2(0.5);
    return uv;
}

vec2 transformUV(vec2 uv) {

    if (mat_lock_aspect) {
        uv.x *= RENDERSIZE.x / RENDERSIZE.y;
    }
    uv *= mat_scale * 2.;

    uv = mirrorUV(uv);

    vec2 uv_shift = mat_shift_amount * mat_shift_scale;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    if (mat_shift_type == 0) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, -1. * 2*PI*(mat_rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    
    if (mat_shift_type == 1) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    return uv;
}









vec3 normalMap(vec3 p, vec3 n);
float calcAO( in vec3 pos, in vec3 nor );
float noise_3(in vec3 p); 
vec3 FlameColour(float f);
mat3 fromEuler(vec3 ang);



float sdSphere( vec3 p, float s )
{
    return length(p)-s;
}
float sdBox( vec3 p, vec3 b )
{
  vec3 d = abs(p) - b;
  return min(max(d.x,max(d.y,d.z)),0.0) + length(max(d,0.0));
}
float sdBox( vec3 p)
{
  vec3 b=vec3(0.4);
  vec3 d = abs(p) - b;
  return min(max(d.x,max(d.y,d.z)),0.0) + length(max(d,0.0));
}
float sdTorus( vec3 p, vec2 t )
{
  vec2 q = vec2(length(p.xy)-t.x,p.z);
  return length(q)-t.y;
}
float udRoundBox(vec3 p, vec3 b, float r) {
    
    return length(max(abs(p) - b, 0.0)) - r;
}

float map(in vec3 p)
{
mat3 rot=fromEuler(vec3(0.0,0.0,mat_a1_time*0.2));
vec3 p1=(p+vec3( 0.0, -0.0, 1.2))*rot;
vec3 p2=(p+vec3( 1.2, -0.0, 0.0))*rot;
vec3 p3=(p+vec3(-1.2, -0.0, 0.0))*rot;
vec3 p4=(p+vec3( 0.0, -0.0,-1.2))*rot;
vec3 p5=(p+vec3( 0.0, -1.2, 0.0))*rot;
return min(min(min(min(sdBox(p1),sdBox(p2)),sdBox(p3)),sdBox(p4)),sdBox(p5));



}


vec3 gradient( in vec3 p ) 
{
    const float d = 0.001;
    vec3 grad = vec3(map(p+vec3(d,0,0))-map(p-vec3(d,0,0)),
                     map(p+vec3(0,d,0))-map(p-vec3(0,d,0)),
                     map(p+vec3(0,0,d))-map(p-vec3(0,0,d)));
    return grad;
}


float trace(vec3 o, vec3 r, out vec3 p)
{
float d=0.0, t=0.0;
for (int i=0; i<mat_iterations1; ++i)
{
    p= o+r*t;
    d=map(p);
    if(d<0.0) break;
    t += d*0.8; 
    }
return t;
}

float traceInner(vec3 o, vec3 r, out vec3 p)
{
float d=0.0, t=0.01;
for (int i=0; i<mat_iterations2; ++i)
{
    p= o+r*t;
    d=-map(p);
    if(d<0.001 || t>10.0) break;
    t += d*0.5; 
    }
return t;
}



float fbm(in vec2 uv);
vec3 getSkyFBM(vec3 e) {    
    vec3 f=e;
    float m = 2.0 * sqrt(f.x*f.x + f.y*f.y + f.z*f.z);
    vec2 st= vec2(-f.x/m + .5, -f.y/m + .5);
    
    float fog= fbm(0.6*st+vec2(-0.2*mat_a1_time, -0.02*mat_a1_time))*0.5+0.3;
    return vec3(fog);
}

vec3 sky_color(vec3 e) {    
    e.y = max(e.y,0.0);
    vec3 ret;
    ret=FlameColour(e.y);
    return ret;
}

vec3 getSkyALL(vec3 e)
{
    return sky_color(e);
}


mat3 setCamera( in vec3 ro, in vec3 ta, float cr )
{
    vec3 cw = normalize(ta-ro);
    vec3 cp = vec3(sin(cr), cos(cr),0.0);
    vec3 cu = normalize( cross(cw,cp) );
    vec3 cv = normalize( cross(cu,cw) );
    return mat3( cu, cv, cw );
}


mat3 fromEuler(vec3 ang) {
    vec2 a1 = vec2(sin(ang.x),cos(ang.x));
    vec2 a2 = vec2(sin(ang.y),cos(ang.y));
    vec2 a3 = vec2(sin(ang.z),cos(ang.z));
    vec3 m0 = vec3(a1.y*a3.y+a1.x*a2.x*a3.x,a1.y*a2.x*a3.x+a3.y*a1.x,-a2.y*a3.x);
    vec3 m1 = vec3(-a2.y*a1.x,a1.y*a2.y,a2.x);
    vec3 m2 = vec3(a3.y*a1.x*a2.x+a1.y*a3.x,a1.x*a3.x-a1.y*a3.y*a2.x,a2.y*a3.y);
    return mat3(m0, m1, m2) / mat_size;
}

vec3 render( in vec3 RayOri, in vec3 RayDir ){

    
    vec3 p,n;
    float t = trace(RayOri, RayDir, p);
    n=normalize(gradient(p));
    vec3 bump=normalMap(p*3.0,n);
    n=n+bump*0.05 * mat_texture;
    float edge= dot(-RayDir, n);
    edge = smoothstep(-.20, 0.5, edge);

    
    vec3 p2,n2;
    float IOR=1.33 * mat_inside;
    vec3 Rd_2=refract(RayDir,n,1.0/IOR) * mat_cycle1;
    float t2 = traceInner(p, Rd_2, p2);
    n2=normalize(gradient(p2));
    
    vec3 Rd_3=refract(Rd_2,-n2,IOR/1.0);
    vec3 refl=getSkyALL(reflect(RayDir,n));
    vec3 refr=getSkyALL(Rd_3)+FlameColour(t2*1.0);
    float F=1.0-0.8*dot(n,-RayDir) * mat_cycle2; 
    vec3 final = mix(refr,refl, F);


    vec3 result;
    result=final*edge * mat_glow;


    vec3 BG=getSkyALL(RayDir) * mat_sky;     

if(t<4.) return result; else return BG;
}




float hash11(float p) {
    return fract(sin(p * 727.1)*43758.5453123);
}
float hash12(vec2 p) {
    float h = dot(p,vec2(127.1,311.7));
    return fract(sin(h)*43758.5453123);
}
vec3 hash31(float p) {
    vec3 h = vec3(1275.231,4461.7,7182.423) * p;
    return fract(sin(h)*43758.543123);
}


float noise_3(in vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f*f*(3.0-2.0*f);

    vec2 ii = i.xy + i.z * vec2(5.0);
    float a = hash12( ii + vec2(0.0,0.0) );
    float b = hash12( ii + vec2(1.0,0.0) );
    float c = hash12( ii + vec2(0.0,1.0) );
    float d = hash12( ii + vec2(1.0,1.0) );
    float v1 = mix(mix(a,b,u.x), mix(c,d,u.x), u.y);

    ii += vec2(5.0);
    a = hash12( ii + vec2(0.0,0.0) );
    b = hash12( ii + vec2(1.0,0.0) );
    c = hash12( ii + vec2(0.0,1.0) );
    d = hash12( ii + vec2(1.0,1.0) );
    float v2 = mix(mix(a,b,u.x), mix(c,d,u.x), u.y);

    return max(mix(v1,v2,u.z),0.0);
}

float glow(float d, float str, float thickness){
    return thickness / pow(d, str);
}


vec2 hash2( vec2 x )            
{
    const vec2 k = vec2( 0.3183099, 0.3678794 );
    x = x*k + k.yx;
    return -1.0 + 2.0*fract( 16.0 * k*fract( x.x*x.y*(x.x+x.y)) );
}
float gnoise( in vec2 p )       
{
    vec2 i = floor( p );
    vec2 f = fract( p );

    vec2 u = f*f*(3.0-2.0*f);

    return mix( mix( dot( hash2( i + vec2(0.0,0.0) ), f - vec2(0.0,0.0) ),
                            dot( hash2( i + vec2(1.0,0.0) ), f - vec2(1.0,0.0) ), u.x),
                         mix( dot( hash2( i + vec2(0.0,1.0) ), f - vec2(0.0,1.0) ),
                            dot( hash2( i + vec2(1.0,1.0) ), f - vec2(1.0,1.0) ), u.x), u.y);
}
float fbm(in vec2 uv)       
{
    float f;                
    mat2 m = mat2( 1.6,  1.2, -1.2,  1.6 );
    f   = 0.5000*gnoise( uv ); uv = m*uv;
    f += 0.2500*gnoise( uv ); uv = m*uv;
    f += 0.1250*gnoise( uv ); uv = m*uv;
    f += 0.0625*gnoise( uv ); uv = m*uv;
    return f;
}


vec3 smoothSampling2(vec2 uv)
{
    const float T_RES = 32.0;
    return vec3(gnoise(uv*T_RES)); 
}

float triplanarSampling(vec3 p, vec3 n)
{
    float fTotal = abs(n.x)+abs(n.y)+abs(n.z);
    return  (abs(n.x)*smoothSampling2(p.yz).x
            +abs(n.y)*smoothSampling2(p.xz).x
            +abs(n.z)*smoothSampling2(p.xy).x)/fTotal;
}

const mat2 m2 = mat2(0.90,0.44,-0.44,0.90);
float triplanarNoise(vec3 p, vec3 n)
{
    const float BUMP_MAP_UV_SCALE = 0.2;
    float fTotal = abs(n.x)+abs(n.y)+abs(n.z);
    float f1 = triplanarSampling(p*BUMP_MAP_UV_SCALE,n);
    p.xy = m2*p.xy;
    p.xz = m2*p.xz;
    p *= 2.1;
    float f2 = triplanarSampling(p*BUMP_MAP_UV_SCALE,n);
    p.yx = m2*p.yx;
    p.yz = m2*p.yz;
    p *= 2.3;
    float f3 = triplanarSampling(p*BUMP_MAP_UV_SCALE,n);
    return f1+0.5*f2+0.25*f3;
}

vec3 normalMap(vec3 p, vec3 n)
{
    float d = 0.005;
    float po = triplanarNoise(p,n);
    float px = triplanarNoise(p+vec3(d,0,0),n);
    float py = triplanarNoise(p+vec3(0,d,0),n);
    float pz = triplanarNoise(p+vec3(0,0,d),n);
    return normalize(vec3((px-po)/d,
                          (py-po)/d,
                          (pz-po)/d));
}






vec3 hsv2rgb_smooth( in vec3 c )
{
    vec3 rgb = clamp( abs(mod(c.x*6.0+vec3(0.0,4.0,2.0),6.0)-3.0)-1.0, 0.0, 1.0 );

    rgb = rgb*rgb*(3.0-2.0*rgb); 

    return c.z * mix( vec3(1.0), rgb, c.y);
}

vec3 hsv2rgb_trigonometric( in vec3 c )
{
    vec3 rgb = 0.5 + 0.5*cos((c.x*6.0+vec3(0.0,4.0,2.0))*3.14159/3.0);

    return c.z * mix( vec3(1.0), rgb, c.y);
}

vec3 FlameColour(float f)
{
    return hsv2rgb_smooth(vec3((f-(2.25/6.))*(1.25/6.),f*1.25+.2,f*.95));
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 cam = flipX(mat_cam, mat_cam_scale * 0.5);
    cam = flipY(cam, 1.);

    if (mat_a2_animate) {
        cam.x += mat_a2_time;
    }


    vec3 CameraRot=vec3(0.0, -cam.y*1.6, -cam.x*6.28);
    vec3 ro= vec3(0.0, 0.0, 0.0);
    vec3 ta =vec3(0.0, 0.0, -1.0)*fromEuler(CameraRot);
    mat3 ca = setCamera( ro, ta, 0.0 );
    vec3 RayDir = ca*normalize(vec3(uv, 1.5));
    vec3 RayOri = ro;
    vec3 col = render(RayOri,RayDir);
    out_color = vec4( col, 1.0 );


    
    if (mat_luma_to_alpha && mat_luma_mode == 0) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
    }

    
    if (mat_invert) out_color.rgb=1-out_color.rgb;

    
    if (mat_hue_shift > 0.01 || mat_saturation != 0) {
        vec3 hsv = rgb2hsv(out_color.rgb);
        hsv.x = fract(0.9999999*(hsv.x+mat_hue_shift));
        hsv.y = max(hsv.y + mat_saturation, 0);
        out_color.rgb = hsv2rgb(hsv);
    }

    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    const vec3 AvgLumin = vec3(0.5, 0.5, 0.5);
    vec3 intensity = vec3(dot(out_color.rgb, LumCoeff));
    out_color.rgb = mix(AvgLumin, out_color.rgb, mat_contrast);

    
    out_color.rgb += mat_brightness;

    
    if (mat_luma_to_alpha && mat_luma_mode == 1) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
