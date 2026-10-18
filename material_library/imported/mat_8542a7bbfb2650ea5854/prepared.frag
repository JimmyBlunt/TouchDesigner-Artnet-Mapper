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
uniform vec4 uMMParam008; // native input: mat_cam_pos
vec2 mat_cam_pos = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_cam_pos_scale
float mat_cam_pos_scale = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_cam2_pos
vec2 mat_cam2_pos = uMMParam010.xy;
uniform vec4 uMMParam011; // native input: mat_cam2_pos_scale
float mat_cam2_pos_scale = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_cloud_pos
vec2 mat_cloud_pos = uMMParam012.xy;
uniform vec4 uMMParam013; // native input: mat_cloud_pos_scale
float mat_cloud_pos_scale = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_dist
float mat_dist = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_cloud_limit
float mat_cloud_limit = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_cycle
float mat_cycle = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_light_intensity
float mat_light_intensity = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_glow
float mat_glow = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_absorption
float mat_absorption = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_cloud_smooth
float mat_cloud_smooth = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_volume_step
float mat_volume_step = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_moon_size
float mat_moon_size = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_moon_brightness
float mat_moon_brightness = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_moon_surface
float mat_moon_surface = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_direction
float mat_direction = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_a1_speed
float mat_a1_speed = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_a1_bpm_sync
bool mat_a1_bpm_sync = uMMParam027.x > 0.5;
uniform vec4 uMMParam028; // native input: mat_a1_reverse
bool mat_a1_reverse = uMMParam028.x > 0.5;
uniform vec4 uMMParam029; // native input: mat_a1_offset
float mat_a1_offset = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_a1_offset_scale
float mat_a1_offset_scale = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_a1_strob
float mat_a1_strob = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_a1_restart
int mat_a1_restart = int(round(uMMParam032.x));
uniform vec4 uMMParam033; // native input: mat_a2_speed
float mat_a2_speed = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_a2_bpm_sync
bool mat_a2_bpm_sync = uMMParam034.x > 0.5;
uniform vec4 uMMParam035; // native input: mat_a2_reverse
bool mat_a2_reverse = uMMParam035.x > 0.5;
uniform vec4 uMMParam036; // native input: mat_a2_offset
float mat_a2_offset = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_a2_offset_scale
float mat_a2_offset_scale = uMMParam037.x;
uniform vec4 uMMParam038; // native input: mat_a2_strob
float mat_a2_strob = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_a2_restart
int mat_a2_restart = int(round(uMMParam039.x));
uniform vec4 uMMParam040; // native input: mat_front_color
vec4 mat_front_color = uMMParam040;
uniform vec4 uMMParam041; // native input: mat_back_color
vec4 mat_back_color = uMMParam041;
uniform vec4 uMMParam042; // native input: mat_contrast
float mat_contrast = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_invert
bool mat_invert = uMMParam043.x > 0.5;
uniform vec4 uMMParam044; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam044.x));
uniform vec4 uMMParam045; // native input: mat_back_thresh
float mat_back_thresh = uMMParam045.x;
uniform vec4 uMMParam046; // native input: mat_back_sensitivity
float mat_back_sensitivity = uMMParam046.x;
float mat_a1_time_source = uTDTime * (mat_a1_speed);
float mat_a2_time_source = uTDTime * (mat_a2_speed);
#define iChannel0 sTD2DInputs[0]

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

float mat_a1_time = (mat_a1_time_source - mat_a1_offset * 8. * mat_a1_offset_scale);
float mat_a2_time = (mat_a2_time_source - mat_a2_offset * 8. * mat_a2_offset_scale) * 16.;

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
    uv *= mat_scale * 0.75;

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





















float CLOUDS_SMOOTHNESS = 1.5 * mat_cloud_smooth;
float LIGHT_INTENSITY = 20. * mat_light_intensity;
float ABSORPTION = 5.5 * mat_absorption;
float VOLUME_STEPS = 40. * mat_volume_step;


#define BEHIND_THE_SCENE  0

#define hash33(p) fract(sin( (p) * mat3( 127.1,311.7,74.7 , 269.5,183.3,246.1 , 113.5,271.9,124.6) ) * 43758.5453123)

mat2 rot(float a) {
    return mat2(cos(a), -sin(a), sin(a), cos(a));
}


float noise(in vec3 p) {
    vec3 ip = floor(p);
    vec3 fp = fract(p);
    fp = fp*fp*(3.0-2.0*fp);
    vec2 tap = (ip.xy+vec2(37.0,17.0)*ip.z) + fp.xy;
    vec2 rz = textureLod(iChannel0, (tap+0.5)/256.0, 0.0).yx;
    return mix(rz.x, rz.y, fp.z) * pow(mat_cycle, 1.5);
}

