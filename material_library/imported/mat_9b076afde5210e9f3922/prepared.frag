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
uniform vec4 uMMParam003; // native input: mat_y_limit
float mat_y_limit = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_aspect
float mat_aspect = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_a1_range
float mat_a1_range = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_a1_speed
float mat_a1_speed = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_a1_offset
float mat_a1_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_a1_strob
float mat_a1_strob = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_a2_range
float mat_a2_range = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_a2_speed
float mat_a2_speed = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam013.x > 0.5;
uniform vec4 uMMParam014; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_a2_offset
float mat_a2_offset = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_a2_strob
float mat_a2_strob = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_a3_range
float mat_a3_range = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_a3_speed
float mat_a3_speed = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_a3_bpm_sync
bool mat_a3_bpm_sync = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_a3_reverse
bool mat_a3_reverse = uMMParam020.x > 0.5;
uniform vec4 uMMParam021; // native input: mat_a3_offset
float mat_a3_offset = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_a3_strob
float mat_a3_strob = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_a4_range
float mat_a4_range = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_a4_speed
float mat_a4_speed = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_a4_bpm_sync
bool mat_a4_bpm_sync = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_a4_reverse
bool mat_a4_reverse = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_a4_offset
float mat_a4_offset = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_a4_strob
float mat_a4_strob = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_a5_speed
float mat_a5_speed = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_a5_bpm_sync
bool mat_a5_bpm_sync = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: mat_a5_reverse
bool mat_a5_reverse = uMMParam031.x > 0.5;
uniform vec4 uMMParam032; // native input: mat_a5_offset
float mat_a5_offset = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_a5_strob
float mat_a5_strob = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_crest
float mat_crest = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_gain_1
float mat_gain_1 = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_gain_2
float mat_gain_2 = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_gain_3
float mat_gain_3 = uMMParam037.x;
uniform vec4 uMMParam038; // native input: mat_gain_4
float mat_gain_4 = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_gain
float mat_gain = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_brightness
float mat_brightness = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_contrast
float mat_contrast = uMMParam041.x;
uniform vec4 uMMParam042; // native input: mat_saturation
float mat_saturation = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_hue_shift
float mat_hue_shift = uMMParam043.x;
uniform vec4 uMMParam044; // native input: mat_invert
bool mat_invert = uMMParam044.x > 0.5;
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);
float mat_a3_time_source = uTDTime * (mat_a3_speed);
float mat_a4_time_source = uTDTime * (mat_a4_speed);
float mat_a5_time_source = uTDTime * (mat_a5_speed);

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
    //vec4 MM_LIBRARY_p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    //vec4 q = mix(vec4(MM_LIBRARY_p.xyw, c.r), vec4(c.r, MM_LIBRARY_p.yzx), step(MM_LIBRARY_p.x, c.r));
    vec4 MM_LIBRARY_p = c.g < c.b ? vec4(c.bg, K.wz) : vec4(c.gb, K.xy);
    vec4 q = c.r < MM_LIBRARY_p.x ? vec4(MM_LIBRARY_p.xyw, c.r) : vec4(c.r, MM_LIBRARY_p.yzx);
    
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 MM_LIBRARY_p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(MM_LIBRARY_p - K.xxx, 0.0, 1.0), c.y);
}

float rgb2hue(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 MM_LIBRARY_p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(MM_LIBRARY_p.xyw, c.r), vec4(c.r, MM_LIBRARY_p.yzx), step(MM_LIBRARY_p.x, c.r));

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

float mat_a1_time = (mat_a1_time_source - mat_a1_offset * 8.) * 0.5;
float mat_a2_time = (mat_a2_time_source - mat_a2_offset * 8.) * 0.5;
float mat_a3_time = (mat_a3_time_source - mat_a3_offset * 8.) * 0.5;
float mat_a4_time = (mat_a4_time_source - mat_a4_offset * 8.) * 0.5;
float mat_a5_time = (mat_a5_time_source - mat_a5_offset * 8.) * 0.5;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}









#define p(t, a, b, c, d) ( a + b*cos( 6.28318*(c*t+d) ) ) 

#define S(x,y,z) smoothstep(x,y,z)

float w(float x, float p){ 
    x *= 5. * mat_aspect;

    
    

    float t1= p*.5+sin(mat_a1_time*.25)*10.5;
    float t2= p*.5+sin(mat_a2_time*.25)*10.5;
    float t3= p*.5+sin(mat_a3_time*.25)*10.5;
    float t4= p*.5+sin(mat_a4_time*.25)*10.5;
    

    return (sin(x*.25 + t1)*5.*mat_a1_range + sin(x*4.5 + t2*3.)*.2*mat_a2_range + sin(x + t3*3.)*2.3 * mat_a3_range  + sin(x*.8 + t4*1.1)*2.5 * mat_a4_range)*0.275;

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

    vec2 r = vec2(1.);
    vec2 st = uv;

    float   th = .05 
            ,sm = 15./r.y+.85*length(S(vec2(01.,.2),vec2(2.,.7),abs(st))) 
            ,c = 0.
            ,t = mat_a5_time*0.25
            ,n = floor((st.y+t)/.1)
            ,y = fract((st.y+t)/.1);

    vec3 clr;
    for (float i = -5.;i<5.;i++)
    {
        float f = w(st.x,(n-i))-y-i;
        c = mix(c,0. + mat_gain - 1.,S(-0.3 / mat_crest,abs(st.y),f));
        c += S(th+sm,th-sm,abs(f))
            *(1.-abs(st.y)*.75 / mat_y_limit)
            + S(5.5 *-abs(f*0.5),0.,f)*0.25;

        clr = mix(clr,p(sin((n-i)*.15),vec3(.5 * mat_gain_1),vec3(.5 * mat_gain_2), vec3(.270 * mat_gain_3), vec3(.0,.05,0.15) * mat_gain_4)*c,S(-0.3,abs(st.y),f));
    }
    out_color = vec4(clr,1.);


    
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
