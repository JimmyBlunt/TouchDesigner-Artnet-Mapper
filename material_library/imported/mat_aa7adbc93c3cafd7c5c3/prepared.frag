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
uniform vec4 uMMParam008; // native input: mat_cam_enable
bool mat_cam_enable = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_cam_pos
vec2 mat_cam_pos = uMMParam009.xy;
uniform vec4 uMMParam010; // native input: mat_cam_pos_scale
float mat_cam_pos_scale = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_cam_zoom
float mat_cam_zoom = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_ridge
float mat_ridge = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_cycle1
float mat_cycle1 = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_cycle2
float mat_cycle2 = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_fill
float mat_fill = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_iterations
int mat_iterations = int(round(uMMParam016.x));
uniform vec4 uMMParam017; // native input: mat_detail
float mat_detail = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_sky
float mat_sky = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_a1_speed
float mat_a1_speed = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam020.x > 0.5;
uniform vec4 uMMParam021; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_a1_offset
float mat_a1_offset = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_a1_strob
float mat_a1_strob = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam025.x));
uniform vec4 uMMParam026; // native input: mat_a2_speed
float mat_a2_speed = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam027.x > 0.5;
uniform vec4 uMMParam028; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam028.x > 0.5;
uniform vec4 uMMParam029; // native input: mat_a2_offset
float mat_a2_offset = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_a2_strob
float mat_a2_strob = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_a2_restart
int mat_a2_restart = int(round(uMMParam032.x));
uniform vec4 uMMParam033; // native input: mat_brightness
float mat_brightness = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_contrast
float mat_contrast = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_saturation
float mat_saturation = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_hue_shift
float mat_hue_shift = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_invert
bool mat_invert = uMMParam037.x > 0.5;
uniform vec4 uMMParam038; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam038.x > 0.5;
uniform vec4 uMMParam039; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam040.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);
#define iChannel0 sTDCubeInputs[0]
#define iChannel1 sTDCubeInputs[1]
#define iChannel2 sTD2DInputs[0]

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

float mat_a1_time = (mat_a1_time_source - mat_a1_offset * 16. * mat_a1_offset_scale) * 8.;
float mat_a2_time = (mat_a2_time_source - mat_a2_offset * 16. * mat_a2_offset_scale) * 2.;

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
    uv *= mat_scale;

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







float Norm = 0.13 * mat_ridge; 
float IOR = 1.3 * mat_fill;  
const float FRB = 0.2;  


float s, c;
#define rotate(p, a) mat2(c=cos(a), s=-sin(a), -s, c) * p

vec3 rotXY(in vec3 p, vec2 r) {
    p.yz = rotate(p.yz, r.x);
    p.xz = rotate(p.xz, r.y);
    return p;
}


vec2 isectSphere(vec3 p, vec3 d, vec3 sPos, float sRad) {
    vec2 ret;
    vec3 v = p - sPos;
    float r  = sRad;
    float dv = dot(d, v);
    float d2 = dot(d, d);
    float sq = dv*dv - d2 * (dot(v, v)-r*r);
    if(sq < 0.) {
        return vec2(-1.);
    }
    else {
        sq = sqrt(sq);
        float t1 = (-dv+sq)/d2;
        float t2 = (-dv-sq)/d2;
        return (t1<t2 ? vec2(t1, t2) : vec2(t2, t1));
    }
}

float map(in vec3 p) {
    vec3 o = vec3(-1., 0., 1.);
    float sph = dot(p-o.yxy, p-o.yxy);
    p = vec3(p.x, 0., p.z) / sph;

    float sc=1.3, f=0.;
    for(float i=0.; i<float(mat_iterations); i++) {
        p = abs(mod(p-1., 2.)-1.);
        p.xz -= .75 - mat_cycle1*.5*vec2(sin(.007145*mat_a1_time), cos(.005072*mat_a1_time));

        p.xz = sc * rotate(p.xz, 1.4+.01*mat_a1_time);

        f += length(p) / pow(sc, i+1.);
    }
    return 2. * abs(fract(2.*f)-.5 * mat_cycle2);
}

vec3 getNorm(vec3 p, float acc) {
    vec3 o = acc * vec3(-1., 0., 1.);
    return
        normalize(
            vec3(
                map(p+o.zyy)-map(p+o.xyy),
                map(p+o.yzy)-map(p+o.yxy),
                map(p+o.yyz)-map(p+o.yyx)
            )
        );
}

