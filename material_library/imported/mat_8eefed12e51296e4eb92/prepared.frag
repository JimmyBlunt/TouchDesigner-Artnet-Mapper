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
uniform vec4 uMMParam008; // native input: mat_shape_scale
float mat_shape_scale = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_complexity
float mat_complexity = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_complexity_sensitivity
float mat_complexity_sensitivity = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_twist
float mat_twist = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_petals
int mat_petals = int(round(uMMParam012.x));
uniform vec4 uMMParam013; // native input: mat_erode
int mat_erode = int(round(uMMParam013.x));
uniform vec4 uMMParam014; // native input: mat_height1
float mat_height1 = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_height2
float mat_height2 = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_edge
float mat_edge = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_distort1
float mat_distort1 = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_distort2
float mat_distort2 = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_distort3
float mat_distort3 = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_cycle1
float mat_cycle1 = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_cycle2
float mat_cycle2 = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_cycle3
float mat_cycle3 = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_detail
float mat_detail = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_speed
float mat_speed = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_reverse
bool mat_reverse = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_offset
float mat_offset = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_offset_scale
float mat_offset_scale = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_strob
float mat_strob = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_restart
int mat_restart = int(round(uMMParam030.x));
uniform vec4 uMMParam031; // native input: mat_light_pwr
float mat_light_pwr = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_light_dist
float mat_light_dist = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_light_angle
float mat_light_angle = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_background
float mat_background = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_animate_lighting
bool mat_animate_lighting = uMMParam035.x > 0.5;
uniform vec4 uMMParam036; // native input: mat_lighting_range
vec2 mat_lighting_range = uMMParam036.xy;
uniform vec4 uMMParam037; // native input: mat_lighting_signal
int mat_lighting_signal = int(round(uMMParam037.x));
uniform vec4 uMMParam038; // native input: mat_lighting_filter
int mat_lighting_filter = int(round(uMMParam038.x));
uniform vec4 uMMParam039; // native input: mat_lighting_curve
float mat_lighting_curve = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_lighting_speed
float mat_lighting_speed = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_lighting_bpm_sync
bool mat_lighting_bpm_sync = uMMParam041.x > 0.5;
uniform vec4 uMMParam042; // native input: mat_lighting_reverse
bool mat_lighting_reverse = uMMParam042.x > 0.5;
uniform vec4 uMMParam043; // native input: mat_lighting_offset
float mat_lighting_offset = uMMParam043.x;
uniform vec4 uMMParam044; // native input: mat_lighting_strob
float mat_lighting_strob = uMMParam044.x;
uniform vec4 uMMParam045; // native input: mat_lighting_restart
int mat_lighting_restart = int(round(uMMParam045.x));
uniform vec4 uMMParam046; // native input: mat_light1_pwr
float mat_light1_pwr = uMMParam046.x;
uniform vec4 uMMParam047; // native input: mat_light1_dist
float mat_light1_dist = uMMParam047.x;
uniform vec4 uMMParam048; // native input: mat_light1_angle
float mat_light1_angle = uMMParam048.x;
uniform vec4 uMMParam049; // native input: mat_light1_hue
float mat_light1_hue = uMMParam049.x;
uniform vec4 uMMParam050; // native input: mat_light2_pwr
float mat_light2_pwr = uMMParam050.x;
uniform vec4 uMMParam051; // native input: mat_light2_dist
float mat_light2_dist = uMMParam051.x;
uniform vec4 uMMParam052; // native input: mat_light2_angle
float mat_light2_angle = uMMParam052.x;
uniform vec4 uMMParam053; // native input: mat_light2_hue
float mat_light2_hue = uMMParam053.x;
uniform vec4 uMMParam054; // native input: mat_glow1
float mat_glow1 = uMMParam054.x;
uniform vec4 uMMParam055; // native input: mat_glow2
float mat_glow2 = uMMParam055.x;
uniform vec4 uMMParam056; // native input: mat_glow3
float mat_glow3 = uMMParam056.x;
uniform vec4 uMMParam057; // native input: mat_glow_hue
float mat_glow_hue = uMMParam057.x;
uniform vec4 uMMParam058; // native input: mat_brightness
float mat_brightness = uMMParam058.x;
uniform vec4 uMMParam059; // native input: mat_contrast
float mat_contrast = uMMParam059.x;
uniform vec4 uMMParam060; // native input: mat_saturation
float mat_saturation = uMMParam060.x;
uniform vec4 uMMParam061; // native input: mat_hue_shift
float mat_hue_shift = uMMParam061.x;
uniform vec4 uMMParam062; // native input: mat_invert
bool mat_invert = uMMParam062.x > 0.5;
uniform vec4 uMMParam063; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam063.x > 0.5;
uniform vec4 uMMParam064; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam064.x;
uniform vec4 uMMParam065; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam065.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
float mat_time_source = uTDTime * (mat_speed);
float mat_lighting_time_source = uTDTime * (mat_lighting_speed);

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

