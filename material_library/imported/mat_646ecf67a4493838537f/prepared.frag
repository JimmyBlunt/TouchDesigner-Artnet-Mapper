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

uniform vec4 uMMParam000; // native input: mat_reps
int mat_reps = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_max_iter
int mat_max_iter = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: mat_scale
float mat_scale = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: mat_speed
float mat_speed = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_reverse
bool mat_reverse = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_offset
float mat_offset = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_offset_scale
float mat_offset_scale = uMMParam008.x;
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

float mat_time = mat_time_source - mat_offset * mat_offset_scale * 100.;







#define TAU        (2.0*PI)
#define TOLERANCE  0.0003

#define mat_max_dist   20.


const vec3  green  = vec3(1.5, 2.0, 1.0);
const vec3  dark   = vec3(0.2);

void rot(inout vec2 p, float a) {
  float c = cos(a);
  float s = sin(a);
  p = vec2(c*p.x + s*p.y, -s*p.x + c*p.y);
}

void r45(inout vec2 p) {
    p = (p + vec2(p.y, -p.x))*sqrt(0.5);
}

float apollian(vec3 p, float tolerance, out int layer) {
  const float s = 1.9;
  float scale = 1.0;

  float r = 0.2;
  vec3 o = vec3(0.22, 0.0, 0.0);

  float d = 0.0;

  for(int i = 0; i < mat_reps; ++i) {
    p = (-1.00 + 2.0*fract(0.5*p+0.5));

    r45(p.xz);

    float r2 = dot(p,p) + 0.0;
    float k = s/r2;
    float ss = pow((1.0 + float(i)), -0.15);
    p *= pow(k, ss);
    scale *= pow(k, -ss*ss);
    d = 0.25*abs(p.y)*scale;
    layer = i;
    if(abs(d) < tolerance) break;
  }

  return d;
}

float df(vec3 p, float tolerance, out int layer) {
  float d = apollian(p, tolerance, layer);
  return d;
}


float intersect(vec3 ro, vec3 rd, out int iter, out int layer) {
  float res;
  float t = 1.6;
  iter = mat_max_iter;

  for(int i = 0; i < mat_max_iter; ++i) {
    vec3 p = ro + rd * t;
    float tolerance = TOLERANCE * t;
    res = df(p, tolerance, layer);
    if(res < tolerance || res > mat_max_dist) {
      iter = i;
      break;
    }
    t += res;
  }

  if(res > mat_max_dist) t = -1.;

  return t;
}

float ambientOcclusion(vec3 p, vec3 n) {
  float stepSize = 0.012;
  float t = stepSize;

  float oc = 0.0;

  int layer;

  for(int i = 0; i < 12; i++) {
    float tolerance = TOLERANCE * t;
    float d = df(p + n * t, tolerance, layer);
    oc += t - d;
    t += stepSize;
  }

  return clamp(oc, 0.0, 1.0);
}

vec3 normal(in vec3 pos) {
  vec3 eps = vec3(.001,0.0,0.0);
  vec3 nor;
  int layer;
  float tolerance = TOLERANCE * eps.x;
  nor.x = df(pos+eps.xyy, tolerance, layer) - df(pos-eps.xyy, tolerance, layer);
  nor.y = df(pos+eps.yxy, tolerance, layer) - df(pos-eps.yxy, tolerance, layer);
  nor.z = df(pos+eps.yyx, tolerance, layer) - df(pos-eps.yyx, tolerance, layer);
  return normalize(nor);
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);


    vec2 uv_shift = mat_shift_amount;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);
    uv += uv_shift;

    uv *= mat_scale * 4.;

    uv.y = 1. - uv.y;

    vec2 q=uv + vec2(mat_scale * 8.);

    vec3 la = vec3(0.0,0.5,0.0);
    vec3 ro = vec3(2.5, 1.5, 0.0);
    rot(ro.xz, mat_time/40.0);

    vec3 cf = normalize(la-ro);
    vec3 cs = normalize(cross(cf,vec3(0.0,1.0,0.0)));
    vec3 cu = normalize(cross(cs,cf));
    vec3 rd = normalize(uv.x*cs + uv.y*cu + 3.0*cf);

    vec3 bg = mix(dark*0.25, dark*0.5, smoothstep(-1.0, 1.0, uv.y));
    vec3 col = bg;

    vec3 p=ro;

    int iter = 0;
    int layer = 0;

    float t = intersect(ro, rd, iter, layer);

    if(t > -1.0) {
      p = ro + t * rd;
      vec3 n = normal(p);
      float fake = float(iter)/float(mat_max_iter);
      float fakeAmb = exp(-fake*fake*4.0);
      float amb = ambientOcclusion(p, n);


      vec3 dif;

      float ll = length(p);

      if (layer == 0)
      {
        dif = 0.75*green;
      } else {
        dif = green*pow((1.0 + 0.5*cos(-PI*2.0*float(layer)/float(mat_reps) + mat_time*0.25 - 0.5*PI*ll)), 4.0)/pow(float(layer), 1.5);
      }


      const float fogPeriod = TAU*2.0;
      float fogHeight = 0.25 + 0.325*(abs(p.y) + 0.125*(sin(fogPeriod*p.x) * cos(fogPeriod*p.z)));
      float dfog = (fogHeight - ro.y)/rd.y;
      float fogDepth = t > dfog && dfog > 0.0 ? t - dfog : 0.0;
      float fogFactor = exp(-fogDepth*4.0);

      col = dif;
      col *= vec3(mix(1.0, 0.125, pow(amb, 3.0)))*vec3(fakeAmb);
      col = mix(green*0.5, col, fogFactor);
      col = mix(bg, col, exp(-0.0125*t*t));
    }

    float pp = 1.0 - (1.0 - step(0.5, q.y))*smoothstep(0.85, 1.3, length(2.0*q-1.0));


    col *= pp;


    out_color=vec4(col.x,col.y,col.z,1.0);




    
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
