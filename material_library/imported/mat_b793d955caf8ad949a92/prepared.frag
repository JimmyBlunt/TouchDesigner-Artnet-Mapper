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
uniform vec4 uMMParam008; // native input: mat_fov
float mat_fov = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_inner_size
float mat_inner_size = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_outer_size
float mat_outer_size = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_refraction
float mat_refraction = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_collapse
float mat_collapse = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_transparency
float mat_transparency = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_bounces
int mat_bounces = int(round(uMMParam014.x));
uniform vec4 uMMParam015; // native input: mat_iterations
int mat_iterations = int(round(uMMParam015.x));
uniform vec4 uMMParam016; // native input: mat_obj_level
float mat_obj_level = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_sky_level
float mat_sky_level = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_spin
float mat_spin = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_roll
float mat_roll = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_speed
float mat_speed = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_reverse
bool mat_reverse = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_offset
float mat_offset = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_offset_scale
float mat_offset_scale = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_strob
float mat_strob = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_restart
int mat_restart = int(round(uMMParam026.x));
uniform vec4 uMMParam027; // native input: mat_brightness
float mat_brightness = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_contrast
float mat_contrast = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_saturation
float mat_saturation = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_hue_shift
float mat_hue_shift = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_invert
bool mat_invert = uMMParam031.x > 0.5;
uniform vec4 uMMParam032; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam032.x > 0.5;
uniform vec4 uMMParam033; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam034.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
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
    uv *= mat_scale * 3.;

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

#define TOLERANCE       0.0001
#define MAX_RAY_LENGTH  20.0
int MAX_RAY_MARCHES = mat_iterations;
#define NORM_OFF        0.001
#define MAX_BOUNCES     mat_bounces


const vec4 hsv2rgb_K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
vec3 mat_hsv2rgb(vec3 c) {
  vec3 p = abs(fract(c.xxx + hsv2rgb_K.xyz) * 6.0 - hsv2rgb_K.www);
  return c.z * mix(hsv2rgb_K.xxx, clamp(p - hsv2rgb_K.xxx, 0.0, 1.0), c.y);
}


#define HSV2RGB(c)  (c.z * mix(hsv2rgb_K.xxx, clamp(abs(fract(c.xxx + hsv2rgb_K.xyz) * 6.0 - hsv2rgb_K.www) - hsv2rgb_K.xxx, 0.0, 1.0), c.y))

vec3 skyCol     = HSV2RGB(vec3(0.6, 0.86, 1.0)) * mat_sky_level;
const vec3 lightPos   = vec3(0.0, 10.0, 0.0);

const float initt       = 0.1;
float refraction  = 0.8 * mat_refraction;

mat3 g_rot = mat3(1.0);
vec2 g_mat = vec2(0.0);
vec3 g_beer = vec3(0.0);


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
  return clamp((v*(a*v+b))/(v*(c*v+d)+e), 0.0f, 1.0f);
}


float tanh_approx(float x) {
  
  
  float x2 = x*x;
  return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0);
}


float box(vec2 p, vec2 b) {
  vec2 d = abs(p)-b;
  return length(max(d,0.0)) + min(max(d.x,d.y),0.0);
}


float rayPlane(vec3 ro, vec3 rd, vec4 p) {
  return -(dot(ro,p.xyz)+p.w)/dot(rd,p.xyz);
}

mat3 rot_z(float a) {
  float c = cos(a);
  float s = sin(a);
  return mat3(
      c,s,0
    ,-s,c,0
    , 0,0,1
    );
}

mat3 rot_y(float a) {
  float c = cos(a);
  float s = sin(a);
  return mat3(
      c,0,s
    , 0,1,0
    ,-s,0,c
    );
}

mat3 rot_x(float a) {
  float c = cos(a);
  float s = sin(a);
  return mat3(
      1, 0,0
    , 0, c,s
    , 0,-s,c
    );
}

float sphere4(vec3 p, float r) {
  p *= p;
  return pow(dot(p, p), 0.25)-r;
}

vec3 skyColor(vec3 ro, vec3 rd) {
  vec3 col = clamp(vec3(0.0025/abs(rd.y))*skyCol, 0.0, 1.0);

  float tp0  = rayPlane(ro, rd, vec4(vec3(0.0, 1.0, 0.0), 4.0));
  float tp1  = rayPlane(ro, rd, vec4(vec3(0.0, -1.0, 0.0), 6.0));
  float tp = tp1;
  tp = max(tp0,tp1);


  if (tp1 > 0.0) {
    vec3 pos  = ro + tp1*rd;
    vec2 pp = pos.xz;
    float db = box(pp, vec2(6.0, 9.0))-1.0;

    col += vec3(4.0)*skyCol*rd.y*rd.y*smoothstep(0.25, 0.0, db);
    col += vec3(0.8)*skyCol*exp(-0.5*max(db, 0.0));
  }

  if (tp0 > 0.0) {
    vec3 pos  = ro + tp0*rd;
    vec2 pp = pos.xz;
    float ds = length(pp) - 0.5;

    col += vec3(0.25)*skyCol*exp(-.5*max(ds, 0.0));
  }

  return clamp(col, 0.0, 10.0);
}

