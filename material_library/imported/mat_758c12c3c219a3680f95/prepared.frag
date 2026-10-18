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
uniform vec4 uMMParam008; // native input: mat_detail
float mat_detail = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_a1_speed
float mat_a1_speed = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_a1_offset
float mat_a1_offset = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_a1_strob
float mat_a1_strob = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam015.x));
uniform vec4 uMMParam016; // native input: mat_front_color
vec4 mat_front_color = uMMParam016;
uniform vec4 uMMParam017; // native input: mat_back_color
vec4 mat_back_color = uMMParam017;
uniform vec4 uMMParam018; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam018.x));
uniform vec4 uMMParam019; // native input: mat_back_thresh
float mat_back_thresh = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_back_sensitivity
float mat_back_sensitivity = uMMParam020.x;
float mat_a1_time_source = uTDTime * (mat_a1_speed);

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

float mat_a1_time = mat_a1_time_source - mat_a1_offset * 8. * mat_a1_offset_scale;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
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
    uv *= mat_scale * 0.925;

    uv = mirrorUV(uv);

    uv.y -= 0.015;

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
#define antialiasing(n) n/(mat_detail * 2000.)
#define S(d,b) smoothstep(antialiasing(1.0),b,d)
#define DF(a,b) length(a) * cos( mod( atan(a.y,a.x)+6.28/(b*8.0), 6.28/((b*8.0)*0.5))+(b-1.)*6.28/(b*8.0) + vec2(0,11) )
#define Tri(p,s,a) max(-dot(p,vec2(cos(-a),sin(-a))),max(dot(p,vec2(cos(a),sin(a))),max(abs(p).x-s.x,abs(p).y-s.y)))
#define B(p,s) max(abs(p).x-s.x,abs(p).y-s.y)


vec2 svgPolygonData[34] = vec2[](vec2(0.1803,0.3769),vec2(0.09420002,0.354),vec2(0.04120001,0.3294),vec2(-0.01189999,0.3049),vec2(-0.0631,0.2727),vec2(-0.1072,0.237),vec2(-0.1487,0.194),vec2(-0.1832,0.1441),vec2(-0.2047,0.09520001),vec2(-0.2229,0.03929999),vec2(-0.2306,-0.0135),vec2(-0.2304,-0.07270001),vec2(-0.2218,-0.1314),vec2(-0.2062,-0.187),vec2(-0.1823,-0.2386),vec2(-0.1472,-0.2851),vec2(-0.1091,-0.3234),vec2(-0.06389999,-0.3516),vec2(-0.01620001,-0.3702),vec2(0.03920001,-0.3802),vec2(0.09659997,-0.3722),vec2(0.151,-0.347),vec2(0.1941,-0.3118),vec2(0.225,-0.2687),vec2(0.2414,-0.2238),vec2(0.2422,-0.1742),vec2(0.2302,-0.1154),vec2(0.2092,-0.059),vec2(0.1846,-0.006),vec2(0.1576,0.05610001),vec2(0.1374,0.118),vec2(0.1255,0.1803),vec2(0.1322,0.2427),vec2(0.1563,0.3115));

float SimpleVesicaDistance(vec2 p, float r, float d) {
    p.x = abs(p.x);
    p.x+=d;
    return length(p)-r;
}

float waveCircle(vec2 p, float s, float numW, float amp, float deg, float thickness){
    float r = s+amp*cos(atan(p.y,p.x)*numW);
    float d = abs(length(p)-r)-thickness;
    p*=Rot(radians(deg));
    r = s+amp*cos(atan(p.y,p.x)*numW);
    float d2 = abs(length(p)-r)-thickness;
    d = min(d,d2);
    return d;
}

float paiselyOutlineItem0(vec2 p, float i){
    vec2 prevP = p;
    float d = abs(length(p)-0.024)-0.001;
    p*=Rot(radians(mat_a1_time*30.*i));
    float d2 = abs(length(p)-0.014)-0.0025;
    d2 = max(-(abs(p.x)-0.005),d2);
    d = min(d,d2);
    return d;
}

