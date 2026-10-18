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

uniform vec4 uMMParam000; // native input: mat_size
float mat_size = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_thick
float mat_thick = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_fov
float mat_fov = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_scale
float mat_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_rotate
float mat_rotate = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam005.xy;
uniform vec4 uMMParam006; // native input: mat_speed
float mat_speed = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_reverse
bool mat_reverse = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_offset
float mat_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_strob
float mat_strob = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_scroll_amount
vec2 mat_scroll_amount = uMMParam011.xy;
uniform vec4 uMMParam012; // native input: mat_animate_scroll
bool mat_animate_scroll = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_scroll_speed
float mat_scroll_speed = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_scroll_bpm_sync
bool mat_scroll_bpm_sync = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_scroll_reverse
bool mat_scroll_reverse = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_scroll_offset
float mat_scroll_offset = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_scroll_strob
float mat_scroll_strob = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_animate_slide
bool mat_animate_slide = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_slide_diff
int mat_slide_diff = int(round(uMMParam019.x));
uniform vec4 uMMParam020; // native input: mat_slide_speed
float mat_slide_speed = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_slide_bpm_sync
bool mat_slide_bpm_sync = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_slide_reverse
bool mat_slide_reverse = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_slide_offset
float mat_slide_offset = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_slide_strob
float mat_slide_strob = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_color_mix
float mat_color_mix = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_animate_color
bool mat_animate_color = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_color_speed
float mat_color_speed = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_color_bpm_sync
bool mat_color_bpm_sync = uMMParam028.x > 0.5;
uniform vec4 uMMParam029; // native input: mat_color_reverse
bool mat_color_reverse = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_color_offset
float mat_color_offset = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_color_strob
float mat_color_strob = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_background
vec4 mat_background = uMMParam032;
uniform vec4 uMMParam033; // native input: mat_brightness
float mat_brightness = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_contrast
float mat_contrast = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_saturation
float mat_saturation = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_hue_shift
float mat_hue_shift = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_invert
bool mat_invert = uMMParam037.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_scroll_time_source = uTDTime * (mat_scroll_speed);
float mat_slide_time_source = uTDTime * (mat_slide_speed);
float mat_color_time_source = uTDTime * (mat_color_speed);

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

float mat_time = (mat_time_source - mat_offset * 8.) * 0.25;
float mat_scroll_time = (mat_scroll_time_source - mat_scroll_offset * 8.) * 0.25;
float mat_slide_time = (mat_slide_time_source - mat_slide_offset * 8.) * 0.25;
float mat_color_time = (mat_color_time_source - mat_color_offset * 32.) * 0.25;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}




mat2 r2(float a){
    float s = sin(a);
    float c = cos(a);
    return mat2(s, c, -c, s);
}

float random (vec2 st) {
    return fract(sin(dot(st.xy,
        vec2(12.9898,78.233)))*43758.5453123);
}

vec3 effect(vec2 uv, float zoomSpeed, float ringCount, float size, float rotationSpeed){
    float spacing = 1.3;
    vec2 id = floor(uv/spacing-.5); 
    float rrr = random(id.yy);
    rrr *= rrr<(mat_slide_diff/2.) ? 1. : -1.;

    float slide_time = mat_slide_time;
    if (!mat_animate_slide) {
        slide_time = 0.;
    }
    uv.x+=rrr*slide_time*1.5;

    id = floor(uv/spacing-.5);
    uv = (fract(uv/spacing-.5)-.5)*spacing;

    float r = random(id);
    float rr = random(id);

    uv*=r2(rr*rotationSpeed*mat_time+(sin(mat_time*r)*3.*r));
    float s = length(uv)-size*mat_size; 

    float f = smoothstep(s-.005, s, .2935);
    f -= smoothstep(s,s + 0.005, .27 / mat_thick);
    


    float color_time = mat_color_time;
    if (!mat_animate_color) {
        color_time = 0.;
    }

    vec3 col = 0.5 + 0.5*cos(r+rr+color_time+uv.xyx+vec3(r*f,3.-rr+r,r+1.)-color_time*2.);

    col = mix(vec3(1.), col, mat_color_mix);

    float a = atan(uv.x,uv.y);
    
    f = f * smoothstep(f,  cos(a*(ringCount+(sin(mat_time*2.*r)*8.*rotationSpeed*r))*sin(r+mat_time)+cos(-mat_time*11.75*rotationSpeed*rr)) +1., .02);   

    return col*f;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale * 2.;

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    vec2 uv_shift = mat_shift_amount;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);
    uv += uv_shift;

    float scroll_time = mat_scroll_time;

    if (!mat_animate_scroll) {
        scroll_time = 0.;
    }

    uv*=r2(sin(scroll_time/2.));
    uv *= 1.0 + dot(uv,uv)*.5 * mat_fov;
    uv.x+=sin(scroll_time/5.)*13.;
    uv.y+=sin(scroll_time/5.5)*11.;

    uv += mat_scroll_amount;

    vec3 col = effect(uv, 4., 11., .125, .75);
    col += effect(uv, 2.5, 8., .2, 1.);
    col += effect(uv, 1.5, 6., .25, 0.5);
    col += effect(uv, 0.5, 7., .34, 0.35);
    col += effect(uv, 0.25, 5., .081, 0.865);
    col += effect(uv, 0.25, 5., .03, 01.1865);



    

    if (col == vec3(0.)) {
        out_color = mat_background;
    } else {
        out_color = vec4(col,1.0);
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
