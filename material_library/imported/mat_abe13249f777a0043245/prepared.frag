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
uniform vec4 uMMParam008; // native input: mat_squares
int mat_squares = int(round(uMMParam008.x));
uniform vec4 uMMParam009; // native input: mat_scale1
float mat_scale1 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_scale2
float mat_scale2 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_scale3
float mat_scale3 = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_a1_speed
float mat_a1_speed = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam013.x > 0.5;
uniform vec4 uMMParam014; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_a1_offset
float mat_a1_offset = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_a1_strob
float mat_a1_strob = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam018.x));
uniform vec4 uMMParam019; // native input: mat_blocks_level
float mat_blocks_level = uMMParam019.x;
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
uniform vec4 uMMParam027; // native input: mat_noise_level
float mat_noise_level = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_a3_speed
float mat_a3_speed = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_a3_bpm_sync
bool mat_a3_bpm_sync = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_a3_reverse
bool mat_a3_reverse = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: mat_a3_offset
float mat_a3_offset = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_a3_offset_scale
float mat_a3_offset_scale = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_a3_strob
float mat_a3_strob = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_a3_restart
int mat_a3_restart = int(round(uMMParam034.x));
uniform vec4 uMMParam035; // native input: mat_a4_speed
float mat_a4_speed = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_a4_bpm_sync
bool mat_a4_bpm_sync = uMMParam036.x > 0.5;
uniform vec4 uMMParam037; // native input: mat_a4_reverse
bool mat_a4_reverse = uMMParam037.x > 0.5;
uniform vec4 uMMParam038; // native input: mat_a4_offset
float mat_a4_offset = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_a4_offset_scale
float mat_a4_offset_scale = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_a4_strob
float mat_a4_strob = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_a4_restart
int mat_a4_restart = int(round(uMMParam041.x));
uniform vec4 uMMParam042; // native input: mat_brightness
float mat_brightness = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_contrast
float mat_contrast = uMMParam043.x;
uniform vec4 uMMParam044; // native input: mat_saturation
float mat_saturation = uMMParam044.x;
uniform vec4 uMMParam045; // native input: mat_hue_shift
float mat_hue_shift = uMMParam045.x;
uniform vec4 uMMParam046; // native input: mat_invert
bool mat_invert = uMMParam046.x > 0.5;
uniform vec4 uMMParam047; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam047.x > 0.5;
uniform vec4 uMMParam048; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam048.x;
uniform vec4 uMMParam049; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam049.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);
float mat_a3_time_source = uTDTime * (mat_a3_speed);
float mat_a4_time_source = uTDTime * (mat_a4_speed);

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
float mat_a4_time = mat_a4_time_source - mat_a4_offset * 8. * mat_a4_offset_scale;

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
    uv *= mat_scale * 2.25;

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