float paiselyOutlineItem1(vec2 p, float deg){
    vec2 prevP = p;
    float d = abs(length(p)-0.03)-0.0005;
    p*=Rot(radians(sin(mat_a1_time)*deg));
    float d2 = abs(length(p)-0.03)-0.003;
    d2 = max(-p.x,d2);
    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(mat_a1_time*deg*0.5));
    d2 = abs(length(p)-0.015)-0.002;
    d2 = max(-(abs(p.x)-0.005),d2);
    d = min(d,d2);

    return d;
}

float paiselyBase(vec2 p){
    vec2 prevP = p;

    float d = 10.;

    int num = svgPolygonData.length();

    float t = mat_a1_time*2.0;
    vec2 a = vec2(0.);
    vec2 b = vec2(0.);

    for( int i=0; i<num; i++ ){
        int scene = i+int(mod(t,float(num)));
        if(scene>=num)  scene -= num;
        if(scene<num-1){
            a = svgPolygonData[scene];
            b = svgPolygonData[scene+1];
        } else {
            a = svgPolygonData[scene];
            b = svgPolygonData[0];
        }

        vec2 newPos = mix(a,b,mod(t,1.));

        float d2 = paiselyOutlineItem0(p-newPos,float(i)*0.3);

        d = min(d,d2);
    }

    return d;
}

float arrow(vec2 p){
    float d = B((p-vec2(-0.015,0.0))*Rot(radians(-45.)),vec2(0.01,0.03));
    float d2 = B((p-vec2(0.025,0.012))*Rot(radians(45.)),vec2(0.01,0.018));
    d = min(d,d2);
    return d;
}

float paiselyItem0(vec2 p){
    vec2 prevP = p;
    p*=Rot(-radians(mat_a1_time*40.));
    p = DF(p,4.0);
    p -= vec2(0.08);
    p*=1.55;
    p*=Rot( radians(150.));
    float d = arrow(p);

    p = prevP;
    p*=Rot(radians(mat_a1_time*30.));
    p = DF(p,0.75);
    p -= vec2(0.03);
    p*=Rot( radians(45.));
    float d2 = B(p,vec2(0.02, 0.5));

    p = prevP;
    d2 = max(-d2, abs(length(p)-0.05)-0.01);

    d = min(d,d2);

    p = prevP;
    p*=Rot(-radians(mat_a1_time*20.));
    d2 = B(p,vec2(0.015));
    d = min(d,d2);

    return abs(d)-0.001;
}

float paiselyItem1(vec2 p){
    vec2 prevP = p;
    p*=Rot(radians(mat_a1_time*50.));
    p = DF(p,2.0);
    p -= vec2(0.055);

    p*=Rot( radians(45.));
    float d = abs(SimpleVesicaDistance(p,0.13,0.11))-0.0005;

    p = prevP;
    p*=Rot(radians(mat_a1_time*50.));
    p = DF(p,4.0);
    p -= vec2(0.04);

    p*=Rot( radians(45.));
    float d2 = abs(SimpleVesicaDistance(p,0.12,0.115))-0.0005;

    d = min(d,d2);
    return d;
}

