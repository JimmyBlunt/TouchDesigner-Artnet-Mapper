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
uniform vec4 uMMParam002; // native input: mat_uv_offset
vec2 mat_uv_offset = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: mat_egg
bool mat_egg = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_big_egg_size
float mat_big_egg_size = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_speed
float mat_speed = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_reverse
bool mat_reverse = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_offset
float mat_offset = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_offset_scale
float mat_offset_scale = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_strob
float mat_strob = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_small_egg_size
float mat_small_egg_size = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_span
float mat_span = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_field_fill
float mat_field_fill = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_hole_size
float mat_hole_size = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_field_offset
vec2 mat_field_offset = uMMParam015.xy;
uniform vec4 uMMParam016; // native input: mat_scroll_angle
float mat_scroll_angle = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_scroll_speed
float mat_scroll_speed = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_scroll_bpm_sync
bool mat_scroll_bpm_sync = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_scroll_reverse
bool mat_scroll_reverse = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_scroll_offset
float mat_scroll_offset = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_scroll_strob
float mat_scroll_strob = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_distort
float mat_distort = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_distort_offset
vec2 mat_distort_offset = uMMParam023.xy;
uniform vec4 uMMParam024; // native input: mat_vignette
bool mat_vignette = uMMParam024.x > 0.5;
uniform vec4 uMMParam025; // native input: mat_vignette_lvl
float mat_vignette_lvl = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_fuzz
bool mat_fuzz = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_back_color
vec4 mat_back_color = uMMParam027;
uniform vec4 uMMParam028; // native input: mat_alpha_background
bool mat_alpha_background = uMMParam028.x > 0.5;
uniform vec4 uMMParam029; // native input: mat_back_thresh
float mat_back_thresh = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_color_simple_mode
bool mat_color_simple_mode = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: mat_outline_color
vec4 mat_outline_color = uMMParam031;
uniform vec4 uMMParam032; // native input: mat_glow_color
vec4 mat_glow_color = uMMParam032;
uniform vec4 uMMParam033; // native input: mat_yolk_color
vec4 mat_yolk_color = uMMParam033;
uniform vec4 uMMParam034; // native input: mat_tint
vec4 mat_tint = uMMParam034;
uniform vec4 uMMParam035; // native input: mat_brightness
float mat_brightness = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_contrast
float mat_contrast = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_saturation
float mat_saturation = uMMParam037.x;
uniform vec4 uMMParam038; // native input: mat_hue_shift
float mat_hue_shift = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_invert
bool mat_invert = uMMParam039.x > 0.5;
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

float mat_scroll_time = mat_scroll_time_source - mat_scroll_offset;

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


float bigsize = .8 * mat_big_egg_size;
float smallsize = .09 * mat_small_egg_size;
float span = .1 * mat_span;


float PI2 = PI*2.;

mat2 rot2D(float r){
    return mat2(cos(r), sin(r), -sin(r), cos(r));
}
float nsin(float x) {
    return cos(x)*.5+.5;
}
vec3 hash32(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yxz+19.19);
    return fract((p3.xxy+p3.yzz)*p3.zyx);
}
float opUnion( float d1, float d2 ) { return min(d1,d2); }
float opSubtraction( float d1, float d2 ) { return max(-d1,d2); }

float sdShape(vec2 p, float r) {
    return length(p+r*.5)-r;
}
void egg(inout vec2 sd, vec2 uv, float t, float r, float a) {
    if (r <= 0.) return;
    float yolk = sdShape((11./sqrt(2.))*uv*rot2D(a), r);
    float white = sdShape((5.2/sqrt(2.))*uv*rot2D(a), r);
    sd = vec2(opUnion(sd.x, white),
              opUnion(sd.y, yolk));
}


float under(vec2 N, float t) {
    const float sz = .001;
    const float range = 1.8;
    vec2 p1 = vec2(sin(-t*1.6666), cos(t)) * range;
    vec2 p2 = vec2(sin(t), sin(t*1.3333)) * range;
    float b = min(length(p1-N)-sz, length(p2-N)-sz);
    return b;
}