float mod289(float x){return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec4 mod289(vec4 x){return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec4 perm(vec4 x){return mod289(((x * 34.0) + 1.0) * x);}

float mat_noise(vec3 p){
    vec3 a = floor(p);
    vec3 d = p - a;
    d = d * d * (3.0 - 2.0 * d);

    vec4 b = a.xxyy + vec4(0.0, 1.0, 0.0, 1.0);
    vec4 k1 = perm(b.xyxy);
    vec4 k2 = perm(k1.xyxy + b.zzww);

    vec4 c = k2 + a.zzzz;
    vec4 k3 = perm(c);
    vec4 k4 = perm(c + 1.0);

    vec4 o1 = fract(k3 * (1.0 / 41.0));
    vec4 o2 = fract(k4 * (1.0 / 41.0));

    vec4 o3 = o2 * d.z + o1 * (1.0 - d.z);
    vec2 o4 = o3.yw * d.x + o3.xz * (1.0 - d.x);

    return (o4.y * d.y + o4.x * (1.0 - d.y)) * mat_noise_level;
}

vec2 rotate(vec2 v, float a) {
    float s = sin(a);
    float c = cos(a);
    mat2 m = mat2(c, -s, s, c);
    return m * v;
}

float mat_saturate (float x){
    return min(1.0, max(0.0,x));
}

vec3 mat_saturate (vec3 x){
    return min(vec3(1.,1.,1.), max(vec3(0.,0.,0.),x));
}






vec3 bump3y (vec3 x, vec3 yoffset)
{
    vec3 y = vec3(1.,1.,1.) - x * x;
    y = mat_saturate(y-yoffset);
    return y;
}




vec3 spectral_zucconi6 (float w)
{
    
    
    float x = mat_saturate((w - 400.0)/ 300.0);

    const vec3 c1 = vec3(3.54585104, 2.93225262, 2.41593945);
    const vec3 x1 = vec3(0.69549072, 0.49228336, 0.27699880);
    const vec3 y1 = vec3(0.02312639, 0.15225084, 0.52607955);

    const vec3 c2 = vec3(3.90307140, 3.21182957, 3.96587128);
    const vec3 x2 = vec3(0.11748627, 0.86755042, 0.66077860);
    const vec3 y2 = vec3(0.84897130, 0.88445281, 0.73949448);

    return
        bump3y(c1 * (x - x1), y1) +
        bump3y(c2 * (x - x2), y2) ;
}


vec3 spectral_jet(float w)
{
    
    
    float x = mat_saturate((w - 400.0)/ 300.0);
    vec3 c;

    if (x < 0.25)
        c = vec3(0.0, 4.0 * x, 1.0);
    else if (x < 0.5)
        c = vec3(0.0, 1.0, 1.0 + 4.0 * (0.25 - x));
    else if (x < 0.75)
        c = vec3(4.0 * (x - 0.5), 1.0, 0.0);
    else
        c = vec3(1.0, 1.0 + 4.0 * (0.75 - x), 0.0);

    
    return mat_saturate(c);
}

float cubicPulse( float c, float w, float x )
{
    x = abs(x - c);
    if( x>w ) return 0.0;
    x /= w;
    return 1.0 - x*x*(3.0-2.0*x);
}

vec3 filmicToneMapping(vec3 color)
{
    color = max(vec3(0.), color - vec3(0.004));
    color = (color * (6.2 * color + .5)) / (color * (6.2 * color + 1.7) + 0.06);
    return color;
}



float SS(float a,float b) {
    return smoothstep(0.5-a,0.5+a,b);
}

float drawSquare(vec2 uv, vec2 p, float size) {
    
    
    return SS(-0.02, (abs(uv.x-p.x) + abs(uv.y-p.y)) / size);
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec3 col = vec3(0.);

    float piTime = mat_a1_time*PI; 
    float spinTime = piTime / 6.;
    float capTime = mat_a2_time;
    float colorTime = mat_a4_time / 6.;

    for (int i = 0; i<mat_squares; i++) {
        float fi = float(i);
        vec2 nuv = rotate(uv,-piTime/12.);
        vec2 suv = rotate(uv,spinTime); 
        suv = rotate(suv,sin(fi*PI/8.)); 
        suv *= 1.+sin(piTime+fi*PI/6.)*0.1;
        suv *= 1.+fi*0.1;

        float sq = max(abs(suv.x), abs(suv.y)) * mat_scale1;
        sq = SS(0.5,abs(sq-.15));
        sq = cubicPulse(0.5,0.05,sq)*5.;
        col += sq*spectral_zucconi6(fract(colorTime+fi/20.)*300.+400.);

        suv *= 0.9+mat_noise(vec3(nuv*10.,mat_a3_time*2.))*0.2;

        sq = max(abs(suv.x), abs(suv.y)) * mat_scale2;
        sq = SS(0.5,abs(sq-.15));
        sq = cubicPulse(0.5,0.05,sq)*5.;
        col += 0.5*sq*spectral_zucconi6(fract(colorTime+fi/20.)*300.+400.);

        suv *= 0.9+mat_noise(vec3(nuv*30.,mat_a3_time*3.))*0.2;

        sq = max(abs(suv.x), abs(suv.y)) * mat_scale3;
        sq = SS(0.5,abs(sq-.15));
        sq = cubicPulse(0.5,0.05,sq)*5.;
        col += 0.5*sq*spectral_zucconi6(fract(colorTime+fi/20.)*300.+400.);
    }

    vec2 pt = vec2(0.,1.);
    vec2 pb = vec2(0.,-1.);
    vec2 pl = vec2(-1.,0.);
    vec2 pr = vec2(1.,0.);

    
    float t3 = fract((5./6.)*capTime*0.4)*3.; 
    float t4 = fract((5./6.)*capTime*0.3+1.)*4.; 

    vec2 p1,p2;

    if (t3 < 1.) {
        p1 = mix(pb,pt,fract(t3));
    } else if (t3 < 2.) {
        p1 = mix(pt,pr,fract(t3));
    } else {
        p1 = mix(pr,pb,fract(t3));
    }

    if (t4 < 1.) {
        p2 = mix(pb,pl,fract(t4));
    } else if (t4 < 2.) {
        p2 = mix(pl,pt,fract(t4));
    } else if (t4 < 3.) {
        p2 = mix(pt,pr,fract(t4));
    } else {
        p2 = mix(pr,pb,fract(t4));
    }

    p1 *= 0.5;
    p2 *= 0.5;

    float d1 = drawSquare(uv,p1,0.25) * mat_blocks_level;
    col += d1*spectral_zucconi6(fract(colorTime)*300.+400.);

    float d2 = drawSquare(uv,p2,0.25) * mat_blocks_level;
    col += d2*spectral_zucconi6(fract(colorTime+PI)*300.+400.);

    
    col = filmicToneMapping(col);
    out_color = vec4(col,1.0);


    
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
