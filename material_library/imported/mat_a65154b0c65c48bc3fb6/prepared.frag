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
uniform vec4 uMMParam003; // native input: mat_shift_scale
float mat_shift_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_shift_type
int mat_shift_type = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_iterations
int mat_iterations = int(round(uMMParam007.x));
uniform vec4 uMMParam008; // native input: mat_fill
float mat_fill = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_level
float mat_level = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_speed
float mat_speed = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_reverse
bool mat_reverse = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_offset
float mat_offset = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_offset_scale
float mat_offset_scale = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_strob
float mat_strob = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_restart
int mat_restart = int(round(uMMParam016.x));
uniform vec4 uMMParam017; // native input: mat_travel_speed
float mat_travel_speed = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_travel_bpm_sync
bool mat_travel_bpm_sync = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_travel_reverse
bool mat_travel_reverse = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_travel_offset
float mat_travel_offset = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_travel_offset_scale
float mat_travel_offset_scale = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_travel_strob
float mat_travel_strob = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_travel_restart
int mat_travel_restart = int(round(uMMParam023.x));
uniform vec4 uMMParam024; // native input: mat_cam_speed
float mat_cam_speed = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_cam_bpm_sync
bool mat_cam_bpm_sync = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_cam_reverse
bool mat_cam_reverse = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_cam_offset
float mat_cam_offset = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_cam_offset_scale
float mat_cam_offset_scale = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_cam_strob
float mat_cam_strob = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_cam_restart
int mat_cam_restart = int(round(uMMParam030.x));
uniform vec4 uMMParam031; // native input: mat_alpha
bool mat_alpha = uMMParam031.x > 0.5;
uniform vec4 uMMParam032; // native input: mat_brightness
float mat_brightness = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_contrast
float mat_contrast = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_saturation
float mat_saturation = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_hue_shift
float mat_hue_shift = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_invert
bool mat_invert = uMMParam036.x > 0.5;
uniform vec4 uMMParam037; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam037.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_cam_time_source = uTDTime * (mat_cam_speed);
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
float mat_cam_time = mat_cam_time_source - mat_cam_offset * 8. * mat_cam_offset_scale;
float mat_travel_time = mat_travel_time_source - mat_travel_offset * 8. * mat_travel_offset_scale;

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
    uv *= mat_scale;

    uv = mirrorUV(uv);

    vec2 uv_shift = mat_shift_amount * mat_shift_scale;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    if (mat_shift_type == 0) {

        
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
        uv += uv_shift;
    }

    return uv;
}









#define TAU 2*PI


mat2 rz2 (float a) { float c=cos(a), s=sin(a); return mat2(c,s,-s,c); }
float sphere (vec3 p, float r) { return length(p)-r; }
float iso (vec3 p, float r) { return dot(p, normalize(sign(p)))-r; }
float cyl (vec2 p, float r) { return length(p)-r; }
float cube (vec3 p, vec3 r) { return length(max(abs(p)-r,0.)); }
vec2 modA (vec2 p, float count) {
    float an = TAU/count;
    float a = atan(p.y,p.x)+an*.5;
    a = mod(a, an)-an*.5;
    return vec2(cos(a),sin(a))*length(p);
}
float smin (float a, float b, float r)
{
    float h = clamp(.5+.5*(b-a)/r,0.,1.);
    return mix(b, a, h) - r*h*(1.-h);
}

float map (vec3 p)
{
    float sph3 = sphere(p, 3.);
    p.yz *= rz2(mat_cam_time*.2);
    p.xy *= rz2(mat_cam_time*.3);

    float d = length(p);

    float a = atan(p.y,p.x);
    float l = length(p.xy)-2.;
    p.xy = vec2(l,a);

    float as = PI*0.3;
    p.z += sin(a*2.+sin(l*4.))*.5;

    float wave1 = sin(p.y*6.)*.5+.5;
    float wave2 = .5+.5*sin(p.z*3.+mat_time);

    p.x -= sin(p.z*1.+mat_travel_time)*.5;
    p.z = mod(p.z+mat_travel_time,as)-as*.5;

    float sphR = .2-.1*wave1;
    float sphC = .3;
    float sphN = 0.2;
    float sph1 = sphere(vec3(p.x,mod(sphN*p.y/TAU+mat_time*.1,sphC)-sphC*.5,p.z), sphR);

    p.xz *= rz2(p.y*3.);
    p.xz = modA(p.xz, 3.);
    p.x -= 0.3*wave2;
    float cyl1 = cyl(p.xz, 0.02) / mat_fill;
    float sph2 = sphere(vec3(p.x,mod(p.y*2.-mat_time,1.)-.5,p.z), .1);

    return smin(sph1, smin(cyl1,sph2,.2), .2);
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    vec3 ro = vec3(uv,-5), rp = vec3(uv,1), mp = ro;
    int i = 0;
    int count = mat_iterations;
    for(;i<count;++i) {
        float md = map(mp);
        if (md < 0.001) {
            break;
        }
        mp += rp*md*.35;
    }
    float r = float(i)/float(count);
    out_color = vec4(1);
    out_color *= smoothstep(.0,10.,length(mp-ro) / mat_level);
    out_color *= r;
    out_color = 1. - out_color;
    if (!mat_alpha) {
        out_color.a = 1.;
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
