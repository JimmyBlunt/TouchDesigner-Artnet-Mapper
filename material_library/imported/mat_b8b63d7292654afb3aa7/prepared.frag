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
uniform vec4 uMMParam007; // native input: mat_voronoi_scale
float mat_voronoi_scale = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_voronoi_offset
vec2 mat_voronoi_offset = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_align
float mat_align = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_distort1
float mat_distort1 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_distort2
float mat_distort2 = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_seed
float mat_seed = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_fov
float mat_fov = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_limit
int mat_limit = int(round(uMMParam014.x));
uniform vec4 uMMParam015; // native input: mat_transparent
float mat_transparent = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_detail
float mat_detail = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_speed
float mat_speed = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_reverse
bool mat_reverse = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_offset
float mat_offset = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_offset_scale
float mat_offset_scale = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_strob
float mat_strob = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_restart
int mat_restart = int(round(uMMParam023.x));
uniform vec4 uMMParam024; // native input: mat_glow
float mat_glow = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_gain
float mat_gain = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_brightness
float mat_brightness = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_contrast
float mat_contrast = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_saturation
float mat_saturation = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_hue_shift
float mat_hue_shift = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_invert
bool mat_invert = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam031.x > 0.5;
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

float mat_time = mat_time_source - mat_offset * 8. * mat_offset_scale;

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
#define PI_2        (0.5*3.141592654)
#define ROT(a)      mat2(cos(a), sin(a), -sin(a), cos(a))
#define DOT2(x)     dot(x,x)

const float planeDist = 1.0-0.25;

float g_hmul = 1.0;


float sRGB(float t) { return mix(1.055*pow(t, 1./2.4) - 0.055, 12.92*t, step(t, 0.0031308)); }

vec3 sRGB(in vec3 c) { return vec3 (sRGB(c.x), sRGB(c.y), sRGB(c.z)); }


const vec4 hsv2rgb_K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);






#define HSV2RGB(c)  (c.z * mix(hsv2rgb_K.xxx, clamp(abs(fract(c.xxx + hsv2rgb_K.xyz) * 6.0 - hsv2rgb_K.www) - hsv2rgb_K.xxx, 0.0, 1.0), c.y))

float zoomOuter = 1.0;
float zoomInner = 0.2;

float tanh_approx(float x) {

  float x2 = x*x;
  return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0);
}


vec4 alphaBlend(vec4 back, vec4 front) {
  float w = front.w + back.w*(1.0-front.w);
  vec3 xyz = (front.xyz*front.w + back.xyz*back.w*(1.0-front.w))/w;
  return w > 0.0 ? vec4(xyz, w) : vec4(0.0);
}


vec3 alphaBlend(vec3 back, vec4 front) {
  return mix(back, front.xyz, front.w);
}


float hash(float co) {
  return fract(sin(co*12.9898) * 13758.5453) * mat_seed;
}

vec2 hash2(vec2 p) {
  p = vec2(dot (p, vec2 (127.1, 311.7)), dot (p, vec2 (269.5, 183.3)));
  return fract (sin (p)*43758.5453123) * (1. - mat_align);
}


float hex(vec2 p, float r ) {
  const vec3 k  = 0.5*vec3(-sqrt(3.0), 1.0, sqrt(4.0/3.0));
  p = abs(p);
  p -= 2.0*min(dot(k.xy,p),0.0)*k.xy;
  p -= vec2(clamp(p.x, -k.z*r, k.z*r), r);
  return length(p)*sign(p.y);
}

vec3 offset(float z) {
  float a = z;
  vec2 p = -0.1*(vec2(cos(a), sin(a*sqrt(2.0))) + vec2(cos(a*sqrt(0.75)), sin(a*sqrt(0.5))));
  return vec3(p, z);
}

vec3 doffset(float z) {
  float eps = 0.05;
  return (offset(z + eps) - offset(z - eps))/(2.0*eps);
}

vec3 ddoffset(float z) {
  float eps = 0.05;
  return (doffset(z + eps) - doffset(z - eps))/(2.0*eps);
}

vec3 skyColor(vec3 ro, vec3 rd) {
  float ld = max(dot(rd, vec3(0.0, 0.0, 1.0)), 0.0);
  vec3 scol = HSV2RGB(vec3(0.1, 0.25, 0.9));
  return scol*tanh_approx(3.0*pow(ld, 100.0)) * pow(mat_glow,1.5);
}

float voronoi2(vec2 p){
  vec2 g = floor(p), o; p -= g;

  vec3 d = vec3(1);

  for(int y = -1; y <= 1; y++){
    for(int x = -1; x <= 1; x++){
      o = vec2(x, y);
      o += hash2(g + o) - p;
      d.z = dot(o, o);
      d.y = max(d.x, min(d.y, d.z));
      d.x = min(d.x, d.z);
    }
  }

  return max(d.y/1.2 - d.x, 0.0)/1.2 * mat_distort1;
}

float hf2(vec2 p) {
  float zo = zoomOuter;
  float zi = zoomInner;

  p /= zo;
  p /= zi;

  float d = -voronoi2(p);
  d *= zi*zo;

  float h = 0.2*tanh_approx(3.0*smoothstep(0.0, 1.0*zo*zi, -d));

  return h*zo*zi * mat_distort2;
}

float height(vec2 p) {
  return -hf2(p)*g_hmul * mat_distort2;
}

vec3 normal(vec2 p, float eps) {
  vec2 v;
  vec2 w;
  vec2 e = vec2(0.00001, 0);

  vec3 n;
  n.x = height(p + e.xy) - height(p - e.xy);
  n.y = height(p + e.yx) - height(p - e.yx);
  n.z = -2.0*e.x;

  return normalize(n);
}

