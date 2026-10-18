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
uniform vec4 uMMParam008; // native input: mat_ring1
float mat_ring1 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_ring2
float mat_ring2 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_ring3
float mat_ring3 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_ring4
float mat_ring4 = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_radius1
float mat_radius1 = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_radius2
float mat_radius2 = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_radius3
float mat_radius3 = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_radius4
float mat_radius4 = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_radius5
float mat_radius5 = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_radius6
float mat_radius6 = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_radius7
float mat_radius7 = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_radius8
float mat_radius8 = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_detail
float mat_detail = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_a1_speed
float mat_a1_speed = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_a1_offset
float mat_a1_offset = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_a1_strob
float mat_a1_strob = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam027.x));
uniform vec4 uMMParam028; // native input: mat_a2_speed
float mat_a2_speed = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: mat_a2_offset
float mat_a2_offset = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_a2_strob
float mat_a2_strob = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_a2_restart
int mat_a2_restart = int(round(uMMParam034.x));
uniform vec4 uMMParam035; // native input: mat_a3_speed
float mat_a3_speed = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_a3_bpm_sync
bool mat_a3_bpm_sync = uMMParam036.x > 0.5;
uniform vec4 uMMParam037; // native input: mat_a3_reverse
bool mat_a3_reverse = uMMParam037.x > 0.5;
uniform vec4 uMMParam038; // native input: mat_a3_offset
float mat_a3_offset = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_a3_offset_scale
float mat_a3_offset_scale = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_a3_strob
float mat_a3_strob = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_a3_restart
int mat_a3_restart = int(round(uMMParam041.x));
uniform vec4 uMMParam042; // native input: mat_front_color
vec4 mat_front_color = uMMParam042;
uniform vec4 uMMParam043; // native input: mat_back_color
vec4 mat_back_color = uMMParam043;
uniform vec4 uMMParam044; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam044.x));
uniform vec4 uMMParam045; // native input: mat_back_thresh
float mat_back_thresh = uMMParam045.x;
uniform vec4 uMMParam046; // native input: mat_back_sensitivity
float mat_back_sensitivity = uMMParam046.x;
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);
float mat_a3_time_source = uTDTime * (mat_a3_speed);

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
float mat_a3_time = mat_a3_time_source - mat_a3_offset * 8. * mat_a3_offset_scale;

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
#define DF(a,b) length(a) * cos( mod( atan(a.y,a.x)+6.28/(b*8.0), 6.28/((b*8.0)*0.5))+(b-1.)*6.28/(b*8.0) + vec2(0,11) )
#define B(p,s) max(abs(p).x-s.x,abs(p).y-s.y)
#define Tri(p,s,a) max(-dot(p,vec2(cos(-a),sin(-a))),max(dot(p,vec2(cos(a),sin(a))),max(abs(p).x-s.x,abs(p).y-s.y)))

float SimpleVesicaDistance(vec2 p, float r, float d) {
    p.x = abs(p.x);
    p.x+=d;
    return (length(p)-r) / pow(mat_ring1,2.);
}

