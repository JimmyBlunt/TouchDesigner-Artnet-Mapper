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
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: mat_reverse
bool mat_reverse = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_offset
float mat_offset = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_strob
float mat_strob = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_brightness
float mat_brightness = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_contrast
float mat_contrast = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_saturation
float mat_saturation = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_hue_shift
float mat_hue_shift = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_invert
bool mat_invert = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_back_color
vec4 mat_back_color = uMMParam013;
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

float mat_time = mat_time_source - mat_offset;

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

const float EPSILON = 0.00005;

float SoftMax(float a, float b, float k)
{
    return log(exp(k*a)+exp(k*b))/k;
}

float SoftMin(float a, float b, float k)
{
    return -(log(exp(k*-a)+exp(k*-b))/k);
}

struct Camera
{
    vec3 position;
    vec3 dir;
    vec3 up;
    vec3 rayDir;
};

struct MapResult
{
    float dist;
    vec3 color;
};

struct MarchResult
{
    vec3 position;
    float dist;
    vec3 color;
};

float smoothcurve(float f) {
    return 0.5*(1.0+cos(3.14*f));
}

mat4 rotationMatrix(vec3 axis, float angle)
{
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    return mat4(oc * axis.x * axis.x + c, oc * axis.x * axis.y - axis.z * s, oc * axis.z * axis.x + axis.y * s, 0.0,
            oc * axis.x * axis.y + axis.z * s, oc * axis.y * axis.y + c, oc * axis.y * axis.z - axis.x * s, 0.0,
            oc * axis.z * axis.x - axis.y * s, oc * axis.y * axis.z + axis.x * s, oc * axis.z * axis.z + c, 0.0,
            0.0, 0.0, 0.0, 1.0);
}

vec3 opCheapBend(vec3 p, float x, float y)
{
    float c = cos(x*p.y);
    float s = sin(y*p.y);
    mat2  m = mat2(c,-s,s,c);
    vec3  q = vec3(m*p.xy,p.z);
    return q;
}

vec3 opTwist(vec3 p, float x, float y)
{
    float c = cos(x*p.y);
    float s = sin(y*p.y);
    mat2  m = mat2(c,-s,s,c);
    vec3  q = vec3(m*p.xz,p.y);
    return q;
}

MapResult map_cube(vec3 position)
{
    MapResult result;


    float sphere = length(position) - 1.2;
    float mat_time2 = mat_time - position.y;


    float c = 10.0;


    position = (rotationMatrix(vec3(0,0,1), mat_time2) * vec4(position, 1.0)).xyz;


    position = (rotationMatrix(vec3(0,1,0), mat_time2) * vec4(position, 1.0)).xyz;
    float cube = length(max(abs(position) - vec3(0.5), 0.0)) - 0.1;

    position = (rotationMatrix(vec3(1,0,0), mat_time2) * vec4(position, 1.0)).xyz;


    vec2 q = vec2(length(position.xz) - 2.5, position.y);
    float torus= length(q) - 0.2;


    float d = SoftMax(cube, -sphere, 7.5);
    

    vec3 color3 = vec3(.5, 0.0, 0.0);
    vec3 color2 = vec3(0.0, 0.5, 0.0);
    vec3 color1 = vec3(0.0, 0.0, 0.5);

    d =+ SoftMin(d, torus, 1.);

    result.color = mix(color1, mix(color3, color2, cube), torus) * 4.;

    result.dist = d;
    return result;
}

MapResult map_torus(vec3 position)
{
    MapResult result;
    result.color = vec3(0.0, 0.5, 0.8);

    position = (rotationMatrix(vec3(0,0,1), mat_time) * vec4(position, 1.0)).xyz;
    position = (rotationMatrix(vec3(0,1,0), mat_time) * vec4(position, 1.0)).xyz;
    position = (rotationMatrix(vec3(1,0,0), mat_time) * vec4(position, 1.0)).xyz;

    vec2 q = vec2(length(position.xz) - 2.5, position.y);
    result.dist = length(q) - 0.2;

    return result;
}

MapResult map(vec3 position)
{
    MapResult result;

    MapResult cube = map_cube(position);


    result = cube;

    return result;
}

vec3 getColor(const in Camera cam, const in vec3 position, const in float dist, const in vec3 color)
{
    vec3 eps = vec3(EPSILON, 0, 0);

    vec3 normal=normalize(
           vec3(dist - map(position-eps.xyy).dist,
            dist - map(position-eps.yxy).dist,
            dist - map(position-eps.yyx).dist));

    float lambert = dot(normal, -cam.rayDir);

    return lambert * color;
}

MarchResult raymarch(const in Camera cam)
{
    MarchResult result;
    result.color = vec3(0);

    const int MAX_ITERATIONS = 128;
    const float MAX_DEPTH = 52.0;

    float depth = 0.0;
    MapResult mapping;
    for(int i = 0; i < MAX_ITERATIONS; ++i)
    {
        result.position = cam.position + cam.rayDir * depth;
        mapping = map(result.position);

        if(mapping.dist <= EPSILON)
        {
            break;
        }

        depth += mapping.dist;

        if(depth > MAX_DEPTH)
        {
            break;
        }
    }

    result.dist = mapping.dist;

    if(depth < MAX_DEPTH)
        result.color = getColor(cam, result.position, result.dist, mapping.color);

    return result;
}

Camera getCamera(vec2 uv)
{
    Camera cam;
    cam.dir = vec3(0,0,0);
    float t = (mat_time+1.0) * 0.15;
    cam.position = vec3(sin(t + 1.0)*4.0, 4, cos(t)*4.0);
    cam.up = vec3(0,1,0);
    vec3 forward = normalize(cam.dir - cam.position);
    vec3 left = cross(forward, cam.up);
    cam.up = cross(left, forward);

    vec3 screenOrigin = (cam.position+forward);
    vec2 screenPos = uv;
    float screenAspectRatio = 1.; 
    vec3 screenHit = screenOrigin + screenPos.x * left * screenAspectRatio + screenPos.y * cam.up;
    cam.rayDir = normalize(screenHit-cam.position);

    
    if(true){ 
        cam.position = vec3(0);

        
        

        float a1 = uv.x*PI;
        float a2 = uv.y*PI;

        cam.rayDir = vec3(cos(a1)*sin(a2), sin(a1)*sin(a2), cos(a2));

    }
    return cam;
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
    uv += uv_shift;

    uv += vec2(0.5);


    Camera cam = getCamera(uv);
    MarchResult result = raymarch(cam);

    vec3 color = result.color; 

    out_color = vec4(color, 1.0);

    if (mat_luma(out_color) < 0.02) {
        out_color = mat_back_color;
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
