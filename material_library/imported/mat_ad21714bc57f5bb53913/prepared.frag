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
uniform vec4 uMMParam003; // native input: mat_shift_scale
float mat_shift_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_shift_type
int mat_shift_type = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_iterations
int mat_iterations = int(round(uMMParam007.x));
uniform vec4 uMMParam008; // native input: mat_limit
float mat_limit = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_orb_offset
float mat_orb_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_height
float mat_height = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_turbulence
float mat_turbulence = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_bounce_freq
float mat_bounce_freq = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_bounce_amp
float mat_bounce_amp = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_bounce_offset
float mat_bounce_offset = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_speed
float mat_speed = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_reverse
bool mat_reverse = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_offset
float mat_offset = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_offset_scale
float mat_offset_scale = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_strob
float mat_strob = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_restart
int mat_restart = int(round(uMMParam021.x));
uniform vec4 uMMParam022; // native input: mat_back_light
float mat_back_light = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_alpha
bool mat_alpha = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_back_thresh
float mat_back_thresh = uMMParam024.x;
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
uniform vec4 uMMParam030; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam030.x > 0.5;
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

float mat_time = mat_time_source - mat_offset * 8. * mat_offset_scale;

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

    vec2 uv_shift = mat_shift_amount * mat_shift_scale * 0.25;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    if (mat_shift_type == 0) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, -1. * (2*PI*(mat_rotate) / 360) + PI);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    uv += vec2(0.5);
    uv = matRot2D(uv, PI + 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    
    if (mat_shift_type == 1) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, PI + 2*PI*(mat_rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }



    return uv;
}
















#define MAX_DIST 1e10
#define EPS .001

float GetSceneDistance(vec3 point, out int obj)
{
    vec4 sphere = vec4(0, 1.5, 6, 1.); 
    vec4 sphere2 = vec4(0., 1.5, 6, 0.38);
    vec4 sphere3 = vec4(0., 1.5, 6, 0.1);
    vec4 sphere4 = vec4(0., 1.5, 6, 0.2);

    float rotate_r2 = 2.0;
    float rotate_r3 = 1.4;
    float rotate_r4 = 1.7;

    float bounce_frequen = 4. + mat_bounce_freq * 16.;
    sphere += vec4(0., 0.1 *sin(bounce_frequen * mat_time) + mat_bounce_offset * 2., 0., 0.) * pow(mat_bounce_amp,2.);

    sphere2 += vec4(rotate_r2 *sin(mat_time),
                    0.8*sin(mat_time),
                    rotate_r2 *cos(mat_time),
                    0.);

    float delta = 1.5 + mat_orb_offset * 4.;
    sphere3 += vec4(rotate_r3 *sin(mat_time+delta),
                    0.5*sin(mat_time+delta),
                    rotate_r3 *cos(mat_time+delta),
                    0.);
    sphere4 += vec4(rotate_r4 *sin(mat_time+2.*delta),
                    -0.6*sin(mat_time+2.*delta),
                    rotate_r4 *cos(mat_time+2.*delta),
                    0.);

    float sphere_dist = length(point - sphere.xyz)-sphere.w;
    float sphere_dist2 = length(point - sphere2.xyz)-sphere2.w;
    float sphere_dist3 = length(point - sphere3.xyz)-sphere3.w;
    float sphere_dist4 = length(point - sphere4.xyz)-sphere4.w;
    float ground_dist =  point.y;

    ground_dist /= pow(mat_height,1.25);

    float t = length(point.xz - sphere.xz);
    float t2 = length(point.xyz - sphere2.xyz) * mat_turbulence;
    float t3 = length(point.xyz - sphere3.xyz);
    float t4 = length(point.xyz - sphere4.xyz);
    bool is_background_obj = false;
    if (t < 15. * mat_limit)
    {
        
        float wave = 0.2 *pow(0.95, t)*  sin( 4. *pow(0.98, t) * t - bounce_frequen * mat_time);
        float wave2 = -10.  *pow(sphere2.w, 3.) * 0.15 *pow(0.8, t)*  sin(4. * t2);
        float wave3 = -5.  *pow(sphere3.w, 3.) *0.15 *pow(0.8, t)*  sin(4. * t3);
        float wave4 = -20.  *pow(sphere4.w, 3.)*0.15 *pow(0.9, t)*  sin(4. * t4);
        
        ground_dist += (wave + wave2 + wave3 + wave4);
    }
    
      
    else
        is_background_obj = true;


    float d =
            min(
            min(
            min(
            min(sphere_dist, ground_dist),
            sphere_dist2),
            sphere_dist3),
            sphere_dist4);
    

    float eps = 0.01;
    if( abs(sphere_dist - d) < eps)
        obj = 1;
    else if( abs(sphere_dist2 - d) < eps)
        obj = 2;
    else if( abs(sphere_dist3 - d) < eps)
        obj = 3;
    else if( abs(sphere_dist4 - d) < eps)
        obj = 4;
    else
        obj = 0;

    if(is_background_obj)
        obj = -1;

    return d;
}