float df(vec3 p) {
  p *= g_rot;
  vec3 p0 = p;
  p *= g_rot;
  vec3 p1 = p;
  float d0 = sphere4(p0, 1.0 * mat_inner_size);
  float d1 = sphere4(p1, 1.75 * mat_outer_size);
  d1 = max(d1, -(d0-0.2));

  vec2 mat = vec2(0.05, 0.5);
  vec3 beer = -vec3(2., 1.0, 2.0);

  float d = d0;
  if (d1 < d) {
    mat = vec2(0.99, 0.6) * mat_transparency;
    d = d1;
    beer = vec3(0.1, 0.2, 0.);
  }

  g_mat = mat;
  g_beer = beer;
  return d * mat_collapse;
}

vec3 normal(vec3 pos) {
  vec2  eps = vec2(NORM_OFF,0.0);
  vec3 nor;
  nor.x = df(pos+eps.xyy) - df(pos-eps.xyy);
  nor.y = df(pos+eps.yxy) - df(pos-eps.yxy);
  nor.z = df(pos+eps.yyx) - df(pos-eps.yyx);
  return normalize(nor);
}

float rayMarch(vec3 ro, vec3 rd, float dfactor, out int ii) {
  float t = 0.0;
  float tol = dfactor*TOLERANCE;
  ii = MAX_RAY_MARCHES;
  for (int i = 0; i < MAX_RAY_MARCHES; ++i) {
    if (t > MAX_RAY_LENGTH) {
      t = MAX_RAY_LENGTH;
      break;
    }
    float d = dfactor*df(ro + rd*t);
    if (d < TOLERANCE) {
      ii = i;
      break;
    }
    t += d;
  }
  return t;
}

vec3 render(vec3 ro, vec3 rd) {
  vec3 agg = vec3(0.0, 0.0, 0.0);
  vec3 ragg = vec3(1.0);

  bool isInside = df(ro) < 0.0;

  for (int bounce = 0; bounce < MAX_BOUNCES; ++bounce) {
    float dfactor = isInside ? -1.0 : 1.0;
    float mragg = min(min(ragg.x, ragg.y), ragg.z);
    if (mragg < 0.025) break;
    int iter;
    float st = rayMarch(ro, rd, dfactor, iter);
    float mrm = 1.0/float(MAX_RAY_MARCHES);
    float ii = float(iter)*mrm;
    vec2 mat = g_mat;
    vec3 beer = g_beer;
    if (st >= MAX_RAY_LENGTH) {
      agg += ragg*skyColor(ro, rd);
      break;
    }

    vec3 sp = ro+rd*st;

    vec3 sn = dfactor*normal(sp);
    float fre = 1.0+dot(rd, sn);
    fre *= fre;
    fre = mix(0.1, 1.0, fre);

    vec3 ld     = normalize(lightPos - sp);

    float dif   = max(dot(ld, sn), 0.0);
    vec3 ref    = reflect(rd, sn);
    float irefraction = 1.0/refraction;
    vec3 refr   = refract(rd, sn, !isInside ? refraction : irefraction);
    vec3 rsky   = skyColor(sp, ref);
    const vec3 dcol = HSV2RGB(vec3(0.6, 0.85, 1.0));
    vec3 col = vec3(0.0);
    col += dcol*dif*dif*(1.0-mat.x);
    col += rsky*mat.y*fre*vec3(1.0)*smoothstep(1.0, 0.9, fre);

    if (isInside) {
      ragg *= exp(-st*beer) * mat_obj_level;
    }
    agg += ragg*col;

    ragg *= mat.x;
    if (refr == vec3(0.0)) {
      rd = ref;
    } else {
      isInside = !isInside;
      rd = refr;
    }

    
    ro = sp+initt*rd;
  }

  return agg;
}

vec3 effect(vec2 p) {
  g_rot = rot_x(0.2*mat_time * mat_roll)*rot_y(0.3*mat_time * mat_spin);
  vec3 ro = 0.6*vec3(0.0, 2.0, 5.0);
  const vec3 la = vec3(0.0, 0.0, 0.0);
  const vec3 up = vec3(0.0, 1.0, 0.0);

  vec3 ww = normalize(la - ro);
  vec3 uu = normalize(cross(up, ww ));
  vec3 vv = normalize(cross(ww,uu));
  float fov = tan(TAU/6.) * mat_fov;
  vec3 rd = normalize(-p.x*uu + p.y*vv + fov*ww);

  vec3 col = render(ro, rd);

  return col;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 q = uv + vec2(0.5);
    vec2 p = uv;

    vec3 col = vec3(0.0);
    col = effect(p);
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
        out_color.rgb = mat_hsv2rgb(hsv);
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