float mat_time = (mat_time_source - mat_offset * 32. * mat_offset_scale) * 4.;
float mat_lighting_time = fract((mat_lighting_time_source * 0.125  - mat_lighting_offset));

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
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
    uv *= mat_scale * 2.5;


    uv = mirrorUV(uv);

    vec2 uv_shift = mat_shift_amount * mat_shift_scale;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    if (mat_shift_type == 0) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, -1. * 2*PI*(mat_rotate + 180.) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*(mat_rotate + 180.) / 360);
    uv -= vec2(0.5);

    
    if (mat_shift_type == 1) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate + 180.) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    
    

    return uv;
}

vec3 applyHue(vec3 color, float hue, float saturation) {
    
    if (hue > 0.01 || saturation != 0) {
        vec3 hsv = rgb2hsv(color.rgb);
        hsv.x = fract(0.9999999*(hsv.x+hue));
        hsv.y = max(hsv.y + saturation, 0);
        color.rgb = hsv2rgb(hsv);
    }
    return color;
}



float matEaseInOut(float t, float curve) {
    
    if (t < 0.5) {
        return pow(2 * t, curve) / 2.;
    } else {
        return 1. - pow(-2. * t + 2, curve) / 2.;
    }
}

float matEaseIn(float t, float curve) {
    
    return pow(t, curve);
}

float matEaseOut(float t, float curve) {
    
    return 1. - pow(1. - t, curve);
}

float matEaseOutIn(float t, float curve) {
    
    
    return (pow(t, 3.) - 2. * pow(t, 2.) + t) * curve + (-2. * pow(t,3.) + 3. * pow(t, 2.)) + (pow(t, 3.) - pow(t, 2.)) * curve;
}


float matFilter(float t, int filter_type, float curve) {
    

    if (filter_type == 0) { 
        return matEaseIn(t, curve);
    } else if (filter_type == 1) { 
        return matEaseOut(t, curve);
    } else if (filter_type == 2) { 
        return matEaseInOut(t, curve);
    } else { 
        return matEaseOutIn(t, curve);
    }
}













#define PI_2        (0.5*PI)
#define TAU         (2.0*PI)
#define ROT(a)      mat2(cos(a), sin(a), -sin(a), cos(a))


#if defined(FASTATAN)
#define ATAN atan_approx
#else
#define ATAN atan
#endif

const float hf = 0.015;


const vec4 hsv2rgb_K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);






#define HSV2RGB(c)  (c.z * mix(hsv2rgb_K.xxx, clamp(abs(fract(c.xxx + hsv2rgb_K.xyz) * 6.0 - hsv2rgb_K.www) - hsv2rgb_K.xxx, 0.0, 1.0), c.y))


vec3 sRGB(vec3 t) {
  return mix(1.055*pow(t, vec3(1./2.4)) - 0.055, 12.92*t, step(t, vec3(0.0031308)));
}


vec3 aces_approx(vec3 v) {
  v = max(v, 0.0);
  v *= 0.6f;
  float a = 2.51f;
  float b = 0.03f;
  float c = 2.43f;
  float d = 0.59f;
  float e = 0.14f;
  return clamp((v*(a*v+b))/(v*(c*v+d)+e), 0.0f, 1.0f) * pow(mat_glow1, 2.);
}


float tanh_approx(float x) {

  float x2 = x*x;
  return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0) * mat_cycle2;
}


float atan_approx(float y, float x) {
  float cosatan2 = x / (abs(x) + abs(y));
  float t = PI_2 - cosatan2 * PI_2;
  return y < 0.0 ? -t : t;
}


float pmin(float a, float b, float k) {
  float h = clamp(0.5+0.5*(b-a)/k, 0.0, 1.0);
  return (mix(b, a, h) * mat_distort3 - k*h*(1.0-h) * pow(mat_edge,3.));
}

float pabs(float a, float k) {
  return -pmin(a, -a, k) * mat_cycle1;
}

float height(vec2 p) {

  float tm = mat_time;
  const float xm = 0.5*0.005123;
  float ym = mix(0.125, 0.25, 0.5-0.5*cos(TAU*mat_time/600.0));

  p *= 0.4 * mat_shape_scale;

  float d = length(p);
  float c = 1E6;
  float x = pow(d, 0.1);
  float y = (mat_petals/2*ATAN(p.x, p.y)+0.05*tm-2.0*d * pow(mat_twist,1.5)) / TAU;

  for (float i = 0.; i < int(mat_erode); ++i) {
    float v = length(fract(vec2(x * pow(mat_complexity,0.25 * mat_complexity_sensitivity) - tm*i*xm, fract(y + i*ym)*.5)*20.)*2.-1.) * mat_distort2;
    c = pmin(c, v, 0.125) * mat_distort1;
  }

  float h =  (-hf*mat_cycle3+hf*(pabs(tanh_approx(5.5*d-80.*c*c*d*d*(mat_height2*.55-d))-0.25*d*mat_background, 0.25)));

  return h * pow(mat_height1,1.5);
}

