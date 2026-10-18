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
uniform vec4 uMMParam008; // native input: mat_center_fill
float mat_center_fill = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_border
float mat_border = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_arrow_split
float mat_arrow_split = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_arrow_thick
float mat_arrow_thick = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_detail
float mat_detail = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_a1_speed
float mat_a1_speed = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_a1_offset
float mat_a1_offset = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_a1_strob
float mat_a1_strob = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam019.x));
uniform vec4 uMMParam020; // native input: mat_a2_speed
float mat_a2_speed = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_a2_offset
float mat_a2_offset = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_a2_strob
float mat_a2_strob = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_a2_restart
int mat_a2_restart = int(round(uMMParam026.x));
uniform vec4 uMMParam027; // native input: mat_front_color
vec4 mat_front_color = uMMParam027;
uniform vec4 uMMParam028; // native input: mat_back_color
vec4 mat_back_color = uMMParam028;
uniform vec4 uMMParam029; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam029.x));
uniform vec4 uMMParam030; // native input: mat_back_thresh
float mat_back_thresh = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_back_sensitivity
float mat_back_sensitivity = uMMParam031.x;
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

float mat_a1_time = mat_a1_time_source - mat_a1_offset * 8. * mat_a1_offset_scale;
float mat_a2_time = mat_a2_time_source - mat_a2_offset * 8. * mat_a2_offset_scale;

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
#define antialiasing(n) n/(mat_detail * 2000.)
#define S(d,b) smoothstep(antialiasing(1.0),b,d)
#define B(p,s) max(abs(p).x-s.x,abs(p).y-s.y)
#define Tri(p,s,a) max(-dot(p,vec2(cos(-a),sin(-a))),max(dot(p,vec2(cos(a),sin(a))),max(abs(p).x-s.x,abs(p).y-s.y)))
#define DF(a,b) length(a) * cos( mod( atan(a.y,a.x)+6.28/(b*8.0), 6.28/((b*8.0)*0.5))+(b-1.)*6.28/(b*8.0) + vec2(0,11) )
#define Skew(a,b) mat2(1.0,tan(a),tan(b),1.0)
#define SkewX(a) mat2(1.0,tan(a),0.0,1.0)
#define SkewY(a) mat2(1.0,0.0,tan(a),1.0)
#define SymdirX(p) mod(floor(p).x,2.)*2.-1.
#define SymdirY(p) mod(floor(p).y,2.)*2.-1.

float Hash21(vec2 p) {
    p = fract(p*vec2(234.56,789.34));
    p+=dot(p,p+34.56);
    return fract(p.x+p.y);
}

float thunderIcon(vec2 p){
    float dir = SymdirY(p);
    p.x = abs(p.x)-0.17;
    vec2 prevP2 = p;
    p.y+=mat_a1_time*0.15*dir;
    p.y = mod(p.y,0.1)-0.05;
    vec2 prevP = p;

    vec2 size = vec2(0.01,0.04);
    float a = radians(-25.);

    p.x+=0.008;
    p.y-=0.035;
    float d = B(p,size);
    p.x-=0.01;
    d = max(-dot(p,vec2(cos(a),sin(a))),d);

    p = prevP;
    p.x-=0.008;
    p.y+=0.035;
    a = radians(-25.);
    float d2 = B(p,size);
    p.x+=0.01;
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);

    d = min(d,d2);

    return abs(d)-0.0005;
}

float arrow(vec2 p){
    float dir = SymdirY(p);
    p.x = abs(p.x)-0.05*mat_arrow_split;
    vec2 prevP = p;

    p.y+=(0.1*mat_a2_time)*dir;

    p.y=mod(p.y,0.07)-0.035;
    p.y+=0.025;
    if(dir == 1.){
        p.y-=0.05;
    }
    p.y*=dir*-1.;
    float a = radians(60.);
    p.x = abs(p.x)-0.1;
    float d = dot(p,vec2(cos(a),sin(a)));
    p.y+=0.03;
    float d2 = dot(p,vec2(cos(a),sin(a)));
    d = max(-d2,d);
    p = prevP;

    d = max(abs(p.x)-0.04,d);

    return abs(d)-0.0005 * pow(mat_arrow_thick,2.);
}

