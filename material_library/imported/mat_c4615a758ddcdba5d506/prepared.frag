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

uniform vec4 uMMParam000; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam000.x > 0.5;
uniform vec4 uMMParam001; // native input: mat_scale
float mat_scale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_rotate
float mat_rotate = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: mat_shift_scale
float mat_shift_scale = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_shift_type
int mat_shift_type = int(round(uMMParam005.x));
uniform vec4 uMMParam006; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_orbit
vec2 mat_orbit = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_noise_scale
float mat_noise_scale = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_height
float mat_height = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_size1
float mat_size1 = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_size2
float mat_size2 = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_shell
float mat_shell = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_iterations
int mat_iterations = int(round(uMMParam014.x));
uniform vec4 uMMParam015; // native input: mat_a1_enable
bool mat_a1_enable = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_a1_speed
float mat_a1_speed = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_a1_offset
float mat_a1_offset = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_a1_strob
float mat_a1_strob = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam022.x));
uniform vec4 uMMParam023; // native input: mat_a2_enable
bool mat_a2_enable = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_a2_speed
float mat_a2_speed = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_a2_offset
float mat_a2_offset = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_a2_strob
float mat_a2_strob = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_a2_restart
int mat_a2_restart = int(round(uMMParam030.x));
uniform vec4 uMMParam031; // native input: mat_a3_enable
bool mat_a3_enable = uMMParam031.x > 0.5;
uniform vec4 uMMParam032; // native input: mat_a3_speed
float mat_a3_speed = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_a3_bpm_sync
bool mat_a3_bpm_sync = uMMParam033.x > 0.5;
uniform vec4 uMMParam034; // native input: mat_a3_reverse
bool mat_a3_reverse = uMMParam034.x > 0.5;
uniform vec4 uMMParam035; // native input: mat_a3_offset
float mat_a3_offset = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_a3_offset_scale
float mat_a3_offset_scale = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_a3_strob
float mat_a3_strob = uMMParam037.x;
uniform vec4 uMMParam038; // native input: mat_a3_restart
int mat_a3_restart = int(round(uMMParam038.x));
uniform vec4 uMMParam039; // native input: mat_texture
float mat_texture = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_color_cycle
float mat_color_cycle = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_gain
float mat_gain = uMMParam041.x;
uniform vec4 uMMParam042; // native input: mat_brightness
float mat_brightness = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_contrast
float mat_contrast = uMMParam043.x;
uniform vec4 uMMParam044; // native input: mat_saturation
float mat_saturation = uMMParam044.x;
uniform vec4 uMMParam045; // native input: mat_hue_shift
float mat_hue_shift = uMMParam045.x;
uniform vec4 uMMParam046; // native input: mat_invert
bool mat_invert = uMMParam046.x > 0.5;
uniform vec4 uMMParam047; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam047.x > 0.5;
uniform vec4 uMMParam048; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam048.x;
uniform vec4 uMMParam049; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam049.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);
float mat_a3_time_source = uTDTime * (mat_a3_speed);

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

float mat_a1_time = (mat_a1_time_source - mat_a1_offset * 8. * mat_a1_offset_scale) * 2.;
float mat_a2_time = (mat_a2_time_source - mat_a2_offset * 8. * mat_a2_offset_scale) * 2.;
float mat_a3_time = (mat_a3_time_source - mat_a3_offset * 8. * mat_a3_offset_scale) * 2.;

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
}

vec2 flipX(vec2 coord, float multiplier) {
    
    
    vec2 new_coord = coord * multiplier;
    new_coord += vec2(0.5);
    new_coord.x = 1.-new_coord.x;
    new_coord -= vec2(0.5);
    return new_coord;
}

vec2 flipY(vec2 coord, float multiplier) {
    
    
    vec2 new_coord = coord * multiplier;
    new_coord += vec2(0.5);
    new_coord.y = 1.-new_coord.y;
    new_coord -= vec2(0.5);
    return new_coord;
}

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


#define thc(a,b) tanh(a*cos(b))/tanh(a)
#define ths(a,b) tanh(a*sin(b))/tanh(a)
#define sabs(x) sqrt(x*x+1e-2)

vec3 pal( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d )
{
    return a + b*cos( 6.28318*(c*t+d) );
}