float RayMarch(vec3 ray_origin, vec3 ray_dir, out int obj)
{
    float d = 0.;
    for(int i = 0; i < mat_iterations; i++)
    {
        vec3 p = ray_origin + ray_dir * d;
        float ds = GetSceneDistance(p, obj);
        d += ds;
        if(d > MAX_DIST || ds < EPS)
            break;  
    }
    return d;
}

vec3 GetNormal(vec3 point)
{
    int obj_nouse;
    float d = GetSceneDistance(point, obj_nouse);
    vec2 e = vec2(0.01, 0);
    vec3 n = d - vec3(
        GetSceneDistance(point - e.xyy, obj_nouse),
        GetSceneDistance(point - e.yxy,  obj_nouse),
        GetSceneDistance(point - e.yyx, obj_nouse)
    );

    return normalize(n);
}

float smoothStep(float edge0, float edge1, float x)
{

    if (x < edge0)
        return 0.;
    if (x > edge1)
        return 1.;
    if(edge1 == edge0)
        return 0.;
    x = (x - edge0) / (edge1 - edge0);
    return x*x * (3.-2.*x);
}

vec3 GetLight(bool is_ground, vec3 point, vec3 light_pos, vec3 light_col, vec3 camera_pos)
{
    vec3 to_light = normalize(light_pos - point);
    vec3 normal = GetNormal(point);

    
    bool in_shadow = false;
    float NdotL = dot(to_light, normal);
    float diffuse = NdotL > 0. ? 1. : 0.;
    if(is_ground)
    {
        float NdotL_smooth = smoothStep(0.4, 1.0, NdotL);
        diffuse = NdotL > 0.4 ? 1.0 : 0.5;
    }

    
    int obj_nouse;
    float d = RayMarch(point+normal*2.*EPS, to_light, obj_nouse);

    
    if (d < length(light_pos - point))
    {
        in_shadow = true;
        diffuse *= 0.;
    }

    
    float ambient = 0.3;

    
    vec3 to_camera = normalize(camera_pos - point);
    vec3 half_vector = normalize(to_camera + to_light);
    float NdotH = dot(normal, half_vector);

    float glossiness = 20.;
    float specular = pow(NdotH, glossiness * glossiness);
    float specular_smooth = smoothStep(0.005, 0.01, specular);

    
    float scale = 0.2;
    if (is_ground)
        scale = 0.3;
    float rimDot = pow(NdotL, scale)* (1. - clamp(dot(to_camera, normal), 0., 1.));
    float rimAmount = 0.616;
    float rim = 0.5 *  smoothStep(rimAmount - 0.01, rimAmount+0.01, rimDot);

    
    float intensity = 0.8;

    float sum = 0.;
    if(in_shadow)
        sum = (diffuse + ambient);
    else
        sum = (diffuse + ambient + specular_smooth + rim);

    vec3 light = intensity * sum * light_col ;

    return light;
}



vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    vec3 ray_origin = vec3(0, 1.5, -1);
    vec3 ray_dir = normalize(vec3(uv.x, uv.y, 1.));

    
    vec3 light_pos = vec3(3, 8, -1);
    vec3 light_col = vec3(60.,179.,113.) / 255.;
    
    vec3 ground_col = vec3(105,26.,235.) / 255.;
    vec3 light_col2 = vec3(10.,149.,237.) / 255.;
    vec3 light_col3 = vec3(200.,100.,37.) / 255.;
    vec3 light_col4 = vec3(100.,149.,27.) / 255.;

    float spin = 5.;
    float range = 2.;
    vec3 light_pos2 = light_pos + range* vec3(sin(spin*mat_time), cos(spin *mat_time), cos(spin*mat_time));

    
    int obj = 0;
    float d = RayMarch(ray_origin, ray_dir, obj);

    vec3 point = ray_origin + d * ray_dir;

    vec3 col;
    if(obj == 1)
        col = GetLight(false, point, light_pos2, light_col, ray_origin);
    else if(obj == 2)
        col = GetLight(false, point, light_pos2, light_col2, ray_origin);
    else if(obj == 3)
        col = GetLight(false, point, light_pos2, light_col3, ray_origin);
    else if(obj == 4)
        col = GetLight(false, point, light_pos2, light_col4, ray_origin);
    else if(obj==-1)
        col = ground_col * 0.1 * mat_back_light;
    else
        col = GetLight(true, point, light_pos, ground_col, ray_origin);

    col = pow(col, vec3(0.4545)); 

    
    out_color = vec4(col,1.0);

    if (mat_luma(out_color.rgb) < mat_back_thresh) {
            out_color.a = 0.;
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
