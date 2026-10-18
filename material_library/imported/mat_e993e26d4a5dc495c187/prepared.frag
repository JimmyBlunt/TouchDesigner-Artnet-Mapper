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
uniform vec4 uMMParam003; // native input: mat_radius_1
float mat_radius_1 = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_constant_sphere_radius
bool mat_constant_sphere_radius = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: mat_radius_2
float mat_radius_2 = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_density
float mat_density = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_layers
int mat_layers = int(round(uMMParam007.x));
uniform vec4 uMMParam008; // native input: mat_p1
float mat_p1 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_p2
float mat_p2 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_a1_speed
float mat_a1_speed = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_a1_offset
float mat_a1_offset = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_a1_strob
float mat_a1_strob = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_a2_speed
float mat_a2_speed = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_a2_offset
float mat_a2_offset = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_a2_strob
float mat_a2_strob = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_back_lvl
float mat_back_lvl = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_back_alpha
bool mat_back_alpha = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_brightness
float mat_brightness = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_contrast
float mat_contrast = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_saturation
float mat_saturation = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_hue_shift
float mat_hue_shift = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_invert
bool mat_invert = uMMParam028.x > 0.5;
float mat_a1_source = uTDTime * (mat_a1_speed);
float mat_a2_source = uTDTime * (mat_a2_speed);

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

float mat_a1_time = (mat_a1_source - mat_a1_offset * 8. * mat_a1_offset_scale) * 0.25;
float mat_a2_time = (mat_a2_source - mat_a2_offset * 8. * mat_a2_offset_scale) * 0.25;

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



float de(vec3 p, float time)
{
    float inner_sphere_scale = 0.7;
    float s=4.0 * mat_density;
    float t=fract(time/0.6);
    float scale=pow(inner_sphere_scale, -t);
    float d=1e4;

    for(int i = 0; i < mat_layers; i += 1)
    {
        vec3 z=p/scale,az=abs(z),w=z;

        if(az.x>az.y && az.x>az.z)
            w/=w.x*sign(w.x);
        else if(az.y>az.x && az.y>az.z)
            w/=w.y*sign(w.y);
            else
                w/=w.z*sign(w.z);

            w=normalize(floor(w*s+vec3(0.5)))*0.4 * mat_radius_1;

        float r2 = mat_radius_2;

        if (!mat_constant_sphere_radius) {
            r2 *=max(az.x, az.y) * 3.;
        }

        d=min(d,(distance(z,w) - r2*0.02*min(1.0, (float(i) + 1.0 - t) / 1.5))*scale);
        scale*=inner_sphere_scale;
    }

    return d;
}

mat3 rotateXMat(float a)
{
    return mat3(1.0, 0.0, 0.0, 0.0, cos(a), -sin(a), 0.0, sin(a), cos(a));
}

mat3 rotateYMat(float a)
{
    return mat3(cos(a), 0.0, -sin(a), 0.0, 1.0, 0.0, sin(a), 0.0, cos(a));
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale * 2.;

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


    float time=mat_a1_time+10.63;

    mat3 m=rotateXMat(mat_a2_time*0.5)*rotateYMat(mat_a2_time*0.7);

    vec2 p=uv;

    vec3 ro=m*vec3(0.0,0.0,0.4);
    vec3 rd=m*normalize(vec3(p, -2.0));

    float t=0.0;

    for(int i=0;i<120;i+=1)
    {
        float d=de(ro+rd*t, time);
        if(abs(d)<1e-4)
            break;
        t+=d;
    }

    vec3 rp=ro+rd*t;

    vec3 col;

    if (mat_back_alpha) {
        col = vec3(0.);
    } else {
        col = mix(vec3(1.0,1.0,0.5) * mat_back_lvl,vec3(1.0,0.5,0.25)*0.1 * mat_back_lvl,pow(abs(rd.y),0.5));
    }

    

    if(t<20.0)
    {
        float e=1e-3, c=de(rp, time);
        vec3 n=normalize(vec3(de(rp+vec3(e,0.0,0.0), time)-c,de(rp+vec3(0.0,e,0.0), time)-c,de(rp+vec3(0.0,0.0,e), time)-c));

        col=mix(vec3(0.0),vec3(1.7,0.6,0.2)*5.0*mix(0.6,1.0,(0.5+0.5*cos(time*30.0))),
                pow(0.5+0.5*cos(rp.x*50.0+sin(rp.y*10.0)*3.0+cos(rp.z*4.0)),3.0));

        col*=vec3(mix(0.3,2.0,0.5+0.5*dot(n,rd)));

        col+=vec3(pow(clamp(0.5+0.5*dot(n,rd),0.0,1.0),2.0))*0.6;

        vec3 l=normalize(vec3(1.0,1.0,-1.0)-rp);
        vec3 h=normalize(normalize(l)+normalize(-rd));

        col+=vec3(pow(clamp(0.5+0.5*dot(h,n),0.0,1.0),80.0))*0.7;
    }

    if (!mat_back_alpha) {
        col+=(0.03+cos(time*7.0)*0.01)*mix(vec3(0.1,0.5,0.0)*0.3,vec3(1.2,0.7,0.1),0.5+0.5*cos(p.y*0.3+sin(p.x*0.1+time)*6.0)*sin(p.y)) * mat_back_lvl;
    }

    out_color.rgb=sqrt(col);
    out_color.a = 1.;


    if (mat_back_alpha) {
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
