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
uniform vec4 uMMParam007; // native input: mat_inner_sphere
bool mat_inner_sphere = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_poly_u
float mat_poly_u = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_poly_v
float mat_poly_v = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_poly_m
float mat_poly_m = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_poly_type
int mat_poly_type = int(round(uMMParam011.x));
uniform vec4 uMMParam012; // native input: mat_container_size
float mat_container_size = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_orbit
vec2 mat_orbit = uMMParam013.xy;
uniform vec4 uMMParam014; // native input: mat_orbit_speed
float mat_orbit_speed = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_orbit_bpm_sync
bool mat_orbit_bpm_sync = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_orbit_reverse
bool mat_orbit_reverse = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_orbit_offset
float mat_orbit_offset = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_orbit_offset_scale
float mat_orbit_offset_scale = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_orbit_strob
float mat_orbit_strob = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_orbit_restart
int mat_orbit_restart = int(round(uMMParam020.x));
uniform vec4 uMMParam021; // native input: mat_speed
float mat_speed = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_reverse
bool mat_reverse = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_offset
float mat_offset = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_offset_scale
float mat_offset_scale = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_strob
float mat_strob = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_restart
int mat_restart = int(round(uMMParam027.x));
uniform vec4 uMMParam028; // native input: mat_light
float mat_light = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_gain
float mat_gain = uMMParam029.x;
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
float mat_orbit_time_source = uTDTime * (mat_orbit_speed);

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
float mat_orbit_time = mat_orbit_time_source - mat_orbit_offset * 8. * mat_orbit_offset_scale;

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













#define INNER_SPHERE


float poly_U        = mat_poly_u;  
float poly_V        = mat_poly_v;  
float poly_W        = mat_poly_m;  
int   poly_type     = mat_poly_type;    

const float zoom = 3.0;



#define TAU         (2.0*PI)

#define TOLERANCE       0.0001
#define MAX_RAY_LENGTH  20.0
#define MAX_RAY_MARCHES 60
#define NORM_OFF        0.001
#define MAX_BOUNCES     6



#define ROT(a)          mat2(cos(a), sin(a), -sin(a), cos(a))



float poly_cospin   = cos(PI/float(poly_type));
float poly_scospin  = sqrt(0.75-poly_cospin*poly_cospin);
vec3  poly_nc       = vec3(-0.5, -poly_cospin, poly_scospin);
vec3  poly_pab      = vec3(0., 0., 1.);
vec3  poly_pbc_     = vec3(poly_scospin, 0., 0.5);
vec3  poly_pca_     = vec3(0., poly_scospin, poly_cospin);
vec3  poly_p        = normalize((poly_U*poly_pab+poly_V*poly_pbc_+poly_W*poly_pca_));
vec3  poly_pbc      = normalize(poly_pbc_);
vec3  poly_pca      = normalize(poly_pca_);

const float initt = 0.125;


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
  return clamp((v*(a*v+b))/(v*(c*v+d)+e), 0.0f, 1.0f);
}


float tanh_approx(float x) {
  
  
  float x2 = x*x;
  return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0);
}


vec2 mod2(inout vec2 p, vec2 size) {
  vec2 c = floor((p + size*0.5)/size);
  p = mod(p + size*0.5,size) - size*0.5;
  return c;
}

float circle(vec2 p, float r) {
  return length(p) - r;
}


float box(vec2 p, vec2 b) {
  vec2 d = abs(p)-b;
  return length(max(d,0.0)) + min(max(d.x,d.y),0.0);
}


float pmin(float a, float b, float k) {
    float h = clamp( 0.5+0.5*(b-a)/k, 0.0, 1.0 );
    return mix( b, a, h ) - k*h*(1.0-h);
}


float rayPlane(vec3 ro, vec3 rd, vec4 p) {
  return -(dot(ro,p.xyz)+p.w)/dot(rd,p.xyz);
}


void poly_fold(inout vec3 pos) {
  vec3 p = pos;

  for(int i = 0; i < poly_type; ++i){
    p.xy  = abs(p.xy);
    p    -= 2.*min(0., dot(p,poly_nc)) * poly_nc;
  }

  pos = p / mat_container_size;
}

float poly_plane(vec3 pos) {
  float d0 = dot(pos, poly_pab);
  float d1 = dot(pos, poly_pbc);
  float d2 = dot(pos, poly_pca);
  float d = d0;
  d = max(d, d1);
  d = max(d, d2);
  return d;
}

float poly_corner(vec3 pos) {
  float d = length(pos) - .1;
  return d;
}

float dot2(vec3 p) {
  return dot(p, p);
}

