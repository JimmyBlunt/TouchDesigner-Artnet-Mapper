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
uniform vec4 uMMParam009; // native input: mat_orbit_scale
float mat_orbit_scale = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_dist1
float mat_dist1 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_dist2
float mat_dist2 = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_fill1
float mat_fill1 = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_fill2
float mat_fill2 = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_iterations
int mat_iterations = int(round(uMMParam014.x));
uniform vec4 uMMParam015; // native input: mat_surface
float mat_surface = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_grid_scale
float mat_grid_scale = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_grid2_scale
float mat_grid2_scale = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_light_offset
float mat_light_offset = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_light_pow
float mat_light_pow = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_shadow
float mat_shadow = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_a1_mode
int mat_a1_mode = int(round(uMMParam021.x));
uniform vec4 uMMParam022; // native input: mat_a1_range
float mat_a1_range = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_a1_speed
float mat_a1_speed = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam024.x > 0.5;
uniform vec4 uMMParam025; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_a1_offset
float mat_a1_offset = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_a1_strob
float mat_a1_strob = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam029.x));
uniform vec4 uMMParam030; // native input: mat_a2_speed
float mat_a2_speed = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam031.x > 0.5;
uniform vec4 uMMParam032; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam032.x > 0.5;
uniform vec4 uMMParam033; // native input: mat_a2_offset
float mat_a2_offset = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_a2_strob
float mat_a2_strob = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_a2_restart
int mat_a2_restart = int(round(uMMParam036.x));
uniform vec4 uMMParam037; // native input: mat_back_level
float mat_back_level = uMMParam037.x;
uniform vec4 uMMParam038; // native input: mat_back_color1
vec4 mat_back_color1 = uMMParam038;
uniform vec4 uMMParam039; // native input: mat_back_color2
vec4 mat_back_color2 = uMMParam039;
uniform vec4 uMMParam040; // native input: mat_brightness
float mat_brightness = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_contrast
float mat_contrast = uMMParam041.x;
uniform vec4 uMMParam042; // native input: mat_saturation
float mat_saturation = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_hue_shift
float mat_hue_shift = uMMParam043.x;
uniform vec4 uMMParam044; // native input: mat_invert
bool mat_invert = uMMParam044.x > 0.5;
uniform vec4 uMMParam045; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam045.x > 0.5;
uniform vec4 uMMParam046; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam046.x;
uniform vec4 uMMParam047; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam047.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);
#define iChannel0 sTDCubeInputs[0]

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

















#define TAU (2.*PI)
#define SIN(x) (sin(x)*.5+.5)
#define BUMP_EPS 0.004


float g_mat;
vec2 g_uv;


struct ObjectInfo {
    float t;
    float mat;
    vec2 uv;
};


mat2 rot(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }











vec3 bump3y (vec3 x, vec3 yoffset)
{
    vec3 y = 1. - x * x;
    y = clamp((y-yoffset), vec3(0), vec3(1));
    return y;
}

const float NOISE_GRANULARITY = 0.5/255.0;

float random(vec2 coords) {
   return fract(sin(dot(coords.xy, vec2(12.9898,78.233))) * 43758.5453);
}

vec3 invGamma(vec3 col) {
    return pow(col, vec3(2.2));
}

vec3 gamma(vec3 col) {
    return pow(col, vec3(1./2.2));
}

vec3 spectralZucconi6(float x) {
    const vec3 c1 = vec3(3.54585104, 2.93225262, 2.41593945);
    const vec3 x1 = vec3(0.69549072, 0.49228336, 0.27699880);
    const vec3 y1 = vec3(0.02312639, 0.15225084, 0.52607955);

    const vec3 c2 = vec3(3.90307140, 3.21182957, 3.96587128);
    const vec3 x2 = vec3(0.11748627, 0.86755042, 0.66077860);
    const vec3 y2 = vec3(0.84897130, 0.88445281, 0.73949448);

    vec3 col =  bump3y(c1 * (x - x1), y1) + bump3y(c2 * (x - x2), y2);
    col = invGamma(col);
    return col;
}


vec3 wrappedSpectralZucconi6(float x) {
    x = fract(x);
    return spectralZucconi6(x);
}


vec3 waveZucconi6(float w) {

    if(w > 700.0 || w < 400.0){
        return vec3(0);
    }

    float x = fract((w - 400.0)/ 300.0);

    return spectralZucconi6(x);
}

float rect( vec2 p, vec2 b, float r ) {
    vec2 d = abs(p) - (b - r);
    return length(max(d, 0.)) + min(max(d.x, d.y), 0.) - r;
}





