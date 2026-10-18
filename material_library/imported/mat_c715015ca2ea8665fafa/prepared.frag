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
uniform vec4 uMMParam007; // native input: mat_fov
float mat_fov = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_glow
float mat_glow = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_speed
float mat_speed = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: mat_reverse
bool mat_reverse = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_offset
float mat_offset = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_offset_scale
float mat_offset_scale = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_strob
float mat_strob = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_restart
int mat_restart = int(round(uMMParam015.x));
uniform vec4 uMMParam016; // native input: mat_cycle1
float mat_cycle1 = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_cycle2
float mat_cycle2 = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_cycle3
float mat_cycle3 = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_speed_2
float mat_speed_2 = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_bpm_sync_2
bool mat_bpm_sync_2 = uMMParam020.x > 0.5;
uniform vec4 uMMParam021; // native input: mat_reverse_2
bool mat_reverse_2 = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_offset_2
float mat_offset_2 = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_offset_scale_2
float mat_offset_scale_2 = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_strob_2
float mat_strob_2 = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_restart_2
int mat_restart_2 = int(round(uMMParam025.x));
uniform vec4 uMMParam026; // native input: mat_sharpness
float mat_sharpness = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_post
bool mat_post = uMMParam027.x > 0.5;
uniform vec4 uMMParam028; // native input: mat_back_color
vec4 mat_back_color = uMMParam028;
uniform vec4 uMMParam029; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_brightness
float mat_brightness = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_contrast
float mat_contrast = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_saturation
float mat_saturation = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_hue_shift
float mat_hue_shift = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_invert
bool mat_invert = uMMParam034.x > 0.5;
uniform vec4 uMMParam035; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam035.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_time_source_2 = uTDTime * (mat_speed_2);

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
float mat_time_2 = mat_time_source_2 - mat_offset_2 * 8. * mat_offset_scale_2;

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










#define TAU             (2.0*PI)


#define ROT(a)          mat2(cos(a), sin(a), -sin(a), cos(a))
#define PSIN(x)         (0.5+0.5*sin(x))
#define LESS(a,b,c)     mix(a,b,step(0.,c))
#define SABS(x,k)       LESS((.5/(k))*(x)*(x)+(k)*.5,abs(x),abs(x)-(k))
#define L2(x)           dot(x, x)
#define PLANE_PERIOD    5.0

const vec3 std_gamma   = vec3(2.2, 2.2, 2.2);




vec3 planeCol    = mat_back_color.rgb / 1.5;
const vec3 baseRingCol = pow(vec3(1.0, 0.65, 0.25), vec3(0.6));
const vec3 sunCol      = vec3(1.25, 1.0, 1.1)/1.25;

struct effect {
  float lw;
  float tw;
  float sk;
  float cs;
};

const effect effects[] = effect[](
    effect(0.125, 0.0, 0.0, 0.0)
  , effect(0.125, 0.0, 0.0, 1.0)
  , effect(0.125, 0.0, 1.0, 1.0)
  , effect(0.125, 1.0, 1.0, 1.0)
  , effect(0.125, 1.0, 1.0, 0.0)
  , effect(0.125, 1.0, 0.0, 0.0)
  );
effect current_effect = effects[5];

float hash(float co) {
  co += 100.0;
  return fract(sin(co*12.9898) * 13758.5453);
}

vec2 toPolar(vec2 p) {
  return vec2(length(p), atan(p.y, p.x));
}

vec2 toRect(vec2 p) {
  return vec2(p.x*cos(p.y), p.x*sin(p.y));
}

float modMirror1(inout float p, float size) {
  float halfsize = size*0.5;
  float c = floor((p + halfsize)/size);
  p = mod(p + halfsize,size) - halfsize;
  p *= mod(c, 2.0)*2.0 - 1.0;
  return c;
}

float smoothKaleidoscope(inout vec2 p, float sm, float rep) {
  vec2 hp = p;
  vec2 hpp = toPolar(hp);
  float rn = modMirror1(hpp.y, TAU/rep);
  float sa = PI/rep - SABS(PI/rep - abs(hpp.y), sm);
  hpp.y = sign(hpp.y)*(sa);
  hp = toRect(hpp);
  p = hp;
  return rn;
}

vec4 alphaBlend(vec4 back, vec4 front) {
  float w = front.w + back.w*(1.0-front.w);
  vec3 xyz = (front.xyz*front.w + back.xyz*back.w*(1.0-front.w))/w;
  return w > 0.0 ? vec4(xyz, w) : vec4(0.0);
}

vec3 alphaBlend(vec3 back, vec4 front) {
  return mix(back, front.xyz, front.w);
}

float tanh_approx(float x) {

  float x2 = x*x;
  return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0);
}

float pmin(float a, float b, float k) {
  float h = clamp(0.5+0.5*(b-a)/k, 0.0, 1.0);

  return mix(b, a, h) - k*h*(1.0-h);
}

float circle(vec2 p, float r) {
  return length(p) - r;
}