float poly_edge(vec3 pos) {
  float dla = dot2(pos-min(0., pos.x)*vec3(1., 0., 0.));
  float dlb = dot2(pos-min(0., pos.y)*vec3(0., 1., 0.));
  float dlc = dot2(pos-min(0., dot(pos, poly_nc))*poly_nc);
  return sqrt(min(min(dla, dlb), dlc))-0.025;
}

float poly_planes(vec3 pos, out vec3 pp) {
  poly_fold(pos);
  pos -= poly_p;

  pp = pos;
  return poly_plane(pos);
}

float poly_edges(vec3 pos, out vec3 pp) {
  poly_fold(pos);
  pos -= poly_p;

  pp = pos;
  return poly_edge(pos);
}


float blobs(vec2 p) {
  
  vec2 bp = p;
  vec2 bn = mod2(bp, vec2(3.0));

  vec2 dp = p;
  vec2 dn = mod2(dp, vec2(0.25));
  float ddots = length(dp);

  
  float dblobs = 1E6;
  for (int i = 0; i < 5; ++i) {
    float dd = circle(bp-1.0*vec2(sin(mat_time+float(i)), sin(float(i*i)+mat_time*sqrt(0.5))), 0.1);
    dblobs = pmin(dblobs, dd, 0.35);
  }

  float d = 1E6;
  d = min(d, ddots);
  
  d = pmin(d, dblobs, 0.35);
  return d;
}

vec3 skyColor(vec3 ro, vec3 rd) {
  const vec3 gcol = HSV2RGB(vec3(0.45, 0.6, 1.0));
  vec3 col = clamp(vec3(0.0025/abs(rd.y))*gcol, 0.0, 1.0);

  float tp0  = rayPlane(ro, rd, vec4(vec3(0.0, 1.0, 0.0), 4.0));
  float tp1  = rayPlane(ro, rd, vec4(vec3(0.0, -1.0, 0.0), 6.0));
  float tp = tp1;
  tp = max(tp0,tp1);
  if (tp > 0.0) {
    vec3 pos  = ro + tp*rd;
    const float fz = 0.25;
    const float bz = 1.0/fz;
    vec2 bpos = pos.xz/bz;
    float db = blobs(bpos)*bz;
    db = abs(db);
    vec2 pp = pos.xz*fz;
    float m = 0.5+0.25*(sin(3.0*pp.x+mat_time*2.1)+sin(3.3*pp.y+mat_time*2.0));
    m *= m;
    m *= m;
    pp = fract(pp+0.5)-0.5;
    float dp = pmin(abs(pp.x), abs(pp.y), 0.125);
    dp = min(dp, db);
    vec3 hsv = vec3(0.4+mix(0.15,0.0, m), tanh_approx(mix(50.0, 10.0, m)*dp), 1.0);
    vec3 pcol = 1.5*hsv2rgb(hsv)*exp(-mix(30.0, 10.0, m)*dp);

    float f = 1.0-tanh_approx(0.1*length(pos.xz));
    col = mix(col, pcol , f);
  }


  if (tp1 > 0.0) {
    vec3 pos  = ro + tp1*rd;
    vec2 pp = pos.xz;
    float db = box(pp, vec2(6.0, 9.0))-1.0;

    col += vec3(2.0)*gcol*rd.y*smoothstep(0.25, 0.0, db);
    col += vec3(0.8)*gcol*exp(-0.5*max(db, 0.0));
  }


  return col * mat_light;
}

float dfExclusion(vec3 p, out vec3 pp) {
  return -poly_edges(p/zoom, pp)*zoom;
}

float shape(vec3 p) {
  vec3 pp;
  return poly_planes(p/zoom, pp)*zoom;
}

float df0(vec3 p) {
  float d0 = shape(p);
  float d = d0;
  return d;
}

float df1(vec3 p) {
  float d0 = -shape(p);
  float d = d0;
    if (mat_inner_sphere) {
      float d1 = length(p) - 2.;
      d = min(d, d1);
    }
  return d;
}

vec3 normal1(vec3 pos) {
  vec2  eps = vec2(NORM_OFF,0.0);
  vec3 nor;
  nor.x = df1(pos+eps.xyy) - df1(pos-eps.xyy);
  nor.y = df1(pos+eps.yxy) - df1(pos-eps.yxy);
  nor.z = df1(pos+eps.yyx) - df1(pos-eps.yyx);
  return normalize(nor);
}

float rayMarch1(vec3 ro, vec3 rd) {
  float t = 0.0;
  for (int i = 0; i < MAX_RAY_MARCHES; i++) {
    if (t > MAX_RAY_LENGTH) {
      t = MAX_RAY_LENGTH;
      break;
    }
    float d = df1(ro + rd*t);
    if (d < TOLERANCE) {
      break;
    }
    t  += d;
  }
  return t;
}

