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
uniform vec4 uMMParam003; // native input: mat_height
float mat_height = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_a1_speed
float mat_a1_speed = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_a1_offset
float mat_a1_offset = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_a1_strob
float mat_a1_strob = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_a2_speed
float mat_a2_speed = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_a2_offset
float mat_a2_offset = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_a2_strob
float mat_a2_strob = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_a3_speed
float mat_a3_speed = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_a3_bpm_sync
bool mat_a3_bpm_sync = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_a3_reverse
bool mat_a3_reverse = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_a3_offset
float mat_a3_offset = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_a3_offset_scale
float mat_a3_offset_scale = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_a3_strob
float mat_a3_strob = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_brightness
float mat_brightness = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_contrast
float mat_contrast = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_saturation
float mat_saturation = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_hue_shift
float mat_hue_shift = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_invert
bool mat_invert = uMMParam026.x > 0.5;
float mat_a1_source = uTDTime * (mat_a1_speed);
float mat_a2_source = uTDTime * (mat_a2_speed);
float mat_a3_source = uTDTime * (mat_a3_speed);

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

float mat_a1_time = mat_a1_source - mat_a1_offset * 8. * mat_a1_offset_scale;
float mat_a2_time = mat_a2_source - mat_a2_offset * 8. * mat_a2_offset_scale;
float mat_a3_time = mat_a3_source - mat_a3_offset * 8. * mat_a3_offset_scale;


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


float st=.025, maxdist=15.;
vec3 ldir=vec3(0.,-1.,-1.),col=vec3(0.);

mat2 rot(float a) {
    float s=sin(a),c=cos(a);
    return mat2(c,s,-s,c);
}

vec3 fractal(vec2 p) {
    vec2 pos=p;
    float d, ml=100.;
    vec2 mc=vec2(100.);
    p=abs(fract(p*.1)-.5);
    vec2 c=p;
    for(int i=0;i<8;i++) {
        d=dot(p,p);
        p=abs(p+1.)-abs(p-1.)-p;
        p=p*-1.5/clamp(d,.5,1.)-c;
        mc=min(mc,abs(p));
        if (i>2) ml=min(ml*(1.+float(i)*.1),abs(p.y-.5));
    }
    mc=max(vec2(0.),1.-mc);
    mc=normalize(mc)*.8;
    ml=pow(max(0.,1.-ml),6.);
    return vec3(mc,d*.4)*ml*(step(.7,fract(d*.1+mat_a3_time*.5+pos.x*.2)))-ml*.1;
}

float map(vec2 p) {
    vec2 pos=p;
    float t=mat_a1_time;
    col+=fractal(p);
    vec2 p2=abs(.5-fract(p*8.+4.));
    float h=0.;
    h+=sin(length(p)+t);
    p=floor(p*2.+1.);
    float l=length(p2*p2);
    h+=(cos(p.x+t)+sin(p.y+t))*.5;
    h+=max(0.,5.-length(p-vec2(18.,0.)))*1.5;
    h+=max(0.,5.-length(p+vec2(18.,0.)))*1.5;
    p=p*2.+.2345;
    t*=.5;
    h+=(cos(p.x+t)+sin(p.y+t))*.3;
    return h * mat_height;
}

vec3 normal(vec2 p, float td) {
    vec2 eps=vec2(0.,.001);
    return normalize(vec3(map(p+eps.yx)-map(p-eps.yx),2.*eps.y,map(p+eps.xy)-map(p-eps.xy)));
}

vec2 hit(vec3 p) {
    float h=map(p.xz);
    return vec2(step(p.y,h),h);
}

vec3 bsearch(vec3 from,vec3 dir,float td) {
    vec3 p;
    st*=-.5;
    td+=st;
    float h2=1.;
    for (int i=0;i<20;i++) {
        p=from+td*dir;
        float h=hit(p).x;
        if (abs(h-h2)>.001) {
            st*=-.5;
            h2=h;
        }
        td+=st;
    }
    return p;
}

vec3 shade(vec3 p,vec3 dir,float h,float td) {
    ldir=normalize(ldir);
    col=vec3(0.);
    vec3 n=normal(p.xz,td);
    col*=.25;
    float dif=max(0.,dot(ldir,-n));
    vec3 ref=reflect(ldir,dir);
    float spe=pow(max(0.,dot(ref,-n)),8.);
    return col+(dif*.5+.2+spe*vec3(1.,.8,.5))*.2;
}


vec3 march(vec3 from, vec3 dir, float y) {
    vec3 p, col=vec3(0.);
    float td=.5, k=0.;
    vec2 h;
    for (int i=0;i<600;i++) {
        p=from+dir*td;
        h=hit(p);
        if (h.x>.5||td>maxdist) break;
        td+=st;
    }
    if (h.x>.5) {
        p=bsearch(from,dir,td);
        col=shade(p,dir,h.y,td);
    } else {
    }
    
    col=mix(col,2.*vec3(mod(y,4.)*.1),pow(td/maxdist,3.));
    return col*vec3(.9,.8,1.);
}

mat3 lookat(vec3 dir,vec3 up) {
    dir=normalize(dir);vec3 rt=normalize(cross(dir,normalize(up)));
    return mat3(rt,cross(rt,dir),dir);
}

vec3 path(float t) {
    return vec3(cos(t)*5.5,1.5-cos(t)*.0,sin(t*2.))*2.5;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord;
    uv.y = 1. - uv.y;
    uv -= vec2(0.5);


    uv *= mat_scale;

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    vec2 uv_shift = mat_shift_amount;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    uv_shift += vec2(0.5);
    uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate) / 360);
    uv_shift -= vec2(0.5);

    uv += uv_shift;

    float t=mat_a2_time*.2;
    vec3 from=path(t);
    vec3 dir=normalize(vec3(uv,.7));
    vec3 adv=path(t+.1)-from;
    dir=lookat(adv+vec3(0.,-.2-(1.+sin(t*2.)),0.),vec3(adv.x*.1,1.,0.))*dir;
    vec3 col=march(from, dir, uv.y * 1000.)*1.5;
    out_color = vec4(col,1.);




    
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
