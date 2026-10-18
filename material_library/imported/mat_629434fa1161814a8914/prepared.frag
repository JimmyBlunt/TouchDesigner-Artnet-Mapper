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
uniform vec4 uMMParam003; // native input: mat_deform_1
float mat_deform_1 = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_deform_2
float mat_deform_2 = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_deform_3
float mat_deform_3 = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_size_1
float mat_size_1 = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_size_2
float mat_size_2 = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_size_3
float mat_size_3 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_f1
float mat_f1 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_f2
float mat_f2 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_speed
float mat_speed = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_reverse
bool mat_reverse = uMMParam013.x > 0.5;
uniform vec4 uMMParam014; // native input: mat_offset
float mat_offset = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_offset_scale
float mat_offset_scale = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_strob
float mat_strob = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_scroll_speed
float mat_scroll_speed = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_scroll_bpm_sync
bool mat_scroll_bpm_sync = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_scroll_reverse
bool mat_scroll_reverse = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_scroll_offset
float mat_scroll_offset = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_scroll_offset_scale
float mat_scroll_offset_scale = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_scroll_strob
float mat_scroll_strob = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_background
bool mat_background = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_back_color
vec4 mat_back_color = uMMParam024;
uniform vec4 uMMParam025; // native input: mat_back_thresh
float mat_back_thresh = uMMParam025.x;
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

float mat_time = (mat_time_source - mat_offset * 8. * mat_offset_scale) * 0.5;
float mat_scroll_time = (mat_scroll_time_source - mat_scroll_offset * 8. * mat_scroll_offset_scale) * 0.5;

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





float rand(vec2 coord){
    return fract(sin(dot(coord,vec2(12.9898,78.233)))*
        43758.5453123);
}




float noise1D(float coord){

    float cellId = floor(coord);
    float cellFraction = fract(coord);
    
    
    return rand(vec2(cellId));
}



float noise2D(vec2 coord){
    vec2 id = floor(coord);
    vec2 fraction = fract(coord);
    
    float a = rand(id);
    float b = rand(id + vec2(1.,0.));
    float c = rand(id + vec2(0.,1.));
    float d = rand(id + vec2(1.,1.));

    
    vec2 smoothCorners = smoothstep(0.,1.,fraction);
    

    
    return mix(a,b,smoothCorners.x) +
           (c - a) * smoothCorners.y * (1.- smoothCorners.x) +
           (d - b) * smoothCorners.x * smoothCorners.y;
}




float drawSquare (vec2 coord, float a, float blur){
    float band1 = smoothstep(a+blur,a-blur,coord.x);
    float band2 = smoothstep(-a-blur,-a+blur,coord.x);
    float band3 = smoothstep(a+blur,a-blur,coord.y);
    float band4 = smoothstep(-a-blur,-a+blur,coord.y);
    return band1*band2*band3*band4;
}



mat2 rotate(float angle){

    return mat2(cos(angle), -sin(angle),
                sin(angle), cos(angle));

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

    float mat_time_orig = mat_time;

    float noise1d1 = noise1D(uv.x*65. * mat_deform_1)*.1;
    float noise1d2 = noise1D(uv.y*15.);
    
    
    

    

    float timeRemapped = (((sin(mat_time))*.5)+.5)*1. * mat_f1;
    float timeSin = sin(mat_time) * mat_f1;
    float timeCos = cos(mat_time) * mat_f1;


   

    vec2 uv2 = abs(uv*.15*150.*(noise1d1*sin(mat_time*1.21))) * mat_deform_2;




    vec2 uv3 = (uv*.15*50. * mat_deform_3);


    

    vec2 uvSquareRot1 = uv*1.7 * mat_size_1;
    vec2 uvSquareRot2 = uv*2.2 * mat_size_2;
    vec2 uvSquareRot3 = uv*2. * mat_size_3;

    
    



    


    vec3 col = vec3(.0);
    vec3 blue = vec3(0.,.5,1.);
    vec3 green = vec3(0.,.7,0.);
    vec3 red = vec3(1.,0.,0.);
    
    float noise1 = noise2D(vec2(uv2.x+mat_time,uv2.y)) *
                  noise2D(vec2(-uv2.x+mat_time,uv2.y)) *
                  noise2D(vec2(-uv2.x,-uv2.y+mat_time)) *
                  noise2D(vec2(uv2.x,-uv2.y+mat_time))
                  ;
    float noise2 = noise2D(vec2(uv3.x+mat_time,uv3.y)) *
                  noise2D(vec2(-uv3.x+mat_time,uv3.y)) *
                  noise2D(vec2(-uv3.x,-uv3.y+mat_time)) *
                  noise2D(vec2(uv3.x,-uv3.y+mat_time))
                  ;
    
    uv2.x += noise1*1.5;



    float noise3x = noise2D(vec2(uv2.x*1.+mat_time*1.1+mat_time));
    noise3x += noise2D(vec2(uv2.x*2.));
    float noise3y = noise2D(vec2(uv3.y*1.+mat_scroll_time*5.));


    

    float time = mat_time*-2.5*mat_f2;




    
    
    

    
    col = 1.-col;

    uvSquareRot1.y += ((noise3x-.5)*.2)*10.* timeSin;
    uvSquareRot2.y += ((noise3x-.5)*.2)*10.* timeSin;
    uvSquareRot3.y += ((noise3x-.5)*.2)*10.* timeSin;

   

    uvSquareRot1.x += ((noise3y-.5)*.2)*5.* timeCos*3.;
    uvSquareRot2.x += ((noise3y-.5)*.2)*5.* timeCos*2.;
    uvSquareRot3.x += ((noise3y-.5)*.2)*5.* timeCos*1.;

    uvSquareRot1 *= rotate(1. * time*.1 *noise1d1*15.); 
    uvSquareRot2 *= rotate(-1. * time*.5);
    uvSquareRot3 *= rotate(1. * time*.25 );

    col *= (drawSquare(uvSquareRot1,.55+noise1,.2) - drawSquare(uvSquareRot1,.55*.99 + noise1,.01)) * blue*.7 +
           (drawSquare(uvSquareRot1,1.+noise1,.2) - drawSquare(uvSquareRot1,1.*.9 + noise1,.01)) * blue*.1 +
           (drawSquare(uvSquareRot2,.5+noise1,.1)- drawSquare(uvSquareRot2,.5*.9 + noise1,.01)) * blue *.5 +
           (drawSquare(uvSquareRot3,.35+noise1,.3) - drawSquare(uvSquareRot3,.35*.9 + noise1,.01)) * blue *1. +
           drawSquare(uvSquareRot3,.1+noise1,.05);


    col += vec3(pow(max(col.x,0.0),1.5));
    col += vec3(pow(max(col.y,0.0),.9));
    col += vec3(pow(max(col.z,0.0),3.5));

   





    

    out_color = vec4(col,1.0);

    if (mat_background) {
        if (mat_luma(out_color) < (0.02 * mat_back_thresh)) {
            out_color = mat_back_color;
        }
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