float h21 (vec2 a) {
    return fract(sin(dot(a.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float mlength(vec2 uv) {
    return max(abs(uv.x), abs(uv.y));
}

float mlength(vec3 uv) {
    return max(max(abs(uv.x), abs(uv.y)), abs(uv.z));
}


float smin(float a, float b)
{
    float k = 0.12;
    float h = clamp(0.5 + 0.5 * (b-a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}












#define MAX_DIST 10.
#define SURF_DIST .001




#define S smoothstep


mat2 Rot(float a) {
    float s=sin(a), c=cos(a);
    return mat2(c, -s, s, c);
}

float sdBox(vec3 p, vec3 s) {
    p = abs(p)-s;
    return length(max(p, 0.))+min(max(p.x, max(p.y, p.z)), 0.);
}


float sdBox(vec4 p, vec4 s) {
    p = abs(p)-s;
    return length(max(p, 0.))+min( max(max(p.x, p.y), max(p.z, p.w)), 0. );
}

float shape(vec4 q) {
    float as = 2. * mat_noise_scale;
    float ls = 0.5;
    float t = 0.5;
    
    
    
    float m = 1.;
    
    for (int i = 0; i<5; i++) {
        q.w = sabs(q.w) - m;
        m *= 0.5 * mat_shell;
    }

    float a1_time = 0;
    float a2_time = 0;
    float a3_time = 0;
    if (mat_a1_enable) {
        a1_time = mat_a1_time;
    }
    if (mat_a2_enable) {
        a2_time = mat_a2_time;
    }
    if (mat_a3_enable) {
        a3_time = mat_a3_time;
    }

    q.xy *= Rot(as * smin(q.w, q.z) + t * a2_time);
    q.yz *= Rot(as * smin(q.x, q.w) + t * a1_time);
    q.zw *= Rot(as * smin(q.y, q.x) + t * a1_time);
    q.wx *= Rot(as * smin(q.z, q.y) + t * a1_time);

    
    





    



    float b = 0.5 - 0.5 * thc(4., 0.5 * q.w + 0.25 * a3_time);

    float m1 = mix(0.2, 0.4, b) * mat_height;
    float m2 = mix(0.7, 0.1, b) * mat_size1;
    float d = sdBox(q / mat_size2, vec4(m1)) - m2;
    return d;
}

float GetDist(vec3 p) {
    float w = length(p) * 2. + 0.25 * mat_a1_time;

    
    
    float center = floor(w) + 0.5;
   

    vec4 q = vec4(p, w);
    

    float me = shape(q - vec4(0,0,0,center));
    
    float d = me;

    float d2 = length(p) - 1.;
   
    
    return 0.7 * d;
}

float RayMarch(vec3 ro, vec3 rd, float z) {
    float dO=0.;

    for(int i=0; i<mat_iterations; i++) {
        vec3 p = ro + rd*dO;
        float dS = z * GetDist(p);
        dO += dS;
        if(dO>MAX_DIST || abs(dS)<SURF_DIST) break;
    }

    return dO;
}

vec3 GetNormal(vec3 p) {
    float d = GetDist(p);
    vec2 e = vec2(.001, 0);

    vec3 n = d - vec3(
        GetDist(p-e.xyy),
        GetDist(p-e.yxy),
        GetDist(p-e.yyx));

    return normalize(n);
}

vec3 GetRayDir(vec2 uv, vec3 p, vec3 l, float z) {
    vec3 f = normalize(l-p),
        r = normalize(cross(vec3(0,1,0), f)),
        u = cross(f,r),
        c = f*z,
        i = c + uv.x*r + uv.y*u,
        d = normalize(i);
    return d;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 m = mat_orbit;

    vec3 ro = vec3(0, 3, -3);
    ro.yz *= Rot(-m.y*3.14+1.);
    ro.xz *= Rot(-m.x*6.2831);
    

    vec3 rd = GetRayDir(uv, ro, vec3(0,0.,0), 1.8);
    vec3 col = vec3(0);

    float d = RayMarch(ro, rd, 1.);

    float IOR = 1.05 ;
    if(d<MAX_DIST) {
        vec3 p = ro + rd * d;
        vec3 n = GetNormal(p);
        vec3 r = reflect(rd, n);

        float dif = dot(n, normalize(vec3(1,2,3)))*.5+.5;
        col = vec3(dif);

        vec3 rdIn = refract(rd, n, 1./IOR);

        vec3 pEnter = p - n*SURF_DIST*30.;
        float dIn = RayMarch(pEnter, rdIn, -1.); 

        vec3 pExit = pEnter + rdIn * dIn; 
        vec3 nExit = -GetNormal(pExit);

        float fresnel = pow(1.+dot(rd, n), 3.);
        col = 2.5 * vec3(fresnel);
        col *= 0.55 + 0.45 * cross(nExit, n) * mat_texture;
        
        col = clamp(col, 0., 1.);
       
       vec3 e = vec3(1.);
        col *= (p.y + 0.95) * pal(1., e, e, e, vec3(0.,0.33,0.66) * mat_color_cycle); 
        col *= 0.6 + 0.4 * n.y;
    }

    col = pow(col, vec3(.4545 / pow(mat_gain, 2.)));    
    
    out_color = vec4(col,1.0);


    
    if (mat_luma_to_alpha && mat_luma_mode == 0) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
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

    
    if (mat_luma_to_alpha && mat_luma_mode == 1) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