float paiselyItem2(vec2 p){
    vec2 prevP2 = p;

    p*=Rot(-radians(mat_a1_time*40.));

    vec2 prevP = p;

    float d = length(p)-0.1;
    d = max(-(abs(p.x)-0.03),d);

    p*=Rot(radians(90.));
    p.x-=0.02;
    p.y-=0.03;

    float d2 = B(p,vec2(0.06,0.02));
    float a = radians(45.);
    p.x = abs(p.x)-0.06;
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);

    d = max(-d2,d);

    p = prevP;
    p*=Rot(radians(90.));
    p.x+=0.02;
    p.y+=0.03;

    d2 = B(p,vec2(0.06,0.02));
    a = radians(-45.);
    p.x = abs(p.x)-0.06;
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);
    d = max(-d2,d);

    p = prevP;
    a = radians(-10.);
    p.x = abs(p.x)-0.07;
    d = max(dot(p,vec2(cos(a),sin(a))),d);

    d = abs(d)-0.001;

    p = prevP;
    d2 = abs(length(p)-0.12)-0.001;

    d = min(d,d2);

    p.x = abs(p.x)-0.09;
    d2 = abs(B(p,vec2(0.005,0.03)))-0.0005;
    d = min(d,d2);

    p = prevP;

    d2 = abs(B(p,vec2(0.01,0.08)))-0.001;
    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(mat_a1_time*50.));
    p = DF(p,6.0);
    p -= vec2(0.1);

    p*=Rot( radians(45.));
    d2 = abs(B(p,vec2(0.01)))-0.0005;
    d = min(d,d2);

    p = prevP;

    p*=Rot( radians(sin(mat_a1_time*3.)*45.));
    d2 = abs(length(p)-0.16)-0.002;
    d2 = max(-(abs(p.x)-0.15),d2);
    d = min(d,d2);

    p = prevP;
    d2 = waveCircle(p,0.18,10.,0.01,18.,0.001);
    d = min(d,d2);
    return d;
}

float paiselyItem3(vec2 p){
    vec2 prevP = p;
    p*=Rot( -radians(mat_a1_time*25.));
    float d = waveCircle(p,0.15,10.,0.03,18.,0.001);
    p = prevP;
    p*=Rot( radians(mat_a1_time*15.));
    float d2 = waveCircle(p,0.11,8.,0.02,18.,0.002);
    d = min(d,d2);
    p = prevP;
    p*=Rot( -radians(mat_a1_time*20.));
    d2 = waveCircle(p,0.07,7.,0.02,18.,0.001);
    d = min(d,d2);
    p = prevP;
    p*=Rot( radians(mat_a1_time*10.));
    d2 = waveCircle(p,0.03,6.,0.02,18.,0.002);
    d = min(d,d2);
    return d;
}

