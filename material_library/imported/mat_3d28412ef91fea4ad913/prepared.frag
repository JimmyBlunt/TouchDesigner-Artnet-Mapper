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

uniform vec4 uMMParam000; // native input: mat_zoom
float mat_zoom = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_reverse
bool mat_reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_offset
float mat_offset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_strob
float mat_strob = uMMParam005.x;
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


#define EPS 0.0001

float random(vec2 st){
    return fract(sin(dot(st, vec2(12.9898, 78.233))) * 43758.5453123);
}

vec2 random2D(vec2 st){
    st = vec2(dot(st, vec2(127.1, 311.7)), dot(st, vec2(269.5, 183.3)));
    return 2.0 * fract(sin(st) * 43758.5453123) - 1.0;
}

float noise(in vec2 st){
    vec2 i = floor(st * 20.);
    vec2 f = fract(st * 20.);

    vec2 u = f*f*(3.0 - 2.0 * f);

    return mix(
        mix(
            dot(random2D(i + vec2(0.0, 0.0)), f - vec2(0.0, 0.0)),
            dot(random2D(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0)),
            u.x
        ),
        mix(
            dot(random2D(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0)),
            dot(random2D(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0)),
            u.x
        ),
        u.y
    );
}

float circle(in vec2 st, float r, float width, float n){
    float w = (width + noise(st) * width) / 2.;
    float l =  length(st) + noise(st) * 0.2 - iTime * 0.1;
    
    l = mod(l , n);
    return min(step(l, r + w), step(r - w, l));
}
float circle2(in vec2 st, float r, float width, float n){
    float w = (width + noise(st) * width) / 2.;
    float l =  length(st) + noise(st) * 0.2 + iTime * 0.1;
    
    l = mod(l , n);
    return min(step(l, r + w), step(r - w, l));
}

float lectangle(vec2 st, vec2 size){
    st = abs(st) - size + noise(st + iTime * 0.05) * 0.5;
    return step(max(st.x, st.y), 0.);
}

vec3 rotate(in vec3 p, float ax, float ay, float az){
    return p *
        mat3(
            1., 0., 0.,
            0., cos(ax), sin(ax),
            0., sin(ax), cos(ax)
        ) *
        mat3(
            cos(ay), 0., sin(ay),
            0., 1., 0.,
            -sin(ay), 0., cos(ay)
        ) *
        mat3(
            cos(az), -sin(az), 0.,
            sin(az),  cos(az), 0.,
            0., 0., 1.
        );
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 st = texCoord - vec2(0.5);
    st *= mat_zoom;

    vec2 p = rotate(vec3(st, 0.), 0., 0., noise(st) * 0.2  + iTime * 0.3).xy;
    vec2 r = rotate(vec3(st, 0.), 0., 0., noise(st) * 0.2  - iTime * 0.5).xy;
    
    vec2 q = rotate(vec3(st, 0.), 0., 0., noise(st) * 5.).xy;
    vec3 col = vec3(0.1333, 0.6235, 0.9451);
    vec3 col2 = vec3(0.3608, 0.9333, 0.8941);
    float f = 0., g = 0., h = 0.;

    
    
    f = max(f, lectangle(q, vec2(.2, .2)));
    g = circle2(r, 0.1, 0.1, 0.5);
    h = min(pow(0.2 / length(st), 5.), 5.);
    h = max(h, lectangle(q, vec2(.2, .2)));

    float n = 0.;
    st = rotate(vec3(st, 0.), 0., 0., -iTime * 0.1).xy;
    for(int j = 0; j < 30; j++){
        st = rotate(vec3(st, 0.), 0., 0., PI / 15000. * float(j)).xy;
        for(int i = 1; i < 3; i++){
            
            n += noise(st * float(i) * 3.) + float(i) * 0.01;
            
        }
        n = pow(n, 6.);
        
    }
    n = min(2., n);
    
    n = pow(n, 1.);
    g = pow(g, 3.);
    f = pow(f, 5.);
    
    
    
    float hoge = max(g,h);
    
    return vec4(hoge * col2 + n * col, 1.);




}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