vec3 normal(vec2 p) {
  vec2 e = vec2(4.0/(mat_detail * 2000.), 0);

  vec3 n;
  n.x = height(p + e.xy) - height(p - e.xy);
  n.y = -2.0*e.x;
  n.z = height(p + e.yx) - height(p - e.yx);

  return normalize(n);
}

vec3 color(vec2 p) {
  const float ss = 1.25;
  const float hh = 1.95;

  
  float lighting_time = 0.;

  if (mat_animate_lighting) {

      if (mat_lighting_signal == 0) { 
          lighting_time = mat_lighting_time;
      } else if (mat_lighting_signal == 1) { 
          lighting_time = 1. - mat_lighting_time;
      } else if (mat_lighting_signal == 2) { 
          lighting_time = floor(mat_lighting_time + 0.5);
      } else if (mat_lighting_signal == 3) { 
          lighting_time = 1. - floor(mat_lighting_time + 0.5);
      } else if (mat_lighting_signal == 4) { 
          lighting_time = abs(0.5 - mat_lighting_time);
      } else { 
          lighting_time = 0.5 + 0.5 * sin(2. * PI * mat_lighting_time);
      }

      lighting_time = 1. - lighting_time;
      lighting_time = matFilter(lighting_time, mat_lighting_filter, mat_lighting_curve);
      float range_min = mat_lighting_range[0];
      float range_max = mat_lighting_range[1];
      lighting_time = range_min + lighting_time * (range_max - range_min);

  }

  lighting_time *= 360.;


  vec2 lp1c = vec2(0., 0.);
  vec2 lp2c = vec2(0., 0.);

  lp1c = matRot2D(lp1c, 2*PI*(-mat_light1_angle - mat_light_angle - 135. - lighting_time) / 360);
  lp2c = matRot2D(lp2c, 2*PI*(-mat_light2_angle - mat_light_angle - 135. - lighting_time) / 360);

  lp1c = (lp1c - 0.5) * 2.;
  lp2c = (lp2c - 0.5) * 2.;

  vec3 lp1 = -vec3(lp1c.x, hh, lp1c.y)*vec3(ss, 1.0, ss) * mat_light1_dist * mat_light_dist;
  vec3 lp2 = -vec3(lp2c.x, hh, lp2c.y)*vec3(ss, 1.0, ss) * mat_light2_dist * mat_light_dist;

  vec3 light1_color = vec3(0.30, 0.35, 2.0);
  vec3 light2_color = vec3(0.57, 0.6 , 2.0);
  vec3 glow_color = vec3(0.55, 0.9, 0.05);

  light1_color = applyHue(light1_color, mat_light1_hue, 0.);
  light2_color = applyHue(light2_color, mat_light2_hue, 0.);
  glow_color = applyHue(glow_color, mat_glow_hue, 0.);

  vec3 lcol1 = HSV2RGB(light1_color) * mat_light1_pwr * mat_light_pwr;
  vec3 lcol2 = HSV2RGB(light2_color) * mat_light2_pwr * mat_light_pwr;
  vec3 mat   = HSV2RGB(glow_color) * pow(mat_glow3, 2.);

  
  
  
  float spe  = 16.0 / mat_glow2;

  float h = height(p);
  vec3  n = normal(p);

  vec3 ro = vec3(0.0, 8.0, 0.0);
  vec3 pp = vec3(p.x, 0.0, p.y);

  vec3 po = vec3(p.x, 0.0, p.y);
  vec3 rd = normalize(ro - po);

  vec3 ld1 = normalize(lp1 - po);
  vec3 ld2 = normalize(lp2 - po);

  float diff1 = max(dot(n, ld1), 0.0);
  float diff2 = max(dot(n, ld2), 0.0);

  vec3  rn    = n;
  vec3  ref   = reflect(rd, rn);
  float ref1  = max(dot(ref, ld1), 0.0);
  float ref2  = max(dot(ref, ld2), 0.0);

  float dm = tanh_approx(abs(h)*120.0);
  float rm = dm;
  dm *= dm;

  vec3 lpow1 = dm*mat*lcol1;
  vec3 lpow2 = dm*mat*lcol2;

  vec3 col = vec3(0.0);
  col += diff1*diff1*lpow1;
  col += diff2*diff2*lpow2;

  col += rm*pow(ref1, spe)*lcol1;
  col += rm*pow(ref2, spe)*lcol2;

  return col;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 q = uv + vec2(0.5);
    vec2 p = uv;

    vec3 col = color(p);
    col = aces_approx(col);
    col = sRGB(col);

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
