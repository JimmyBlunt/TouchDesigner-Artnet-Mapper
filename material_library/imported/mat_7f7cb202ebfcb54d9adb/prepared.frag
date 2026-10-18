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

uniform vec4 uMMParam000; // native input: center
vec2 center = uMMParam000.xy;
uniform vec4 uMMParam001; // native input: flip
bool flip = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_zoom
float mat_zoom = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_wave_scale_y
float mat_wave_scale_y = uMMParam003.x;
uniform vec4 uMMParam004; // native input: seed1
float seed1 = uMMParam004.x;
uniform vec4 uMMParam005; // native input: seed2
float seed2 = uMMParam005.x;
uniform vec4 uMMParam006; // native input: seed3
float seed3 = uMMParam006.x;
uniform vec4 uMMParam007; // native input: freq
float freq = uMMParam007.x;
uniform vec4 uMMParam008; // native input: freq2
float freq2 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: freq3
float freq3 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: mat_reverse
bool mat_reverse = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_speed
float mat_speed = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_offset
float mat_offset = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_strob
float mat_strob = uMMParam014.x;
uniform vec4 uMMParam015; // native input: Rx
float Rx = uMMParam015.x;
uniform vec4 uMMParam016; // native input: Gx
float Gx = uMMParam016.x;
uniform vec4 uMMParam017; // native input: Bx
float Bx = uMMParam017.x;
uniform vec4 uMMParam018; // native input: offset
float offset = uMMParam018.x;
uniform vec4 uMMParam019; // native input: offset2
float offset2 = uMMParam019.x;
uniform vec4 uMMParam020; // native input: offset3
float offset3 = uMMParam020.x;
uniform vec4 uMMParam021; // native input: invert
bool invert = uMMParam021.x > 0.5;
float mat_time = uTDTime * (mat_speed);

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

float iTime = mat_time - mat_offset * 10;












float fade(float t) { return t * t * t * (t * (t * 6.0 - 15.0) + 10.0); }

vec2 smoothify(vec2 x) { return vec2( fade(x.x), fade(x.y)); }

vec2 hash(vec2 co) {
    float m = dot(co, vec2(seed1, seed2));
    return fract( vec2( sin(m), cos(m)) * seed3) * 2.0 - 1.0;
}

float pNoise(vec2 uv) {
    vec2 PT  = floor(uv);
    vec2 pt  = fract(uv);
    vec2 mmpt = smoothify(pt);
    vec4 grads = vec4(dot(hash(PT + vec2(0.0, 1.0)), pt-vec2(0.0, 1.0)),
                    dot(hash(PT + vec2(1.0, 1.0)), pt-vec2(1.0, 1.0)),
                    dot(hash(PT + vec2(0.0, 0.0)), pt-vec2(0.0, 0.0)),
                    dot(hash(PT + vec2(1.0, 0.0)), pt-vec2(1.0, 0.0)));
    return 5.*mix (mix (grads.z, grads.w, mmpt.x), mix (grads.x, grads.y, mmpt.x), mmpt.y);
}

float fbm(vec2 uv) {
    float N = iTime;
    N += 1.0000*pNoise(10.0*uv);
    N += 0.50000*pNoise(20.0*uv);
    N += 0.25000*pNoise(40.0*uv);
    N += 0.12500*pNoise(80.0*uv);
    N += 0.06250*pNoise(160.0*uv);
    N += 0.03125*pNoise(320.0*uv);
    return N;
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 uv = (texCoord - vec2(0.5)) + center;
    vec2 p = (mat_zoom * 0.02) * uv;

    

    float e, f;
    vec3 g, h, j, k, q;
    
    
    if (flip) {
        f = p.x * 100. * mat_wave_scale_y;
    } else {
        f = p.y * 100. * mat_wave_scale_y;
    }

    e = sin( floor(freq2) * f + fbm( floor(freq) * p) + fbm( floor(freq2) * p) + fbm( floor(freq3) * p));
    g = vec3(e);
    h = mix( g,vec3(1.0, 0.0, 0.0), Rx);
    j = mix( g,vec3(0.0, 1.0, 0.0), Gx);
    k = mix( g,vec3(0.0, 0.0, 1.0), Bx);
    q = vec3( reflect( reflect( offset + h ,offset2 - j ), offset3 + k ));
    if (invert) {
        return vec4( 1.0 - vec3(q), 1.0);
    } else {
        return vec4( q, 1.0);
    }




}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
