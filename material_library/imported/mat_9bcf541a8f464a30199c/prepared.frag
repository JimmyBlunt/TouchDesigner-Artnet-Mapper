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
uniform vec4 uMMParam007; // native input: mat_height
float mat_height = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_cycle_1
float mat_cycle_1 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_cycle_2
float mat_cycle_2 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_cycle_3
float mat_cycle_3 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_cycle_4
float mat_cycle_4 = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_detail
float mat_detail = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_iterations_1
int mat_iterations_1 = int(round(uMMParam013.x));
uniform vec4 uMMParam014; // native input: mat_iterations_2
int mat_iterations_2 = int(round(uMMParam014.x));
uniform vec4 uMMParam015; // native input: mat_speed
float mat_speed = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_reverse
bool mat_reverse = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_offset
float mat_offset = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_offset_scale
float mat_offset_scale = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_strob
float mat_strob = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_restart
int mat_restart = int(round(uMMParam021.x));
uniform vec4 uMMParam022; // native input: mat_scroll_xy_offset
vec2 mat_scroll_xy_offset = uMMParam022.xy;
uniform vec4 uMMParam023; // native input: mat_scroll_speed
float mat_scroll_speed = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_scroll_bpm_sync
bool mat_scroll_bpm_sync = uMMParam024.x > 0.5;
uniform vec4 uMMParam025; // native input: mat_scroll_reverse
bool mat_scroll_reverse = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_scroll_offset
float mat_scroll_offset = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_scroll_offset_scale
float mat_scroll_offset_scale = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_scroll_strob
float mat_scroll_strob = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_scroll_restart
int mat_scroll_restart = int(round(uMMParam029.x));
uniform vec4 uMMParam030; // native input: mat_light_size
float mat_light_size = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_light_offset
vec2 mat_light_offset = uMMParam031.xy;
uniform vec4 uMMParam032; // native input: mat_light_offset_scale
float mat_light_offset_scale = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_light_glow
float mat_light_glow = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_light_power1
float mat_light_power1 = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_light_power2
float mat_light_power2 = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_lcolor_1
vec4 mat_lcolor_1 = uMMParam036;
uniform vec4 uMMParam037; // native input: mat_lcolor_2
vec4 mat_lcolor_2 = uMMParam037;
uniform vec4 uMMParam038; // native input: mat_light_mod
float mat_light_mod = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_brightness
float mat_brightness = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_contrast
float mat_contrast = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_saturation
float mat_saturation = uMMParam041.x;
uniform vec4 uMMParam042; // native input: mat_hue_shift
float mat_hue_shift = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_invert
bool mat_invert = uMMParam043.x > 0.5;
uniform vec4 uMMParam044; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam044.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_scroll_time_source = uTDTime * (mat_scroll_speed);

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
float mat_scroll_time = mat_scroll_time_source - mat_scroll_offset * 8. * mat_scroll_offset_scale;

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
    uv *= mat_scale * 2.;

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






#define TAU         (2.0*PI)
#define L2(x)       dot(x, x)
#define ROT(a)      mat2(cos(a), sin(a), -sin(a), cos(a))

float tanh_approx(float x) {

  float x2 = x*x;
  return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0);
}

float pmin(float a, float b, float k) {
  float h = clamp(0.5+0.5*(b-a)/k, 0.0, 1.0);
  return mix(b, a, h) - k*h*(1.0-h);
}

float pmax(float a, float b, float k) {
  return -pmin(-a, -b, k);
}

float pabs(float a, float k) {
  return pmax(a, -a, k);
}

vec2 hash(vec2 p) {
  p += 0.5;
  p = vec2(dot (p, vec2 (127.1, 311.7)), dot (p, vec2 (269.5, 183.3)));
  return -1. + 2.*fract (sin (p)*43758.5453123) ;
}
float height_(vec2 p, float tm) {
  p *= 0.125*1.5;
  vec2 n = floor(p + 0.5);
  vec2 r = hash(n);
  p = fract(p+0.5)-0.5;
  float d = length(p);



  float c = 1E6;
  float x = pow(d, 0.1);
  float y = atan(p.x, p.y) / TAU;

  for (float i = 0.; i < float(mat_iterations_1); ++i) {
    float ltm = tm+10.0*(r.x+r.y);
    float v = length(fract(vec2(x - ltm*i*.005123, fract(y + i*.125)*.5)*20.)*2.-1.);
    c = pmin(c, v, 0.125) * mat_cycle_2;
  }

  return -0.125*pabs(1.0-tanh_approx(5.5*d-80.*c*c*d*d*(.55-d))-0.25*d, 0.25);
}


