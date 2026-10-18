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
uniform vec4 uMMParam008; // native input: mat_flip_x
bool mat_flip_x = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_flip_y
bool mat_flip_y = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: mat_fov
float mat_fov = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_dist
float mat_dist = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_tilt
float mat_tilt = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_cam1
vec2 mat_cam1 = uMMParam013.xy;
uniform vec4 uMMParam014; // native input: mat_cam2
vec2 mat_cam2 = uMMParam014.xy;
uniform vec4 uMMParam015; // native input: mat_expand
float mat_expand = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_mod1
float mat_mod1 = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_mod2
float mat_mod2 = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_mod3
float mat_mod3 = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_mod4
float mat_mod4 = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_light_pos
vec2 mat_light_pos = uMMParam020.xy;
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
uniform vec4 uMMParam029; // native input: mat_front_color
vec4 mat_front_color = uMMParam029;
uniform vec4 uMMParam030; // native input: mat_back_color
vec4 mat_back_color = uMMParam030;
uniform vec4 uMMParam031; // native input: mat_brightness
float mat_brightness = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_contrast
float mat_contrast = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_invert
bool mat_invert = uMMParam033.x > 0.5;
uniform vec4 uMMParam034; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam034.x));
uniform vec4 uMMParam035; // native input: mat_back_thresh
float mat_back_thresh = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_back_sensitivity
float mat_back_sensitivity = uMMParam036.x;
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

float mat_time = (mat_time_source - mat_offset * 8. * mat_offset_scale) * 2.;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

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



    vec2 uv_shift = mat_shift_amount * mat_shift_scale * 2.;
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

#define ROT(a)      mat2(cos(a), sin(a), -sin(a), cos(a))
#define PCOS(x)     (0.5+0.5*cos(x))


float rayTorus(vec3 ro, vec3 rd, vec2 tor) {
  float po = 1.0;

  float Ra2 = tor.x*tor.x * mat_expand;
  float ra2 = tor.y*tor.y;

  float m = dot(ro,ro);
  float n = dot(ro,rd);

  
  {
    float h = n*n - m + (tor.x+tor.y)*(tor.x+tor.y);
    if(h<0.0) return -1.0;

    
  }

  
  float k = (m - ra2 - Ra2)/2.0;
  float k3 = n;
  float k2 = n*n + Ra2*rd.z*rd.z + k;
  float k1 = k*n + Ra2*ro.z*rd.z;
  float k0 = k*k + Ra2*ro.z*ro.z - Ra2*ra2;

  #ifndef TORUS_REDUCE_PRECISION
  
  if(abs(k3*(k3*k3 - k2) + k1) < 0.01)
  {
    po = -1.0;
    float tmp=k1; k1=k3; k3=tmp;
    k0 = 1.0/k0;
    k1 = k1*k0;
    k2 = k2*k0;
    k3 = k3*k0;
  }
  #endif

  float c2 = 2.0*k2 - 3.0*k3*k3;
  float c1 = k3*(k3*k3 - k2) + k1;
  float c0 = k3*(k3*(-3.0*k3*k3 + 4.0*k2) - 8.0*k1) + 4.0*k0;


  c2 /= 3.0;
  c1 *= 2.0;
  c0 /= 3.0;

  float Q = c2*c2 + c0;
  float R = 3.0*c0*c2 - c2*c2*c2 - c1*c1;

  float h = R*R - Q*Q*Q;
  float z = 0.0;
  if(h < 0.0) {
    
    float sQ = sqrt(Q);
    z = 2.0*sQ*cos(acos(R/(sQ*Q)) / 3.0);
  } else {
    
    float sQ = pow(sqrt(h) + abs(R), 1.0/3.0);
    z = sign(R)*abs(sQ + Q/sQ);
  }
  z = c2 - z;

  float d1 = z   - 3.0*c2;
  float d2 = z*z - 3.0*c0;
  if(abs(d1) < 1.0e-4) {
    if(d2 < 0.0) return -1.0;
    d2 = sqrt(d2);
  } else {
    if(d1 < 0.0) return -1.0;
    d1 = sqrt(d1/2.0);
    d2 = c1/d1;
  }

  

  float result = 1e20;

  h = d1*d1 - z + d2;
  if(h > 0.0) {
    h = sqrt(h);
    float t1 = -d1 - h - k3; t1 = (po<0.0)?2.0/t1:t1;
    float t2 = -d1 + h - k3; t2 = (po<0.0)?2.0/t2:t2;
    if(t1 > 0.0) result=t1;
    if(t2 > 0.0) result=min(result,t2);
  }

  h = d1*d1 - z - d2;
  if(h > 0.0) {
    h = sqrt(h);
    float t1 = d1 - h - k3;  t1 = (po<0.0)?2.0/t1:t1;
    float t2 = d1 + h - k3;  t2 = (po<0.0)?2.0/t2:t2;
    if(t1 > 0.0) result=min(result,t1);
    if(t2 > 0.0) result=min(result,t2);
  }

  return result;
}


