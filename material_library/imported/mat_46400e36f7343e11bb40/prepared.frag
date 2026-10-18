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
uniform vec4 uMMParam005; // native input: mat_pattern_scale
float mat_pattern_scale = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_cycle1
float mat_cycle1 = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_cycle2
float mat_cycle2 = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_spread
float mat_spread = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_travel
float mat_travel = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_kaleido
int mat_kaleido = int(round(uMMParam010.x));
uniform vec4 uMMParam011; // native input: mat_speed
float mat_speed = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_reverse
bool mat_reverse = uMMParam013.x > 0.5;
uniform vec4 uMMParam014; // native input: mat_offset
float mat_offset = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_offset_scale
float mat_offset_scale = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_strob
float mat_strob = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_restart
int mat_restart = int(round(uMMParam017.x));
uniform vec4 uMMParam018; // native input: mat_vignette
float mat_vignette = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_aa
bool mat_aa = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_background
bool mat_background = uMMParam020.x > 0.5;
uniform vec4 uMMParam021; // native input: mat_back_color
vec4 mat_back_color = uMMParam021;
uniform vec4 uMMParam022; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam022.x));
uniform vec4 uMMParam023; // native input: mat_back_thresh
float mat_back_thresh = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_gain
float mat_gain = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_brightness
float mat_brightness = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_contrast
float mat_contrast = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_saturation
float mat_saturation = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_hue_shift
float mat_hue_shift = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_invert
bool mat_invert = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam030.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);

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

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}


vec2 transformUV(vec2 uv) {

    if (mat_lock_aspect) {
        uv.x *= RENDERSIZE.x / RENDERSIZE.y;
    }
    uv *= mat_scale * 350. * 2.;

    vec2 uv_shift = mat_shift_amount * mat_shift_scale * 350.;
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

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
}



const float RECORD_PERIOD = 15.;




vec2 pSFold(vec2 p, float n) {
    float e = 5e-3;
    float h = floor(log2(n));
    float a = 6.2831 * exp2(h) / n;
    for (float i = 0.0; i < h + 2.0 * mat_kaleido; i++) {
        vec2 v = vec2(-cos(a), sin(a));
        float g = dot(p, v);
        
        p -= (g - sqrt(g * g + e)) * v;
        a *= 0.5;
    }
    return p;
}

mat2 rot(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

float hash(float n) {
    return fract(sin(n) * 43758.5453123);
}

float hash21(vec2 coord){
    return fract(sin(dot(coord.xy, vec2(12.9898, 78.233))) * 43758.5453);
}




float loop_noise(float x, float loopLen) {
    
    x = mod(x, loopLen);

    float i = floor(x);  
    float f = fract(x);  
    float u =
        f * f * f * (f * (f * 6. - 15.) + 10.) * mat_travel;  

    
    return mix(hash(i), hash(mod(i + 1.0, loopLen)), u) * mat_cycle1;
}

vec3 pattern(vec2 uv, float time, float n) {
    float num_seg = n;
    uv *= rot(PI / num_seg) * mat_pattern_scale;
    uv = pSFold(uv, num_seg);

    float loop_length = RECORD_PERIOD;
    float transition_start = RECORD_PERIOD / 3.;

    float phi = atan(uv.y, uv.x + 1e-6);
    phi = phi / PI * 0.5 + 0.5;
    float seg = floor(phi * num_seg);
    float width = sin(seg) + 8. * pow(mat_spread,2.5);

    float theta = (seg + 0.5) / num_seg * PI * 2.;
    vec2 dir1 = vec2(cos(theta), sin(theta));
    vec2 dir2 = vec2(-dir1.y, dir1.x);

    float radial_length = dot(dir1, uv);
    float prog = radial_length / width;
    float idx = floor(prog);

    const int NUM_CHANNELS = 3;
    vec3 col = vec3(0.);
    for (int i = 0; i < NUM_CHANNELS; ++i) {
        float off = float(i) / float(NUM_CHANNELS) - 1.5;
        time = time + off * .015;

        float theta1 = loop_noise(idx * 34.61798 + time,      loop_length);
        float theta2 = loop_noise(idx * 21.63448 + time + 1., loop_length);

        float transition_progress =
            (time - transition_start) / (loop_length - transition_start);
        float progress = clamp(transition_progress, 0., 1.);

        float threshold = mix(theta1, theta2, progress);

        float width2 = fract(idx * 32.721784) * 500. * mat_cycle2;
        float slide = fract(idx * seg * 32.74853) * 50. 
                      + loop_noise(time, loop_length) * 100. +
                      1000. * (hash(idx) - 0.5);
        float prog2 = (dot(dir2, uv) - slide) / width2;

        float c = clamp(width  * (fract(prog)  - threshold),      0., 1.)
                * clamp(width2 * (fract(prog2) + threshold - 1.), 0., 1.);

        c *= mat_gain;

        col[i] = c;
    }
    return col;
}

float v1gnette(vec2 uv) {
    vec2 d = abs(uv) * 1.21;
    d = pow(d, vec2(2.0));
    return pow(clamp(1.0 - dot(d, d), 0., 1.0), 3.5);
}

vec3 draw(vec2 uv, float fold_n, float release, float time) {
    vec3 col = vec3(0.);

    vec2 block = floor(uv / vec2(64.));
    vec2 uv_noise = block / vec2(125);
    uv_noise += floor(vec2(fract(time)) * vec2(1234.0, 3543.0)) / vec2(2);

    float block_thresh = pow(fract(time), 2.0) * 0.5 * release;
    float line_thresh = pow(fract(time), 2.0) * 0.5 * release;

    vec2 uv_r = uv, uv_g = uv, uv_b = uv;

    if (hash21(uv_noise) < block_thresh ||
        hash21(uv_noise) < line_thresh) {
        vec2 dist = (fract(uv_noise) - 0.5);
        uv_r += dist * 50.1;
        uv_g += dist * 40.2;
        uv_b += dist * 60.125;
    }

    uv_r += 2.;

    col.r = pattern(uv_r, time, fold_n).r;
    col.g = pattern(uv_g, time, fold_n).g;
    col.b = pattern(uv_b, time, fold_n).b;
    return col;
}



vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    float time = mat_time;

    vec3 col = vec3(0.);
    float n = RECORD_PERIOD / 2.;
    
    float release = smoothstep(1., 0., abs(mod(2. * time + 1., n) - 1.));
    release = pow(release, 5.);
    float type = step(n / 2., mod(time, n));
    float fold_n = 4. + 2. * type;
    uv *= 1. - 0.08 * type;

    if (!mat_aa) {
        col = draw(uv, fold_n, release, time);
    } else {
        const int N = 1;
        for (int i = -N; i <= N; i++) {
            for (int j = -N; j <= N; j++) {
                col += draw(uv - vec2(i, j),
                            fold_n, release, time);
            }
        }
        float k = 2. * float(N) + 1.;
        col /= k * k;
    }

    col *= v1gnette((texCoord - vec2(0.5)) / 1000 * pow(mat_vignette,2.));

    out_color = vec4(col,1.0);


    if (mat_background) {
        
        if (mat_back_mode == 1) {
            
            if (mat_luma(out_color.rgb) < mat_back_thresh) {
                out_color = mat_back_color;
            }
        } else {
            
            out_color = mix(mat_back_color, out_color, mat_luma(out_color.rgb) + mat_back_thresh);
        }
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


    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