void pixarONB(vec3 n, out vec3 b1, out vec3 b2){
    float sign_ = sign(n.z);
    float a = -1.0 / (sign_ + n.z);
    float b = n.x * n.y * a;
    b1 = vec3(1.0 + sign_ * n.x * n.x * a, sign_ * b, -sign_ * n.x);
    b2 = vec3(b, sign_ + n.y * n.y * a, -n.y);
}

vec3 diffraction(vec3 rd, vec3 n, vec3 td, vec3 l, float d) {

    vec3 col = vec3(0);

    float cos_ThetaL = dot(l, td);
    float cos_ThetaV = dot(rd, td);

    float u = abs(cos_ThetaL - cos_ThetaV);

    if(u == 0.) {
        return vec3(0);
    }

    for(float i=1.; i < 2.; i++) {
        float wavelength = u * d / i;
        col += waveZucconi6(wavelength);
    }
    col = clamp(col, vec3(0), vec3(1));
    return col;
}


float sdBoxFrame( vec3 p, vec3 b, float e ){

  p = abs(p)-b;
  vec3 q = abs(p+e)-e;
  return min(min(
      length(max(vec3(p.x,q.y,q.z),0.0))+min(max(p.x,max(q.y,q.z)),0.0),
      length(max(vec3(q.x,p.y,q.z),0.0))+min(max(q.x,max(p.y,q.z)),0.0)),
      length(max(vec3(q.x,q.y,p.z),0.0))+min(max(q.x,max(q.y,p.z)),0.0));
}


float box(vec3 p, vec3 r) {
  vec3 d = abs(p) - r;
  return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}


vec3 transform(vec3 p) {

    float spin;

    if (mat_a1_mode == 0) { 
        spin = mat_a1_range * sin(0.25*mat_a1_time);
    } else { 
        spin = 0.25*mat_a1_time;
    }

    vec2 orbit = flipX(mat_orbit, mat_orbit_scale * 0.25);

    p.z -= 5.;

    p.yz *= rot(.3*PI*spin);

    p.xz += vec2(0.5);
    p.xz = matRot2D(p.xz, -2*PI*orbit.x);
    p.xz -= vec2(0.5);

    p.yz += vec2(0.5);
    p.yz = matRot2D(p.yz, -2*PI*orbit.y);
    p.yz -= vec2(0.5);

    p.yx *= rot(PI*.25 );

    
    
    
    
    return p;
}


vec2 torusUV(vec3 p) {
    float a = atan(p.z, p.x);
    float r = length(p.zx);

    return vec2(r, a);
}


vec2 cubeUV(in vec3 p) {
    vec2 x = p.zy/p.x;
    vec2 y = p.xz/p.y;
    vec2 z = p.xy/p.z;

    
    p = abs(p);
    if (p.x > p.y && p.x > p.z) return x;
    else if (p.y > p.x && p.y > p.z) return y;
    else return z;
}

float map(vec3 p) {

    vec3 bp = p;
    float edge = 0.005;

    p = transform(p);

    vec3 p1 = abs(p)- mix(.0, 1.9 * mat_dist1, SIN(0.5*mat_a2_time));
    float f1 = sdBoxFrame(p1, vec3(1.0), .15 * mat_fill1)-edge;

    vec3 p2 = abs(p)- mix(.0, 1.9*2. * mat_dist2, SIN(.25*mat_a2_time))-edge;
    float f2 = sdBoxFrame(p2, vec3(1.+.5*SIN(.25*mat_a2_time)), .15 * mat_fill2)*.75;

    g_uv = f1 < f2 ? cubeUV(p1) : cubeUV(p2);  

    float d = min(f1, f2);
    return d;

}


vec3 getNormal(vec3 p) {

    vec2 eps = vec2(0.001, 0.0);
    return normalize(vec3(map(p + eps.xyy) - map(p - eps.xyy),
                          map(p + eps.yxy) - map(p - eps.yxy),
                          map(p + eps.yyx) - map(p - eps.yyx)
                         )
                     );
}


float gridSurface( in vec3 p){
    p = abs(mod(p*2., 1.*0.125 * mat_grid_scale)-0.0125);

    float x = min(p.x,min(p.z, p.y))/0.03125;

    return clamp(x, 0., 1.);
}


vec3 doBumpMap(in vec3 p, in vec3 nor, float bumpfactor){

    const float eps = BUMP_EPS;
    float ref = gridSurface(p);
    vec3 grad = vec3( gridSurface(vec3(p.x-eps, p.y, p.z))-ref,
                      gridSurface(vec3(p.x, p.y-eps, p.z))-ref,
                      gridSurface(vec3(p.x, p.y, p.z-eps))-ref )/eps;

    grad -= nor*dot(nor, grad);

    return normalize( nor + bumpfactor*grad ) * mat_surface;

}


