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
uniform vec4 uMMParam006; // native input: mat_flip_x
bool mat_flip_x = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_flip_y
bool mat_flip_y = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: mat_morph1
float mat_morph1 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_morph2
float mat_morph2 = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_morph3
float mat_morph3 = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_morph4
float mat_morph4 = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_morph5
float mat_morph5 = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_speed
float mat_speed = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_reverse
bool mat_reverse = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_offset
float mat_offset = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_offset_scale
float mat_offset_scale = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_strob
float mat_strob = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_restart
int mat_restart = int(round(uMMParam021.x));
uniform vec4 uMMParam022; // native input: mat_color_mod1
float mat_color_mod1 = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_color_mod2
float mat_color_mod2 = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_brightness
float mat_brightness = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_contrast
float mat_contrast = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_saturation
float mat_saturation = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_hue_shift
float mat_hue_shift = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_invert
bool mat_invert = uMMParam028.x > 0.5;
uniform vec4 uMMParam029; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam031.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
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

    uv *= mat_scale * 1.;

    if (mat_flip_x) {
        uv.x = 1. - uv.x;
    }
    if (mat_flip_y) {
        uv.y = 1. - uv.y;
    }

    uv = mirrorUV(uv);

    vec2 uv_shift = mat_shift_amount * mat_shift_scale;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);



    
    if (mat_shift_type == 0) {

        uv_shift += vec2(0.5,0.5);

        
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
        uv_shift += vec2(0.5,0.5);
        uv += uv_shift;
    }

    uv.y = 1. - uv.y;

    

    return uv;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 position = uv;
    position.y *= dot(position,position);

    vec2 mouse = vec2(0.5);

    float color1 = 0.0;
    float color2 = 0.0;
    float color3 = 0.0;
    float color4 = 0.0;
    float color5 = 0.0;
    float color6 = 0.0;
    float equation = 0.0;
    float equation2 = 0.0;
    
    float size = 10.0 *0.4 + .0;
    float posx = size - position.x * size * 2.0;
    float posy = size - position.y * size * 2.0;
    float moux = mouse.x - 0.5;
    float mouy = mouse.y - 0.5;
    float wavy = 0.0;

    
    wavy = sin((posx+posy)*cos(posx-mat_time)-sin(posy-mat_time)-cos(posy-mat_time))  * mat_morph1;
    equation = pow(mat_morph5,1.5)*sin(mat_time*.1)+((posx+posy)/mat_morph2 + wavy);
    float equation_orig = equation;
    equation /= mat_morph3;

    
    equation2 = equation / mat_morph4;
    

    color1 = 0.0 - equation;
    color3 = equation;
    if (equation > 3.0) {
        color1 = 0.5;
        color2 = 0.75;
        color3 = 0.75;
    } else if (equation > 2.0) {
        color1 = equation - 2.0;
        color2 = 1.0;
    } else if (equation > 1.0) {
        color2 = equation - 1.0;
    };
    if (equation < -3.0) {
        color3 = 0.5;
        color2 = 0.75;
        color1 = 0.75;
    } else if (equation < -2.0) {
        color3 = 0.0 - equation - 2.0;
        color2 = 1.0;
    } else if (equation < -1.0) {
        color2 = 0.0 - equation - 1.0;
    };


    color4 = 0.0 - equation2;
    color6 = equation2;
    if (equation2 > 3.0) {
        color4 = 0.5;
        color5 = 0.75;
        color6 = 0.75;
    } else if (equation2 > 2.0) {
        color4 = equation2 - 2.0;
        color5 = 1.0;
    } else if (equation2 > 1.0) {
        color5 = equation2 - 1.0;
    };
    if (equation2 < -3.0) {
        color6 = 0.5;
        color5 = 0.75;
        color4 = 0.75;
    } else if (equation2 < -2.0) {
        color6 = 0.0 - equation2 - 2.0;
        color5 = 1.0;
    } else if (equation2 < -1.0) {
        color5 = 0.0 - equation2 - 1.0;
    };



    

    out_color = vec4( mat_color_mod1*.2-mat_color_mod2*vec3((color1+color4)/4.0,(color2+color5)/1.0, (color3+color6)/23.0 ), 1.0 );


    
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
