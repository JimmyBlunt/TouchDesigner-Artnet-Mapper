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
uniform vec4 uMMParam003; // native input: mat_goo_aspect
float mat_goo_aspect = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_distort
float mat_distort = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_noise_scale
float mat_noise_scale = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_animate
bool mat_animate = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_speed
float mat_speed = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_reverse
bool mat_reverse = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: mat_offset
float mat_offset = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_offset_scale
float mat_offset_scale = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_strob
float mat_strob = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_travel_amount
vec2 mat_travel_amount = uMMParam013.xy;
uniform vec4 uMMParam014; // native input: mat_travel_animate
bool mat_travel_animate = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_travel_angle
float mat_travel_angle = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_travel_speed
float mat_travel_speed = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_travel_bpm_sync
bool mat_travel_bpm_sync = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_travel_reverse
bool mat_travel_reverse = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_travel_offset
float mat_travel_offset = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_travel_offset_scale
float mat_travel_offset_scale = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_travel_strob
float mat_travel_strob = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_front_color
vec4 mat_front_color = uMMParam022;
uniform vec4 uMMParam023; // native input: mat_shine_color
vec4 mat_shine_color = uMMParam023;
uniform vec4 uMMParam024; // native input: mat_use_alpha
bool mat_use_alpha = uMMParam024.x > 0.5;
uniform vec4 uMMParam025; // native input: mat_noise_contrast
float mat_noise_contrast = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_noise_contrast2
float mat_noise_contrast2 = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_shine
float mat_shine = uMMParam027.x;
float mat_time_source = uTDTime * (mat_speed);
float mat_travel_time_source = uTDTime * (mat_travel_speed);

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
float mat_travel_time = mat_travel_time_source - mat_travel_offset * 8. * mat_travel_offset_scale;

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





float psrdnoise(vec2 x, vec2 period, float alpha, out vec2 gradient)
{
    vec2 uv = vec2(x.x+x.y*0.5, x.y);
    vec2 i0 = floor(uv), f0 = fract(uv);
    float cmp = step(f0.y, f0.x);
    vec2 o1 = vec2(cmp, 1.0-cmp);
    vec2 i1 = i0 + o1, i2 = i0 + 1.0;
    vec2 v0 = vec2(i0.x - i0.y*0.5, i0.y);
    vec2 v1 = vec2(v0.x + o1.x - o1.y*0.5, v0.y + o1.y);
    vec2 v2 = vec2(v0.x + 0.5, v0.y + 1.0);
    vec2 x0 = x - v0, x1 = x - v1, x2 = x - v2;
    vec3 iu, iv, xw, yw;
    if(any(greaterThan(period, vec2(0.0)))) {
        xw = vec3(v0.x, v1.x, v2.x);
        yw = vec3(v0.y, v1.y, v2.y);
        if(period.x > 0.0)
            xw = mod(vec3(v0.x, v1.x, v2.x), period.x);
        if(period.y > 0.0)
            yw = mod(vec3(v0.y, v1.y, v2.y), period.y);
        iu = floor(xw + 0.5*yw + 0.5); iv = floor(yw + 0.5);
    } else {
        iu = vec3(i0.x, i1.x, i2.x); iv = vec3(i0.y, i1.y, i2.y);
    }
    vec3 hash = mod(iu, 289.0);
    hash = mod((hash*51.0 + 2.0)*hash + iv, 289.0);
    hash = mod((hash*34.0 + 10.0)*hash, 289.0);
    vec3 psi = hash*0.07482 + alpha;

    vec3 gx = cos(psi); vec3 gy = sin(psi);
    vec2 g0 = vec2(gx.x, gy.x);
    vec2 g1 = vec2(gx.y, gy.y);
    vec2 g2 = vec2(gx.z, gy.z);
    vec3 w = 0.8*mat_distort - vec3(dot(x0, x0), dot(x1, x1), dot(x2, x2));
    w = max(w, 0.0); vec3 w2 = w*w; vec3 w4 = w2*w2;
    vec3 gdotx = vec3(dot(g0, x0), dot(g1, x1), dot(g2, x2));
    float n = dot(w4, gdotx);
    vec3 w3 = w2*w; vec3 dw = -8.0*w3*gdotx;
    vec2 dn0 = w4.x*g0 + dw.x*x0;
    vec2 dn1 = w4.y*g1 + dw.y*x1;
    vec2 dn2 = w4.z*g2 + dw.z*x2;
    gradient = 10.9*(dn0 + dn1 + dn2);
    return 10.9*n;
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale;

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    vec2 uv_shift = mat_shift_amount;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    uv_shift += vec2(0.5);
    uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate) / 360);
    uv_shift -= vec2(0.5);

    uv += uv_shift;

    float noise_time = mat_time;
    float travel_time = mat_travel_time;

    if (!mat_animate) {
        noise_time = 0.;
    }
    if (!mat_travel_animate) {
        travel_time = 0.;
    }

    float travel_time_x = travel_time * cos(PI * mat_travel_angle);
    float travel_time_y = travel_time * sin(PI * mat_travel_angle);

    vec2 travel_shift = mat_travel_amount;
    travel_shift += vec2(0.5);
    travel_shift.x = 1.-travel_shift.x;
    travel_shift -= vec2(0.5);

    vec2 goo_shift = vec2(travel_time_x + travel_shift.x, travel_time_y + travel_shift.y);

    const float nscale = 8.0;
    vec2 v = nscale*(uv-0.5);
    const vec2 p = vec2(0.0, 0.0);

    float alpha = noise_time;
    vec2 g, gsum;

    float n = 0.5;
    vec2 v2 = v + goo_shift;

    v2 -= vec2(0.5);
    v2.x *= mat_goo_aspect;
    v2 += vec2(0.5);

    n += mat_noise_contrast * 0.4 * psrdnoise(v2, p, alpha, g);
    gsum = g;


    vec2 v3 = v * 2. + 0.1*gsum;

    
    v3 *= mat_noise_scale;
    

    n += mat_noise_contrast2 * 0.2 * psrdnoise(v3, p*2.0,
        alpha*2.0, g);
    gsum += g; 
    vec3 N = normalize(vec3(-gsum, 1.0));
    vec3 L = normalize(vec3(1.0,1.0,1.0));
    float s = pow(max(dot(N,L), 0.0), 10.0 / mat_shine); 
    
    

    vec3 scolor = mat_shine_color.rgb;
    vec3 ncolor = n*mat_front_color.rgb; 

    out_color = vec4(mix(ncolor, scolor, s), 1.0);

    if (mat_use_alpha) {
        out_color.a = mat_luma(out_color);
    }

    

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