vec3 normal0(vec3 pos) {
  vec2  eps = vec2(NORM_OFF,0.0);
  vec3 nor;
  nor.x = df0(pos+eps.xyy) - df0(pos-eps.xyy);
  nor.y = df0(pos+eps.yxy) - df0(pos-eps.yxy);
  nor.z = df0(pos+eps.yyx) - df0(pos-eps.yyx);
  return normalize(nor);
}

float rayMarch0(vec3 ro, vec3 rd) {
  float t = 0.0;
  for (int i = 0; i < MAX_RAY_MARCHES; i++) {
    if (t > MAX_RAY_LENGTH) {
      t = MAX_RAY_LENGTH;
      break;
    }
    float d = df0(ro + rd*t);
    if (d < TOLERANCE) {
      break;
    }
    t  += d;
  }
  return t;
}

vec3 render1(vec3 ro, vec3 rd) {
  vec3 agg = vec3(0.0, 0.0, 0.0);
  float tagg = initt;
  vec3 ragg = vec3(1.0);

  for (int bounce = 0; bounce < MAX_BOUNCES; ++bounce) {
    float mragg = max(max(ragg.x, ragg.y), ragg.z);
    if (mragg < 0.1) break;
    float st = rayMarch1(ro, rd);
    tagg += st;
    vec3 sp = ro+rd*st;
    vec3 spp;
    float de = dfExclusion(sp, spp);
    vec3 sn = normal1(sp);

    float si = cos(5.0*TAU*zoom*spp.z-0.5*sp.y+mat_time);
    const vec3 lcol = vec3(1.0, 1.5, 2.0)*0.8;
    float lf = mix(0.0, 1.0, smoothstep(0., 0.9, si));

    vec3 gcol = ragg*lcol*exp(8.0*(min(de-0.2, 0.0)));
    
    if (de < 0.0) {
      agg += gcol;
      ragg *= vec3(0.5, 0.6,0.8);
    } else {
      agg += gcol*lf;
      agg += ragg*lcol*1.5*lf;
      ragg = vec3(0.0);
    }

    rd = reflect(rd, sn);
    ro = sp+initt*rd;
    tagg += initt;
  }
#if defined(GOT_BEER)
  return agg*exp(-.5*vec3(0.3, 0.15, 0.1)*tagg);
#else
  return agg;
#endif
}

vec3 render0(vec3 ro, vec3 rd) {
  vec3 skyCol = skyColor(ro, rd);

  vec3 col = skyCol;

  float st = rayMarch0(ro, rd);
  vec3 sp = ro+rd*st;
  vec3 sn = normal0(sp);
    vec3 spp;
  float de = dfExclusion(sp, spp);
  float ptime = mod(mat_time, 30.0);
  if (st < MAX_RAY_LENGTH) {
    float sfre = 1.0+dot(rd, sn);
    sfre *= sfre;
    sfre = mix(0.1, 1.0, sfre);
    vec3 sref   = reflect(rd, sn);
    vec3 srefr  = refract(rd, sn, 0.9);
    vec3 ssky = sfre*skyColor(sp, sref);

    if (de > 0.0) {
      col = ssky;
    } else {
      col = 0.5*sfre*ssky;
      vec3 col1 = (1.0-sfre)*render1(sp+srefr*initt, srefr);
      col += col1;
    }

  }

  return col;
}

vec3 effect(vec2 p) {
  vec3 ro = 0.8*vec3(0.0, 4.0, 5.0);
  const vec3 la = vec3(0.0, 0.0, 0.0);
  const vec3 up = vec3(0.0, 1.0, 0.0);
  float a = 0.5*(-0.5+0.5*sin(0.123*mat_orbit_time));
  float b = 0.1*mat_orbit_time;

    vec2 m = mat_orbit.xy;
    

    a -=2.0*m.y;
    b -=2.0*m.x;



  
  
  
  
  
  

  ro.yz *= ROT(a);
  ro.xz *= ROT(b);

  vec3 ww = normalize(la - ro);
  vec3 uu = normalize(cross(up, ww ));
  vec3 vv = normalize(cross(ww,uu));
  float fov = tan(TAU/6.0);
  vec3 rd = normalize(-p.x*uu + p.y*vv + fov*ww);

  vec3 col = render0(ro, rd);

  return col;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 q = uv + vec2(0.);
    vec2 p = uv;
    
    vec3 col = vec3(0.0);
    col = effect(p);
    col *= smoothstep(0.0, 4.0, mat_time);
    col = aces_approx(col) * pow(mat_gain,2.);
    col = sRGB(col);
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
