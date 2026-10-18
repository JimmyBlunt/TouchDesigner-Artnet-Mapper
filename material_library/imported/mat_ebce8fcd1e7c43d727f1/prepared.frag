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

uniform vec4 uMMParam000; // native input: mat_scale
float mat_scale = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_rotate
float mat_rotate = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: mat_shift_scale
float mat_shift_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_shift_type
int mat_shift_type = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_scale1
float mat_scale1 = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_scale2
float mat_scale2 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_scale3
float mat_scale3 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_speed
float mat_speed = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_reverse
bool mat_reverse = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_offset
float mat_offset = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_offset_scale
float mat_offset_scale = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_strob
float mat_strob = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_restart
int mat_restart = int(round(uMMParam016.x));
uniform vec4 uMMParam017; // native input: mat_scroll_speed
float mat_scroll_speed = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_scroll_bpm_sync
bool mat_scroll_bpm_sync = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_scroll_reverse
bool mat_scroll_reverse = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_scroll_offset
float mat_scroll_offset = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_scroll_offset_scale
float mat_scroll_offset_scale = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_scroll_strob
float mat_scroll_strob = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_scroll_restart
int mat_scroll_restart = int(round(uMMParam023.x));
uniform vec4 uMMParam024; // native input: mat_front_color
vec4 mat_front_color = uMMParam024;
uniform vec4 uMMParam025; // native input: mat_back_color
vec4 mat_back_color = uMMParam025;
uniform vec4 uMMParam026; // native input: mat_invert
bool mat_invert = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam027.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_scroll_time_source = uTDTime * (mat_scroll_speed);

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

float mat_time = mat_time_source - mat_offset * 8. * mat_offset_scale;
float mat_scroll_time = mat_scroll_time_source - mat_scroll_offset * 8. * mat_scroll_offset_scale;

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
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
    uv *= mat_scale;

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



#define Rot(a) mat2(cos(a),-sin(a),sin(a),cos(a))
#define antialiasing(n) n/min(RENDERSIZE.y,RENDERSIZE.x)
#define S(d,b) smoothstep(antialiasing(1.0),b,d)
#define B(p,s) max(abs(p).x-s.x,abs(p).y-s.y)
#define Tri(p,s,a) max(-dot(p,vec2(cos(-a),sin(-a))),max(dot(p,vec2(cos(a),sin(a))),max(abs(p).x-s.x,abs(p).y-s.y)))
#define DF(a,b) length(a) * cos( mod( atan(a.y,a.x)+6.28/(b*8.0), 6.28/((b*8.0)*0.5))+(b-1.)*6.28/(b*8.0) + vec2(0,11) )

float FS = 0.46 / mat_scale1; 
float FGS = FS/5. / mat_scale2; 



#define char_0 0
#define char_1 1
#define char_2 2
#define char_3 3
#define char_4 4
#define char_5 5
#define char_6 6
#define char_7 7
#define char_8 8
#define char_9 9
#define char_A 10
#define char_B 11
#define char_C 12
#define char_D 13
#define char_E 14
#define char_F 15
#define char_G 16
#define char_H 17
#define char_I 18
#define char_J 19
#define char_K 20
#define char_L 21
#define char_M 22
#define char_N 23
#define char_O 24
#define char_P 25
#define char_Q 26
#define char_R 27
#define char_S 28
#define char_T 29
#define char_U 30
#define char_V 31
#define char_W 32
#define char_X 33
#define char_Y 34
#define char_Z 35

float random (vec2 p) {
    return fract(sin(dot(p.xy, vec2(12.9898,78.233)))* 43758.5453123);
}

float charA(vec2 p){
    vec2 prevP = p;
    float d = B(p-vec2(0.0,FGS*4.),vec2(FS,FGS));
    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);
    p.x = abs(p.x);
    d2 = B(p-vec2(FGS*4.,0.),vec2(FGS,FS));
    d = min(d,d2);
    return d;
}