float hex(vec2 p, float r) {
  const vec3 k = vec3(-sqrt(3.0)/2.0,1.0/2.0,sqrt(3.0)/3.0);
  p = p.yx;
  p = abs(p);
  p -= 2.0*min(dot(k.xy,p),0.0)*k.xy;
  p -= vec2(clamp(p.x, -k.z*r, k.z*r), r);
  return length(p)*sign(p.y);
}

float apollian(vec4 p, float s) {
  float scale = 1.0;
  for(int i=0; i<7; ++i) {
    p = -1.0 + 2.0*fract(0.5*p+0.5);
    float r2 = dot(p,p);
    float k  = s/r2;
    p       *= k;
    scale   *= k;
  }

  float lw = 0.00125*current_effect.lw;

  float d0 = abs(p.y)-lw*scale;
  float d1 = abs(circle(p.xz, 0.005*scale))-lw*scale;
  float d = d0;
  d = mix(d, min(d, d1), current_effect.tw);
  return (d/scale);
}






vec3 offset(float z) {
  float a = z;
  vec2 p = -0.075*(vec2(cos(a), sin(a*sqrt(2.0))) + vec2(cos(a*sqrt(0.75)), sin(a*sqrt(0.5))));
  return vec3(p, z);
}



vec3 doffset(float z) {
  float eps = 0.1;
  return 0.5*(offset(z + eps) - offset(z - eps))/eps;
}



vec3 ddoffset(float z) {
  float eps = 0.1;
  return 0.125*(doffset(z + eps) - doffset(z - eps))/eps;
}





float weird(vec2 p, float h) {
  float z = 4.0 * mat_cycle1;
  float tm = 0.1*mat_time_2+h*10.0;
  p *= ROT(tm*0.5);
  float r = 0.5;
  vec4 off = vec4(r*PSIN(tm*sqrt(3.0)), r*PSIN(tm*sqrt(1.5)), r*PSIN(tm*sqrt(2.0)), 0.0)  * mat_cycle2;
  vec4 pp = vec4(p.x, p.y, 0.0, 0.0)+off;
  pp.w = 0.125*(1.0-tanh_approx(length(pp.xyz)));
  pp.yz *= ROT(tm);
  pp.xz *= ROT(tm*sqrt(0.5));
  pp /= z;
  float d = apollian(pp, mat_cycle3*0.8+h);
  return d*z;
}

float circles(vec2 p) {
  vec2 pp = toPolar(p);
  const float ss = 2.0;
  pp.x = fract(pp.x/ss)*ss;
  p = toRect(pp);
  float d = circle(p, 1.0);
  return d;
}

vec2 df(vec2 p, float h) {
  vec2 wp = p;
  float rep = 2.0*round(mix(5.0, 15.0, h*h));
  float ss = 0.05*6.0/rep;

  if (current_effect.sk > 0.0) {
    smoothKaleidoscope(wp, ss, rep);
  }

  float d0 = weird(wp, h);
  float d1 = hex(p, 0.25)-0.1;
  float d2 = circles(p);
  const float lw = 0.0125;
  d2 = abs(d2)-lw;
  float d = d0;

  if (current_effect.cs > 0.0) {
    d  = pmin(d, d2, 0.1);
  }

  d  = pmin(d, abs(d1)-lw, 0.1);
  d  = max(d, -(d1+lw));
  return vec2(d, d1+lw);
}

vec2 df(vec3 p, vec3 off, float s, mat2 rot, float h) {
  vec2 p2 = p.xy;
  p2 -= off.xy;
  p2 *= rot;
  return df(p2/s, h)*s;
}

vec3 skyColor(vec3 ro, vec3 rd) {
  float ld = max(dot(rd, vec3(0.0, 0.0, 1.0)), 0.0);
  return 1.0*sunCol*tanh_approx(3.0*pow(ld, 100.0));
}