vec4 plane(vec3 pro, vec3 ro, vec3 rd, vec3 pp, vec3 off, float aa, float n_, out vec3 pnor) {
  float h0 = hash(n_);
  float h1 = fract(7793.0*h0);
  float h2 = fract(6337.0*h0);

  vec2 p = (pp-off*vec3(1.0, 1.0, 0.0)).xy * mat_fov;
  const float s = 1.0;
  vec3 lp1 = vec3(5.0,  1.0, 0.0)*vec3(s, 1.0, s)+pro;
  vec3 lp2 = vec3(-5.0, 1.0, 0.0)*vec3(s, 1.0, s)+pro;
  const float hsz = 0.2;
  float hd = hex(p.yx, hsz);

  g_hmul = smoothstep(0.0, 0.125, (hd-hsz/2.0));

  p += vec2(h0,h1)*20.0;
  p *= mix(0.5, 1.0, h2);


  vec2 offset = mat_voronoi_offset;
  offset += vec2(0.5);
  offset.x = 1.-offset.x;
  offset -= vec2(0.5);

  
  p *= pow(mat_voronoi_scale,2.);
  p += offset;
  float he  = height(p);
  vec3  nor = normal(p,2.0*aa);
  vec3 po   = pp;

  pnor = nor;

  vec3 ld1 = normalize(lp1 - po);
  vec3 ld2 = normalize(lp2 - po);

  float diff1 = max(dot(nor, ld1), 0.0);
  float diff2 = max(dot(nor, ld2), 0.0);
  diff1 = ld1.z*nor.z;;

  vec3  ref   = reflect(rd, nor);
  float ref1  = max(dot(ref, ld1), 0.0);
  float ref2  = max(dot(ref, ld2), 0.0);

  const vec3 mat   = HSV2RGB(vec3(0.55, 0.45, 0.05));
  const vec3 lcol1 = HSV2RGB(vec3(0.6, 0.5, 0.9));
  const vec3 lcol2 = HSV2RGB(vec3(0.1, 0.65, 0.9));

  float hf = smoothstep(0.0, 0.0002, -he);
  vec3 lpow1 = 1.0*lcol1/DOT2(ld1);
  vec3 lpow2 = 1.0*lcol2/DOT2(ld2);
  vec3 col = vec3(0.0);
  col += hf*mat*diff1*diff1*lpow1;
  col += hf*mat*diff2*diff2*lpow2;
  float spes = 20.0;
  col += pow(ref1, spes)*lcol1;
  col += pow(ref2, spes)*lcol2;

  float t = 1.0;
  t *= smoothstep(aa, -aa, -(hd-hsz/4.0));
  t *= mix(1.0, 0.75, hf * pow(mat_transparent,0.9));

  return vec4(col, t);
}

vec3 color(vec3 ww, vec3 uu, vec3 vv, vec3 pro, vec3 ro, vec2 p) {
  float lp = length(p);
  vec2 np = p + 1.0/vec2(1000. * mat_detail);
  float rdd = 2.0+tanh_approx(length(0.25*p));

  vec3 rd = normalize(p.x*uu + p.y*vv + rdd*ww);
  vec3 nrd = normalize(np.x*uu + np.y*vv + rdd*ww);

  int furthest = mat_limit;
  int fadeFrom = max(furthest-2, 0);

  float fadeDist = planeDist*float(furthest - fadeFrom);
  float nz = floor(ro.z / planeDist);

  vec3 skyCol = skyColor(ro, rd);

  vec4 acol = vec4(0.0);
  const float cutOff = 0.98;
  bool cutOut = false;

  
  for (int i = 1; i <= furthest; ++i) {
    float pz = planeDist*nz + planeDist*float(i);

    float pd = (pz - ro.z)/rd.z;

    if (pd > 0.0 && acol.w < cutOff) {
      vec3 pp = ro + rd*pd;
      vec3 npp = ro + nrd*pd;

      float aa = 3.0*length(pp - npp);

      vec3 off = offset(pp.z);

      vec3 pnor = vec3(0.0);
      vec4 pcol = plane(pro, ro, rd, pp, off, aa, nz+float(i), pnor);

      vec3 refr = refract(rd, pnor, 1.0-0.075);
      if (pcol.w > (1.0-cutOff)&&refr != vec3(0.0)) {
        rd = refr;
      }

      float dz = pp.z-ro.z;
      const float fi = -0.;
      float fadeIn = smoothstep(planeDist*(float(furthest)+fi), planeDist*(float(fadeFrom)-fi), dz);
      float fadeOut = smoothstep(0.0, planeDist*0.1, dz);
      pcol.w *= fadeOut*fadeIn;

      acol = alphaBlend(pcol, acol);
    } else {
      cutOut = true;
      acol.w = acol.w > cutOff ? 1.0 : acol.w;
      break;
    }

  }

  vec3 col = alphaBlend(skyCol, acol);


  return col;
}

vec3 effect(vec2 p, vec2 q) {
  float z   = 0.33*planeDist*mat_time;
  vec3 pro  = offset(z-1.0);
  vec3 ro   = offset(z);
  vec3 dro  = doffset(z);
  vec3 ddro = ddoffset(z);

  vec3 ww = normalize(dro);
  vec3 uu = normalize(cross(normalize(vec3(0.0,1.0,0.0)+ddro), ww));
  vec3 vv = cross(ww, uu);

  vec3 col = color(ww, uu, vv, pro, ro, p);

  return col;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 p = uv;
    vec2 q = texCoord;

    vec3 col = effect(p, q);
    
    col = sRGB(col) * mat_gain;

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
