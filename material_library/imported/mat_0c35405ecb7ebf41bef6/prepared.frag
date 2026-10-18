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
uniform vec4 uMMParam001; // native input: mat_center
vec2 mat_center = uMMParam001.xy;
uniform vec4 uMMParam002; // native input: mat_glow
float mat_glow = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_intensity
float mat_intensity = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_trace
float mat_trace = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_sharpness
float mat_sharpness = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_reverse
bool mat_reverse = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_speed
float mat_speed = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_offset
float mat_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_strob
float mat_strob = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_scroll_bpm_sync
bool mat_scroll_bpm_sync = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_scroll_reverse
bool mat_scroll_reverse = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_scroll_speed
float mat_scroll_speed = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_scroll_offset
float mat_scroll_offset = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_scroll_strob
float mat_scroll_strob = uMMParam015.x;
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

float mat_time = mat_time_source - mat_offset * 20.;
float mat_scroll_time = mat_scroll_time_source - mat_scroll_offset * 20.;

#define     pisq    9.869604401089359   
#define     twpi    6.283185307179586   
#define     phicu   4.236067977499791   
#define     cuphi   1.173984996705329   
#define     rctwpi  0.159154943091895   
#define     r36     0.027777777777778


vec3 color = vec3(0.0,0.5,0.0);
float S = mat_glow;
float T = mat_time*0.005;
float T2 = mat_scroll_time*0.005;

vec2 hash22(vec2 p) { return fract(vec2(21.0, 97.0)*sin(dot(p, vec2(92.0, 61.0)))); }

void formula(vec2 uv, vec2 z, float f)
{
    float m = 0.0;
    float o, ot2, ot=ot2=10000.0;
    for (int i=0; i<9; i++) {
        z = abs(z)/clamp(dot(z,z), 0.1, 0.5)-f;
        float l = length(z);
        o = min(max(abs(min(z.x, z.y)),-l+0.25), abs(l-0.25));
        ot = min(ot, o);
        ot2 = min(l*0.1, ot2);
        m = max(m, float(i)*(1.0-abs(sign(ot-o))));
    }
    m += 1.0;
    float w = mat_intensity*m*2.0;
    float circ = pow(max(0.0,w-ot2)/w,6.0);
    S += max(pow(max(0.0,w-ot)/w,0.25),circ);
    vec3 col = vec3(hash22(z),f);
    color += col*(0.4+mod(m/9.0-T*mat_trace+ot2*2.0, 1.0)*1.6);
    color += vec3(1.0, 0.7, 0.3)*circ*(10.0-m)*3.0
             *smoothstep(0.0, 0.5, vec3(f, uv.x, uv.y));
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale;

    vec2 pos = uv;

    vec2 center_alt = mat_center;
    center_alt.x = 1. - center_alt.x;

    uv -= center_alt;
    vec2 uv_orig = uv;

    

    
    float a = T2 + T2*cuphi;

    float mat_circuit_offset = 0.05;

    float b = a*phicu;
    uv *= mat2(cos(b),sin(b),-sin(b),cos(b));
    uv += vec2(sin(a),cos(a*cuphi))*pisq;
    
    uv *= mat_circuit_offset;
    
    
    
    float pix = cuphi/(4000. * mat_sharpness / mat_scale)*mat_circuit_offset;
    float c = 1.5+mod(floor(T2), 16.0)*0.125;
    for (int aa=0; aa<36; aa++) {
        vec2 aauv = floor(vec2(float(aa)*rctwpi, mod(float(aa), twpi)));
        formula(uv_orig, uv+aauv*pix, c);
    }
    S *= r36, color *= r36;
    vec3 colo = mix(vec3(0.025), color, S)*(1.5-length(pos));
    colo *= vec3(1.2, 1.1, 1.0);
    out_color = vec4(colo, 1.0);


    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
