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
uniform vec4 uMMParam002; // native input: mat_uv_amount
vec2 mat_uv_amount = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: mat_magic
float mat_magic = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_cycle_1
float mat_cycle_1 = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_cycle_2
float mat_cycle_2 = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_cycle_3
float mat_cycle_3 = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_iterations
int mat_iterations = int(round(uMMParam007.x));
uniform vec4 uMMParam008; // native input: mat_speed
float mat_speed = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: mat_reverse
bool mat_reverse = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: mat_offset
float mat_offset = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_offset_scale
float mat_offset_scale = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_strob
float mat_strob = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_anim_counter_uv
bool mat_anim_counter_uv = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_anim_x_adjust
float mat_anim_x_adjust = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_anim_y_adjust
float mat_anim_y_adjust = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_uv_animate
bool mat_uv_animate = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_uv_zoom_factor
float mat_uv_zoom_factor = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_uv_rot_factor
float mat_uv_rot_factor = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_uv_xy_factor
float mat_uv_xy_factor = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_uv_speed
float mat_uv_speed = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_uv_bpm_sync
bool mat_uv_bpm_sync = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_uv_reverse
bool mat_uv_reverse = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_uv_offset
float mat_uv_offset = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_uv_strob
float mat_uv_strob = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_scroll_animate
bool mat_scroll_animate = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_scroll_angle
float mat_scroll_angle = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_scroll_speed
float mat_scroll_speed = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_scroll_bpm_sync
bool mat_scroll_bpm_sync = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_scroll_reverse
bool mat_scroll_reverse = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: mat_scroll_offset
float mat_scroll_offset = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_scroll_strob
float mat_scroll_strob = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_color_dark
bool mat_color_dark = uMMParam033.x > 0.5;
uniform vec4 uMMParam034; // native input: mat_color_cycle_1
float mat_color_cycle_1 = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_color_cycle_2
float mat_color_cycle_2 = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_color_cycle_3
float mat_color_cycle_3 = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_brightness
float mat_brightness = uMMParam037.x;
uniform vec4 uMMParam038; // native input: mat_contrast
float mat_contrast = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_saturation
float mat_saturation = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_hue_shift
float mat_hue_shift = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_invert
bool mat_invert = uMMParam041.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_uv_time_source = uTDTime * (mat_uv_speed);
float mat_scroll_time_source = uTDTime * (mat_scroll_speed);
























































































































































































































































































































































































































float pbmRepairNonzero(float v) { return v == 0.0 ? 1e-6 : v; }
vec3 pbmRepairNonzero(vec3 v) { return vec3(pbmRepairNonzero(v.x), pbmRepairNonzero(v.y), pbmRepairNonzero(v.z)); }
vec3 pbmRepairNormal(vec3 v) { return dot(v,v) == 0.0 ? vec3(0.0) : normalize(v); }
vec2 pbmRepairNormal(vec2 v) { return dot(v,v) == 0.0 ? vec2(0.0) : normalize(v); }

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

float mat_time = (mat_time_source - mat_offset * 8. * mat_offset_scale) * 0.5;

float mat_uv_time = (mat_uv_time_source - mat_uv_offset) * 0.25;

float mat_scroll_time = (mat_scroll_time_source - mat_scroll_offset) * 0.25;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}







float magicBox(vec3 p) {
    
    
    
    p = 1.0 - abs(1.0 - mod(p, 2.0)) * mat_cycle_2;

    float lastLength = length(p) * mat_cycle_3;
    float tot = 0.0;
    
    
    for (int i=0; i < mat_iterations; i++) {
      
      
      p = abs(p)/(lastLength*lastLength) - mat_magic;
      float newLength = length(p);
      tot += abs(newLength-lastLength);
      lastLength = newLength;
    }

    return tot;
}



const mat3 M = mat3(0.28862355854826727, 0.6997227302779844, 0.6535170557707412,
                    0.06997493955670424, 0.6653237235314099, -0.7432683571499161,
                    -0.9548821651308448, 0.26025457467376617, 0.14306504491456504);


mat2 mat_rot(float deg)
{
    return mat2(cos(deg),-sin(deg),
                sin(deg), cos(deg));

}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale * 2.;

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    vec2 uv_shift = mat_uv_amount;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    uv_shift += vec2(0.5);
    uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate) / 360);
    uv_shift -= vec2(0.5);

    uv += uv_shift;

    float uv_time = mat_uv_time;

    if (!mat_uv_animate) {
        uv_time = 0.;
    }

    uv*=3.5+.5-sin(uv_time*.75*mat_uv_zoom_factor);   

    
    
    uv-=.5;                  

    uv*=mat_rot(sin(-uv_time*1.6*mat_uv_rot_factor)/3.); 
    uv.y -= uv_time*1.8*mat_uv_xy_factor;           
    uv.x += sin(uv_time*.12*mat_uv_xy_factor)*21.;  

    
    
    
    
    
    

    
    
    
    if (mat_anim_counter_uv) {
        uv.x += mat_time * mat_anim_x_adjust;
        uv.y += mat_time * mat_anim_y_adjust;
    }

    if (mat_scroll_animate) {
        float shift_time_x = mat_scroll_time * cos(2.*PI * mat_scroll_angle/360.0);
        float shift_time_y = mat_scroll_time * sin(2.*PI * mat_scroll_angle/360.0);
        uv.x -= shift_time_x;
        uv.y -= shift_time_y;

    }

    vec3 p = 0.5*M*vec3(uv, 0.0);

    float r = magicBox(p-mat_time*.25);

    
    r *= 0.05245 * mat_cycle_1;      
    

    out_color = vec4(vec3(cos(r*r-3.3 * mat_color_cycle_1),cos(r+r+r+2.49 * mat_color_cycle_2),cos(r+r+r+r-3.9 * mat_color_cycle_3)),1.0);


    if (mat_color_dark) {
        out_color.rgb = sqrt(max(out_color.rgb, vec3(0.0)));
        out_color.rgb = pbmRepairNormal(out_color.rgb);
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

    if (!mat_color_dark) {
        out_color.rgb = sqrt(max(out_color.rgb, vec3(0.0)));
    }

    
    out_color.rgb += mat_brightness;

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