vec3 torusNormal(vec3 pos, vec2 tor) {
  return normalize(pos*(dot(pos,pos)- tor.y*tor.y - tor.x*tor.x*vec3(1.0,1.0,-1.0)));
}


float tanh_approx(float x) {
  
  
  float x2 = x*x;
  return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0);
}

vec3 color(vec2 p, vec2 q) {
  float rdd = 2.0 * mat_fov;
  vec3 ro  = 1.*vec3(0. + mat_cam2.x * 0.5, 0.75 * mat_dist, -0.2 + mat_cam2.y * 0.5);
  vec3 la  = vec3(0.0 + mat_cam1.x, 0.0  - pow(mat_tilt,2.), 0.2 - mat_cam1.y);
  vec3 up  = vec3(0.3, 0.0, 1.0);
  vec3 lp1 = ro;
  lp1.xy  *= ROT(0.85 + mat_light_pos.x * 2.);
  lp1.xz  *= ROT(-0.5 + mat_light_pos.y);

  vec3 ww = normalize(la - ro);
  vec3 uu = normalize(cross(up, ww));
  vec3 vv = normalize(cross(ww,uu));
  vec3 rd = normalize(p.x*uu + p.y*vv + rdd*ww);

  const vec2 tor = 0.55*vec2(1.0, 0.75);
  float td    = rayTorus(ro, rd, tor) * mat_mod4;
  vec3  tpos  = ro + rd*td;

  tpos.x *= mat_mod1;
  tpos.y *= mat_mod2;
  tpos.z *= mat_mod3;
  vec3  tnor  = -torusNormal(tpos, tor);
  vec3  tref  = reflect(rd, tnor);

  vec3  ldif1 = lp1 - tpos;
  float ldd1  = dot(ldif1, ldif1);
  float ldl1  = sqrt(ldd1);
  vec3  ld1   = ldif1/ldl1;
  vec3  sro   = tpos+0.05*tnor;
  float sd    = rayTorus(sro, ld1, tor);
  vec3  spos  = sro+ld1*sd;
  vec3  snor  = -torusNormal(spos, tor);

  float dif1  = max(dot(tnor, ld1), 0.0);
  float spe1  = pow(max(dot(tref, ld1), 0.0), 10.0);
  float r     = length(tpos.xy);
  float a     = atan(tpos.y, tpos.x)-PI*tpos.z/(r+0.5*abs(tpos.z))-(mat_time * TAU)/45.0;
  float s     = mix(0.05, 0.5, tanh_approx(2.0*abs(td-0.75)));
  vec3  bcol0 = vec3(0.3);
  vec3  bcol1 = vec3(0.025);
  vec3  tcol  = mix(bcol0, bcol1, smoothstep(-s, s, sin(9.0*a)));

  vec3 col = vec3(0.0);

  if (td > -1.0) {
    col += tcol*mix(0.2, 1.0, dif1/ldd1)+0.25*spe1;
    col *= sqrt(abs(dot(rd, tnor)));
  }

  if (sd < ldl1) {
    col *= mix(1.0, 0.0, pow(abs(dot(ld1, snor)), 3.0*tanh_approx(sd)));
  }

  return col;
}


vec3 postProcess(vec3 col, vec2 q) {
  col = clamp(col, 0.0, 1.0);
  col = pow(col, 1.0/vec3(2.2));
  col = col*0.6+0.4*col*col*(3.0-2.0*col);
  col = mix(col, vec3(dot(col, vec3(0.33))), -0.4);
  col *=0.5 * mat_brightness+0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y),0.7) * mat_light;
  return col;
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    if (mat_flip_x) {
        uv.x = 1. - uv.x;
    }
    if (mat_flip_y) {
        uv.y = 1. - uv.y;
    }

    vec2 q = texCoord;
    vec2 p = uv;

    
    
    vec3 col = color(p, q);
    col = postProcess(col, q);
    out_color = vec4(col, 1.0);

    
    if (mat_invert) out_color.rgb=1-out_color.rgb;

    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    const vec3 AvgLumin = vec3(0.5, 0.5, 0.5);
    vec3 intensity = vec3(dot(out_color.rgb, LumCoeff));
    out_color.rgb = mix(AvgLumin, out_color.rgb, mat_contrast);

    
    if (mat_back_mode == 1) {
        
        if (mat_luma(out_color.rgb) < mat_back_thresh) {
            out_color = mat_back_color;
        } else {
            out_color = mat_front_color;
        }
    } else {
        
        out_color = mix(mat_back_color, mat_front_color, mat_luma(out_color.rgb) * mat_back_sensitivity + mat_back_thresh);
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
