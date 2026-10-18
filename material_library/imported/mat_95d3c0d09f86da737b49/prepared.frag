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
uniform vec4 uMMParam003; // native input: mat_wave_scale
float mat_wave_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_factor_1
float mat_factor_1 = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_factor_2
float mat_factor_2 = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_factor_3
float mat_factor_3 = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_distort_1
float mat_distort_1 = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_distort_2
float mat_distort_2 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_distort_3
float mat_distort_3 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_distort_4
float mat_distort_4 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_height
float mat_height = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_wave_pos
vec2 mat_wave_pos = uMMParam012.xy;
uniform vec4 uMMParam013; // native input: mat_dist
float mat_dist = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_speed
float mat_speed = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_reverse
bool mat_reverse = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_offset
float mat_offset = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_offset_scale
float mat_offset_scale = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_strob
float mat_strob = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_light_pos
vec2 mat_light_pos = uMMParam020.xy;
uniform vec4 uMMParam021; // native input: mat_light_height
float mat_light_height = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_power
float mat_power = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_tint
vec4 mat_tint = uMMParam023;
uniform vec4 uMMParam024; // native input: mat_gamma
float mat_gamma = uMMParam024.x;
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













const int MAX_STEPS = 1;
const float MAX_DIST = 1.;
const float SURF_DIST = 0.0001;
const float NORMAL_DIST = 0.001;
float SHININESS = 10 / pow(mat_power, 2.);
const float DOWNSTEP = 0.1;


vec2 uv;
vec2 lightOffset;
vec3 lightPos;

float rayLength;
float closestDist;
float hitDist;
vec3 hit;
vec3 intersect;
vec2 m;

mat2 rotate(float a){
  return mat2(cos(a), -sin(a), sin(a), cos(a));
}


float wave(vec2 p) {

    p *= mat_wave_scale;
    float v = sin(p.x*0.7*mat_factor_1 + sin(p.y*2.2*mat_factor_2) + sin(p.y * .43*mat_factor_3));
    return v*v;
}

const mat2 rot = mat2(0.5, 0.86, -0.86, 0.5);

float get(vec2 p,float t)
{
  float v = 0.0;
  v += wave(p) * mat_distort_1;
  p.y += t;

  
  
  

  p *= rot;
  v += wave(p) * mat_distort_2;
  p.y += t * .17;   
  p *= rot;
  v += wave(p) * mat_distort_3;
  v+=pow(abs(sin(p.x+v)),2.0);

  v = abs(1.5 - v) * mat_distort_4;
  return v;
}

float sdf(vec3 p){
    float v = get(p.xy*6.0,mat_time)*0.1;
        v = smoothstep(0.02,3.5,v)*2.5 * mat_height;

    return p.z+v;
}

float rayMarch(vec3 ro, vec3 rd)
{
    float dO=0.;
    for(int i=0; i<MAX_STEPS; i++) {
        vec3 p = ro + rd*dO;
        float dS = sdf(p);
        closestDist = min(dS, closestDist);
        dO += dS*DOWNSTEP;
        if(dO>MAX_DIST || dS<SURF_DIST) break;
    }
    return dO;
}

vec3 normal(vec3 p)
{
    float d = sdf(p);
    vec2 e = vec2(NORMAL_DIST, 0);
    vec3 n = d - vec3(
        sdf(p-e.xyy),
        sdf(p-e.yxy),
        sdf(p-e.yyx));
    return normalize(n);
}

float diffuseLight(vec3 p, vec3 normal)
{
    vec3 l = normalize(lightPos-p);
    float dif = clamp(dot(normal, l), 0., 1.);
    float d = rayMarch(p+normal*SURF_DIST*2., l);
    if(d<length(lightPos-p)){ dif *= .1; }
    return dif;
}


float specularLight(vec3 p, vec3 rayDir, vec3 normal) {
    vec3 lightDir = normalize(p-lightPos);
    vec3 reflectionDirection = reflect(-lightDir, normal);
    float specularAngle = max(dot(reflectionDirection, rayDir), 0.);
    return pow(specularAngle, SHININESS);
}

float render(vec2 uv)
{

    vec2 wave_pos = mat_wave_pos;
    wave_pos += vec2(0.5);
    wave_pos.x = 1.-wave_pos.x;
    wave_pos -= vec2(0.5);

    vec3 rayOrigin = vec3(uv+vec2(0. + wave_pos.x, 0.25 + wave_pos.y), 0. + mat_dist);


    
    vec3 rayDir = normalize(vec3(uv.x, uv.y, 1.));
    hitDist = rayMarch(rayOrigin, rayDir);
    hit = rayOrigin + rayDir * hitDist;
    vec3 normal = normal(hit);
    float diff = diffuseLight(hit, normal);
    float spec = specularLight(hit, rayDir, normal);
    return .5*diff + .5*spec;
}

float aaRender(vec2 uv){
    
    vec2 third = vec2(1./(1000.), 1./(1000.)) / 3.0;
    vec2 mult = vec2(1, -1);
    float c1 = render(uv+third*mult.xx);
    float c2 = render(uv+third*mult.xy);
    float c3 = render(uv+third*mult.yx);
    float c4 = render(uv+third*mult.yy);
    return (c1+c2+c3+c4) / 4.;
}

vec3 gammaCorrection(vec3 rgb){
    float gamma = 2.2 * mat_gamma;
    rgb = smoothstep(0., 1., rgb);
    return pow(max(rgb, 0.), vec3(1.0/gamma));
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

    vec2 light_pos = mat_light_pos;
    light_pos += vec2(0.5);
    light_pos.y = 1.-light_pos.y;
    light_pos *= 4.;
    light_pos -= vec2(0.5);


    
    
    lightPos = vec3(0. + light_pos.x,5.0 + light_pos.y,-16.0 + mat_light_height * 2.);

    float lit = render(uv);
    lit *= smoothstep(MAX_DIST*.15, MAX_DIST*.05, hitDist);
    

    
    vec3 col = 1.8 * mat_tint.rgb * lit;

    out_color = vec4(gammaCorrection(col),1.0);
    

    
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