float charB(vec2 p) {
    vec2 prevP = p;
    p.y = abs(p.y);
    float d = B(p-vec2(0.0,FGS*4.),vec2(FS,FGS));
    p = prevP;
    float d2 = B(p-vec2(-FGS,0.0),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*4.,0.),vec2(FGS,FS));
    d = min(d,d2);

    p.y = abs(p.y);
    p-=vec2(FGS*2.,FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charC(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.0,FGS*4.),vec2(FS,FGS));

    float d2 = B(p-vec2(FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*4.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    p-=vec2(-FGS*2.,-FGS*2.);
    p*=Rot(radians(-45.));

    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charD(vec2 p){
    vec2 prevP = p;
    p.y=abs(p.y);
    float d = B(p-vec2(0.0,FGS*4.),vec2(FS,FGS));
    p = prevP;
    float d2 = B(p-vec2(FGS*4.,0.),vec2(FGS,FS));
    d = min(d,d2);

    d2 = B(p,vec2(FGS,FS));
    d = min(d,d2);
    return d;
}

float charE(vec2 p) {
    vec2 prevP = p;

    float d = charC(p);
    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    return d;
}

float charF(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.0,FGS*4.),vec2(FS,FGS));

    float d2 = B(p-vec2(-FGS,0.),vec2(FGS*4.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*4.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    p-=vec2(0.,-FGS*2.);

    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charG(vec2 p) {
    vec2 prevP = p;

    float d = charC(p);
    float d2 = B(p-vec2(FGS*2.,0.),vec2(FGS*3.,FGS));
    d = min(d,d2);
    d2 = B(p-vec2(FGS*4.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charH(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(FGS*4.,0.0),vec2(FGS,FS));

    float d2 = B(p-vec2(0.0,0.0),vec2(FGS,FS));
    d = min(d,d2);
    d2 = B(p-vec2(FGS*2.,0.0),vec2(FGS*3.,FGS));
    d = min(d,d2);
    p.y = abs(p.y);
    d2 = B(p-vec2(-FGS*2.,FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    return d;
}

float charI(vec2 p) {
    vec2 prevP = p;
    p.y = abs(p.y);
    float d = B(p-vec2(0.,FGS*4.),vec2(FS,FGS));
    p = prevP;
    float d2 = B(p,vec2(FGS,FS));
    d = min(d,d2);
    d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);
    return d;
}

float charJ(vec2 p) {
    vec2 prevP = p;
    float d = B(p-vec2(0.,FGS*4.),vec2(FS,FGS));

    float d2 = B(p-vec2(0.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);
    d2 = B(p-vec2(-FGS*4.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    p-=vec2(-FGS*2.,-FGS*2.);
    p*=Rot(radians(45.));

    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charK(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(FGS*4.,FGS*2.),vec2(FGS,FGS*3.));

    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*4.,0.0),vec2(FGS,FS));
    d = min(d,d2);

    d2 = B(p-vec2(FGS*2.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charL(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*4.,FGS*2.),vec2(FGS,FGS*3.));

    float d2 = B(p-vec2(FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);


    p-=vec2(-FGS*2.,-FGS*2.);
    p*=Rot(radians(-45.));

    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charM(vec2 p) {
    vec2 prevP = p;

    float d = B(p,vec2(FS,FGS));

    float d2 = B(p,vec2(FGS,FS));
    d = min(d,d2);

    p.x = abs(p.x);
    d2 = B(p-vec2(FGS*4.,-FGS),vec2(FGS,FGS*4.));
    d = min(d,d2);

    return d;
}

float charN(vec2 p) {
    vec2 prevP = p;

    p.x = abs(p.x);
    float d = B(p-vec2(FGS*4.,0.),vec2(FGS,FS));

    p = prevP;
    float d2 = B(p,vec2(FGS,FS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*2.,FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    return d;
}

float charO(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(FGS*4.,FGS*2.),vec2(FGS,FGS*3.));

    p = prevP;
    float d2 = B(p-vec2(FGS*2.,FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*4.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    p-=vec2(-FGS*2.,FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    p =prevP;
    p-=vec2(FGS*2.,-FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charP(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.,FGS*4.),vec2(FS,FGS));

    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*2.,0.),vec2(FGS,FS));
    d = min(d,d2);

    d2 = B(p-vec2(FGS*4.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charQ(vec2 p) {
    vec2 prevP = p;

    float d = charO(p);

    p-=vec2(FGS*2.,-FGS*2.);
    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS*3.,FGS));
    d = min(d,d2);

    return d;
}

float charR(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.,FGS*4.),vec2(FS,FGS));

    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*4.,0.),vec2(FGS,FS));
    d = min(d,d2);

    d2 = B(p-vec2(FGS*4.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    d2 = B(p-vec2(0.0,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    d2 = B(p-vec2(FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    return d;
}

float charS(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(FGS*2.,FGS*4.),vec2(FGS*3.,FGS));

    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    p-=vec2(-FGS*2.,FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    p = prevP;
    d2 = B(p-vec2(-FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    p-=vec2(FGS*2.,-FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float charT(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.,FGS*2.),vec2(FS,FGS));

    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    return d;
}

float charU(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.,-FGS*2.),vec2(FS,FGS));

    p.x = abs(p.x);
    float d2 = B(p-vec2(FGS*2.,0.),vec2(FGS,FS));
    d = min(d,d2);

    return d;
}

float charV(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*4.,0.),vec2(FGS,FS));

    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    return d;
}

float charW(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*4.,0.),vec2(FGS,FS));

    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    p = prevP;
    d2 = B(p,vec2(FGS,FS));
    d = min(d,d2);

    p-=vec2(FGS*2.,-FGS*2.);
    p*=Rot(radians(-45.));
    d2 = B(p,vec2(FGS*3.,FGS));
    d = min(d,d2);

    return d;
}

float charX(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*4.,FGS*2.),vec2(FGS,FGS*3.));

    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    p = prevP;
    d2 = B(p-vec2(FGS*4.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    return d;
}

float charY(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*4.,FGS*2.),vec2(FGS,FGS*3.));

    float d2 = B(p-vec2(0.,-FGS),vec2(FGS,FGS*4.));
    d = min(d,d2);

    p = prevP;
    d2 = B(p-vec2(FGS*4.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    return d;
}

float charZ(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*4.,FGS*3.),vec2(FGS,FGS*2.));

    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    p = prevP;
    d2 = B(p-vec2(FGS*4.,-FGS*3.),vec2(FGS,FGS*2.));
    d = min(d,d2);

    p.y = abs(p.y);
    d2 = B(p-vec2(0., FGS*4.),vec2(FS,FGS));
    d = min(d,d2);

    return d;
}

float char1(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*2.,FGS*4.),vec2(FGS*3.,FGS));

    float d2 = B(p,vec2(FGS,FS));
    d = min(d,d2);

    d2 = B(p-vec2(0.,-FGS*4.),vec2(FS,FGS));
    d = min(d,d2);

    return d;
}

float char2(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(FGS*2.,FGS*4.),vec2(FGS*3.,FGS));

    float d2 = B(p-vec2(FGS*4.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);
    d2 = B(p-vec2(FGS*2.,0.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(0.,-FGS*4.),vec2(FS,FGS));
    d = min(d,d2);

    p-=vec2(-FGS*2.,FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    p = prevP;
    p-=vec2(-FGS*2.,-FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float char3(vec2 p) {
    vec2 prevP = p;

    p.y = abs(p.y);
    float d = B(p-vec2(0.,FGS*4.),vec2(FS,FGS));

    p = prevP;
    p.x = abs(p.x);
    float d2 = B(p-vec2(FGS*4.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    p = prevP;
    d2 = B(p-vec2(FGS*2.,0.),vec2(FGS*3.,FGS));
    d = min(d,d2);


    p-=vec2(FGS*2.,FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float char4(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.,-FGS*2.),vec2(FS,FGS));

    float d2 = B(p-vec2(-FGS*2.,0.),vec2(FGS,FS));
    d = min(d,d2);

    d2 = B(p-vec2(FGS*2.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float char5(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(0.,FGS*4.),vec2(FS,FGS));

    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*4.,FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    p = prevP;
    d2 = B(p-vec2(-FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    p-=vec2(FGS*2.,-FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float char6(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(FGS*2.,FGS*4.),vec2(FGS*3.,FGS));

    float d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    p-=vec2(-FGS*2.,FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    p = prevP;
    d2 = B(p-vec2(0.,-FGS*4.),vec2(FS,FGS));
    d = min(d,d2);

    p.x = abs(p.x);
    d2 = B(p-vec2(FGS*4.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float char7(vec2 p) {
    vec2 prevP = p;

    float d = B(p,vec2(FS,FGS));

    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    p = prevP;


    d2 = B(p-vec2(0., FGS*4.),vec2(FS,FGS));
    d = min(d,d2);

    return d;
}

float char8(vec2 p) {
    vec2 prevP = p;

    p.y = abs(p.y);
    float d = B(p-vec2(0., FGS*4.),vec2(FS,FGS));

    p = prevP;
    p*=Rot(radians(45.));
    float d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(-45.));
    d2 = B(p,vec2(FGS,FS*1.2));
    d = min(d,d2);

    return d;
}

float char9(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(FGS*4.,FGS*2.),vec2(FGS,FGS*3.));

    p = prevP;
    float d2 = B(p-vec2(FGS*2.,FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(-FGS*2.,-FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p,vec2(FS,FGS));
    d = min(d,d2);

    p-=vec2(-FGS*2.,FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    p =prevP;
    p-=vec2(FGS*2.,-FGS*2.);
    p*=Rot(radians(45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float char0(vec2 p) {
    vec2 prevP = p;

    float d = B(p-vec2(-FGS*4.,0.),vec2(FGS,FS));

    float d2 = B(p-vec2(-FGS*2.,FGS*4.),vec2(FGS*3.,FGS));
    d = min(d,d2);

    d2 = B(p-vec2(0.0,-FGS*4.),vec2(FS,FGS));
    d = min(d,d2);

    p-=vec2(FGS*2.,FGS*2.);
    p*=Rot(radians(-45.));
    d2 = B(p,vec2(FGS,FGS*3.));
    d = min(d,d2);

    p =prevP;
    d2 = B(p-vec2(FGS*4.,-FGS*2.),vec2(FGS,FGS*3.));
    d = min(d,d2);

    return d;
}

float checkChar(int targetChar, int char2){
    return 1.-abs(sign(float(targetChar) - float(char2)));
}

float drawFont(vec2 p, int char_in){
    float d = char0(p)*checkChar(char_0,char_in);
    d += char1(p)*checkChar(char_1,char_in);
    d += char2(p)*checkChar(char_2,char_in);
    d += char3(p)*checkChar(char_3,char_in);
    d += char4(p)*checkChar(char_4,char_in);
    d += char5(p)*checkChar(char_5,char_in);
    d += char6(p)*checkChar(char_6,char_in);
    d += char7(p)*checkChar(char_7,char_in);
    d += char8(p)*checkChar(char_8,char_in);
    d += char9(p)*checkChar(char_9,char_in);
    d += charA(p)*checkChar(char_A,char_in);
    d += charB(p)*checkChar(char_B,char_in);
    d += charC(p)*checkChar(char_C,char_in);
    d += charD(p)*checkChar(char_D,char_in);
    d += charE(p)*checkChar(char_E,char_in);
    d += charF(p)*checkChar(char_F,char_in);
    d += charG(p)*checkChar(char_G,char_in);
    d += charH(p)*checkChar(char_H,char_in);
    d += charI(p)*checkChar(char_I,char_in);
    d += charJ(p)*checkChar(char_J,char_in);
    d += charK(p)*checkChar(char_K,char_in);
    d += charL(p)*checkChar(char_L,char_in);
    d += charM(p)*checkChar(char_M,char_in);
    d += charN(p)*checkChar(char_N,char_in);
    d += charO(p)*checkChar(char_O,char_in);
    d += charP(p)*checkChar(char_P,char_in);
    d += charQ(p)*checkChar(char_Q,char_in);
    d += charR(p)*checkChar(char_R,char_in);
    d += charS(p)*checkChar(char_S,char_in);
    d += charT(p)*checkChar(char_T,char_in);
    d += charU(p)*checkChar(char_U,char_in);
    d += charV(p)*checkChar(char_V,char_in);
    d += charW(p)*checkChar(char_W,char_in);
    d += charX(p)*checkChar(char_X,char_in);
    d += charY(p)*checkChar(char_Y,char_in);
    d += charZ(p)*checkChar(char_Z,char_in);

    float a = radians(45.);
    p = abs(p)-0.37;
    d = max(dot(p,vec2(cos(a),sin(a))),d);

    #ifdef OUTLINE
        return abs(d)-0.01;
    #endif

    return d;
}

float dSlopeLines(vec2 p){
    float lineSize = 24.;
    float d = tan((mix(p.x,p.y,0.7)+(-mat_time*1.5/lineSize))*lineSize)*lineSize;
    return d;
}

float blocks(vec2 p){
    vec2 prevP = p;

    p.x = mod(p.x,0.24)-0.12;
    float d = B(p, vec2(FGS*0.55));
    p = prevP;
    p.x+=0.12;
    p.x = mod(p.x,0.24)-0.12;
    p.y = abs(p.y)-0.12;
    float d2 = B(p, vec2(FGS*0.55));
    return min(d,d2);
}

float blocks2(vec2 p){
    p.y = mod(p.y,0.92)-0.46;
    vec2 prevP = p;
    p.y-=FGS*2.5;
    float d = abs(B(p,vec2(FGS*1.7)))-0.03;
    float d2 = B(p,vec2(FGS*0.5));
    d = min(d,d2);
    p = prevP;
    p.y-=-FGS*2.5;
    d2 = abs(B(p,vec2(FGS)))-0.03;
    d = min(d,d2);

    return d;
}

float cubicInOut(float t) {
  return t < 0.5
    ? 4.0 * t * t * t
    : 0.5 * pow(2.0 * t - 2.0, 3.0) + 1.0;
}

float getTime(float t, float duration){
    return clamp(t,0.0,duration)/duration;
}

float drawFonts4GridsSpace(int char_in, float scale, vec2 grd, vec2 prevGrd, vec2 pa, vec2 pb, vec2 pc, vec2 pd){
    grd-=pa;
    grd*=scale;

    float d = drawFont(grd,char_in);
    grd = prevGrd;

    grd -=pb;
    grd*=scale;
    float d2 = drawFont(grd,(char_in+1>=35)?10:char_in+1);
    d = min(d,d2);
    grd = prevGrd;

    grd -=pc;
    grd*=scale;
    d2 = drawFont(grd,(char_in+2>=35)?10:char_in+2);
    d = min(d,d2);
    grd = prevGrd;

    grd -=pd;
    grd*=scale;
    d2 = drawFont(grd,(char_in+3>=35)?10:char_in+3);
    d = min(d,d2);
    return d;
}

float gridSystem(vec2 p){
    vec2 prevP = p;
    p*=3.;
    p.y-=mat_scroll_time*0.5;
    vec2 id = floor(p);
    vec2 grd = fract(p)-0.5;

    float n = random(id);
    float nChar = random(id)*35.0;
    int char_in = int(nChar);
    float d = drawFont(grd,char_in);
    if(n>=0.1 && n<0.2 && char_in < 10){
        int num = int(mod(mat_time*float(nChar),10.0));
        d = drawFont(grd,num);
    }

    float d2 = 10.;

    vec2 prevGrd = grd;
    float scale = 2.1 * mat_scale3;
    if(n>=0.2 && n<0.5){

        float frame = mod(mat_time,10.0);
        float time = frame;

        vec2 pa = vec2(-0.24,0.24);
        vec2 pb = vec2(-0.24,-0.24);
        vec2 pc = vec2(0.24,-0.24);
        vec2 pd = vec2(0.24,0.24);
        if(frame>=1. && frame<3.){
            time = getTime(time-1.,0.6);
            float val = cubicInOut(time)*0.48;
            pa = vec2(-0.24,0.24-val);
            pb = vec2(-0.24+val,-0.24);
            pc = vec2(0.24,-0.24+val);
            pd = vec2(0.24-val,0.24);
        } else if(frame>=3. && frame<5.){
            time = getTime(time-3.,0.6);
            float val = cubicInOut(time)*0.48;
            pa = vec2(-0.24+val,-0.24);
            pb = vec2(0.24,-0.24+val);
            pc = vec2(0.24-val,0.24);
            pd = vec2(-0.24,0.24-val);
        } else if(frame>=5. && frame<7.){
            time = getTime(time-5.,0.6);
            float val = cubicInOut(time)*0.48;
            pa = vec2(0.24,-0.24+val);
            pb = vec2(0.24-val,0.24);
            pc = vec2(-0.24,0.24-val);
            pd = vec2(-0.24+val,-0.24);
        } else if(frame>=7. && frame<10.){
            time = getTime(time-7.,0.6);
            float val = cubicInOut(time)*0.48;
            pa = vec2(0.24-val,0.24);
            pb = vec2(-0.24,0.24-val);
            pc = vec2(-0.24+val,-0.24);
            pd = vec2(0.24,-0.24+val);
        }

        d = drawFonts4GridsSpace(char_in, scale, grd, prevGrd, pa, pb, pc, pd);

    } else if(n>=0.5 && n<0.6){
        
        grd-=vec2(-0.24,0.24);
        grd*=scale;
        d = drawFont(grd,char_in);
        grd = prevGrd;

        grd -= vec2(0.24,0.24);
        grd*=scale;
        d2 = drawFont(grd,(char_in+1>=35)?10:char_in+1);
        d = min(d,d2);
        grd = prevGrd;

        float d3 = B(grd-vec2(0.,-0.24),vec2(0.46,0.22));

        float dir = (n>=0.55)?-1.:1.;
        grd.x*=dir;
        grd.x+=mat_time*n*0.5;
        grd.x = mod(grd.x,0.2)-0.1;
        grd.x+=0.1;
        grd-=vec2(0.,-0.24);
        grd*=Rot(radians(-90.));

        d2 = Tri(grd,vec2(FGS*2.),radians(45.));
        float mask = Tri(grd-vec2(0.0,-FGS),vec2(FGS*2.),radians(45.));
        d2 = max(-mask,d2);
        d2 = max(d3,d2);
        d2 = min(d2,abs(d3)-0.01);
        d = min(d,d2);

    } else if(n>=0.7 && n<0.8){
        
        grd-=vec2(-0.24,-0.24);
        grd*=scale;
        d = drawFont(grd,char_in);
        grd = prevGrd;

        grd -= vec2(0.24,-0.24);
        grd*=scale;
        d2 = drawFont(grd,(char_in+1>=35)?10:char_in+1);
        d = min(d,d2);
        grd = prevGrd;

        float d3 = B(grd-vec2(0.,0.24),vec2(0.46,0.22));

        float dir = (n>=0.75)?-1.:1.;
        grd.x += dir*mat_time*0.2;
        d2 = blocks(grd-vec2(0.,0.24));
        d2 = max(d3,d2);
        d2 = min(d2,abs(d3)-0.01);
        d = min(d,d2);
    } else if(n>=0.8 && n<0.9){
        
        grd-=vec2(-0.24,0.24);
        grd*=scale;
        d = drawFont(grd,char_in);
        grd = prevGrd;

        grd -= vec2(-0.24,-0.24);
        grd*=scale;
        d2 = drawFont(grd,(char_in+1>=35)?10:char_in+1);
        d = min(d,d2);
        grd = prevGrd;


        float d3 = B(grd-vec2(0.24,0.0),vec2(0.22,0.46));

        grd-=vec2(0.24,0.0);
        d2 = dSlopeLines(grd);
        d2 = max(d3,d2);
        d2 = min(d2,abs(d3)-0.01);
        d = min(d,d2);
    } else if(n>=0.9 && n<1.){
        
        grd-=vec2(0.24,0.24);
        grd*=scale;
        d = drawFont(grd,char_in);
        grd = prevGrd;

        grd -= vec2(0.24,-0.24);
        grd*=scale;
        d2 = drawFont(grd,(char_in+1>=35)?10:char_in+1);
        d = min(d,d2);
        grd = prevGrd;

        float d3 = B(grd-vec2(-0.24,0.0),vec2(0.22,0.46));

        float dir = (n>=0.95)?-1.:1.;
        grd.y += dir*mat_time*0.2;
        d2 = blocks2(grd-vec2(-0.24,0.0));
        d2 = max(d3,d2);
        d2 = min(d2,abs(d3)-0.01);

        d = min(d,d2);
    }

    return d;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    vec2 p = uv;
    vec3 col =vec3(0.0);
    float d = gridSystem(p);
    col = mix(col,vec3(1.),S(d,0.0));
    out_color = vec4(sqrt(col),1.0);




    
    if (mat_invert) out_color.rgb=1-out_color.rgb;


    if (mat_luma(out_color.rgb) > 0.02) {
        out_color = mat_front_color;
    } else {
        out_color = mat_back_color;
    }


    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