float triOutside(vec2 p){
    vec2 prevP = p;

    p.x*=1.5;

    float d = abs(Tri(p,vec2(0.175),radians(45.)))-0.001;

    p*=1.5;
    p += vec2(0.0,0.05);
    float d2 = abs(Tri(p,vec2(0.175),radians(45.)))-0.001;
    d = min(d,d2);

    p*=1.5;
    p += vec2(0.0,0.06);
    d2 = abs(Tri(p,vec2(0.175),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    p.y+=0.11;
    d2 = abs(length(p)-0.015)-0.001;
    d = min(d,d2);

    return d / pow(mat_ring3,3.);
}

float triAnimation(vec2 p){
    vec2 prevP = p;

    p.y-=mat_a3_time*0.1+0.09;
    p.y = mod(p.y,0.16)-0.08;
    p.y -=0.01;
    p.x*=1.5;
    float d = Tri(p-vec2(0.0,0.032),vec2(0.015),radians(45.));
    float d2 = abs(Tri(p,vec2(0.02),radians(45.)))-0.001;
    d = min(d,d2);
    d2 = abs(Tri(p-vec2(0.0,-0.04),vec2(0.03),radians(45.)))-0.001;
    d = min(d,d2);

    p = prevP;
    d = max(abs(p.y)-0.06,d);

    return d;
}

float waveCircle(vec2 p, float s, float numW, float amp, float deg, float thickness){
    float r = s+amp*cos(atan(p.y,p.x)*numW);
    float d = abs(length(p)-r)-thickness;
    p*=Rot(radians(deg));
    r = s+amp*cos(atan(p.y,p.x)*numW);
    float d2 = abs(length(p)-r)-thickness;
    d = min(d,d2);
    return d / pow(mat_ring4, 3.);
}

vec3 centerGraphic(vec2 p, vec3 col){
    p*=1.2;
    vec2 prevP = p;
    float thickness = 0.003 * pow(mat_ring2,1.5);
    float deg = -40.;
    float speed0 = -mat_a1_time*30.;
    float speed1 = mat_a2_time*20.; 
    float speed2 = -mat_a1_time*10.; 
    float speed3 = mat_a2_time*15.; 
    float speed4 = mat_a2_time*25.;

    p*=Rot(radians(speed0));
    p = DF(p,3.0);
    p -= vec2(0.205);

    p*=Rot( radians(deg));
    float a = atan(p.x,p.y);
    float d = abs(length(p)-0.039)-thickness;
    d = max(-p.x,d);

    col = mix(col,vec3(1.)*a,S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed0));

    float deg2 = -44.5;
    p*=Rot( radians(deg2));
    p = DF(p,3.0);
    p -= vec2(0.2);

    p*=-1.;
    p*=Rot( radians(deg));
    a = atan(p.x,p.y);
    d = abs(length(p)-0.04)-thickness;
    d = max(-p.x,d);
    col = mix(col,vec3(1.)*a,S(d,0.0));

    p = prevP;

    d = abs(length(p)-0.29)-thickness;
    col = mix(col,vec3(1.),S(d,0.0));

    p*=Rot(radians(speed1));
    p+=sin(p*25.)*0.025;
    d = abs(length(p)-0.37)-thickness*0.2;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed0));

    p = DF(p,3.0);
    p -= vec2(0.217);
    d = abs(length(p)-0.007)-0.0005;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed0));

    p*=Rot( radians(deg2));
    p = DF(p,3.0);
    p -= vec2(0.19);
    d = abs(length(p)-0.007)-0.0005;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed0));

    p*=Rot( radians(deg2));
    p = DF(p,3.0);
    p -= vec2(0.225) * mat_radius8;
    d = abs(length(p)-0.015)-0.002;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed0));

    p = DF(p,3.0);
    p -= vec2(0.18) * mat_radius8;
    d = abs(length(p)-0.015)-0.0005;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed2));
    p = DF(p,6.0);
    p -= vec2(0.161);
    d = max(-(length(p)-0.012),abs(length(prevP)-0.21)-0.02);
    p += vec2(0.024);
    d = max(-(length(p)-0.012),d);

    col = mix(col,vec3(1.),S(abs(d)-0.002,0.0));

    p = prevP;
    p*=Rot(radians(speed3));
    p = DF(p,6.0);
    p -= vec2(0.11) * mat_radius1;
    p*=Rot( radians(45.));
    p.y*=2.0;
    d = abs(SimpleVesicaDistance(p,0.12,0.11))-0.0005;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed4));
    p = DF(p,3.0);
    p -= vec2(0.075) * mat_radius2;
    p*=Rot( radians(45.));
    d = abs(B(p,vec2(0.02,0.01)))-0.002;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(speed2));
    p*=Rot( radians(90.));
    p = DF(p,1.5);
    p -= vec2(0.04) * mat_radius3;
    d = abs(length(p)-0.025)-0.0005;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot( radians(-60.));
    p = DF(p,1.5);
    p -= vec2(0.032) * mat_radius4;
    p*=Rot( radians(45.));
    d = B(p,vec2(0.04,0.003));
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot( radians(45.));
    d = abs(B(p,vec2(0.015)))-0.001;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(-speed2*0.5));
    p = DF(p,24.0);
    p -= vec2(0.29) * mat_radius5;
    d = abs(B(p,vec2(0.005, 0.2)))-0.0005;
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(-speed3));
    p = DF(p,2.);
    p -= vec2(0.4) * mat_radius6;
    p*=Rot( radians(45.));

    d = triOutside(p);

    d = max(-(length(prevP)-0.44),d);
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(-speed3));
    p = DF(p,2.);
    p -= vec2(0.32);
    p*=Rot( radians(45.));
    d = B(p,vec2(0.12, 0.2));

    p = prevP;
    d = max(-d, abs(length(p)-0.47)-0.01);
    col = mix(col,vec3(1.),S(abs(d)-0.001,0.0));

    p = prevP;
    p*=Rot(radians(-speed3));
    p = DF(p,2.);
    p -= vec2(0.32);
    p*=Rot( radians(45.));
    d = B(p,vec2(0.08, 0.2));

    p = prevP;
    d = max(-d, abs(length(p)-0.53)-0.01);
    col = mix(col,vec3(1.),S(abs(d)-0.001,0.0));

    p = prevP;
    p = DF(p,1.999);
    p -= vec2(0.475);
    p*=Rot( radians(45.));
    d = triAnimation(p);
    col = mix(col,vec3(1.),S(d,0.0));

    p = prevP;
    p*=Rot(radians(-speed3));
    d = waveCircle(p,0.485,10.,0.052,18.,0.001);

    p = prevP;
    p*=Rot(radians(-speed2));
    float d2 = waveCircle(p,0.585,10.,0.012,18.,0.001);
    d = min(d,d2);
    col = mix(col,vec3(1.),S(d,0.0));

    return col;
}