vec4 plane(vec3 ro, vec3 rd, vec3 pp, float pd, vec3 off, float aa, float n) {
  int pi = int(mod(n/PLANE_PERIOD, float(effects.length())));
  current_effect = effects[pi];

  float h = hash(n);
  float s = 0.25*mix(0.5, 0.25, h);
  const float lw = 0.0235;
  const float lh = 1.25;

  const vec3 nor  = vec3(0.0, 0.0, -1.0);
  const vec3 loff = 2.0*vec3(0.25*0.5, 0.125*0.5, -0.125);
  vec3 lp1  = ro + loff;
  vec3 lp2  = ro + loff*vec3(-2.0, 1.0, 1.0);

  vec2 p = pp.xy-off.xy;

  mat2 rot = ROT(TAU*h);

  vec2 d2 = df(pp, off, s, rot, h);

  vec3 ld1   = normalize(lp1 - pp);
  vec3 ld2   = normalize(lp2 - pp);
  float dif1 = pow(max(dot(nor, ld1), 0.0), 5.0);
  float dif2 = pow(max(dot(nor, ld2), 0.0), 5.0);
  vec3 ref   = reflect(rd, nor);
  float spe1= pow(max(dot(ref, ld1), 0.0), 30.0);
  float spe2= pow(max(dot(ref, ld2), 0.0), 30.0);

  const float boff = 0.0125*0.5;
  float dbt = boff/rd.z;

  vec3 bpp = ro + (pd + dbt)*rd;
  vec2 bp = bpp.xy - off.xy;

  vec3 srd1 = normalize(lp1-bpp);
  vec3 srd2 = normalize(lp2-bpp);
  float bl21= L2(lp1-bpp);
  float bl22= L2(lp2-bpp);

  float st1 = -boff/srd1.z;
  float st2 = -boff/srd2.z;

  vec3 spp1 = bpp + st1*srd1;
  vec3 spp2 = bpp + st2*srd2;

  vec2 bd  = df(bpp, off, s, rot, h);
  vec2 sd1 = df(spp1, off, s, rot, h);
  vec2 sd2 = df(spp2, off, s, rot, h);

  vec3 col  = vec3(0.0);
  const float ss = 200.0;

  col       += 0.1125*planeCol*dif1*(1.0-exp(-ss*(max((sd1.x), 0.0))))/bl21;
  col       += 0.1125*planeCol*dif2*0.5*(1.0-exp(-ss*(max((sd2.x), 0.0))))/bl22;

  vec3 ringCol = baseRingCol;
  ringCol *= vec3(clamp(0.1+2.5*(0.1+0.25*((dif1*dif1/bl21+dif2*dif2/bl22))), 0.0, 1.0));
  ringCol += sqrt(baseRingCol)*spe1*2.0;
  ringCol += sqrt(baseRingCol)*spe2*2.0;
  col       = mix(col, ringCol, smoothstep(-aa, aa, -d2.x));

  float ha = smoothstep(-aa, aa, bd.y);

  return vec4(col, mix(0.0, 1.0, ha));
}

vec3 color(vec3 ww, vec3 uu, vec3 vv, vec3 ro, vec2 p) {
  float lp = length(p);
  vec2 np = p + 1.0/(vec2(1024.) * pow(mat_sharpness,2.) * 2.);
  float rdd = (2.0-0.5*tanh_approx(lp)) * mat_fov;  
  vec3 rd = normalize(p.x*uu + p.y*vv + rdd*ww);
  vec3 nrd = normalize(np.x*uu + np.y*vv + rdd*ww);

  const float planeDist = 1.0-0.75;
  const int furthest = 9;
  const int fadeFrom = max(furthest-4, 0);
  const float fadeDist = planeDist*float(furthest - fadeFrom);
  float nz = floor(ro.z / planeDist);

  vec3 skyCol = skyColor(ro, rd) * mat_glow;

  

  vec4 acol = vec4(0.0);
  const float cutOff = 0.95;
  bool cutOut = false;

  for (int i = 1; i <= furthest; ++i) {
    float pz = planeDist*nz + planeDist*float(i);

    float pd = (pz - ro.z)/rd.z;

    if (pd > 0.0 && acol.w < cutOff) {
      vec3 pp = ro + rd*pd;
      vec3 npp = ro + nrd*pd;

      float aa = 3.0*length(pp - npp);

      vec3 off = offset(pp.z);

      vec4 pcol = plane(ro, rd, pp, pd, off, aa, nz+float(i));

      float nz = pp.z-ro.z;
      float fadeIn = exp(-2.5*max((nz - planeDist*float(fadeFrom))/fadeDist, 0.0));
      float fadeOut = smoothstep(0.0, planeDist*0.1, nz);
      pcol.xyz = mix(skyCol, pcol.xyz, (fadeIn));
      pcol.w *= fadeOut;

      pcol = clamp(pcol, 0.0, 1.0);

      acol = alphaBlend(pcol, acol);
    } else {
      cutOut = true;
      break;
    }

  }

  vec3 col = alphaBlend(skyCol, acol);


  return col;
}

vec3 postProcess(vec3 col, vec2 q) {
    if (mat_post) {
        col = clamp(col, 0.0, 1.0);
        col = pow(col, 1.0/std_gamma);
        col = col*0.6+0.4*col*col*(3.0-2.0*col);
        col = mix(col, vec3(dot(col, vec3(0.33))), -0.4);
        col *=0.5+0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y),0.7);
    }
    return col;
}

vec3 color(vec2 p, vec2 q) {
  float tm  = mat_time*0.125;
  vec3 ro   = offset(tm);
  vec3 dro  = doffset(tm);
  vec3 ddro = ddoffset(tm);

  vec3 ww = normalize(dro);
  vec3 uu = normalize(cross(normalize(vec3(0.0,1.0,0.0)+ddro), ww));
  vec3 vv = normalize(cross(ww, uu));

  vec3 col = color(ww, uu, vv, ro, p);
  col = clamp(col, 0.0, 1.0);
  
  col = postProcess(col, q);

  return col;
}



vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 p = uv;
    vec2 q = texCoord;
    vec3 col = color(p, q);
    out_color = vec4(col, 1.0);

    if (mat_luma_to_alpha) {
        out_color.a = mat_luma(out_color);
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
