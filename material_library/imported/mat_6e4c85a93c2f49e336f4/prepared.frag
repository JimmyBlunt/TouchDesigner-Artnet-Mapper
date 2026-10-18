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
uniform vec4 uMMParam001; // native input: mat_speed
float mat_speed = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_reverse
bool mat_reverse = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_offset
float mat_offset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_strob
float mat_strob = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_cam_amount
vec2 mat_cam_amount = uMMParam006.xy;
uniform vec4 uMMParam007; // native input: mat_cam_speed
float mat_cam_speed = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_cam_bpm_sync
bool mat_cam_bpm_sync = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_cam_reverse
bool mat_cam_reverse = uMMParam009.x > 0.5;
uniform vec4 uMMParam010; // native input: mat_cam_offset
float mat_cam_offset = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_cam_strob
float mat_cam_strob = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_rotate
float mat_rotate = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_rot_speed
float mat_rot_speed = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_rot_bpm_sync
bool mat_rot_bpm_sync = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_rot_reverse
bool mat_rot_reverse = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_rot_offset
float mat_rot_offset = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_rot_strob
float mat_rot_strob = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_color_speed
float mat_color_speed = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_color_bpm_sync
bool mat_color_bpm_sync = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_color_reverse
bool mat_color_reverse = uMMParam020.x > 0.5;
uniform vec4 uMMParam021; // native input: mat_color_offset
float mat_color_offset = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_color_strob
float mat_color_strob = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_brightness
float mat_brightness = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_contrast
float mat_contrast = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_saturation
float mat_saturation = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_hue_shift
float mat_hue_shift = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_invert
bool mat_invert = uMMParam027.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_cam_time_source = uTDTime * (mat_cam_speed);
float mat_color_time_source = uTDTime * (mat_color_speed);
float mat_rot_time_source = uTDTime * (mat_rot_speed);

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

float mat_time = mat_time_source - mat_offset * 16.;
float mat_cam_time = mat_cam_time_source - mat_cam_offset * 16.;
float mat_rot_time = mat_rot_time_source - mat_rot_offset * 16.;
float mat_color_time = mat_color_time_source - mat_color_offset * 16.;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}




#define P 6.2831853071795

float rand(in vec2 st){ return fract(sin(dot(st.xy,vec2(12.9898,78.233)))*43758.585); }
vec3 SpectrumPoly(in float x) {
    
    return (vec3( 1.220023e0,-1.933277e0, 1.623776e0)+(vec3(-2.965000e1, 6.806567e1,-3.606269e1)+(vec3( 5.451365e2,-7.921759e2, 6.966892e2)+(vec3(-4.121053e3, 4.432167e3,-4.463157e3)+(vec3( 1.501655e4,-1.264621e4, 1.375260e4)+(vec3(-2.904744e4, 1.969591e4,-2.330431e4)+(vec3( 3.068214e4,-1.698411e4, 2.229810e4)+(vec3(-1.675434e4, 7.594470e3,-1.131826e4)+ vec3( 3.707437e3,-1.366175e3, 2.372779e3)*x)*x)*x)*x)*x)*x)*x)*x)*x;
}
mat2 rot(in float a) { return mat2(cos(a),sin(a),-sin(a),cos(a)); }

vec4 tri(in vec2 p) {
    #define R .86602544038
    vec2 r = vec2(R,1.);
    vec2 pr = p*r;
    vec3 floorPy = vec3(floor(p.y)*.5,floor(p.y)*.5 + .5,0.);

    vec3 pTm1 = (fract(pr.xxy + floorPy.xyz));
    vec4 pTm2 = (pTm1.xzyz - vec3(.5,1./3.,2./3.).xyxz)/r.xyxy;
    vec2 pT = fract(pr + vec2(p.y*.5,0.));
    vec2 pId;
    if(pT.y < pT.x) {
        pId = floor(pr + floorPy.xz);
        pT = pTm2.xy;
    } else {
        pId = 1. + floor(pr + floorPy.yz);
        pT = pTm2.zw;
    }
    return vec4(pT,pId);
}
float cosa(in float x, in float y, in float w) { return cos((x/P)*y + w)*.5+.5; }
float sq(in vec2 p, in float s, in float r) { return length(max(abs(p) - s,0.)) - r; }

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale;

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);



    float aa = 0.001;

    vec2 st = uv;

    st -= st*length(st)*.5;
    float sz = 8.;
    

    
    st *= rot(P*.125 + .1*mat_rot_time);

    vec2 uv_shift = mat_cam_amount;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);



    vec2 p = st + vec2(mat_cam_time*.1,0.);

    p += uv_shift;

    vec4 pT = tri(p*sz);
    sz *= 1. + floor(rand(vec2(pT.zw))*15.);
    pT = tri(p*sz);

    float taille = cosa(mat_time,12.,pT.w*.25);
    float d = (length(pT.xy) - taille/3.)/sz;
    d = max(d,-sq(pT.xy*rot(P/8. + mat_time*2. + pT.w),.2125*taille,.02)/sz);
    float dd = (.3 - d*2.);
    d = smoothstep(-aa,aa,-d) + dd;

    vec3 color = SpectrumPoly(rand(vec2(pT.zw))*.1 + mix(.2,.625, smoothstep(.46,.52,cosa(mat_color_time + pT.w*.25,1.,0.)) ))*(dd*8.)*d;

    out_color = vec4(pow(color - length(st)*length(st)*1.69,vec3(1.2)),1.0);




    
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