float graphicItem0(vec2 p){
    vec2 prevP2 = p;
    p.x+=mat_a3_time*0.2;
    p.x+=0.2;
    p.x = mod(p.x,0.2)-0.1;
    p.x-=0.02;
    p*=1.5;
    p.x*=-1.;
    vec2 prevP = p;

    float d = B(p,vec2(0.1,0.015));
    float a = radians(45.0);
    p.x = abs(p.x)-0.065;
    d = max(dot(p,vec2(cos(a),sin(a))),d);
    p = prevP;
    float d2 = B(p-vec2(0.09,-0.008),vec2(0.08,0.007));
    d = min(d,d2);
    p.x-=0.145;
    a = radians(55.0);
    d = max(dot(p,vec2(cos(a),sin(a))),d);

    p = prevP;

    p-=vec2(0.0,-0.01);
    d2 = B(p,vec2(0.06,0.01));
    a = radians(45.0);
    p.x = abs(p.x)-0.035;
    d2 = max(dot(p,vec2(cos(a),sin(a))),d2);
    d = max(-d2,d);

    p = prevP2;
    d = max(abs(p.x)-0.25,d);

    return d;
}

float graphicItem1(vec2 p){
    vec2 prevP = p;
    p.x-=mat_a3_time*0.1;
    p.y-=0.03;
    p.x = mod(p.x,0.06)-0.03;
    float d = abs(Tri(p,vec2(0.02),radians(45.)))-0.001;
    p = prevP;

    p.x+=mat_a3_time*0.06;
    p.x+=0.03;
    p.y+=0.03;
    p.x = mod(p.x,0.06)-0.03;
    p.y*=-1.0;

    float d2 = Tri(p,vec2(0.02),radians(45.));
    d = min(d,d2);

    p = prevP;
    d = max(abs(p.x)-0.2,d);

    return d;
}

float graphicItem2(vec2 p){
    vec2 prevP = p;

    p.x+=mat_a3_time*0.08;
    p.x = mod(p.x,0.12)-0.06;
    p.x+=0.05;
    p.x*=-1.;
    p*=Rot(radians(90.));
    p.x*=3.;
    p.y*=0.3;
    float d = Tri(p,vec2(0.03),radians(45.));

    p = prevP;
    d = max(abs(p.x)-0.2,d);

    return d;
}