float paiselyItem4(vec2 p){
    vec2 prevP = p;
    p*=Rot(-radians(mat_a1_time*30.));
    p = DF(p,6.0);
    p -= vec2(0.1);

    p*=Rot( radians(45.));
    float d = B(p,vec2(0.001,0.015));

    p = prevP;
    p*=Rot(-radians(mat_a1_time*30.));
    p*=Rot( radians(7.));
    p = DF(p,6.0);
    p -= vec2(0.095);
    p*=Rot( radians(45.));
    float d2 = B(p,vec2(0.001,0.01));
    d = min(d,d2);

    p = prevP;
    p*=Rot( -radians(45.-sin(mat_a1_time)*150.));
    p.y=abs(p.y)-0.17;
    p.y*=-1.;
    d2 = abs(Tri(p,vec2(0.02),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(mat_a1_time*25.));
    p = DF(p,1.25);
    p -= vec2(0.06);
    p*=Rot( radians(45.));
    d2 = B(p,vec2(0.02, 0.5));

    p = prevP;
    d2 = abs(max(-d2, abs(length(p)-0.09)-0.02))-0.001;
    d = min(d,d2);

    p = prevP;
    p*=Rot( radians(45.+sin(mat_a1_time*0.5)*150.));
    p.y=abs(p.y)-0.05;
    d2 = abs(Tri(p,vec2(0.02),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    d2 = length(p)-0.01;
    d = min(d,d2);

    return d;
}

float paiselyItem5(vec2 p){
    vec2 prevP = p;
    p*=Rot(radians(mat_a1_time*50.));
    p = DF(p,4.0);
    p -= vec2(0.09);

    p*=Rot( radians(45.));
    float d = abs(SimpleVesicaDistance(p,0.115,0.10))-0.001;

    p = prevP;
    p*=Rot(-radians(mat_a1_time*40.));
    p = DF(p,2.0);
    p -= vec2(0.033);

    p*=Rot( radians(45.));
    float d2 = abs(B(p,vec2(0.01)))-0.0005;
    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(12.));
    p*=Rot(radians(mat_a1_time*50.));
    p = DF(p,4.0);
    p -= vec2(0.115+sin(mat_a1_time*3.)*0.005);

    p*=Rot( radians(225.));
    d2 = abs(Tri(p,vec2(0.02),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p*=Rot(-radians(mat_a1_time*30.));
    d2 = abs(length(p)-0.21)-0.006;
    d2 = max(p.x+0.1,d2);
    d = min(d,d2);

    p = prevP;
    d2 = abs(length(p)-0.21)-0.0005;
    d = min(d,d2);

    return d;
}

float paiselyItem6(vec2 p){
    vec2 prevP = p;

    float d = abs(length(p)-0.09)-0.001;
    p*=Rot(radians(mat_a1_time*25.));
    p = DF(p,1.25);
    p -= vec2(0.09);
    p*=Rot( radians(45.));
    float d2 = B(p,vec2(0.02, 0.5));
    d = max(d2,d);

    p = prevP;
    d2 = abs(max(-d2, abs(length(p)-0.09)-0.012))-0.001;

    d = min(d,d2);

    p = prevP;
    p*=Rot(-radians(sin(mat_a1_time)*135.));
    p = DF(p,0.5);
    p -= vec2(0.02);
    p*=Rot( radians(45.));
    d2 = B(p,vec2(0.03, 0.5));

    p = prevP;
    d2 = max(-d2, abs(length(p)-0.05)-0.005);
    d = min(d,d2);

    p = prevP;
    d2 = abs(length(p)-0.12)-0.005;
    p*=Rot(radians(-mat_a1_time*60.+50.));
    float deg = 135.;
    float a = radians(deg);
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);
    a = radians(-deg);
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);
    d = min(d,d2);

    p = prevP;
    d2 = abs(length(p)-0.02)-0.001;
    d = min(d,d2);

    return d;
}

float paiselyItem7(vec2 p){
    p*=Rot(radians(mat_a1_time*50.));

    vec2 prevP = p;
    p = DF(p,0.75);
    p -= vec2(0.04);

    p*=Rot( radians(45.));
    float d = abs(SimpleVesicaDistance(p,0.115,0.10))-0.001;

    p = prevP;
    p*=Rot(radians(60.));
    p = DF(p,0.75);
    p -= vec2(0.03);

    p*=Rot( radians(225.));
    float d2 = abs(Tri(p,vec2(0.03),radians(45.)))-0.002;
    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(60.));
    p = DF(p,0.75);
    p -= vec2(0.07);

    p*=Rot( radians(45.));
    d2 = B(p,vec2(0.07,0.001));

    p = prevP;
    p*=Rot(-radians(mat_a1_time*35.));
    d2 = max(-(abs(p.x)-0.035),d2);
    d2 = max(-(abs(p.y)-0.035),d2);
    d = min(d,d2);

    return d;
}

float paiselyItem8(vec2 p){
    
    vec2 prevP = p;
    p-=vec2(-0.01,0.04);
    float d =  B(p,vec2(0.02,0.05));
    float a = radians(-22.);
    p.x-=0.01;
    d = max(-dot(p,vec2(cos(a),sin(a))),d);
    p = prevP;
    p-=vec2(0.01,-0.04);
    float d2 = B(p,vec2(0.02,0.05));
    a = radians(-22.);
    p.x+=0.01;
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);
    d = min(d,d2);

    return abs(d)-0.0005;
}

float paiselyItem9(vec2 p){
    vec2 prevP = p;

    float d = 10.;
    for(float i = 0.; i<2.; i++){
        p*= 1.0+i*0.03;
        p*=Rot(radians(i*30.0+mat_a1_time*50.));
        p = abs(p);
        p-=0.025+i*0.01;
        float d2 = arrow(p);
        d = min(d,d2);
    }

    return abs(d)-0.001;
}