float arrowItem (vec2 p){
    vec2 prevP = p;
    float dist = 0.16;
    p.x = abs(p.x)-dist;
    p*=SkewX(radians(45.));
    float d = B(p,vec2(0.04,0.01));

    p = prevP;
    p.x = abs(p.x)-dist;
    p-=vec2(-0.04,0.07);
    p*=SkewY(radians(45.));
    float d2 = B(p,vec2(0.01,0.07));
    d = abs(min(d,d2))-0.0005;

    p =  prevP;
    p.y-=mat_a1_time*0.23;
    p.y = mod(p.y,0.3)-0.15;

    p.x = abs(p.x)-dist;
    p-=vec2(-0.04,0.0);
    p*=SkewY(radians(45.));
    d2 = B(p,vec2(0.01,0.1));
    p = prevP;
    d2 = max(-p.y+0.16,d2);

    p.x = abs(p.x);
    float a = radians(45.);

    p.y-=0.3;
    d2 = max(-dot(p,vec2(cos(a),sin(a))),d2);

    d = abs(min(d,d2))-0.0005;

    return d;
}

float arrows(vec2 p){
    vec2 prevP = p;
    p*=Rot(radians(45.));
    float d = arrow(p);

    p = prevP;
    p*=Rot(radians(-45.));
    float d2 = arrow(p);

    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(45.));

    d2 = B(p,vec2(0.32));
    d = max(-d2,d);

    p = prevP;

    p*=Rot(radians(45.));
    p.y=abs(p.y)-0.34;

    d2 = arrowItem(p);
    d = min(d,d2);

    p = prevP;

    p*=Rot(radians(-45.));
    p.y=abs(p.y)-0.34;

    d2 = arrowItem(p);
    d = min(d,d2);


    p = prevP;
    p*=Rot(radians(-45.));
    d2 = thunderIcon(p);

    p = prevP;
    p*=Rot(radians(45.));
    float d3 = thunderIcon(p);
    d2 = min(d2,d3);

    p = prevP;
    p*=Rot(radians(45.));

    float mask = B(p,vec2(0.38));
    d2 = max(-mask,d2);


    d = min(d,d2);

    return d;
}

float arrow2(vec2 p){
    vec2 prevP = p;

    float dir = SymdirY(p);
    p.y-=0.03;
    p.y+=(0.1*mat_a1_time)*dir;
    p.y=mod(p.y,0.08)-0.04;
    p.x = abs(p.x)-0.04;
    p*=SkewY(radians(45.*dir*-1.));
    float d = abs(B(p,vec2(0.025,0.015)))-0.0005;

    return d;
}

float arrowItem2 (vec2 p, float dist){
    vec2 prevP = p;
    p.x = abs(p.x)-dist;
    float d = B(p,vec2(0.0119,0.057));

    p = prevP;
    p.x = abs(p.x)-dist;
    p-=vec2(0.025,0.075);
    p*=Rot(radians(-45.));
    float d2 = B(p,vec2(0.04,0.0125));
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-dist;
    p-=vec2(0.0487,0.225);
    d2 = B(p,vec2(0.0127,0.13));
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x);
    float a = radians(45.);

    p.y-=0.49;
    d = max(dot(p,vec2(cos(a),sin(a))),d);


    return abs(d)-0.0005;
}


