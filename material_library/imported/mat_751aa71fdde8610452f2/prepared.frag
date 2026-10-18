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
uniform vec4 uMMParam007; // native input: mat_container_size
float mat_container_size = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_cube_size
float mat_cube_size = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_corner_size
float mat_corner_size = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_corner_spread
float mat_corner_spread = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_inner_size
float mat_inner_size = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_stretch_x
float mat_stretch_x = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_stretch_y
float mat_stretch_y = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_stretch_z
float mat_stretch_z = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_opacity
float mat_opacity = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_orbit
vec2 mat_orbit = uMMParam016.xy;
uniform vec4 uMMParam017; // native input: mat_orbit_speed
float mat_orbit_speed = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_orbit_bpm_sync
bool mat_orbit_bpm_sync = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_orbit_reverse
bool mat_orbit_reverse = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_orbit_offset
float mat_orbit_offset = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_orbit_offset_scale
float mat_orbit_offset_scale = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_orbit_strob
float mat_orbit_strob = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_orbit_restart
int mat_orbit_restart = int(round(uMMParam023.x));
uniform vec4 uMMParam024; // native input: mat_inside_speed
float mat_inside_speed = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_inside_bpm_sync
bool mat_inside_bpm_sync = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_inside_reverse
bool mat_inside_reverse = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_inside_offset
float mat_inside_offset = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_inside_offset_scale
float mat_inside_offset_scale = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_inside_strob
float mat_inside_strob = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_inside_restart
int mat_inside_restart = int(round(uMMParam030.x));
uniform vec4 uMMParam031; // native input: mat_background
bool mat_background = uMMParam031.x > 0.5;
uniform vec4 uMMParam032; // native input: mat_back_color
vec4 mat_back_color = uMMParam032;
uniform vec4 uMMParam033; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam033.x));
uniform vec4 uMMParam034; // native input: mat_back_thresh
float mat_back_thresh = uMMParam034.x;
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
uniform vec4 uMMParam040; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam040.x > 0.5;
float mat_orbit_time_source = uTDTime * (mat_orbit_speed);
float mat_inside_time_source = uTDTime * (mat_inside_speed);

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

float mat_orbit_time = mat_orbit_time_source - mat_orbit_offset * 8. * mat_orbit_offset_scale;
float mat_inside_time = mat_inside_time_source - mat_inside_offset * 8. * mat_inside_offset_scale;


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

    vec2 uv_shift = mat_shift_amount * mat_shift_scale * 0.5;
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

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
}



vec3 gl1 = vec3(0.);
vec3 gl2 = vec3(0.);
vec3 gl3 = vec3(0.);
vec3 gl4 = vec3(0.);

mat2 r2d(float a){
    float s = sin(a), c = cos(a);
    return mat2(c, s, -s, c);
}

float vma(vec3 v) {
    return max(v.x, max(v.y, v.z)) / (mat_opacity * 4. + 1.);
}


float fBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, vec3(0))) + vma(min(d, vec3(0)));
}

vec2 de(vec3 p) {

    float d = 0.;

    p.xz *= r2d(mat_orbit_time * .5 - mat_orbit.x * 2.);
    p.zy *= r2d(mat_orbit_time * .5 - mat_orbit.y * 2.);

    vec3 q = p;
    vec3 z = p;

    vec2 a = vec2(9999.);
    vec2 b = vec2(9999.);

    float h = .5 * mat_container_size;
    vec3 k = vec3(.2) * mat_corner_size;

    a.x = max ( fBox(p, vec3(h * mat_stretch_x * mat_cube_size + .18, h * mat_stretch_y * mat_cube_size + .18, h * mat_stretch_z * mat_cube_size + .18)), -length(p) + .8);
    a.x = max ( a.x, -fBox(abs(p) - vec3( h * mat_stretch_x, h * mat_stretch_y, h * mat_stretch_z), k));

    gl1+=(0.0004/(0.03+a.x*a.x))*vec3(0,1,1);
    a.y = .5;

    b.x = fBox(abs(p) - vec3( h * mat_stretch_x * mat_corner_spread, h * mat_stretch_y * mat_corner_spread, h * mat_stretch_z * mat_corner_spread), k);
    b.y = .3;
    gl3+=(0.0004/(0.03+b.x*b.x))*vec3(0,1,0);
    a = (a.x < b.x) ? a : b;

    p = q;
    p.xz *= r2d(mat_inside_time * 2.);
    b.x = length(abs(p) - vec3(.5, 0., 0.)) - .2 * mat_inner_size;
    gl4+=(0.0004/(0.03+b.x*b.x))*vec3(0,0,1);
    b.y = .3;
    a = (a.x < b.x) ? a : b;

    p = q;
    p.xy *= r2d(mat_inside_time * 2.);
    b.x = length(abs(p) - vec3(0., .5, 0.)) - .2 * mat_inner_size;
    gl4+=(0.0004/(0.03+b.x*b.x))*vec3(0,0,1);
    b.y = .5;
    a = (a.x < b.x) ? a : b;

    return a;
}

const vec2 e = vec2(.000035, -.000035);
vec3 norm(vec3 po) {
        return normalize(e.yyx*de(po+e.yyx).x + e.yxy*de(po+e.yxy).x +
                         e.xyy*de(po+e.xyy).x + e.xxx*de(po+e.xxx).x);
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    

    vec3 ro = vec3(0., 0., 7.);
    vec3 ta = vec3(0.);

    vec3 vd = normalize(ta - ro);
    vec3 ri = normalize(cross(vd, vec3(.0, 1., 0.)));
    vec3 dw = normalize(cross(ri, vd));
    vec3 rd = normalize(ri * uv.x + dw * uv.y + 3. * vd);

    float t = 0.;
    vec2 h;
    vec3 po = vec3(0.);

    for (int i = 0; i < 64; i++) {
        po = ro + rd * t;
        h = de(po);
        if (h.x < .001) {
            if (h.y == .5) {
                vec3 n = norm(po);
                rd = reflect(rd, n);
                ro = po + n * .01;
                t = .0;
            } else
                if(h.y == .3)
                    h.x = abs(h.x) + .001;
        }
        t += h.x;
    }

    vec3 c = vec3(.1);
    c += gl1 * .7;
    c += gl2 * .9;
    c += gl3 * .5;
    c += gl4 * .9;

    float alpha = 1.;

    
    
    

    out_color = vec4(c, alpha);


    if (mat_background) {
        
        if (mat_back_mode == 1) {
            
            if (mat_luma(out_color.rgb) < mat_back_thresh) {
                out_color = mat_back_color;
            }
        } else {
            
            out_color = mix(mat_back_color, out_color, mat_luma(out_color.rgb) + mat_back_thresh);
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