void smallEggField(inout vec2 sd, vec2 uv, vec2 uvbig, float t) {

    

    float t_x = 0.3 * t * cos(2.*PI * mat_scroll_angle/360.0);
    float t_y = 0.3 * t * sin(2.*PI * mat_scroll_angle/360.0);

    vec2 field_shift = mat_field_offset;
    field_shift += vec2(0.5);
    field_shift.x = 1.-field_shift.x;
    field_shift -= vec2(0.5);
    field_shift *= 0.5;

    vec2 uvsmall = mod(uv+vec2(t_x + field_shift.x,t_y + field_shift.y),span)-span*.5;


    vec2 uvsmall_q = (uv-uvsmall) / mat_hole_size;
    vec2 sdquant = vec2(1e6);
    
    egg(sdquant, uvsmall_q, t, bigsize, under(uvsmall_q, t));
    egg(sd,uvsmall, t, smallsize * smoothstep(0.,.8,sdquant.x - .5), under(uvbig*10., t));
}

vec3 color(vec2 sd, float fact) {
    
    
    
    
    
    

    
    
    
    
    

    vec3 o;

    if (mat_color_simple_mode) {

        o.rgb = 1.-smoothstep(vec3(0),mat_field_fill*fact*vec3(0.), vec3(sd.x));
        o.rgb *= mat_tint.rgb;

        if (!mat_alpha_background) {
            o += mat_back_color.rgb;
        }
        o = clamp(o,o-o,o-o+1.);

    } else {

        o.rgb = 1.-smoothstep(vec3(0),mat_field_fill*fact*mat_outline_color.rgb, vec3(sd.x));
        o.rgb *= mat_tint.rgb;

        if (!mat_alpha_background) {
            o += mat_back_color.rgb;
        }
        if (sd.x < 0.) o -= sd.x*.6;
        o = clamp(o,o-o,o-o+1.);

        vec3 ayolk = 1.-smoothstep(vec3(0),fact*mat_glow_color.rgb,sd.yyy);
        o.rgb = mix(o.rgb, mat_yolk_color.rgb, ayolk);
        if (sd.y < 0.) o -= sd.y*.1;
        o = clamp(o,o-o,o-o+1.);
    }

    return o;

}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale * 1.25;

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    vec2 uv_shift = mat_uv_offset;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    uv_shift += vec2(0.5);
    uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate) / 360);
    uv_shift -= vec2(0.5);

    uv += uv_shift;

    vec2 N = texCoord - vec2(0.5);

    uv.y -= .1;
    vec2 sd = vec2(1e6);
    vec2 uvbig = uv * mat_distort;
    
    if (mat_egg) {
        egg(sd, uv, mat_time, bigsize, under(uvbig, mat_time));
    }
    
    vec2 sdsmall = vec2(1e6);

    vec2 distort_shift = mat_distort_offset;
    distort_shift += vec2(0.5);
    distort_shift.x = 1.-distort_shift.x;
    distort_shift -= vec2(0.5);

    uvbig += distort_shift;

    smallEggField(sdsmall, uv, uvbig, mat_scroll_time);
    uv -= span * .5;
    smallEggField(sdsmall, uv, uvbig, mat_scroll_time);

    out_color.rgb = mix(color(sd, 2.), color(sdsmall, .2), vec3(step(.1,sd.x)));
    out_color = pow(out_color, out_color-out_color+.5);
    

    if (mat_fuzz) {
        out_color.rgb += (hash32(uv+mat_time)-.5)*.1;
        out_color = clamp(out_color,out_color-out_color,out_color-out_color+1.);
    }

    if (mat_vignette) {
        out_color *= 1.-length(13.*pow(abs(N), vec2(4.))) * mat_vignette_lvl;
    }

    out_color.a = 1.;

    if (mat_alpha_background) {
        if (mat_luma(out_color.rgb) < mat_back_thresh) {
            out_color.a = 0.;
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