vec3 getSky(vec3 p) {
    return - .25 * p.y + 1.5 * mix(texture(iChannel0,p).rgb, texture(iChannel1,p).rgb, .7) * mat_sky;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    
    
    

    vec2 res = vec2(10.) * pow(mat_detail + 1., 8.);

    vec2 mPos = 0.5*mat_cam_pos + vec2(0.5);

    
    vec3 o = vec3(-1., 0., 1.);

    
    float Zoom = 1.3;

    
    if(mat_cam_enable) {
        
        uv += flipX(mat_cam_pos, mat_cam_pos_scale);
        Zoom *= mat_cam_zoom;
    }

    
    vec3 rayBeg = 3. * o.yyx;
    vec3 rayDir = normalize(vec3(uv, Zoom));

    
    vec2 rot = .1 * vec2(2.+1.94*cos(.14*mat_a2_time), mat_a2_time);
    rayBeg = rotXY(rayBeg, rot);
    rayDir = rotXY(rayDir, rot);

    
    vec2 hitDists = isectSphere(rayBeg, rayDir, o.yyy, 1.);
    vec3 hit1 = rayBeg + rayDir * hitDists.x, hit2;

    vec3 outCol;

    
    vec3 sky = getSky(-rayDir);

    
    if(hitDists.x>0.) {

        
        float f1, f2, aoi, thk, iBl;
        vec3 norm, col1, col2, ref, sCol, iCol;
        
        vec3 lPos = 3. * o.yzy;
        
        iCol = vec3(.2, .3, .425);


        

        
        f1 = max(0., map(hit1));

        
        norm = normalize(hit1-Norm*getNorm(hit1, 2./res.y/Zoom));

        
        sCol = IMG_NORM_PIXEL(iChannel2,mod(vec2(.15*f1, 0.),1.0)).rgb;

        
        col1 = .1  * sCol;

        
        col1 += .42 * sCol * mix(f1, 1., .5) * pow(max(0., 1.+.25*dot(norm, lPos)), 2.);
        col1 += .2*texture(iChannel1,-norm).rgb;

        
        col1 *= mix(smoothstep(.5, .7, f1), 1., .75);

        
        ref = getSky(reflect(-rayDir, norm));

        
        aoi = pow(max(0., (1.+1.*dot(normalize(rayDir), norm))), 1.);


        

        
        rayBeg = hit1 + .01*norm;
        rayDir = refract(normalize(rayDir), norm, 1./IOR);
        hitDists = isectSphere(rayBeg, rayDir, vec3(0.), 1.);
        hit2 = rayBeg + rayDir * hitDists.y;

        
        f2 = max(0., map(hit2));

        
        norm = normalize(hit2+Norm*getNorm(hit2, (80.*FRB)/res.y/Zoom));

        
        sCol = IMG_NORM_PIXEL(iChannel2,mod(vec2(.15*f2, 0.),1.0)).rgb;

        
        col2 = .1 * sCol;

        
        col2 += .42 * sCol * mix(f2, 1., .5) * pow(max(0., 1.+.25*dot(norm, lPos)), 2.);
        col2 += .2 * texture(iChannel1,-norm).rgb;

        
        col2 *= mix(smoothstep(.5, .7, f2), 1., .75);


        

        
        thk = distance(hit1, hit2);

        
        vec2 edge = .5 + vec2(.0, .01);

        
        f1 = clamp(smoothstep(edge.x, edge.y, 1.-f1), 0., 1.);

        
        iBl = FRB * thk;

        
        f2 = clamp(smoothstep(edge.x-iBl, edge.y+iBl, 1.-f2), 0., 1.);

        
        rayDir = refract(normalize(rayDir), -norm, IOR);

        
        sky = getSky(-rayDir);

        
        col2 = mix(col2, vec3(sky), f2);

        
        col2 = mix(col2, .7 * iCol, min(1., .4*thk));

        
        outCol = mix(col1, col2, f1);

        
        ref = mix(outCol, ref, f1/2.+.2);

        
        outCol = mix(outCol, ref, aoi);

    }
    
    else
        outCol = sky;

    out_color = vec4(outCol, 1.);


    
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
