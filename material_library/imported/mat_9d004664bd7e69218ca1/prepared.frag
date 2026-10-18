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
uniform vec4 uMMParam001; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam001.xy;
uniform vec4 uMMParam002; // native input: mat_iterations
float mat_iterations = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_amplitude
float mat_amplitude = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_frequency
float mat_frequency = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_density
float mat_density = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_speed
float mat_speed = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_reverse
bool mat_reverse = uMMParam008.x > 0.5;
uniform vec4 uMMParam009; // native input: mat_offset
float mat_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_strob
float mat_strob = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_restart
int mat_restart = int(round(uMMParam011.x));
uniform vec4 uMMParam012; // native input: mat_spin_active
bool mat_spin_active = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_spin_amount
float mat_spin_amount = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_spin_animate
bool mat_spin_animate = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_spin_speed
float mat_spin_speed = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_spin_bpm_sync
bool mat_spin_bpm_sync = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_spin_reverse
bool mat_spin_reverse = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_spin_offset
float mat_spin_offset = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_spin_strob
float mat_spin_strob = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_spin_decay
float mat_spin_decay = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_spin_release
float mat_spin_release = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_spin_restart
int mat_spin_restart = int(round(uMMParam022.x));
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
float mat_spin_time_source = uTDTime * (mat_spin_speed);

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

float mat_noise_time = 8. * mat_time_source - mat_offset;



















#define ANIMATION_SPEED 0.075






mat3 m = mat3( 0.00,  0.80,  0.60,
              -0.80,  0.36, -0.48,
              -0.60, -0.48,  0.64 );

float mat_hash( float n )
{
    return fract(sin(n)*43758.5453123);
}


float mat_noise( in vec3 x )
{
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f*f*(3.0-2.0*f);
    float n = p.x + p.y*57.0 + 113.0*p.z;
    float res = mix(mix(mix( mat_hash(n+  0.0), mat_hash(n+  1.0),f.x),
                        mix( mat_hash(n+ 57.0), mat_hash(n+ 58.0),f.x),f.y),
                    mix(mix( mat_hash(n+113.0), mat_hash(n+114.0),f.x),
                        mix( mat_hash(n+170.0), mat_hash(n+171.0),f.x),f.y),f.z);
    return res;
}


float mat_fbm( vec3 p )
{
    float f = 0.0;
    f += 0.5000*mat_noise( p );
    p = m*p*2.02;
    f += 0.2500*mat_noise( p );

#if 0
    return f/0.75;
#else
    p = m*p*2.03;
    f += 0.1250*mat_noise( p );

#if 1
    return f/0.875;
#else
    p = m*p*2.01;
    f += 0.0625*mat_noise( p );
    return f/0.9375;
#endif
#endif
}




vec3 mat_gradient(float s)
{
    return vec3(0.0, max(1.0-s*2.0, 0.0), max(s>0.5?1.0-(s-0.5)*5.0:1.0, 0.0));
}


#define RADIUS 0.5
bool intersectSphere(vec3 origin, vec3 direction, out float tmin, out float tmax)
{
    bool hit = false;
    float a = dot(direction, direction);
    float b = 2.0*dot(origin, direction);
    float c = dot(origin, origin) - 0.5*0.5;
    float disc = b*b - 4.0*a*c;           
    tmin = tmax = 0.0;

    if (disc > 0.0) {
        
        float sdisc = sqrt(disc);
        float t0 = (-b - sdisc)/(2.0*a);          
        float t1 = (-b + sdisc)/(2.0*a);          

        tmax = t1;
        if (t0 >= 0.0)
            tmin = t0;
        hit = true;
    }

    return hit;
}


vec2 rt(vec2 x,float y)
{
    return vec2(cos(y)*x.x-sin(y)*x.y,sin(y)*x.x+cos(y)*x.y);
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale * 2.;

    vec2 uv_shift = mat_shift_amount;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);
    uv += uv_shift;


    
    vec2 p = uv;

    float spin_time = 0.;

    if (mat_spin_active) {


        if (mat_spin_animate) {
            spin_time = fract(0.25*mat_spin_time_source - mat_spin_offset);
        } else {
            spin_time = 0.;
        }

        if (spin_time < mat_spin_decay) {
            spin_time = 1.;
        } else {
            
            spin_time = (spin_time - mat_spin_decay) * 1. / (1. - mat_spin_decay);
            if (spin_time < mat_spin_release) {
                spin_time = 1. - spin_time * 1. / mat_spin_release;
            } else {
                spin_time = 0.;
            }
        }

        spin_time = 1. - spin_time;

        spin_time += mat_spin_amount / 360.;
    }



    
    

    vec3 oo = vec3(0., 0., 1.);

    vec3 od = normalize(vec3(p.x, p.y, -2.0));
    vec3 o,d;
    o.xz = rt(oo.xz, 6.3*spin_time);
    o.y = oo.y;
    d.xz = rt(od.xz, 6.3*spin_time);
    d.y = od.y;
    
    vec4 col = vec4(0, 0, 0, 0);
    float tmin, tmax;
    if (intersectSphere(o, d, tmin, tmax))
    {
        
        for (float i = 0.0; i < mat_iterations; i+=1.0)
        {
            
            float t = tmin+i/mat_iterations;
            if (t > tmax)
                break;
            vec3 curpos = o + d*t;

            
            float s = (0.5-length(curpos))*2.0;

            s*=s;
            
            float a = mat_amplitude;
            float b = mat_frequency;
            float d = mat_density;
            for (int j = 0; j < 3; j++)
            {
                d += 0.5/abs((mat_fbm(5.0*curpos*b+ANIMATION_SPEED*mat_noise_time/b)*2.0-1.0)/a);
                b *= 2.0;
                a /= 2.0;
            }

            
            col.rgb += mat_gradient(s)*max(d*s,0.0);
        }
    }
    out_color = col;

    out_color.a = 1.;




    
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
