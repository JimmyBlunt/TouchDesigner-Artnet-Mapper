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
uniform vec4 uMMParam008; // native input: mat_pos
vec2 mat_pos = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_pos_scale
float mat_pos_scale = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_cam
vec2 mat_cam = uMMParam010.xy;
uniform vec4 uMMParam011; // native input: mat_cloud_scale
float mat_cloud_scale = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_cycle1
float mat_cycle1 = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_fade
float mat_fade = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_glow
float mat_glow = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_align
float mat_align = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_iterations
int mat_iterations = int(round(uMMParam016.x));
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
uniform vec4 uMMParam029; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam029.x > 0.5;
uniform vec4 uMMParam030; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam031.x;
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

float mat_time = (mat_time_source - mat_offset * 8. * mat_offset_scale) * 0.25;

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















#define iterations 4
#define formuparam2 0.89
#define volsteps 10
float stepsize = 0.190;
float zoom = 3.900 * pow(mat_align,3.);
float tile = 0.450 * pow(mat_cycle1,0.5);
#define speed2  0.010
#define brightness 0.3
#define darkmatter 0.400
float distfading = 0.560 / mat_fade;
#define saturation 0.400
#define transverseSpeed 1.1
#define cloud 0.2

float triangle(float x, float a)
{

float output2 = 2.0*abs(  2.0*  ( (x/a) - floor( (x/a) + 0.5) ) ) - 1.0;
    return output2;
}

float field(in vec3 p) {

    float strength = 7. + .03 * log(1.e-6 + fract(sin(mat_time) * 4373.11));
    float accum = 0.;
    float prev = 0.;
    float tw = 0.;

    for (int i = 0; i < mat_iterations; ++i) {
        float mag = dot(p, p);
        p = abs(p) / mag + vec3(-.5, -.8 + 0.1*sin(mat_time*0.2 + 2.0), -1.1+0.3*cos(mat_time*0.15));
        float w = exp(-float(i) / 7.);
        accum += w * exp(-strength * pow(abs(mag - prev), 2.3));
        tw += w;
        prev = mag;
    }
    return max(0., 5. * accum / tw - .7);
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    float time2 = mat_time*1.9;

    float speed = speed2;
    speed = 0.005 * cos(time2*0.02 + 3.1415926/4.0);

    

    float formuparam = formuparam2;

    
    
    
    

    float a_xz = 0.9 + mat_cam.x;
    float a_yz = -.6 + mat_cam.y;
    float a_xy = 0.9  + mat_time*0.04;

    mat2 rot_xz = mat2(cos(a_xz),sin(a_xz),-sin(a_xz),cos(a_xz));
    mat2 rot_yz = mat2(cos(a_yz),sin(a_yz),-sin(a_yz),cos(a_yz));
    mat2 rot_xy = mat2(cos(a_xy),sin(a_xy),-sin(a_xy),cos(a_xy));

    float v2 =1.0;

    vec3 dir=vec3(uv*zoom,1.);

    vec3 from=vec3(0.0, 0.0,0.0);

    from.x -= .5*(-0.5);
    from.y -= .5*(-0.5);

    vec3 forward = vec3(0.,1.,1.);

    from.xy += flipY(mat_pos, mat_pos_scale);

    from.x += transverseSpeed*(1.0)*cos(0.01*mat_time) + 0.001*mat_time;
    from.y += transverseSpeed*(1.0)*sin(0.01*mat_time) + 0.001*mat_time;
    from.z += 0.003*mat_time;

    dir.xy*=rot_xy;
    forward.xy *= rot_xy;

    dir.xz*=rot_xz;
    forward.xz *= rot_xz;

    dir.yz*= rot_yz;
    forward.yz *= rot_yz;

    from.xy*=-rot_xy;
    from.xz*=rot_xz;
    from.yz*= rot_yz;

    
    float zooom = (time2-3311.)*speed;
    from += forward* zooom;
    float sampleShift = mod( zooom, stepsize );

    float zoffset = -sampleShift;
    sampleShift /= stepsize; 

    
    float s=0.24 * pow(mat_cloud_scale,3.);
    float s3 = s + stepsize/2.0;
    vec3 v=vec3(0.);
    float t3 = 0.0;

    vec3 backCol2 = vec3(0.);
    for (int r=0; r<volsteps; r++) {
        vec3 p2=from+(s+zoffset)*dir;
        vec3 p3=(from+(s3+zoffset)*dir )* (1.9/zoom);

        p2 = abs(vec3(tile)-mod(p2,vec3(tile*2.))); 
        p3 = abs(vec3(tile)-mod(p3,vec3(tile*2.))); 

        #ifdef cloud
        t3 = field(p3);
        #endif

        float pa,a=pa=0.;
        for (int i=0; i<iterations; i++) {
            p2=abs(p2)/dot(p2,p2)-formuparam; 
            
            float D = abs(length(p2)-pa); 

            if (i > 2)
            {
            a += i > 7 ? min( 12., D) : D;
            }
                pa=length(p2);
        }

        
        a*=a*a; 
        
        
        float s1 = s+zoffset;
        
        float fade = pow(distfading,max(0.,float(r)-sampleShift)) * mat_glow;

        

        v+=fade;
                

        
        if( r == 0 )
            fade *= (1. - (sampleShift));
        
        if( r == volsteps-1 )
            fade *= sampleShift;
        v+=vec3(s1,s1*s1,s1*s1*s1*s1)*a*brightness*fade; 

        backCol2 += mix(.4, 1., v2) * vec3(0.20 * t3 * t3 * t3, 0.4 * t3 * t3, t3 * 0.7) * fade;

        s+=stepsize;
        s3 += stepsize;

        }

    v=mix(vec3(length(v)),v,saturation); 

    vec4 forCol2 = vec4(v*.01,1.);

    #ifdef cloud
    backCol2 *= cloud;
    #endif

    backCol2.r *= 1.80;
    backCol2.g *= 0.05;
    backCol2.b *= 0.90;

    
    
    
    

    out_color = vec4(backCol2, 1.0);

    
    if (mat_luma_to_alpha && mat_luma_mode == 0) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
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

    
    if (mat_luma_to_alpha && mat_luma_mode == 1) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