float graphicItem3(vec2 p){
    vec2 prevP = p;

    p.x-=mat_a3_time*0.12;
    p.x = mod(p.x,0.3)-0.15;

    float d = length(p)-0.01;
    float d2 = length(p-vec2(-0.06,0.0))-0.013;
    d = min(d,d2);
    d2 = length(p-vec2(0.06,0.0))-0.007;
    d = min(d,d2);
    d2 = length(p-vec2(-0.12,0.0))-0.014;
    d = min(d,d2);
    d2 = length(p-vec2(0.12,0.0))-0.005;
    d = min(d,d2);

    p = prevP;
    d = max(abs(p.x)-0.25,d);

    return d;
}

float graphicItem4(vec2 p){
    vec2 prevP = p;
    float d = abs(length(p)-0.04)-0.001;
    p*=Rot(radians(mat_a3_time*50.));
    float d2 = abs(length(p)-0.026)-0.006;
    d2 = max(-(abs(p.x)-0.01),d2);
    d = min(d,abs(d2)-0.001);

    return d;
}

float graphicItem5(vec2 p){
    vec2 prevP = p;
    p.x*=0.8;
    float d = abs(Tri(p,vec2(0.06),radians(45.)))-0.001;
    float d2 = abs(Tri(p,vec2(0.06),radians(45.)))-0.005;
    p.y+=0.05;
    p*=Rot(radians(45.+mat_a3_time*-70.));
    d2 = max(-(abs(p.y)-0.02),d2);
    d = min(d,d2);

    return d;
}

float graphicItem6(vec2 p){
    vec2 prevP = p;
    float d = abs(Tri(p,vec2(0.025),radians(45.)))-0.001;
    float d2 = Tri(p-vec2(0.055,-0.01),vec2(0.015),radians(45.));
    d = min(d,d2);
    return d;
}

float graphicItem7(vec2 p){
    vec2 prevP = p;
    p.x-=mat_a3_time*0.12;
    p.x = mod(p.x,0.07)-0.035;
    p.x-=0.0325;

    p*=vec2(0.9,1.5);
    p*=Rot(radians(90.));
    float d = Tri(p,vec2(0.05),radians(45.));
    d = max(-Tri(p-vec2(0.,-0.03),vec2(0.05),radians(45.)),d);
    d = abs(d)-0.001;
    p = prevP;
    d = max(abs(p.x)-0.15,d);
    return d;
}

float graphicItems(vec2 p) {

    vec2 prevP = p;

    p-=vec2(-0.71,-0.33);
    p*=Rot(radians(-25.));
    float d = graphicItem0(p);

    p = prevP;

    p-=vec2(-0.7,-0.16);
    p*=Rot(radians(-15.));
    float d2 = graphicItem1(p);

    d = min(d,d2);

    p = prevP;

    p-=vec2(-0.585,-0.44);
    p*=Rot(radians(-35.));
    d2 = graphicItem2(p);

    d = min(d,d2);

    p = prevP;

    p-=vec2(-0.73,-0.26);
    p*=Rot(radians(-20.));
    d2 = abs(graphicItem3(p))-0.001;

    d = min(d,d2);

    p = prevP;

    p-=vec2(-0.67,-0.4);
    p*=Rot(radians(-30.));
    d2 = graphicItem3(p);

    d = min(d,d2);

    p = prevP;

    p-=vec2(-0.78,-0.09);
    p*=Rot(radians(-10.));
    d2 = graphicItem3(p);

    d = min(d,d2);

    p = prevP;
    d2 = graphicItem4(p-vec2(-0.34,-0.45));
    d = min(d,d2);

    d2 = graphicItem5(p-vec2(-0.48,-0.42));
    d = min(d,d2);

    d2 = graphicItem6(p-vec2(-0.265,-0.46));
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

    col = centerGraphic(p,col);

    p = abs(p);
    p*=Rot(radians(180.));
    float d = graphicItems(p);
    col = mix(col,vec3(0.6),S(d,0.));

    p = prevP;
    p.x = abs(p.x)-0.77;
    d = graphicItem7(p);
    col = mix(col,vec3(0.6),S(d,0.));
    out_color = vec4(col,1.0);


    
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
