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

uniform vec4 uMMParam000; // native input: mat_fill
float mat_fill = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_layers
float mat_layers = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_scale
float mat_scale = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_rotate
float mat_rotate = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam004.xy;
uniform vec4 uMMParam005; // native input: mat_speed
float mat_speed = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_reverse
bool mat_reverse = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_offset
float mat_offset = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_strob
float mat_strob = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_brightness
float mat_brightness = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_contrast
float mat_contrast = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_saturation
float mat_saturation = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_hue_shift
float mat_hue_shift = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_invert
bool mat_invert = uMMParam014.x > 0.5;
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

float mat_time = mat_time_source - mat_offset * 8.;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}









float rand(vec2 p){ return fract(sin(dot(p, vec2(12.989, 78.233)))*43758.5453); }

float plane(vec2 p, vec2 n){ return dot(p, normalize(n)); }



int binLand(in vec2 p, vec2 o) {
    p = floor(-p);

    float noise = rand(p-o);
    float land = noise - p.y/(100.-100.*(1.-mat_fill) );

    return (land < .15 ? 1: 0);
}


float roof(vec2 p) {
    return p.y*2.;
}
float wall(vec2 p) {
    return p.x*2.-1.;
}
float ceiling(vec2 p) {
    return -p.y*2.+1.;
}
float ceilingDiag(vec2 p) {
    return dot(p, normalize(vec2(-1., -1.)))*2.+1.;
}


float tileEmpty(vec2 p) {
    return 1.;
}
float tileFilled(vec2 p) {
    return -1.;
}
float tileCornerOut_ul(in vec2 p, float r) {
    p.x = 1.-p.x;
    return max(wall(p), roof(p));
}
float tileCornerOut_ur(in vec2 p, float r) {
    return max(wall(p), roof(p));
}
float tileCornerOut_dl(in vec2 p, float r) {
    vec2 p_ = vec2(1.-p.x, p.y);
    return max(max(wall(p_), ceiling(p)), ceilingDiag(p-.3));
}
float tileCornerOut_dr(in vec2 p, float r) {
    vec2 p_ = vec2(1.-p.x, p.y);
    return max(max(wall(p), ceiling(p)), ceilingDiag(p_-.3));
}
float tileCornerIn_ul(in vec2 p, float r) {
    p.x = 1.-p.x;
    return (min(wall(p), roof(p)));
}
float tileCornerIn_ur(in vec2 p, float r) {
    return (min(wall(p), roof(p)));
}
float tileCornerIn_dl(in vec2 p, float r) {
    p.x = 1. - p.x;
    return min(wall(p), ceiling(p));
}
float tileCornerIn_dr(in vec2 p, float r) {
    return (min(wall(p), ceiling(p)));
}
float tileWall_l(in vec2 p, float r) {
    p.x = 1.-p.x;
    return wall(p);
}
float tileWall_r(in vec2 p, float r) {
    return wall(p);
}
float tileWall_u(in vec2 p, in float r) {
    r *= .4;
    return min(roof(p), clamp(length(p-vec2(r+(1.-2.*r)*r, .5))/r, 1.-r*2.5, 1.));
}
float tileWall_d(in vec2 p, float r) {
    return ceiling(p);
}
float tileJoin_a(in vec2 p, float r) {
    return min(max(wall(vec2(1.-p.x, p.y)), roof(p)), tileCornerOut_dr(p, r));
}
float tileJoin_b(in vec2 p, float r) {
    return min(max(wall(p), roof(p)), tileCornerOut_dl(p, r));
}


float getLand(in vec2 p, vec2 o) {
    
    int dec = 0;
    dec += 1 * binLand(vec2(p.x,    p.y), o);
    dec += 2 * binLand(vec2(p.x+1., p.y), o);
    dec += 4 * binLand(vec2(p.x,    p.y+1.), o);
    dec += 8 * binLand(vec2(p.x+1., p.y+1.), o);

    float r = rand(floor(p));

    
    p = fract((p*p));
    float f;

    
    if(dec==0)
        f = tileEmpty(p);
    else if(dec==1)
        f = tileCornerOut_ur(p, 0.);
    else if(dec==2)
        f = tileCornerOut_ul(p, 0.);
    else if(dec==3)
        f = tileWall_u(p, r);
    else if(dec==4)
        f = tileCornerOut_dr(p, 0.);
    else if(dec==5)
        f = tileWall_r(p, 0.);
    else if(dec==6)
        f = tileJoin_a(p, 0.);
    else if(dec==7)
        f = tileCornerIn_ur(p, 0.);
    else if(dec==8)
        f = tileCornerOut_dl(p, 0.);
    else if(dec==9)
        f = tileJoin_b(p, 0.);
    else if(dec==10)
        f = tileWall_l(p, 0.);
    else if(dec==11)
        f = tileCornerIn_ul(p, 0.);
    else if(dec==12)
        f = tileWall_d(p, 0.);
    else if(dec==13)
        f = tileCornerIn_dr(p, 0.);
    else if(dec==14)
        f = tileCornerIn_dl(p, 0.);
    else if(dec==15)
        f = tileFilled(p);


    return clamp(1.-f, 0., 1.);

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

    uv *= 8.;

    uv.y = 1. - uv.y;

    float scale;
    vec3 bg =
        mix(
            vec3(1.975, 1.43, 1.),
            vec3(1., .4, 1.),
            vec3(0.)
        );

    vec3 RGB = bg;
    vec2 uvb;

    vec2 camPos = vec2(0., 0.);
    vec2 camLook    = vec2(2.*mat_time, 0.);

    vec2 rayDir = (vec2(uv+camLook));

    vec2 v = camPos;
    float nLayers = mat_layers;
    for(float i=0.; i<nLayers; i++) {

        v += rayDir;

        float fTemp = getLand(v.xy, vec2(0., .1*float(i)));

        if(fTemp>0.9) {
            RGB = mix(vec3(fTemp+v.y/4.) * vec3(.9, .0, .1), bg, clamp((i+1.)/nLayers, 0.0, 1.));
            break;
        }

    }

    out_color = vec4(1.-RGB, 1.0);




    
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