float softshadow( in vec3 ro, in vec3 rd, float mint, float maxt, float k )
{
    float res = 1.0;
    float ph = 1e20;
    for( float t=mint; t<maxt; )
    {
        float h = map(ro + rd*t);
        if( h<0.001 )
            return 0.0;
        float y = h*h/(2.0*ph);
        float d = sqrt(h*h-y*y);
        res = min( res, k*d/max(0.0,t-y) );
        ph = h;
        t += h;
    }
    return res;
}

ObjectInfo raymarch(vec3 ro, vec3 rd, float steps) {

    float mat = 0.,
          t   = 0.,
          d   = 0.;

    vec2 uv; 

    vec3 p = ro;
    for(float i=.0; i<steps; i++) {

        d = map(p);
        mat = g_mat;  
        uv = g_uv;

        if(abs(d) < 0.0001 || t > 100.) break;

        t += d;
        p += rd*d;
    }

    return ObjectInfo(t, mat, uv);
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec3 ro = vec3(uv*9.,-4.),      
         rd = vec3(0,0,1.),         
         lp = vec3(3., 4., -4) * mat_light_offset,
         lp2 = vec3(-3., -4., -2);
    vec3 col;

    float mat = 0.,
          t   = 0.,
          d   = 0.;
    vec2 e = vec2(0.0035, -0.0035);

    
    
    

    vec3 c1 = mat_back_color1.rgb;
    vec3 c2 = mat_back_color2.rgb;

    c1 *= mat_back_level;
    c2 *= mat_back_level;

    float steps = float(mat_iterations);
    ObjectInfo objectInfo = raymarch(ro, rd, steps);
    mat = objectInfo.mat;
    vec3 p = ro + objectInfo.t*rd;
    vec3 n = normalize(e.xyy*map(p+e.xyy) + e.yyx*map(p+e.yyx) +
                       e.yxy*map(p+e.yxy) + e.xxx*map(p+e.xxx));
    vec2 tuv = objectInfo.uv;
    n = doBumpMap(vec3(tuv*.5, 0.), n, .009);
    if(objectInfo.t < 50.) {
        vec3 l = normalize(lp-p);
        vec3 l2 = normalize(lp2-p);
        float dif = max(dot(n, l), .0);
        float dif2 = max(dot(n, l2), .0);
        float spe = pow(max(dot(reflect(-rd, n), -l), .0),40. * mat_shadow);
        float shd = softshadow(p, l2, 0.1, 50., 5.0) * mat_light_pow;
        float sss = smoothstep(0., 1., map(p + l * .4)) / .4;
        float height = atan(n.y, n.x);
        
        vec3 iri = spectralZucconi6(height*1.11)*smoothstep(.8, .2, abs(n.z))-.08 * mat_shadow;
        
        vec3 tangent;
        vec3 bitangent;
        pixarONB(n, tangent, bitangent);
        tangent = normalize(tangent);
        bitangent = normalize(bitangent);

        mat3 tbn = mat3(tangent, bitangent, n);
        vec3 td = normalize(tbn * vec3(tuv, 0.));

        l = normalize(vec3(0, 1, 0));
        vec3 difr = diffraction(-rd, n, td, l, 780.); 
        col += .5*(c1*dif + c2*dif2)+ 1.8*difr + .9*iri + .4*sss + .2;
        float grids = 60. * mat_grid2_scale;
        vec2 grid = smoothstep(.0, .1, SIN(grids*(tuv+.5)));
        col *= dot(grid, vec2(.5));

        if(mat == 0.) {
            vec3 refld = reflect(ro, n);
            vec3 refl = texture(iChannel0,refld).rgb;

            refl = invGamma(refl);
            col = mix(col, refl, .5);
        }
        col *= 1.3; 

        
        float t = objectInfo.t;
        float fog = 1.-exp(-t*t*0.005);

        col = mix(col, c1, fog);
        col = mix(col, col*shd, .7);
    } else {
        col =  mix(c1, c2, (pow(dot(uv, uv), .8)))*.9; 
        col = invGamma(col);
    }

    col += mix(-NOISE_GRANULARITY, NOISE_GRANULARITY, random(uv)); 
    col *= mix(.2, 1., (1.5-pow(dot(uv, uv), .5))); 
    col = gamma(col); 

    out_color = vec4(col, 1.0);


    
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
