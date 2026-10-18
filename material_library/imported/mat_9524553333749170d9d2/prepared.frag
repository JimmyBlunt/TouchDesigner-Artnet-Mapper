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
uniform vec4 uMMParam008; // native input: mat_adjust_pos
vec2 mat_adjust_pos = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_adjust_pos_scale
float mat_adjust_pos_scale = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_wave_scale
float mat_wave_scale = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_separation
float mat_separation = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_wave1_level
float mat_wave1_level = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_wave2_level
float mat_wave2_level = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_soften1
float mat_soften1 = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_soften2
float mat_soften2 = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_mod1
float mat_mod1 = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_mod2
float mat_mod2 = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_glow
float mat_glow = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_speed
float mat_speed = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam020.x > 0.5;
uniform vec4 uMMParam021; // native input: mat_reverse
bool mat_reverse = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_offset
float mat_offset = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_offset_scale
float mat_offset_scale = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_strob
float mat_strob = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_restart
int mat_restart = int(round(uMMParam025.x));
uniform vec4 uMMParam026; // native input: mat_animate_rotate
bool mat_animate_rotate = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_rotate_range
vec2 mat_rotate_range = uMMParam027.xy;
uniform vec4 uMMParam028; // native input: mat_rotate_signal
int mat_rotate_signal = int(round(uMMParam028.x));
uniform vec4 uMMParam029; // native input: mat_rotate_filter
int mat_rotate_filter = int(round(uMMParam029.x));
uniform vec4 uMMParam030; // native input: mat_rotate_curve
float mat_rotate_curve = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_rotate_speed
float mat_rotate_speed = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_rotate_bpm_sync
bool mat_rotate_bpm_sync = uMMParam032.x > 0.5;
uniform vec4 uMMParam033; // native input: mat_rotate_reverse
bool mat_rotate_reverse = uMMParam033.x > 0.5;
uniform vec4 uMMParam034; // native input: mat_rotate_offset
float mat_rotate_offset = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_rotate_strob
float mat_rotate_strob = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_rotate_restart
int mat_rotate_restart = int(round(uMMParam036.x));
uniform vec4 uMMParam037; // native input: mat_front_color
vec4 mat_front_color = uMMParam037;
uniform vec4 uMMParam038; // native input: mat_back_color
vec4 mat_back_color = uMMParam038;
uniform vec4 uMMParam039; // native input: mat_contrast
float mat_contrast = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_invert
bool mat_invert = uMMParam040.x > 0.5;
uniform vec4 uMMParam041; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam041.x));
uniform vec4 uMMParam042; // native input: mat_back_thresh
float mat_back_thresh = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_back_sensitivity
float mat_back_sensitivity = uMMParam043.x;
float mat_time_source = uTDTime * (mat_speed);
float mat_rotate_time_source = uTDTime * (mat_rotate_speed);

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

float mat_time = (mat_time_source - mat_offset * 8. * mat_offset_scale) * 4.;

float mat_rotate_time = fract((mat_rotate_time_source * 0.05  - mat_rotate_offset));

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



float matEaseInOut(float t, float curve) {
    
    if (t < 0.5) {
        return pow(2 * t, curve) / 2.;
    } else {
        return 1. - pow(-2. * t + 2, curve) / 2.;
    }
}

float matEaseIn(float t, float curve) {
    
    return pow(t, curve);
}

float matEaseOut(float t, float curve) {
    
    return 1. - pow(1. - t, curve);
}

float matEaseOutIn(float t, float curve) {
    
    
    return (pow(t, 3.) - 2. * pow(t, 2.) + t) * curve + (-2. * pow(t,3.) + 3. * pow(t, 2.)) + (pow(t, 3.) - pow(t, 2.)) * curve;
}


float matFilter(float t, int filter_type, float curve) {
    

    if (filter_type == 0) { 
        return matEaseIn(t, curve);
    } else if (filter_type == 1) { 
        return matEaseOut(t, curve);
    } else if (filter_type == 2) { 
        return matEaseInOut(t, curve);
    } else { 
        return matEaseOutIn(t, curve);
    }
}

float getRotateValue() {
    

    float rotate;
    float rotate_time;

    if (mat_animate_rotate) {

        if (mat_rotate_signal == 0) { 
            rotate_time = mat_rotate_time;
        } else if (mat_rotate_signal == 1) { 
            rotate_time = 1. - mat_rotate_time;
        } else if (mat_rotate_signal == 2) { 
            rotate_time = floor(mat_rotate_time + 0.5);
        } else if (mat_rotate_signal == 3) { 
            rotate_time = 1. - floor(mat_rotate_time + 0.5);
        } else if (mat_rotate_signal == 4) { 
            rotate_time = abs(0.5 - mat_rotate_time);
        } else { 
            rotate_time = 0.5 + 0.5 * sin(2. * PI * mat_rotate_time);
        }

        rotate_time = 1. - rotate_time;
        
        rotate_time = matFilter(rotate_time, mat_rotate_filter, mat_rotate_curve);
        float range_min = mat_rotate_range[0] / 360.0;
        float range_max = mat_rotate_range[1] / 360.0;
        rotate_time = range_min + rotate_time * (range_max - range_min);

        rotate = (rotate_time + mat_rotate / 360.) * 360.;
    } else {
        rotate = mat_rotate;
    }
    return rotate;
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
    uv *= mat_scale * 20.;

    uv = mirrorUV(uv);

    vec2 uv_shift = mat_shift_amount * mat_shift_scale * 10.;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    float rotate = getRotateValue();

    
    if (mat_shift_type == 0) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, -1. * 2*PI*(rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*rotate / 360);
    uv -= vec2(0.5);

    
    if (mat_shift_type == 1) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, 2*PI*(rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    return uv;
}


vec2 wave(vec2 p) {
    
    float a = .5 * pow(mat_soften1,2.);
    float b = 2. * mat_wave_scale;
    float x1 = a * length(p) + 1. * pow(mat_soften2,2.);
    float x2 = length(p) * b - mat_time;
    return - normalize(p) * (b * x1 * sin(x2) + a * cos(x2))/x1/x1;
}

vec3 normal( vec2 p ) {
    vec2 d = mat_wave2_level * wave(p-vec2(5 * mat_separation,0)) + mat_wave1_level * wave(p+vec2(5 * mat_separation,0));
    return normalize(cross(vec3(1 * mat_mod1, 0, d.x), vec3(0, 1 * mat_mod2, d.y)));
}



vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    

    vec2 light_pos = mat_adjust_pos * mat_adjust_pos_scale * 4.;
    light_pos = flipX(light_pos, 1.);
    

    out_color = vec4(vec3(1., 1., 1.) * dot(
        normal(uv),
        normalize(vec3(light_pos, 1 * mat_glow))),
    1);

    
    if (mat_invert) out_color.rgb=1-out_color.rgb;

    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    const vec3 AvgLumin = vec3(0.5, 0.5, 0.5);
    vec3 intensity = vec3(dot(out_color.rgb, LumCoeff));
    out_color.rgb = mix(AvgLumin, out_color.rgb, mat_contrast);

    
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