float arrows2(vec2 p){
    vec2 prevP = p;
    float d = arrow2(p);

    p*=Rot(radians(90.));
    float d2 = arrow2(p);

    d = min(d,d2);

    p = prevP;
    p*=Rot(radians(45.));

    d2 = B(p,vec2(0.32));
    d = max(-d2,d);

    p = prevP;

    p.x = abs(p.x)-0.47;
    p*=Rot(radians(90.));
    d2 = arrowItem2(p,0.095);
    d = min(d,d2);

    p = prevP;

    p.y = abs(p.y)-0.47;
    d2 = arrowItem2(p,0.095);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.6;
    p.x -= 0.05;
    p.y = abs(p.y)-0.1;
    p.x = mod(p.x,0.08)-0.04;
    d2 = abs(length(p)-0.01)-0.001;
    p = prevP;
    d2 = max(-(abs(p.x)-0.58),d2);
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.46;
    p.y = abs(p.y)-0.17;
    d2 = abs(Tri(p,vec2(0.035),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.17;
    p.y = abs(p.y)-0.46;
    p*=Rot(radians(90.));
    d2 = abs(Tri(p,vec2(0.035),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.505;
    p.y = abs(p.y)-0.18;
    p*=Rot(radians(45.));
    d2 = abs(B(p,vec2(0.03,0.01)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.18;
    p.y = abs(p.y)-0.505;
    p*=Rot(radians(45.));
    d2 = abs(B(p,vec2(0.03,0.01)))-0.001;
    d = min(d,d2);

    return d;
}

float shapeBase(vec2 p, float s, int mode){
    vec2 prevP = p;
    p*=10.;

    if(mode ==1){
        p = abs(p);
        p-=mat_a1_time*0.5;
    } else {
        p*=2.;
        p.x-=0.2;
        p.y+=mat_a1_time*1.;
    }

    vec2 id = floor(p);
    vec2 gv = fract(p)-0.5;

    float n = Hash21(id);

    float w = 0.1;
    if(n<0.5 || n>=0.8){
        float dir = (n>=0.8)?1.0:-1.0;
        gv*=Rot(radians(dir*45.0));
        if(mode ==1){
            gv.x = abs(gv.x);
        }
        gv.x-=0.355;
    } else {
        w = 0.135;
    }

    w*=s;
    float d = B(gv,vec2(w,1.));
    return d;
}

float centerItem(vec2 p){
    vec2 prevP = p;

    float d = shapeBase(p,1. * mat_center_fill,1);

    p = prevP;
    p*=Rot(radians(45.));
    float d2 = B(p,vec2(0.2));
    d = max(d2,d);

    d2 = abs(B(p,vec2(0.22)))-0.005;
    p = prevP;
    d2 = max(abs(p.x)-0.1,d2);
    d = min(d,d2);

    p*=Rot(radians(45.));
    d2 = abs(B(p,vec2(0.22)))-0.005;
    p = prevP;
    d2 = max(abs(p.y)-0.1,d2);
    d = min(d,d2);

    p*=Rot(radians(45.));
    d2 = abs(B(p,vec2(0.24)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.2;
    p.y-=0.2;
    p*=Rot(radians(-225.));
    d2 = shapeBase(p,1. * mat_border,0);

    d2 = max(abs(p.x)-0.02,d2);
    d2 = max(abs(p.y)-0.3,d2);
    p = prevP;
    d2 = max(-p.y,d2);

    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.2;
    p.y+=0.2;
    p*=Rot(radians(225.));
    d2 = shapeBase(p,1. * mat_border,0);

    d2 = max(abs(p.x)-0.02,d2);
    d2 = max(abs(p.y)-0.3,d2);
    p = prevP;
    d2 = max(p.y,d2);
    d = min(d,d2);


    return d;
}

float circleItem(vec2 p){
    vec2 prevP = p;
    p*=Rot(radians(mat_a1_time*-30.));
    p = DF(p,2.);
    p -= vec2(0.06);
    p*=Rot( radians(-45.+sin(mat_a1_time*2.)*-10.));

    p.x*=2.;
    float d = abs(Tri(p,vec2(0.025),radians(45.)))-0.002;
    p = prevP;
    float d2 = abs(length(p)-0.05)-0.002;
    d = min(d,d2);
    d2 = length(p)-0.02;
    d = min(d,d2);
    return d;
}

float circleItems(vec2 p){
    vec2 prevP = p;

    p.x = abs(p.x)-0.77;
    p.y = abs(p.y)-0.32;
    float d = circleItem(p);

    p = prevP;
    p.x = abs(p.x)-0.61;
    p.y = abs(p.y)-0.21;
    p*=Rot(radians(45.));
    float d2 = B(p,vec2(0.07,0.04));
    float a = radians(-45.);
    p.y+=0.03;
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);

    d = min(d,abs(abs(d2)-0.01)-0.001);

    p = prevP;
    p.x = abs(p.x)-0.815;
    p.y = abs(p.y)-0.19;
    p*=Rot(radians(-90.));
    d2 = abs(Tri(p,vec2(0.04),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.63;
    p.y = abs(p.y)-0.32;
    d2 = abs(length(p)-0.015)-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.84;
    p.y = abs(p.y)-0.46;
    d2 = abs(length(p)-0.025)-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.77;
    p.y = abs(p.y)-0.46;
    d2 = abs(length(p)-0.013)-0.001;
    d = min(d,d2);

    p = prevP;
    p.x = abs(p.x)-0.7585;
    p.y = abs(p.y)-0.186;
    d2 = abs(B(p,vec2(0.04,0.006)))-0.001;
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
    float d = centerItem(p);
    col = mix(col,vec3(1.),S(d,0.0));

    d = arrows2(p);

    float d2 = arrows(p);
    d = min(d,d2);
    d2 = circleItems(p);
    d = min(d,d2);

    col = mix(col,vec3(0.5),S(d,0.0));


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