float paisely(vec2 p){
    vec2 prevP = p;
    float d = paiselyBase(p);
    float d2 = 10.;

    p*=0.95;
    d2 = paiselyItem0(p-vec2(0.04,-0.18));
    d = min(d,d2);

    p*=1.6;
    d2 = paiselyItem4(p-vec2(-0.045,0.14));
    d = min(d,d2);

    p = prevP;
    p-=vec2(-0.145,-0.075);
    p*=2.3;
    d2 = paiselyItem6(p);
    d = min(d,d2);

    p = prevP;
    p*=0.95;
    d2 = paiselyOutlineItem1(p-vec2(0.105,0.0),-160.);
    d = min(d,d2);

    p = prevP;
    p-=vec2(0.06,0.25);
    p*=0.9;
    d2 = paiselyOutlineItem1(p,-170.);
    d = min(d,d2);

    return d;
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 p = uv;
    vec2 prevP = p;
    vec3 col = vec3(0.);

    p*=0.9;
    p.x = abs(p.x)-0.35;
    p.x*=-1.0;
    p.y-=-0.04;
    p*=Rot(radians(-20.));
    float d = paisely(p);

    p = prevP;
    p-= vec2(0.0,0.23);
    float d2 =  paiselyItem2(p);
    d = min(d,d2);

    p = prevP;
    p-= vec2(0.0,-0.42);
    p*=1.8;
    d2 =  paiselyItem7(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-= vec2(0.72,0.32);
    p*=1.2;
    d2 =  paiselyItem3(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-= vec2(0.735,-0.335);
    p*=1.1;
    d2 =  paiselyItem1(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-= vec2(0.78,-0.02);
    p*=1.3;
    d2 =  paiselyItem9(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.035,-0.05);
    p*=Rot(radians(10.));
    d2 =  paiselyItem8(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.53,-0.43);
    p*=Rot(radians(45.));
    d2 =  paiselyItem8(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.53,0.43);
    p*=Rot(radians(60.));
    d2 =  paiselyItem8(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.25,0.38);
    p*=Rot(radians(10.));
    d2 =  paiselyItem8(p);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.25,0.25);
    d2 =abs( length(p)-0.02)-0.001;
    d = min(d,d2);
    p-=vec2(-0.04,-0.12);
    d2 = abs(length(p)-0.015)-0.0005;
    d = min(d,d2);
    p-=vec2(-0.09,-0.1);
    d2 = length(p)-0.01;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.17,0.4);
    p.y*=-1.;
    d2 = abs(Tri(p,vec2(0.04),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.12,-0.44);
    d2 = abs(Tri(p,vec2(0.03),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.y+=0.02;
    p = abs(p);
    p-=vec2(0.83,0.15);
    d2 = abs( length(p)-0.03)-0.001;
    d = min(d,d2);

    p-=vec2(-0.12,-0.03);
    d2 = length(p)-0.015;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.53,0.36);
    d2 = abs( length(p)-0.015)-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    p-=vec2(0.6,-0.46);
    d2 = abs( length(p)-0.015)-0.001;
    d = min(d,d2);

    p = prevP;
    p-=vec2(0.0,-0.3);
    d2 = abs( length(p)-0.015)-0.001;
    d = min(d,d2);

    col = mix(col,vec3(1.),S(d,0.0));
    
    out_color = vec4(sqrt(col),1.0);

    
    if (mat_back_mode == 1) {
        
        if (mat_luma(out_color.rgb) < mat_back_thresh) {
            out_color = mat_back_color;
        } else {
            out_color = mat_front_color;
        }
    } else {
        
        out_color = mix(mat_back_color, mat_front_color, mat_luma(out_color.rgb) * mat_back_sensitivity + mat_back_thresh);
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
