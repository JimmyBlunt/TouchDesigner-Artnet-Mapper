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
uniform vec4 uMMParam003; // native input: mat_p_offset
float mat_p_offset = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_p_deviation
float mat_p_deviation = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_p_edge
float mat_p_edge = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_speed
float mat_speed = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_reverse
bool mat_reverse = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_offset
float mat_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_offset_scale
float mat_offset_scale = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_strob
float mat_strob = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_shift_animate
bool mat_shift_animate = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_shift_angle
float mat_shift_angle = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_shift_speed
float mat_shift_speed = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_shift_bpm_sync
bool mat_shift_bpm_sync = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_shift_reverse
bool mat_shift_reverse = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_shift_offset
float mat_shift_offset = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_shift_strob
float mat_shift_strob = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_p_bump
float mat_p_bump = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_light_speed
float mat_light_speed = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_light_bpm_sync
bool mat_light_bpm_sync = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_light_reverse
bool mat_light_reverse = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_light_offset
float mat_light_offset = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_light_strob
float mat_light_strob = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_brightness
float mat_brightness = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_contrast
float mat_contrast = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_saturation
float mat_saturation = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_hue_shift
float mat_hue_shift = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_invert
bool mat_invert = uMMParam029.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_shift_time_source = uTDTime * (mat_shift_speed);
float mat_light_time_source = uTDTime * (mat_light_speed);

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

float mat_shift_time = mat_shift_time_source - mat_shift_offset;
float mat_light_time = (mat_light_time_source - mat_light_offset) * 0.5;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

















































#define OFFSET_ROW



mat2 rot2(in float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }



float hash21(vec2 p){  return fract(sin(dot(p, vec2(27.619, 57.583)))*43758.5453); }


vec2 cellID; 



vec2 hash22B(vec2 p) {

    
    
    
    
    float n = sin(dot(p, vec2(41, 289)));
    return fract(vec2(262144, 32768)*n)*2. - 1.;
    
}


float n2D3G( in vec2 p ){

    
    vec2 i = floor(p); p -= i;

    
    vec4 v;
    v.x = dot(hash22B(i), p);
    v.y = dot(hash22B(i + vec2(1, 0)), p - vec2(1, 0));
    v.z = dot(hash22B(i + vec2(0, 1)), p - vec2(0, 1));
    v.w = dot(hash22B(i + 1.), p - 1.);

    
    p = p*p*(3. - 2.*p);

    
    return mix(mix(v.x, v.y, p.x), mix(v.z, v.w, p.x), p.y);

}


float fBm(vec2 p){ return n2D3G(p)*.66 + n2D3G(p*2.)*.34; }


float bMap(vec2 p){

    
    p *= rot2(-PI/5.);

    #ifdef OFFSET_ROW
    
    if(mod(floor(p.y), 2.)<.5) p.x += .5 * mat_p_offset;
    #endif


    
    vec2 ip = floor(p);
    p -= ip + .5;

    
    cellID = ip;

    
    

    
    
    float ang = -3.14159*3./5. + (fBm(ip/8. + mat_time/3.))*6.2831*2.;
    
    
    vec2 offs = vec2(cos(ang), sin(ang))*.35 * mat_p_deviation;

    
    
    
    
    if(p.x<offs.x)  p.x = 1. - (p.x + .5)/abs(offs.x  + .5);
    else p.x = (p.x - offs.x)/(.5 - offs.x);

    if(p.y<offs.y) p.y = 1. - (p.y + .5)/abs(offs.y + .5);
    else p.y = (p.y - offs.y)/(.5 - offs.y);

    
    return 1. - max(p.x, p.y);
}




vec3 doBumpMap(in vec2 p, in vec3 n, float bumpfactor, inout float edge){

    
    
    vec2 e = vec2(.025, 0);

    float f = bMap(p); 
    float fx = bMap(p - e.xy); 
    float fy = bMap(p - e.yx); 
    float fx2 = bMap(p + e.xy); 
    float fy2 = bMap(p + e.yx); 

    vec3 grad = (vec3(fx - fx2, fy - fx2, 0))/e.x/2.;

    
    edge = length(vec2(fx, fy) + vec2(fx2, fy2) - f*2.);
    
    
    
    edge = smoothstep(0., 1., edge/e.x) * mat_p_edge;

    
    grad -= n*dot(n, grad);

    
    return normalize( n + grad*bumpfactor );

}



float doHatch(vec2 p, float res){


    
    p *= res/16.;

    
    float hatch = clamp(sin((p.x - p.y)*3.14159*200.)*2. + .5, 0., 1.); 

    
    
    float hRnd = hash21(floor(p*6.) + .73);
    if(hRnd>.66) hatch = hRnd;


    return hatch;


}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
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



    

    
    
    
    
    
    
    
    

    



    
    vec3 rd = normalize(vec3(uv, .5));

    
    const float gSc = 10.;
    
    vec2 p = uv*gSc;

    if (mat_shift_animate) {
        float shift_time_x = mat_shift_time * cos(PI * mat_shift_angle/360.0 * 2.);
        float shift_time_y = mat_shift_time * sin(PI * mat_shift_angle/360.0 * 2.);

        p += vec2(shift_time_x, shift_time_y) / 2.;

    }

    vec2 oP = p; 


    
    float m = bMap(p);

    vec2 svID = cellID;

    
    vec3 n = vec3(0, 0, -1);

    
    float edge = 0., bumpFactor = .25 * mat_p_bump;
    n = doBumpMap(p, n, bumpFactor, edge);

    
    vec3 lp =  vec3(-0. + sin(mat_light_time)*.3, .0 + cos(mat_light_time*1.3)*.3, -1) - vec3(uv, 0);

    
    float lDist = max(length(lp), .001);
    vec3 ld = lp/lDist;
    
    

    
    float diff = max(dot(n, ld), 0.);
    diff = pow(diff, 4.);
    float spec = pow(max(dot(reflect(-ld, n), -rd), 0.), 16.);
    
    float fre = min(pow(max(1. + dot(n, rd), 0.), 4.), 3.);

    
    vec3 col = vec3(.15)*(diff + .251 + spec*vec3(1, .7, .3)*9. + fre*vec3(.1, .3, 1)*12.);


    
    
    float rf = smoothstep(0., .35, bMap(reflect(rd, n).xy*2.)*fBm(reflect(rd, n).xy*3.) + .1);
    col += col*col*rf*rf*vec3(1, .1, .1)*15.;

    







     
    float shade = m*.83 + .17;
    col *= shade;

    
    
    
    col *= 1. - edge*.8;

    

    float res = 1.;;
    float hatch = doHatch(oP/gSc, res);
    col *= hatch*.5 + .7;

    
    


    
    
    
    
    

    out_color = vec4(sqrt(max(col, 0.)), 1);




    
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