float fbm(in vec3 x) {
    float rz = 0.;
    float a = .35;
    for (int i = 0; i<4; i++) {
        rz += noise(x)*a;
        a*=.35;
        x*= 4.;
    }
    return (rz - .25);
}

vec2 boxIntersection(in vec3 ro, in vec3 rd) {
    vec3 rad = vec3(6., 6., 2.);
    vec3 m = 1.0/rd;
    vec3 n = m*ro;
    vec3 k = abs(m)*rad;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max( max( t1.x, t1.y ), t1.z );
    float tF = min( min( t2.x, t2.y ), t2.z );
    if( tN>tF || tF<0.0) return vec2(-1.0); 
    return vec2( tN, tF );
}

void marchVolume(vec3 ro, vec3 rd, float near, float far, inout vec3 color) {
    vec3 vColor = vec3(0.);
    float visibility = 1.;

    float inside = far - near + hash33(ro).x*.01;
    float stepSize = inside / VOLUME_STEPS;

    float a1_time_x = mat_a1_time * cos(2.*PI * mat_direction/360.0);
    float a1_time_y = mat_a1_time * sin(2.*PI * mat_direction/360.0);

    vec2 cloud_pos = (mat_cloud_pos) * mat_cloud_pos_scale * 2.;
    cloud_pos += vec2(0.5);
    cloud_pos.x = 1.-cloud_pos.x;
    cloud_pos -= vec2(0.5);

    float i = 0.;

    for (float t = near; t <= far; t += stepSize) {
        vec3 p = ro + t*rd;

        float s = CLOUDS_SMOOTHNESS*.01;
        
        float dens = smoothstep(-s, s, fbm(p + vec3(cloud_pos.x + a1_time_x, cloud_pos.y + a1_time_y, 1.+mat_a2_time*.02)))*.1;

        float prev = visibility;
        visibility *= exp(-stepSize*dens*ABSORPTION);

        float absorption = prev - visibility;
        float light = smoothstep(2.5, 6.5, p.z); 
        vColor += absorption * dens * light * LIGHT_INTENSITY;

        if (i++ > VOLUME_STEPS) break;
    }

    color = min(vColor, 1.) + color * visibility;
}

void initCamera(vec2 uv, inout vec3 ro, inout vec3 rd) {

    vec2 cam_pos = (mat_cam_pos) * mat_cam_pos_scale * 2.;
    cam_pos += vec2(0.5);
    cam_pos.x = 1.-cam_pos.x;
    cam_pos -= vec2(0.5);

    vec2 m = false ? vec2(.5) : cam_pos;

    ro = vec3(m.x-.5, m.y-.5, .01)*.8;

    #if BEHIND_THE_SCENE
    ro.x += 8.; ro.z -= 8.;
    #endif

    vec3 ro2 = ro;

    ro.z += 6.*mat_dist;

    vec3 f = normalize(vec3(0., 0., 1.) - ro2*.05),
         r = normalize(cross(vec3(0,1,0), f)),
         u = cross(f,r),
         c = ro+f,
         i = c + uv.x*r + uv.y*u;
    rd = normalize(i-ro); 
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec3 ro, rd;
    initCamera(uv, ro, rd);



    vec2 cam2_pos = (mat_cam2_pos) * mat_cam2_pos_scale * 2.;
    cam2_pos += vec2(0.5);
    cam2_pos.x = 1.-cam2_pos.x;
    cam2_pos -= vec2(0.5);

    rd.x += cam2_pos.x;
    rd.y += cam2_pos.y;

    
    float moon = dot(rd, vec3(0., 0., 1.)) * mat_moon_size;
    
    vec3 color = (mat_moon_brightness*.7-fbm(rd*10.)*3.*mat_moon_surface) * vec3(smoothstep(.995, .9955, moon));
    color += (1.25-color)*pow((moon+.1) * mat_glow * 0.75, 6.)*.25;

    
    vec3 h = hash33(vec3(floor(rd.xy*80.), 0.));
    float stars = length(fract(rd.xy*80. + h.xy*.75)-.5);
    

    
    vec2 hit = boxIntersection(ro - vec3(0., 0., 4.), rd) * mat_cloud_limit;
    marchVolume(ro, rd, hit.x, hit.y, color);

    out_color = vec4(color, 1.);

    
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