float height(vec2 p) {
  float tm = mat_scroll_time*0.00075;

  vec2 xy_offset = mat_scroll_xy_offset;
  xy_offset += vec2(0.5);
  xy_offset.x = 1.-xy_offset.x;
  xy_offset -= vec2(0.5);


  p += 100.0*vec2(cos(tm), sin(tm));
  p += xy_offset;
  const float aa = -0.35;
  const mat2  pp = 0.9*(1.0/aa)*ROT(1.0);
  float h = 0.0;
  float a = 1.0;
  float d = 0.0;
  for (int i = 0; i < mat_iterations_2; ++i) {
    h += a*height_(p, 0.125*mat_time+10.0*sqrt(float(i)));
    h = pmin(h, -h, 0.025) * pow(mat_cycle_1,0.5);
    d += a / mat_cycle_3;
    a *= aa * mat_cycle_4;
    p *= pp;
  }
  return (h/d) * mat_height;
}


vec3 normal(vec2 p) {
  vec2 v;
  vec2 w;
  vec2 e = vec2(4.0/(mat_detail * 1000.), 0);

  vec3 n;
  n.x = height(p + e.xy) - height(p - e.xy);
  n.y = 2.0*e.x;
  n.z = height(p + e.yx) - height(p - e.yx);

  return normalize(n);
}

vec3 color(vec2 p) {
  const float s = 1.0;
  const vec3 lp1 = vec3(1.0, 1.25, 1.0)*vec3(s, 1.0, s);
  const vec3 lp2 = vec3(-1.0, 1.25, 1.0)*vec3(s, 1.0, s);

  float h = height(p);
  vec3  n = normal(p);

  vec3 ro = vec3(0.0, -10.0, 0.0) * mat_light_mod;
  vec3 pp = vec3(p.x, 0.0, p.y);





  vec2 light_offset = mat_light_offset * mat_light_offset_scale;
  light_offset += vec2(0.5);
  light_offset.x = 1.-light_offset.x;
  light_offset -= vec2(0.5);


  p.x += light_offset.x;
  p.y += light_offset.y;

  p -= vec2(0.5);
  p *= mat_light_size;

  p += vec2(0.5);


  vec3 po = vec3(p.x, h, p.y);
  vec3 rd = normalize(ro - po);

  vec3 ld1 = normalize(lp1 - po);
  vec3 ld2 = normalize(lp2 - po);

  float diff1 = max(dot(n, ld1), 0.0);
  float diff2 = max(dot(n, ld2), 0.0);

  vec3  rn    = n;
  vec3  ref   = reflect(rd, rn);
  float ref1  = max(dot(ref, ld1), 0.0) * mat_light_power1;
  float ref2  = max(dot(ref, ld2), 0.0) * mat_light_power2;



  

  

  
  
  vec3 lcol1 = mat_lcolor_1.rgb;
  vec3 lcol2 = mat_lcolor_2.rgb;
  vec3 lpow1 = 0.15*lcol1/L2(ld1) * pow(mat_light_glow,1.5);
  vec3 lpow2 = 0.5*lcol2/L2(ld2) * pow(mat_light_glow,1.5);
  vec3 dm = vec3(1.0)*tanh(-h*10.0+0.125);
  vec3 col = vec3(0.0);
  col += dm*diff1*diff1*lpow1;
  col += dm*diff2*diff2*lpow2;
  vec3 rm = vec3(1.0)*mix(0.25, 1.0, tanh_approx(-h*1000.0));
  
  
  col += rm*pow(ref1, 10.0)*lcol1/0.15;
  col += rm*pow(ref2, 10.0)*lcol2/0.5;

  return col;
}

vec3 postProcess(vec3 col, vec2 q) {
  col = clamp(col, 0.0, 1.0);
  col = pow(col, 1.0/vec3(2.2));
  col = col*0.6+0.4*col*col*(3.0-2.0*col);
  col = mix(col, vec3(dot(col, vec3(0.33))), -0.4);
  col *=0.5+0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y),0.7) ;
  return col;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 p = uv;
    vec2 q = texCoord;

    vec3 col = color(p);
    col = tanh(0.33*col);
    col = postProcess(col, q);

    out_color = vec4(col, 1.0);


    
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
