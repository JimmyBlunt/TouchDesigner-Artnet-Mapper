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

const int lightSource = 2;
#define lightSource_IS__575W_HPL_3200k
const int Gel = 90;
#define Gel_IS_R80_Primary_Blue
const int mode = 1;
#define mode_IS_Solid

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


// BEGIN MadNoise.glsl
/*
MadNoise Glsl Library

Copyright (c) 2016, Garage Cube, All rights reserved.
Copyright (c) 2016, Simon Geilfus, All rights reserved.

Portions of code adapted from Brian Sharpe Noise Library
Portions of code adapted from Stefan Gustavson Simplex Noise Public Domain implementation
Curl noise adapted from Robert Bridson papers

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

//#define NOISE_TEXTURE_BASED
//#define NOISE_WORLEY_ASHIMA_IMPL

#ifndef NOISE_LUT_INV_SIZE
    #define NOISE_LUT_INV_SIZE 1.0 / 256
#endif

//! Returns a 2D value noise in the range [0,1]
float vnoise( vec2 p );
//! Returns a 3D value noise in the range [0,1]
float vnoise( vec3 p );

//! Returns a 2D value noise with derivatives in the range [0,1] 
vec3 dvnoise( vec2 p );
//! Returns a 3D value noise with derivatives in the range [0,1]
vec4 dvnoise( vec3 p );

//! Returns a 2D simplex noise in the range [-1,1]
float noise( vec2 p );
//! Returns a 3D simplex noise in the range [-1,1]
float noise( vec3 p );

//! Returns a 2D simplex noise with derivatives in the range [-1,1]
vec3 dnoise( vec2 p );
//! Returns a 3D simplex noise with derivatives in the range [-1,1]
vec4 dnoise( vec3 p );

#if ! defined( NOISE_WORLEY_ASHIMA_IMPL )
//! Returns a 2D worley/cellular noise in the range [0,1]
float worleyNoise( vec2 p );
//! Returns a 3D worley/cellular noise in the range [0,1]
float worleyNoise( vec3 p );
#else 
//! Returns a 2D worley/cellular noise F1 and F2 in the range [0,1]
vec2 worleyNoise( vec2 p );
//! Returns a 3D worley/cellular noise F1 and F2 in the range [0,1]
vec2 worleyNoise( vec3 p );
#endif

//! Returns a 2D worley/cellular noise with derivatives in the range [0,1]
vec3 dWorleyNoise( vec2 p );
//! Returns a 3D worley/cellular noise with derivatives in the range [0,1]
vec4 dWorleyNoise( vec3 p );

//! Returns a 2D simplex noise with rotating gradients in the range [-1,-1]
float flowNoise( vec2 pos, float rot );
//! Returns a 2D simplex noise with rotating gradients and derivatives in the range [-1,-1]
vec3 dFlowNoise( vec2 pos, float rot );

//! Returns a 2D Billowed Noise in the range [0,1]
float billowedNoise( vec2 p );
//! Returns a 3D Billowed Noise in the range [0,1]
float billowedNoise( vec3 p );

//! Returns a 2D Billowed Noise with Derivatives in the range [0,1]
vec3 dBillowedNoise( vec2 p );
//! Returns a 3D Billowed Noise with Derivatives in the range [0,1]
vec4 dBillowedNoise( vec3 p );

//! Returns a 2D Ridged Noise in the range [0,1]
float ridgedNoise( vec2 p );
//! Returns a 2D Ridged Noise in the range [0,1]
float ridgedNoise( vec2 p, float ridge );
//! Returns a 3D Ridged Noise in the range [0,1]
float ridgedNoise( vec3 p );
//! Returns a 3D Ridged Noise in the range [0,1]
float ridgedNoise( vec3 p, float ridge );

//! Returns a 2D Ridged Noise with Derivatives in the range [0,1]
vec3 dRidgedNoise( vec2 p );
//! Returns a 2D Ridged Noise with Derivatives in the range [0,1]
vec3 dRidgedNoise( vec2 p, float ridge );
//! Returns a 3D Ridged Noise with Derivatives in the range [0,1]
vec4 dRidgedNoise( vec3 p );
//! Returns a 3D Ridged Noise with Derivatives in the range [0,1]
vec4 dRidgedNoise( vec3 p, float ridge );

//! Returns a 2D Curl of a Simplex Noise in the range [-1,1]
vec2 curlNoise( vec2 v );
//! Returns a 2D Curl of a Simplex Flow Noise in the range [-1,1]
vec2 curlNoise( vec2 v, float t );

//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec2 p );
//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec2 p, int octaves, float lacunarity, float gain );
//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec3 p );
//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec3 p, int octaves, float lacunarity, float gain );

//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
vec3 dfBm( vec2 p );
//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dfBm( vec2 p, int octaves, float lacunarity, float gain );
//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dfBm( vec3 p );
//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dfBm( vec3 p, int octaves, float lacunarity, float gain );

//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec2 p );
//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec2 p, int octaves, float lacunarity, float gain );
//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec3 p );
//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec3 p, int octaves, float lacunarity, float gain );

//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec3 dBillowyTurbulence( vec2 p );
//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec3 dBillowyTurbulence( vec2 p, int octaves, float lacunarity, float gain );
//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec4 dBillowyTurbulence( vec3 p );
//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec4 dBillowyTurbulence( vec3 p, int octaves, float lacunarity, float gain );

//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec2 p );
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec2 p, float ridgeOffset );
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec2 p, float ridgeOffset, int octaves, float lacunarity, float gain );
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec3 p );
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec3 p, float ridgeOffset );
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec3 p, float ridgeOffset, int octaves, float lacunarity, float gain );

//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
vec3 dRidgedMF( vec2 p );
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dRidgedMF( vec2 p, float ridgeOffset );
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dRidgedMF( vec2 p, float ridgeOffset, int octaves, float lacunarity, float gain );
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dRidgedMF( vec3 p );
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dRidgedMF( vec3 p, float ridgeOffset );
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dRidgedMF( vec3 p, float ridgeOffset, int octaves, float lacunarity, float gain );

// Implementation

// Adapted from Brian Sharpe Noise Library
// https://github.com/BrianSharpe/Wombat/

//! Returns a 2D value noise in the range [0,1]
#ifndef NOISE_TEXTURE_BASED
float vnoise( vec2 p )
{
    //  establish our grid cell and unit position
    vec2 Pi = floor(p);
    vec2 Pf = p - Pi;

    //  calculate the hash.
    vec4 Pt = vec4( Pi.xy, Pi.xy + 1.0 );
    Pt = Pt - floor(Pt * ( 1.0 / 71.0 )) * 71.0;
    Pt += vec2( 26.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec4 hash = fract( Pt * ( 1.0 / 951.135664 ) );

    //  blend the results and return
    vec2 blend = Pf * Pf * Pf * (Pf * (Pf * 6.0 - 15.0) + 10.0);
    vec4 blend2 = vec4( blend, vec2( 1.0 - blend ) );
    return dot( hash, blend2.zxzx * blend2.wwyy );
}
#else
float vnoise( vec2 p )
{
    vec2 ip = floor( p );
    vec2 fp = p - ip;
    vec2 uv = ( ip + ( fp * fp * ( 3.0f - 2.0f * fp ) ) + 0.5f ) * NOISE_LUT_INV_SIZE;
    return texture( noiseLUT, uv ).x;
}
#endif

//! Returns a 2D value noise with derivatives in the range [0,1] 
//#ifndef NOISE_TEXTURE_BASED
vec3 dvnoise( vec2 p )
{
    //  establish our grid cell and unit position
    vec2 Pi = floor(p);
    vec2 Pf = p - Pi;

    //  calculate the hash.
    vec4 Pt = vec4( Pi.xy, Pi.xy + 1.0 );
    Pt = Pt - floor(Pt * ( 1.0 / 71.0 )) * 71.0;
    Pt += vec2( 26.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec4 hash = fract( Pt * ( 1.0 / 951.135664 ) );

    //  blend the results and return
    vec4 blend = Pf.xyxy * Pf.xyxy * ( Pf.xyxy * ( Pf.xyxy * ( Pf.xyxy * vec2( 6.0, 0.0 ).xxyy + vec2( -15.0, 30.0 ).xxyy ) + vec2( 10.0, -60.0 ).xxyy ) + vec2( 0.0, 30.0 ).xxyy );
    vec4 res0 = mix( hash.xyxz, hash.zwyw, blend.yyxx );
    return vec3( res0.x, 0.0, 0.0 ) + ( res0.yyw - res0.xxz ) * blend.xzw;
}
//#else 
//#endif

//! Returns a 3D value noise in the range [0,1]
#ifndef NOISE_TEXTURE_BASED
float vnoise( vec3 p )
{
    // establish our grid cell and unit position
    vec3 Pi = floor(p);
    vec3 Pf = p - Pi;
    vec3 Pf_min1 = Pf - 1.0;

    // clamp the domain
    Pi.xyz = Pi.xyz - floor(Pi.xyz * ( 1.0 / 69.0 )) * 69.0;
    vec3 Pi_inc1 = step( Pi, vec3( 69.0 - 1.5 ) ) * ( Pi + 1.0 );

    // calculate the hash
    vec4 Pt = vec4( Pi.xy, Pi_inc1.xy ) + vec2( 50.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec2 hash_mod = vec2( 1.0 / ( 635.298681 + vec2( Pi.z, Pi_inc1.z ) * 48.500388 ) );
    vec4 hash_lowz = fract( Pt * hash_mod.xxxx );
    vec4 hash_highz = fract( Pt * hash_mod.yyyy );

    //  blend the results and return
    vec3 blend = Pf * Pf * Pf * (Pf * (Pf * 6.0 - 15.0) + 10.0);
    vec4 res0 = mix( hash_lowz, hash_highz, blend.z );
    vec4 blend2 = vec4( blend.xy, vec2( 1.0 - blend.xy ) );
    return dot( res0, blend2.zxzx * blend2.wwyy );
}
#else
float vnoise( vec3 p )
{
    vec3 ip = floor( p );
    vec3 fp = p - ip;
    fp      = ( fp * fp * ( 3.0f - 2.0f * fp ) );
    
    vec2 uv = ( ip.xy + vec2( 37.0f, 17.0f ) * ip.z ) + fp.xy;
    vec2 rg = texture( noiseLUT, ( uv + 0.5f ) * NOISE_LUT_INV_SIZE, -100.0f ).yx;
    return mix( rg.x, rg.y, fp.z );
}
#endif

//! Returns a 3D value noise with derivatives in the range [0,1]
vec4 dvnoise( vec3 p )
{
    // establish our grid cell and unit position
    vec3 Pi = floor(p);
    vec3 Pf = p - Pi;
    vec3 Pf_min1 = Pf - 1.0;

    // clamp the domain
    Pi.xyz = Pi.xyz - floor(Pi.xyz * ( 1.0 / 69.0 )) * 69.0;
    vec3 Pi_inc1 = step( Pi, vec3( 69.0 - 1.5 ) ) * ( Pi + 1.0 );

    // calculate the hash
    vec4 Pt = vec4( Pi.xy, Pi_inc1.xy ) + vec2( 50.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec2 hash_mod = vec2( 1.0 / ( 635.298681 + vec2( Pi.z, Pi_inc1.z ) * 48.500388 ) );
    vec4 hash_lowz = fract( Pt * hash_mod.xxxx );
    vec4 hash_highz = fract( Pt * hash_mod.yyyy );

    //  blend the results and return
    vec3 blend = Pf * Pf * Pf * (Pf * (Pf * 6.0 - 15.0) + 10.0);
    vec3 blendDeriv = Pf * Pf * (Pf * (Pf * 30.0 - 60.0) + 30.0);
    vec4 res0 = mix( hash_lowz, hash_highz, blend.z );
    vec4 res1 = mix( res0.xyxz, res0.zwyw, blend.yyxx );
    vec4 res3 = mix( vec4( hash_lowz.xy, hash_highz.xy ), vec4( hash_lowz.zw, hash_highz.zw ), blend.y );
    vec2 res4 = mix( res3.xz, res3.yw, blend.x );
    return vec4( res1.x, 0.0, 0.0, 0.0 ) + ( vec4( res1.yyw, res4.y ) - vec4( res1.xxz, res4.x ) ) * vec4( blend.x, blendDeriv );
}

//! Returns a 2D simplex noise in the range [-1,1]
float noise( vec2 p )
{
    //  simplex math constants
    const float SKEWFACTOR = 0.36602540378443864676372317075294;            // 0.5*(sqrt(3.0)-1.0)
    const float UNSKEWFACTOR = 0.21132486540518711774542560974902;          // (3.0-sqrt(3.0))/6.0
    const float SIMPLEX_TRI_HEIGHT = 0.70710678118654752440084436210485;    // sqrt( 0.5 )  height of simplex triangle
    const vec3 SIMPLEX_POINTS = vec3( 1.0-UNSKEWFACTOR, -UNSKEWFACTOR, 1.0-2.0*UNSKEWFACTOR );  //  simplex triangle geo

    //  establish our grid cell.
    p *= SIMPLEX_TRI_HEIGHT;    // scale space so we can have an approx feature size of 1.0
    vec2 Pi = floor( p + dot( p, vec2( SKEWFACTOR ) ) );

    // calculate the hash
    vec4 Pt = vec4( Pi.xy, Pi.xy + 1.0 );
    Pt = Pt - floor(Pt * ( 1.0 / 71.0 )) * 71.0;
    Pt += vec2( 26.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec4 hash_x = fract( Pt * ( 1.0 / 951.135664 ) );
    vec4 hash_y = fract( Pt * ( 1.0 / 642.949883 ) );

    //  establish vectors to the 3 corners of our simplex triangle
    vec2 v0 = Pi - dot( Pi, vec2( UNSKEWFACTOR ) ) - p;
    vec4 v1pos_v1hash = (v0.x < v0.y) ? vec4(SIMPLEX_POINTS.xy, hash_x.y, hash_y.y) : vec4(SIMPLEX_POINTS.yx, hash_x.z, hash_y.z);
    vec4 v12 = vec4( v1pos_v1hash.xy, SIMPLEX_POINTS.zz ) + v0.xyxy;

    //  calculate the dotproduct of our 3 corner vectors with 3 random normalized vectors
    vec3 grad_x = vec3( hash_x.x, v1pos_v1hash.z, hash_x.w ) - 0.49999;
    vec3 grad_y = vec3( hash_y.x, v1pos_v1hash.w, hash_y.w ) - 0.49999;
    vec3 grad_results = inversesqrt( grad_x * grad_x + grad_y * grad_y ) * ( grad_x * vec3( v0.x, v12.xz ) + grad_y * vec3( v0.y, v12.yw ) );

    //  Normalization factor to scale the final result to a strict 1.0->-1.0 range
    //  http://briansharpe.wordpress.com/2012/01/13/simplex-noise/#comment-36
    const float FINAL_NORMALIZATION = 99.204334582718712976990005025589;

    //  evaluate and return
    vec3 m = vec3( v0.x, v12.xz ) * vec3( v0.x, v12.xz ) + vec3( v0.y, v12.yw ) * vec3( v0.y, v12.yw );
    m = max(0.5 - m, 0.0);
    m = m*m;
    return dot(m*m, grad_results) * FINAL_NORMALIZATION;
}

//! Returns a 2D simplex noise with derivatives in the range [-1,1]
vec3 dnoise( vec2 p )
{
    //  simplex math constants
    const float SKEWFACTOR = 0.36602540378443864676372317075294;            // 0.5*(sqrt(3.0)-1.0)
    const float UNSKEWFACTOR = 0.21132486540518711774542560974902;          // (3.0-sqrt(3.0))/6.0
    const float SIMPLEX_TRI_HEIGHT = 0.70710678118654752440084436210485;    // sqrt( 0.5 )  height of simplex triangle
    const vec3 SIMPLEX_POINTS = vec3( 1.0-UNSKEWFACTOR, -UNSKEWFACTOR, 1.0-2.0*UNSKEWFACTOR );  //  simplex triangle geo

    //  establish our grid cell.
    p *= SIMPLEX_TRI_HEIGHT;    // scale space so we can have an approx feature size of 1.0
    vec2 Pi = floor( p + dot( p, vec2( SKEWFACTOR ) ) );

    // calculate the hash
    vec4 Pt = vec4( Pi.xy, Pi.xy + 1.0 );
    Pt = Pt - floor(Pt * ( 1.0 / 71.0 )) * 71.0;
    Pt += vec2( 26.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec4 hash_x = fract( Pt * ( 1.0 / 951.135664 ) );
    vec4 hash_y = fract( Pt * ( 1.0 / 642.949883 ) );

    //  establish vectors to the 3 corners of our simplex triangle
    vec2 v0 = Pi - dot( Pi, vec2( UNSKEWFACTOR ) ) - p;
    vec4 v1pos_v1hash = (v0.x < v0.y) ? vec4(SIMPLEX_POINTS.xy, hash_x.y, hash_y.y) : vec4(SIMPLEX_POINTS.yx, hash_x.z, hash_y.z);
    vec4 v12 = vec4( v1pos_v1hash.xy, SIMPLEX_POINTS.zz ) + v0.xyxy;

    //  calculate the dotproduct of our 3 corner vectors with 3 random normalized vectors
    vec3 grad_x = vec3( hash_x.x, v1pos_v1hash.z, hash_x.w ) - 0.49999;
    vec3 grad_y = vec3( hash_y.x, v1pos_v1hash.w, hash_y.w ) - 0.49999;
    vec3 norm = inversesqrt( grad_x * grad_x + grad_y * grad_y );
    grad_x *= norm;
    grad_y *= norm;
    vec3 grad_results = grad_x * vec3( v0.x, v12.xz ) + grad_y * vec3( v0.y, v12.yw );

    //  evaluate the kernel
    vec3 m = vec3( v0.x, v12.xz ) * vec3( v0.x, v12.xz ) + vec3( v0.y, v12.yw ) * vec3( v0.y, v12.yw );
    m = max(0.5 - m, 0.0);
    vec3 m2 = m*m;
    vec3 m4 = m2*m2;

    //  calc the derivatives
    vec3 temp = 8.0 * m2 * m * grad_results;
    float xderiv = dot( temp, vec3( v0.x, v12.xz ) ) - dot( m4, grad_x );
    float yderiv = dot( temp, vec3( v0.y, v12.yw ) ) - dot( m4, grad_y );

    //  Normalization factor to scale the final result to a strict 1.0->-1.0 range
    //  http://briansharpe.wordpress.com/2012/01/13/simplex-noise/#comment-36
    const float FINAL_NORMALIZATION = 99.204334582718712976990005025589;

    //  sum and return all results as a vec3
    return vec3( dot( m4, grad_results ), xderiv, yderiv ) * FINAL_NORMALIZATION;
}

//! Returns a 3D simplex noise in the range [-1,1]
float noise( vec3 p )
{
    //  simplex math constants
    const float SKEWFACTOR = 1.0/3.0;
    const float UNSKEWFACTOR = 1.0/6.0;
    const float SIMPLEX_CORNER_POS = 0.5;
    const float SIMPLEX_TETRAHADRON_HEIGHT = 0.70710678118654752440084436210485;    // sqrt( 0.5 )

    //  establish our grid cell.
    p *= SIMPLEX_TETRAHADRON_HEIGHT;    // scale space so we can have an approx feature size of 1.0
    vec3 Pi = floor( p + dot( p, vec3( SKEWFACTOR) ) );

    //  Find the vectors to the corners of our simplex tetrahedron
    vec3 x0 = p - Pi + dot(Pi, vec3( UNSKEWFACTOR ) );
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 Pi_1 = min( g.xyz, l.zxy );
    vec3 Pi_2 = max( g.xyz, l.zxy );
    vec3 x1 = x0 - Pi_1 + UNSKEWFACTOR;
    vec3 x2 = x0 - Pi_2 + SKEWFACTOR;
    vec3 x3 = x0 - SIMPLEX_CORNER_POS;

    //  pack them into a parallel-friendly arrangement
    vec4 v1234_x = vec4( x0.x, x1.x, x2.x, x3.x );
    vec4 v1234_y = vec4( x0.y, x1.y, x2.y, x3.y );
    vec4 v1234_z = vec4( x0.z, x1.z, x2.z, x3.z );

    // clamp the domain of our grid cell
    Pi.xyz = Pi.xyz - floor(Pi.xyz * ( 1.0 / 69.0 )) * 69.0;
    vec3 Pi_inc1 = step( Pi, vec3( 69.0 - 1.5 ) ) * ( Pi + 1.0 );

    //  generate the random vectors
    vec4 Pt = vec4( Pi.xy, Pi_inc1.xy ) + vec2( 50.0, 161.0 ).xyxy;
    Pt *= Pt;
    vec4 V1xy_V2xy = mix( Pt.xyxy, Pt.zwzw, vec4( Pi_1.xy, Pi_2.xy ) );
    Pt = vec4( Pt.x, V1xy_V2xy.xz, Pt.z ) * vec4( Pt.y, V1xy_V2xy.yw, Pt.w );
    const vec3 SOMELARGEFLOATS = vec3( 635.298681, 682.357502, 668.926525 );
    const vec3 ZINC = vec3( 48.500388, 65.294118, 63.934599 );
    vec3 lowz_mods = vec3( 1.0 / ( SOMELARGEFLOATS.xyz + Pi.zzz * ZINC.xyz ) );
    vec3 highz_mods = vec3( 1.0 / ( SOMELARGEFLOATS.xyz + Pi_inc1.zzz * ZINC.xyz ) );
    Pi_1 = ( Pi_1.z < 0.5 ) ? lowz_mods : highz_mods;
    Pi_2 = ( Pi_2.z < 0.5 ) ? lowz_mods : highz_mods;
    vec4 hash_0 = fract( Pt * vec4( lowz_mods.x, Pi_1.x, Pi_2.x, highz_mods.x ) ) - 0.49999;
    vec4 hash_1 = fract( Pt * vec4( lowz_mods.y, Pi_1.y, Pi_2.y, highz_mods.y ) ) - 0.49999;
    vec4 hash_2 = fract( Pt * vec4( lowz_mods.z, Pi_1.z, Pi_2.z, highz_mods.z ) ) - 0.49999;

    //  evaluate gradients
    vec4 grad_results = inversesqrt( hash_0 * hash_0 + hash_1 * hash_1 + hash_2 * hash_2 ) * ( hash_0 * v1234_x + hash_1 * v1234_y + hash_2 * v1234_z );

    //  Normalization factor to scale the final result to a strict 1.0->-1.0 range
    //  http://briansharpe.wordpress.com/2012/01/13/simplex-noise/#comment-36
    const float FINAL_NORMALIZATION = 37.837227241611314102871574478976;

    //  evaulate the kernel weights ( use (0.5-x*x)^3 instead of (0.6-x*x)^4 to fix discontinuities )
    vec4 kernel_weights = v1234_x * v1234_x + v1234_y * v1234_y + v1234_z * v1234_z;
    kernel_weights = max(0.5 - kernel_weights, 0.0);
    kernel_weights = kernel_weights*kernel_weights*kernel_weights;

    //  sum with the kernel and return
    return dot( kernel_weights, grad_results ) * FINAL_NORMALIZATION;
}

//! Returns a 3D simplex noise with derivatives in the range [-1,1]
vec4 dnoise( vec3 p )
{
    //  simplex math constants
    const float SKEWFACTOR = 1.0/3.0;
    const float UNSKEWFACTOR = 1.0/6.0;
    const float SIMPLEX_CORNER_POS = 0.5;
    const float SIMPLEX_TETRAHADRON_HEIGHT = 0.70710678118654752440084436210485;    // sqrt( 0.5 )

    //  establish our grid cell.
    p *= SIMPLEX_TETRAHADRON_HEIGHT;    // scale space so we can have an approx feature size of 1.0
    vec3 Pi = floor( p + dot( p, vec3( SKEWFACTOR) ) );

    //  Find the vectors to the corners of our simplex tetrahedron
    vec3 x0 = p - Pi + dot(Pi, vec3( UNSKEWFACTOR ) );
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 Pi_1 = min( g.xyz, l.zxy );
    vec3 Pi_2 = max( g.xyz, l.zxy );
    vec3 x1 = x0 - Pi_1 + UNSKEWFACTOR;
    vec3 x2 = x0 - Pi_2 + SKEWFACTOR;
    vec3 x3 = x0 - SIMPLEX_CORNER_POS;

    //  pack them into a parallel-friendly arrangement
    vec4 v1234_x = vec4( x0.x, x1.x, x2.x, x3.x );
    vec4 v1234_y = vec4( x0.y, x1.y, x2.y, x3.y );
    vec4 v1234_z = vec4( x0.z, x1.z, x2.z, x3.z );

    // clamp the domain of our grid cell
    Pi.xyz = Pi.xyz - floor(Pi.xyz * ( 1.0 / 69.0 )) * 69.0;
    vec3 Pi_inc1 = step( Pi, vec3( 69.0 - 1.5 ) ) * ( Pi + 1.0 );

    //  generate the random vectors
    vec4 Pt = vec4( Pi.xy, Pi_inc1.xy ) + vec2( 50.0, 161.0 ).xyxy;
    Pt *= Pt;
    vec4 V1xy_V2xy = mix( Pt.xyxy, Pt.zwzw, vec4( Pi_1.xy, Pi_2.xy ) );
    Pt = vec4( Pt.x, V1xy_V2xy.xz, Pt.z ) * vec4( Pt.y, V1xy_V2xy.yw, Pt.w );
    const vec3 SOMELARGEFLOATS = vec3( 635.298681, 682.357502, 668.926525 );
    const vec3 ZINC = vec3( 48.500388, 65.294118, 63.934599 );
    vec3 lowz_mods = vec3( 1.0 / ( SOMELARGEFLOATS.xyz + Pi.zzz * ZINC.xyz ) );
    vec3 highz_mods = vec3( 1.0 / ( SOMELARGEFLOATS.xyz + Pi_inc1.zzz * ZINC.xyz ) );
    Pi_1 = ( Pi_1.z < 0.5 ) ? lowz_mods : highz_mods;
    Pi_2 = ( Pi_2.z < 0.5 ) ? lowz_mods : highz_mods;
    vec4 hash_0 = fract( Pt * vec4( lowz_mods.x, Pi_1.x, Pi_2.x, highz_mods.x ) ) - 0.49999;
    vec4 hash_1 = fract( Pt * vec4( lowz_mods.y, Pi_1.y, Pi_2.y, highz_mods.y ) ) - 0.49999;
    vec4 hash_2 = fract( Pt * vec4( lowz_mods.z, Pi_1.z, Pi_2.z, highz_mods.z ) ) - 0.49999;

    //  normalize random gradient vectors
    vec4 norm = inversesqrt( hash_0 * hash_0 + hash_1 * hash_1 + hash_2 * hash_2 );
    hash_0 *= norm;
    hash_1 *= norm;
    hash_2 *= norm;

    //  evaluate gradients
    vec4 grad_results = hash_0 * v1234_x + hash_1 * v1234_y + hash_2 * v1234_z;

    //  evaulate the kernel weights ( use (0.5-x*x)^3 instead of (0.6-x*x)^4 to fix discontinuities )
    vec4 m = v1234_x * v1234_x + v1234_y * v1234_y + v1234_z * v1234_z;
    m = max(0.5 - m, 0.0);
    vec4 m2 = m*m;
    vec4 m3 = m*m2;

    //  calc the derivatives
    vec4 temp = -6.0 * m2 * grad_results;
    float xderiv = dot( temp, v1234_x ) + dot( m3, hash_0 );
    float yderiv = dot( temp, v1234_y ) + dot( m3, hash_1 );
    float zderiv = dot( temp, v1234_z ) + dot( m3, hash_2 );

    //  Normalization factor to scale the final result to a strict 1.0->-1.0 range
    //  http://briansharpe.wordpress.com/2012/01/13/simplex-noise/#comment-36
    const float FINAL_NORMALIZATION = 37.837227241611314102871574478976;

    //  sum and return all results as a vec3
    return vec4( dot( m3, grad_results ), xderiv, yderiv, zderiv ) * FINAL_NORMALIZATION;
}

// Modulo 289, optimizes to code without divisions
float mod289(float x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }

// Permutation polynomial (ring size 289 = 17*17)
float permute(float x) { return mod289(((x*34.0)+1.0)*x); }
vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }

// Modulo 7 without a division
vec3 mod7(vec3 x) {  return x - floor(x * (1.0 / 7.0)) * 7.0; }

#if ! defined( NOISE_WORLEY_ASHIMA_IMPL )
//! Returns a 2D worley/cellular noise in the range [0,1]
float worleyNoise( vec2 p )
{
    //  establish our grid cell and unit position
    vec2 Pi = floor(p);
    vec2 Pf = p - Pi;

    //  calculate the hash
    vec4 Pt = vec4( Pi.xy, Pi.xy + 1.0 );
    Pt = Pt - floor(Pt * ( 1.0 / 71.0 )) * 71.0;
    Pt += vec2( 26.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec4 hash_x = fract( Pt * ( 1.0 / 951.135664 ) );
    vec4 hash_y = fract( Pt * ( 1.0 / 642.949883 ) );

    //  generate the 4 points
    hash_x = hash_x * 2.0 - 1.0;
    hash_y = hash_y * 2.0 - 1.0;
    const float JITTER_WINDOW = 0.25;   // 0.25 will guarentee no artifacts
    hash_x = ( ( hash_x * hash_x * hash_x ) - sign( hash_x ) ) * JITTER_WINDOW + vec4( 0.0, 1.0, 0.0, 1.0 );
    hash_y = ( ( hash_y * hash_y * hash_y ) - sign( hash_y ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 1.0, 1.0 );

    //  return the closest squared distance
    vec4 dx = Pf.xxxx - hash_x;
    vec4 dy = Pf.yyyy - hash_y;
    vec4 d = dx * dx + dy * dy;
    d.xy = min(d.xy, d.zw);
    return min(d.x, d.y) * ( 1.0 / 1.125 ); // return a value scaled to 0.0->1.0
}
#else

// Cellular noise ("Worley noise") in 2D in GLSL.
// Copyright (c) Stefan Gustavson 2011-04-19. All rights reserved.
// This code is released under the conditions of the MIT license.
// See LICENSE file for details.
// https://github.com/stegu/webgl-noise
// Cellular noise, returning F1 and F2 in a vec2.
// Standard 3x3 search window for good F1 and F2 values
vec2 worleyNoise( vec2 P ) 
{
    const float K = 0.142857142857; // 1/7
    const float Ko = 0.428571428571; // 3/7
    const float jitter = 1.0; // Less gives more regular pattern
    vec2 Pi = mod289(floor(P));
    vec2 Pf = fract(P);
    vec3 oi = vec3(-1.0, 0.0, 1.0);
    vec3 of = vec3(-0.5, 0.5, 1.5);
    vec3 px = permute(Pi.x + oi);
    vec3 p = permute(px.x + Pi.y + oi); // p11, p12, p13
    vec3 ox = fract(p*K) - Ko;
    vec3 oy = mod7(floor(p*K))*K - Ko;
    vec3 dx = Pf.x + 0.5 + jitter*ox;
    vec3 dy = Pf.y - of + jitter*oy;
    vec3 d1 = dx * dx + dy * dy; // d11, d12 and d13, squared
    p = permute(px.y + Pi.y + oi); // p21, p22, p23
    ox = fract(p*K) - Ko;
    oy = mod7(floor(p*K))*K - Ko;
    dx = Pf.x - 0.5 + jitter*ox;
    dy = Pf.y - of + jitter*oy;
    vec3 d2 = dx * dx + dy * dy; // d21, d22 and d23, squared
    p = permute(px.z + Pi.y + oi); // p31, p32, p33
    ox = fract(p*K) - Ko;
    oy = mod7(floor(p*K))*K - Ko;
    dx = Pf.x - 1.5 + jitter*ox;
    dy = Pf.y - of + jitter*oy;
    vec3 d3 = dx * dx + dy * dy; // d31, d32 and d33, squared
    // Sort out the two smallest distances (F1, F2)
    vec3 d1a = min(d1, d2);
    d2 = max(d1, d2); // Swap to keep candidates for F2
    d2 = min(d2, d3); // neither F1 nor F2 are now in d3
    d1 = min(d1a, d2); // F1 is now in d1
    d2 = max(d1a, d2); // Swap to keep candidates for F2
    d1.xy = (d1.x < d1.y) ? d1.xy : d1.yx; // Swap if smaller
    d1.xz = (d1.x < d1.z) ? d1.xz : d1.zx; // F1 is in d1.x
    d1.yz = min(d1.yz, d2.yz); // F2 is now not in d2.yz
    d1.y = min(d1.y, d1.z); // nor in  d1.z
    d1.y = min(d1.y, d2.x); // F2 is in d1.y, we're done.
    return sqrt(d1.xy);
}

#endif

//! Returns a 2D worley/cellular noise with derivatives in the range [0,1]
vec3 dWorleyNoise( vec2 p )
{
    //  establish our grid cell and unit position
    vec2 Pi = floor(p);
    vec2 Pf = p - Pi;

    //  calculate the hash
    vec4 Pt = vec4( Pi.xy, Pi.xy + 1.0 );
    Pt = Pt - floor(Pt * ( 1.0 / 71.0 )) * 71.0;
    Pt += vec2( 26.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec4 hash_x = fract( Pt * ( 1.0 / 951.135664 ) );
    vec4 hash_y = fract( Pt * ( 1.0 / 642.949883 ) );

    //  generate the 4 points
    hash_x = hash_x * 2.0 - 1.0;
    hash_y = hash_y * 2.0 - 1.0;
    const float JITTER_WINDOW = 0.25;   // 0.25 will guarentee no artifacts
    hash_x = ( ( hash_x * hash_x * hash_x ) - sign( hash_x ) ) * JITTER_WINDOW + vec4( 0.0, 1.0, 0.0, 1.0 );
    hash_y = ( ( hash_y * hash_y * hash_y ) - sign( hash_y ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 1.0, 1.0 );

    //  return the closest squared distance + derivatives ( thanks to Jonathan Dupuy )
    vec4 dx = Pf.xxxx - hash_x;
    vec4 dy = Pf.yyyy - hash_y;
    vec4 d = dx * dx + dy * dy;
    vec3 t1 = d.x < d.y ? vec3( d.x, dx.x, dy.x ) : vec3( d.y, dx.y, dy.y );
    vec3 t2 = d.z < d.w ? vec3( d.z, dx.z, dy.z ) : vec3( d.w, dx.w, dy.w );
    return ( t1.x < t2.x ? t1 : t2 ) * vec3( 1.0, 2.0, 2.0 ) * ( 1.0 / 1.125 ); // return a value scaled to 0.0->1.0
}

#if ! defined( NOISE_WORLEY_ASHIMA_IMPL )
//! Returns a 3D worley/cellular noise in the range [0,1]
float worleyNoise( vec3 p )
{
    //  establish our grid cell and unit position
    vec3 Pi = floor(p);
    vec3 Pf = p - Pi;

    // clamp the domain
    Pi.xyz = Pi.xyz - floor(Pi.xyz * ( 1.0 / 69.0 )) * 69.0;
    vec3 Pi_inc1 = step( Pi, vec3( 69.0 - 1.5 ) ) * ( Pi + 1.0 );

    // calculate the hash ( over -1.0->1.0 range )
    vec4 Pt = vec4( Pi.xy, Pi_inc1.xy ) + vec2( 50.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    const vec3 SOMELARGEFLOATS = vec3( 635.298681, 682.357502, 668.926525 );
    const vec3 ZINC = vec3( 48.500388, 65.294118, 63.934599 );
    vec3 lowz_mod = vec3( 1.0 / ( SOMELARGEFLOATS + Pi.zzz * ZINC ) );
    vec3 highz_mod = vec3( 1.0 / ( SOMELARGEFLOATS + Pi_inc1.zzz * ZINC ) );
    vec4 hash_x0 = fract( Pt * lowz_mod.xxxx ) * 2.0 - 1.0;
    vec4 hash_x1 = fract( Pt * highz_mod.xxxx ) * 2.0 - 1.0;
    vec4 hash_y0 = fract( Pt * lowz_mod.yyyy ) * 2.0 - 1.0;
    vec4 hash_y1 = fract( Pt * highz_mod.yyyy ) * 2.0 - 1.0;
    vec4 hash_z0 = fract( Pt * lowz_mod.zzzz ) * 2.0 - 1.0;
    vec4 hash_z1 = fract( Pt * highz_mod.zzzz ) * 2.0 - 1.0;

    //  generate the 8 point positions
    const float JITTER_WINDOW = 0.166666666;  // 0.166666666 will guarentee no artifacts.
    hash_x0 = ( ( hash_x0 * hash_x0 * hash_x0 ) - sign( hash_x0 ) ) * JITTER_WINDOW + vec4( 0.0, 1.0, 0.0, 1.0 );
    hash_y0 = ( ( hash_y0 * hash_y0 * hash_y0 ) - sign( hash_y0 ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 1.0, 1.0 );
    hash_x1 = ( ( hash_x1 * hash_x1 * hash_x1 ) - sign( hash_x1 ) ) * JITTER_WINDOW + vec4( 0.0, 1.0, 0.0, 1.0 );
    hash_y1 = ( ( hash_y1 * hash_y1 * hash_y1 ) - sign( hash_y1 ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 1.0, 1.0 );
    hash_z0 = ( ( hash_z0 * hash_z0 * hash_z0 ) - sign( hash_z0 ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 0.0, 0.0 );
    hash_z1 = ( ( hash_z1 * hash_z1 * hash_z1 ) - sign( hash_z1 ) ) * JITTER_WINDOW + vec4( 1.0, 1.0, 1.0, 1.0 );

    //  return the closest squared distance
    vec4 dx1 = Pf.xxxx - hash_x0;
    vec4 dy1 = Pf.yyyy - hash_y0;
    vec4 dz1 = Pf.zzzz - hash_z0;
    vec4 dx2 = Pf.xxxx - hash_x1;
    vec4 dy2 = Pf.yyyy - hash_y1;
    vec4 dz2 = Pf.zzzz - hash_z1;
    vec4 d1 = dx1 * dx1 + dy1 * dy1 + dz1 * dz1;
    vec4 d2 = dx2 * dx2 + dy2 * dy2 + dz2 * dz2;
    d1 = min(d1, d2);
    d1.xy = min(d1.xy, d1.wz);
    return min(d1.x, d1.y) * ( 9.0 / 12.0 ); // return a value scaled to 0.0->1.0
}
#else

// Cellular noise ("Worley noise") in 3D in GLSL.
// Copyright (c) Stefan Gustavson 2011-04-19. All rights reserved.
// This code is released under the conditions of the MIT license.
// See LICENSE file for details.
// https://github.com/stegu/webgl-noise
// Cellular noise, returning F1 and F2 in a vec2.
// 3x3x3 search region for good F2 everywhere, but a lot
// slower than the 2x2x2 version.
// The code below is a bit scary even to its author,
// but it has at least half decent performance on a
// modern GPU. In any case, it beats any software
// implementation of Worley noise hands down.

vec2 worleyNoise( vec3 P ) 
{
    const float K = 0.142857142857; // 1/7
    const float Ko = 0.428571428571; // 1/2-K/2
    const float K2 = 0.020408163265306; // 1/(7*7)
    const float Kz = 0.166666666667; // 1/6
    const float Kzo = 0.416666666667; // 1/2-1/6*2
    const float jitter = 1.0; // smaller jitter gives more regular pattern

    vec3 Pi = mod289(floor(P));
    vec3 Pf = fract(P) - 0.5;

    vec3 Pfx = Pf.x + vec3(1.0, 0.0, -1.0);
    vec3 Pfy = Pf.y + vec3(1.0, 0.0, -1.0);
    vec3 Pfz = Pf.z + vec3(1.0, 0.0, -1.0);

    vec3 p = permute(Pi.x + vec3(-1.0, 0.0, 1.0));
    vec3 p1 = permute(p + Pi.y - 1.0);
    vec3 p2 = permute(p + Pi.y);
    vec3 p3 = permute(p + Pi.y + 1.0);

    vec3 p11 = permute(p1 + Pi.z - 1.0);
    vec3 p12 = permute(p1 + Pi.z);
    vec3 p13 = permute(p1 + Pi.z + 1.0);

    vec3 p21 = permute(p2 + Pi.z - 1.0);
    vec3 p22 = permute(p2 + Pi.z);
    vec3 p23 = permute(p2 + Pi.z + 1.0);

    vec3 p31 = permute(p3 + Pi.z - 1.0);
    vec3 p32 = permute(p3 + Pi.z);
    vec3 p33 = permute(p3 + Pi.z + 1.0);

    vec3 ox11 = fract(p11*K) - Ko;
    vec3 oy11 = mod7(floor(p11*K))*K - Ko;
    vec3 oz11 = floor(p11*K2)*Kz - Kzo; // p11 < 289 guaranteed

    vec3 ox12 = fract(p12*K) - Ko;
    vec3 oy12 = mod7(floor(p12*K))*K - Ko;
    vec3 oz12 = floor(p12*K2)*Kz - Kzo;

    vec3 ox13 = fract(p13*K) - Ko;
    vec3 oy13 = mod7(floor(p13*K))*K - Ko;
    vec3 oz13 = floor(p13*K2)*Kz - Kzo;

    vec3 ox21 = fract(p21*K) - Ko;
    vec3 oy21 = mod7(floor(p21*K))*K - Ko;
    vec3 oz21 = floor(p21*K2)*Kz - Kzo;

    vec3 ox22 = fract(p22*K) - Ko;
    vec3 oy22 = mod7(floor(p22*K))*K - Ko;
    vec3 oz22 = floor(p22*K2)*Kz - Kzo;

    vec3 ox23 = fract(p23*K) - Ko;
    vec3 oy23 = mod7(floor(p23*K))*K - Ko;
    vec3 oz23 = floor(p23*K2)*Kz - Kzo;

    vec3 ox31 = fract(p31*K) - Ko;
    vec3 oy31 = mod7(floor(p31*K))*K - Ko;
    vec3 oz31 = floor(p31*K2)*Kz - Kzo;

    vec3 ox32 = fract(p32*K) - Ko;
    vec3 oy32 = mod7(floor(p32*K))*K - Ko;
    vec3 oz32 = floor(p32*K2)*Kz - Kzo;

    vec3 ox33 = fract(p33*K) - Ko;
    vec3 oy33 = mod7(floor(p33*K))*K - Ko;
    vec3 oz33 = floor(p33*K2)*Kz - Kzo;

    vec3 dx11 = Pfx + jitter*ox11;
    vec3 dy11 = Pfy.x + jitter*oy11;
    vec3 dz11 = Pfz.x + jitter*oz11;

    vec3 dx12 = Pfx + jitter*ox12;
    vec3 dy12 = Pfy.x + jitter*oy12;
    vec3 dz12 = Pfz.y + jitter*oz12;

    vec3 dx13 = Pfx + jitter*ox13;
    vec3 dy13 = Pfy.x + jitter*oy13;
    vec3 dz13 = Pfz.z + jitter*oz13;

    vec3 dx21 = Pfx + jitter*ox21;
    vec3 dy21 = Pfy.y + jitter*oy21;
    vec3 dz21 = Pfz.x + jitter*oz21;

    vec3 dx22 = Pfx + jitter*ox22;
    vec3 dy22 = Pfy.y + jitter*oy22;
    vec3 dz22 = Pfz.y + jitter*oz22;

    vec3 dx23 = Pfx + jitter*ox23;
    vec3 dy23 = Pfy.y + jitter*oy23;
    vec3 dz23 = Pfz.z + jitter*oz23;

    vec3 dx31 = Pfx + jitter*ox31;
    vec3 dy31 = Pfy.z + jitter*oy31;
    vec3 dz31 = Pfz.x + jitter*oz31;

    vec3 dx32 = Pfx + jitter*ox32;
    vec3 dy32 = Pfy.z + jitter*oy32;
    vec3 dz32 = Pfz.y + jitter*oz32;

    vec3 dx33 = Pfx + jitter*ox33;
    vec3 dy33 = Pfy.z + jitter*oy33;
    vec3 dz33 = Pfz.z + jitter*oz33;

    vec3 d11 = dx11 * dx11 + dy11 * dy11 + dz11 * dz11;
    vec3 d12 = dx12 * dx12 + dy12 * dy12 + dz12 * dz12;
    vec3 d13 = dx13 * dx13 + dy13 * dy13 + dz13 * dz13;
    vec3 d21 = dx21 * dx21 + dy21 * dy21 + dz21 * dz21;
    vec3 d22 = dx22 * dx22 + dy22 * dy22 + dz22 * dz22;
    vec3 d23 = dx23 * dx23 + dy23 * dy23 + dz23 * dz23;
    vec3 d31 = dx31 * dx31 + dy31 * dy31 + dz31 * dz31;
    vec3 d32 = dx32 * dx32 + dy32 * dy32 + dz32 * dz32;
    vec3 d33 = dx33 * dx33 + dy33 * dy33 + dz33 * dz33;

    // Sort out the two smallest distances (F1, F2)
#if 0
    // Cheat and sort out only F1
    vec3 d1 = min(min(d11,d12), d13);
    vec3 d2 = min(min(d21,d22), d23);
    vec3 d3 = min(min(d31,d32), d33);
    vec3 d = min(min(d1,d2), d3);
    d.x = min(min(d.x,d.y),d.z);
    return vec2(sqrt(d.x)); // F1 duplicated, no F2 computed
#else
    // Do it right and sort out both F1 and F2
    vec3 d1a = min(d11, d12);
    d12 = max(d11, d12);
    d11 = min(d1a, d13); // Smallest now not in d12 or d13
    d13 = max(d1a, d13);
    d12 = min(d12, d13); // 2nd smallest now not in d13
    vec3 d2a = min(d21, d22);
    d22 = max(d21, d22);
    d21 = min(d2a, d23); // Smallest now not in d22 or d23
    d23 = max(d2a, d23);
    d22 = min(d22, d23); // 2nd smallest now not in d23
    vec3 d3a = min(d31, d32);
    d32 = max(d31, d32);
    d31 = min(d3a, d33); // Smallest now not in d32 or d33
    d33 = max(d3a, d33);
    d32 = min(d32, d33); // 2nd smallest now not in d33
    vec3 da = min(d11, d21);
    d21 = max(d11, d21);
    d11 = min(da, d31); // Smallest now in d11
    d31 = max(da, d31); // 2nd smallest now not in d31
    d11.xy = (d11.x < d11.y) ? d11.xy : d11.yx;
    d11.xz = (d11.x < d11.z) ? d11.xz : d11.zx; // d11.x now smallest
    d12 = min(d12, d21); // 2nd smallest now not in d21
    d12 = min(d12, d22); // nor in d22
    d12 = min(d12, d31); // nor in d31
    d12 = min(d12, d32); // nor in d32
    d11.yz = min(d11.yz,d12.xy); // nor in d12.yz
    d11.y = min(d11.y,d12.z); // Only two more to go
    d11.y = min(d11.y,d11.z); // Done! (Phew!)
    return sqrt(d11.xy); // F1, F2
#endif
}
#endif

//! Returns a 3D worley/cellular noise with derivatives in the range [0,1]
vec4 dWorleyNoise( vec3 p )
{
    //  establish our grid cell and unit position
    vec3 Pi = floor(p);
    vec3 Pf = p - Pi;

    // clamp the domain
    Pi.xyz = Pi.xyz - floor(Pi.xyz * ( 1.0 / 69.0 )) * 69.0;
    vec3 Pi_inc1 = step( Pi, vec3( 69.0 - 1.5 ) ) * ( Pi + 1.0 );

    // calculate the hash ( over -1.0->1.0 range )
    vec4 Pt = vec4( Pi.xy, Pi_inc1.xy ) + vec2( 50.0, 161.0 ).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    const vec3 SOMELARGEFLOATS = vec3( 635.298681, 682.357502, 668.926525 );
    const vec3 ZINC = vec3( 48.500388, 65.294118, 63.934599 );
    vec3 lowz_mod = vec3( 1.0 / ( SOMELARGEFLOATS + Pi.zzz * ZINC ) );
    vec3 highz_mod = vec3( 1.0 / ( SOMELARGEFLOATS + Pi_inc1.zzz * ZINC ) );
    vec4 hash_x0 = fract( Pt * lowz_mod.xxxx ) * 2.0 - 1.0;
    vec4 hash_x1 = fract( Pt * highz_mod.xxxx ) * 2.0 - 1.0;
    vec4 hash_y0 = fract( Pt * lowz_mod.yyyy ) * 2.0 - 1.0;
    vec4 hash_y1 = fract( Pt * highz_mod.yyyy ) * 2.0 - 1.0;
    vec4 hash_z0 = fract( Pt * lowz_mod.zzzz ) * 2.0 - 1.0;
    vec4 hash_z1 = fract( Pt * highz_mod.zzzz ) * 2.0 - 1.0;

    //  generate the 8 point positions
    const float JITTER_WINDOW = 0.166666666;  // 0.166666666 will guarentee no artifacts.
    hash_x0 = ( ( hash_x0 * hash_x0 * hash_x0 ) - sign( hash_x0 ) ) * JITTER_WINDOW + vec4( 0.0, 1.0, 0.0, 1.0 );
    hash_y0 = ( ( hash_y0 * hash_y0 * hash_y0 ) - sign( hash_y0 ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 1.0, 1.0 );
    hash_x1 = ( ( hash_x1 * hash_x1 * hash_x1 ) - sign( hash_x1 ) ) * JITTER_WINDOW + vec4( 0.0, 1.0, 0.0, 1.0 );
    hash_y1 = ( ( hash_y1 * hash_y1 * hash_y1 ) - sign( hash_y1 ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 1.0, 1.0 );
    hash_z0 = ( ( hash_z0 * hash_z0 * hash_z0 ) - sign( hash_z0 ) ) * JITTER_WINDOW + vec4( 0.0, 0.0, 0.0, 0.0 );
    hash_z1 = ( ( hash_z1 * hash_z1 * hash_z1 ) - sign( hash_z1 ) ) * JITTER_WINDOW + vec4( 1.0, 1.0, 1.0, 1.0 );

    //  return the closest squared distance + derivatives ( thanks to Jonathan Dupuy )
    vec4 dx1 = Pf.xxxx - hash_x0;
    vec4 dy1 = Pf.yyyy - hash_y0;
    vec4 dz1 = Pf.zzzz - hash_z0;
    vec4 dx2 = Pf.xxxx - hash_x1;
    vec4 dy2 = Pf.yyyy - hash_y1;
    vec4 dz2 = Pf.zzzz - hash_z1;
    vec4 d1 = dx1 * dx1 + dy1 * dy1 + dz1 * dz1;
    vec4 d2 = dx2 * dx2 + dy2 * dy2 + dz2 * dz2;
    vec4 r1 = d1.x < d1.y ? vec4( d1.x, dx1.x, dy1.x, dz1.x ) : vec4( d1.y, dx1.y, dy1.y, dz1.y );
    vec4 r2 = d1.z < d1.w ? vec4( d1.z, dx1.z, dy1.z, dz1.z ) : vec4( d1.w, dx1.w, dy1.w, dz1.w );
    vec4 r3 = d2.x < d2.y ? vec4( d2.x, dx2.x, dy2.x, dz2.x ) : vec4( d2.y, dx2.y, dy2.y, dz2.y );
    vec4 r4 = d2.z < d2.w ? vec4( d2.z, dx2.z, dy2.z, dz2.z ) : vec4( d2.w, dx2.w, dy2.w, dz2.w );
    vec4 t1 = r1.x < r2.x ? r1 : r2;
    vec4 t2 = r3.x < r4.x ? r3 : r4;
    return ( t1.x < t2.x ? t1 : t2 ) * vec4( 1.0, vec3( 2.0 ) ) * ( 9.0 / 12.0 ); // return a value scaled to 0.0->1.0
}


// Adapted from Ashima Arts Simplex noise
// https://github.com/ashima/webgl-noise/
// https://github.com/stegu/webgl-noise/

// Copyright (C) 2011 by Ashima Arts (Simplex noise)
// Copyright (C) 2011-2016 by Stefan Gustavson (Classic noise and others)

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.

// Hashed 2-D gradients with an extra rotation.
// (The constant 0.0243902439 is 1/41)
vec2 rgrad2(vec2 p, float rot) {
#if 0
// Map from a line to a diamond such that a shift maps to a rotation.
  float u = permute(permute(p.x) + p.y) * 0.0243902439 + rot; // Rotate by shift
  u = 4.0 * fract(u) - 2.0;
  // (This vector could be normalized, exactly or approximately.)
  return vec2(abs(u)-1.0, abs(abs(u+1.0)-2.0)-1.0);
#else
// For more isotropic gradients, sin/cos can be used instead.
  float u = permute(permute(p.x) + p.y) * 0.0243902439 + rot; // Rotate by shift
  u = fract(u) * 6.28318530718; // 2*pi
  return vec2(cos(u), sin(u));
#endif
}

//! Returns a 2D simplex noise with rotating gradients in the range [-1,-1]
float flowNoise( vec2 pos, float rot ) 
{
  // Offset y slightly to hide some rare artifacts
  pos.y += 0.001;
  // Skew to hexagonal grid
  vec2 uv = vec2(pos.x + pos.y*0.5, pos.y);
  
  vec2 i0 = floor(uv);
  vec2 f0 = fract(uv);
  // Traversal order
  vec2 i1 = (f0.x > f0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);

  // Unskewed grid points in (x,y) space
  vec2 p0 = vec2(i0.x - i0.y * 0.5, i0.y);
  vec2 p1 = vec2(p0.x + i1.x - i1.y * 0.5, p0.y + i1.y);
  vec2 p2 = vec2(p0.x + 0.5, p0.y + 1.0);

  // Integer grid point indices in (u,v) space
  i1 = i0 + i1;
  vec2 i2 = i0 + vec2(1.0, 1.0);

  // Vectors in unskewed (x,y) coordinates from
  // each of the simplex corners to the evaluation point
  vec2 d0 = pos - p0;
  vec2 d1 = pos - p1;
  vec2 d2 = pos - p2;

  // Wrap i0, i1 and i2 to the desired period before gradient hashing:
  // wrap points in (x,y), map to (u,v)
  vec3 x = vec3(p0.x, p1.x, p2.x);
  vec3 y = vec3(p0.y, p1.y, p2.y);
  vec3 iuw = x + 0.5 * y;
  vec3 ivw = y;
  
  // Avoid precision issues in permutation
  iuw = mod289(iuw);
  ivw = mod289(ivw);

  // Create gradients from indices
  vec2 g0 = rgrad2(vec2(iuw.x, ivw.x), rot);
  vec2 g1 = rgrad2(vec2(iuw.y, ivw.y), rot);
  vec2 g2 = rgrad2(vec2(iuw.z, ivw.z), rot);

  // Gradients dot vectors to corresponding corners
  // (The derivatives of this are simply the gradients)
  vec3 w = vec3(dot(g0, d0), dot(g1, d1), dot(g2, d2));
  
  // Radial weights from corners
  // 0.8 is the square of 2/sqrt(5), the distance from
  // a grid point to the nearest simplex boundary
  vec3 t = 0.8 - vec3(dot(d0, d0), dot(d1, d1), dot(d2, d2));

  // Set influence of each surflet to zero outside radius sqrt(0.8)
  t = max(t, 0.0);

  // Fourth power of t
  vec3 t2 = t * t;
  vec3 t4 = t2 * t2;
  
  // Final noise value is:
  // sum of ((radial weights) times (gradient dot vector from corner))
  float n = dot(t4, w);
  
  // Rescale to cover the range [-1,1] reasonably well
  return 11.0*n;
}

//! Returns a 2D simplex noise with rotating gradients and derivatives in the range [-1,-1]
vec3 dFlowNoise( vec2 pos, float rot ) 
{
  // Offset y slightly to hide some rare artifacts
  pos.y += 0.001;
  // Skew to hexagonal grid
  vec2 uv = vec2(pos.x + pos.y*0.5, pos.y);
  
  vec2 i0 = floor(uv);
  vec2 f0 = fract(uv);
  // Traversal order
  vec2 i1 = (f0.x > f0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);

  // Unskewed grid points in (x,y) space
  vec2 p0 = vec2(i0.x - i0.y * 0.5, i0.y);
  vec2 p1 = vec2(p0.x + i1.x - i1.y * 0.5, p0.y + i1.y);
  vec2 p2 = vec2(p0.x + 0.5, p0.y + 1.0);

  // Integer grid point indices in (u,v) space
  i1 = i0 + i1;
  vec2 i2 = i0 + vec2(1.0, 1.0);

  // Vectors in unskewed (x,y) coordinates from
  // each of the simplex corners to the evaluation point
  vec2 d0 = pos - p0;
  vec2 d1 = pos - p1;
  vec2 d2 = pos - p2;

  vec3 x = vec3(p0.x, p1.x, p2.x);
  vec3 y = vec3(p0.y, p1.y, p2.y);
  vec3 iuw = x + 0.5 * y;
  vec3 ivw = y;
  
  // Avoid precision issues in permutation
  iuw = mod289(iuw);
  ivw = mod289(ivw);

  // Create gradients from indices
  vec2 g0 = rgrad2(vec2(iuw.x, ivw.x), rot);
  vec2 g1 = rgrad2(vec2(iuw.y, ivw.y), rot);
  vec2 g2 = rgrad2(vec2(iuw.z, ivw.z), rot);

  // Gradients dot vectors to corresponding corners
  // (The derivatives of this are simply the gradients)
  vec3 w = vec3(dot(g0, d0), dot(g1, d1), dot(g2, d2));
  
  // Radial weights from corners
  // 0.8 is the square of 2/sqrt(5), the distance from
  // a grid point to the nearest simplex boundary
  vec3 t = 0.8 - vec3(dot(d0, d0), dot(d1, d1), dot(d2, d2));

  // Partial derivatives for analytical gradient computation
  vec3 dtdx = -2.0 * vec3(d0.x, d1.x, d2.x);
  vec3 dtdy = -2.0 * vec3(d0.y, d1.y, d2.y);

  // Set influence of each surflet to zero outside radius sqrt(0.8)
  if (t.x < 0.0) {
    dtdx.x = 0.0;
    dtdy.x = 0.0;
  t.x = 0.0;
  }
  if (t.y < 0.0) {
    dtdx.y = 0.0;
    dtdy.y = 0.0;
  t.y = 0.0;
  }
  if (t.z < 0.0) {
    dtdx.z = 0.0;
    dtdy.z = 0.0;
  t.z = 0.0;
  }

  // Fourth power of t (and third power for derivative)
  vec3 t2 = t * t;
  vec3 t4 = t2 * t2;
  vec3 t3 = t2 * t;
  
  // Final noise value is:
  // sum of ((radial weights) times (gradient dot vector from corner))
  float n = dot(t4, w);
  
  // Final analytical derivative (gradient of a sum of scalar products)
  vec2 dt0 = vec2(dtdx.x, dtdy.x) * 4.0 * t3.x;
  vec2 dn0 = t4.x * g0 + dt0 * w.x;
  vec2 dt1 = vec2(dtdx.y, dtdy.y) * 4.0 * t3.y;
  vec2 dn1 = t4.y * g1 + dt1 * w.y;
  vec2 dt2 = vec2(dtdx.z, dtdy.z) * 4.0 * t3.z;
  vec2 dn2 = t4.z * g2 + dt2 * w.z;

  return 11.0*vec3(n, dn0 + dn1 + dn2);
}

// Adapted from https://github.com/simongeilfus/SimplexNoise/

// Copyright (c) 2016, Simon Geilfus, All rights reserved.
// Code adapted from Stefan Gustavson Simplex Noise Public Domain implementation
// Curl noise adapted from Robert Bridson papers
// This code also includes variation of noise sums by Iñigo Quilez

// Redistribution and use in source and binary forms, with or without modification, are permitted provided that
// the following conditions are met:

// * Redistributions of source code must retain the above copyright notice, this list of conditions and
//  the following disclaimer.
// * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
//  the following disclaimer in the documentation and/or other materials provided with the distribution.

// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
// WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
// PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
// TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
// HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
// NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.


//! Returns a 2D Billowed Noise in the range [0,1]
float billowedNoise( vec2 p )
{
#ifndef NOISE_TEXTURE_BASED
    return abs( noise( p ) );
#else
    return abs( vnoise( p * 2.0f ) * 2.0f - 1.0f );
#endif
}

//! Returns a 3D Billowed Noise in the range [0,1]
float billowedNoise( vec3 p )
{
#ifndef NOISE_TEXTURE_BASED
    return abs( noise( p ) );
#else
    return abs( vnoise( p * 2.0f ) * 2.0f - 1.0f );
#endif
}

//! Returns a 2D Billowed Noise with Derivatives in the range [0,1]
vec3 dBillowedNoise( vec2 p )
{
  return abs( dnoise( p ) );
}

//! Returns a 3D Billowed Noise with Derivatives in the range [0,1]
vec4 dBillowedNoise( vec3 p )
{
  return abs( dnoise( p ) );
}

//! Returns a 2D Ridged Noise in the range [0,1]
float ridgedNoise( vec2 p )
{
#ifndef NOISE_TEXTURE_BASED
    return 1.0f - abs( noise( p ) );
#else
    return 1.0f - abs( vnoise( p * 2.0f ) * 2.0f - 1.0f );
#endif
}

//! Returns a 2D Ridged Noise in the range [0,1]
float ridgedNoise( vec2 p, float ridge )
{
#ifndef NOISE_TEXTURE_BASED
    return ridge - abs( noise( p ) );
#else
    return ridge - abs( vnoise( p * 2.0f ) * 2.0f - 1.0f );
#endif
}

//! Returns a 3D Ridged Noise in the range [0,1]
float ridgedNoise( vec3 p )
{
#ifndef NOISE_TEXTURE_BASED
    return 1.0f - abs( noise( p ) );
#else
    return 1.0f - abs( vnoise( p * 2.0f ) * 2.0f - 1.0f );
#endif
}

//! Returns a 3D Ridged Noise in the range [0,1]
float ridgedNoise( vec3 p, float ridge )
{
#ifndef NOISE_TEXTURE_BASED
    return ridge - abs( noise( p ) );
#else
    return ridge - abs( vnoise( p * 2.0f ) * 2.0f - 1.0f );
#endif
}

//! Returns a 2D Ridged Noise with Derivatives in the range [0,1]
vec3 dRidgedNoise( vec2 p )
{
  return vec3( 1.0f ) - abs( dnoise( p ) );
}

//! Returns a 2D Ridged Noise with Derivatives in the range [0,1]
vec3 dRidgedNoise( vec2 p, float ridge )
{
  return vec3( ridge ) - abs( dnoise( p ) );
}

//! Returns a 3D Ridged Noise with Derivatives in the range [0,1]
vec4 dRidgedNoise( vec3 p )
{
  return vec4( 1.0f ) - abs( dnoise( p ) );
}

//! Returns a 3D Ridged Noise with Derivatives in the range [0,1]
vec4 dRidgedNoise( vec3 p, float ridge )
{
  return vec4( ridge ) - abs( dnoise( p ) );
}

//! Returns a 2D Curl of a Simplex Noise in the range [-1,1]
vec2 curlNoise( vec2 v )
{
  vec3 derivative = dnoise( v );
  return vec2( derivative.z, -derivative.y );
}

//! Returns a 2D Curl of a Simplex Flow Noise in the range [-1,1]
vec2 curlNoise( vec2 v, float t )
{
  vec3 derivative = dFlowNoise( v, t );
  return vec2( derivative.z, -derivative.y );
}

//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec2 p )
{
  return fBm( p, 4, 2.0f, 0.5f );
}
//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec2 p, int octaves, float lacunarity, float gain )
{
  float sum   = 0.0f;
#ifndef NOISE_TEXTURE_BASED  
  float freq  = 1.0f;
#else  
  float freq  = 2.0f;
#endif
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
#ifndef NOISE_TEXTURE_BASED
    float n     = noise( p * freq );
#else
    float n     = vnoise( p * freq ) * 2.0f - 1.0f;
#endif
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}

//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec3 p )
{
  return fBm( p, 4, 2.0f, 0.5f );
}
//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise in the range [-1,1]
float fBm( vec3 p, int octaves, float lacunarity, float gain )
{
  float sum   = 0.0f;
#ifndef NOISE_TEXTURE_BASED  
  float freq  = 1.0f;
#else  
  float freq  = 2.0f;
#endif
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
#ifndef NOISE_TEXTURE_BASED
    float n     = noise( p * freq );
#else
    float n     = vnoise( p * freq ) * 2.0f - 1.0f;
#endif
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}

//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dfBm( vec2 p )
{
  return dfBm( p, 4, 2.0f, 0.5f );
}
//! Returns a 2D Fractal Brownian Motion sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dfBm( vec2 p, int octaves, float lacunarity, float gain )
{
  vec3 sum   = vec3( 0.0f );
  float freq  = 1.0f;
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
    vec3 n     = dnoise( p * freq );
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}

//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dfBm( vec3 p )
{
  return dfBm( p, 4, 2.0f, 0.5f );
}
//! Returns a 3D Fractal Brownian Motion sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dfBm( vec3 p, int octaves, float lacunarity, float gain )
{
  vec4 sum   = vec4( 0.0f );
  float freq  = 1.0f;
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
    vec4 n     = dnoise( p * freq );
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}


//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec2 p )
{
  return billowyTurbulence( p, 4, 2.0f, 0.5f );
}
//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec2 p, int octaves, float lacunarity, float gain )
{
  float sum   = 0.0f;
  float freq  = 1.0f;
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
    float n     = billowedNoise( p * freq );
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}

//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec3 p )
{
  return billowyTurbulence( p, 4, 2.0f, 0.5f );
}
//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise in the range [-1,1]
float billowyTurbulence( vec3 p, int octaves, float lacunarity, float gain )
{
  float sum   = 0.0f;
  float freq  = 1.0f;
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
    float n     = billowedNoise( p * freq );
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}

//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec3 dBillowyTurbulence( vec2 p )
{
  return dBillowyTurbulence( p, 4, 2.0f, 0.5f );
}
//! Returns a 2D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec3 dBillowyTurbulence( vec2 p, int octaves, float lacunarity, float gain )
{
  vec3 sum   = vec3( 0.0f );
  float freq  = 1.0f;
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
    vec3 n     = dBillowedNoise( p * freq );
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}

//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec4 dBillowyTurbulence( vec3 p )
{
  return dBillowyTurbulence( p, 4, 2.0f, 0.5f );
}
//! Returns a 3D Fractal Brownian Motion sum of Billowed Noise with Derivatives in the range [-1,1]
vec4 dBillowyTurbulence( vec3 p, int octaves, float lacunarity, float gain )
{
  vec4 sum   = vec4( 0.0f );
  float freq  = 1.0f;
  float amp   = 0.5f;
  
  for( int i = 0; i < octaves; i++ ){
    vec4 n     = dBillowedNoise( p * freq );
    sum        += n*amp;
    freq       *= lacunarity;
    amp        *= gain;
  }
  
  return sum;
}

//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec2 p )
{
  return ridgedMF( p, 1.0f, 4, 2.0f, 0.5f );
}
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec2 p, float ridgeOffset )
{
  return ridgedMF( p, ridgeOffset, 4, 2.0f, 0.5f );
}
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec2 p, float ridgeOffset, int octaves, float lacunarity, float gain )
{
  float sum = 0;
  float freq  = 1.0;
  float amp = 0.5;
  float prev  = 1.0;
  
  for( int i = 0; i < octaves; i++ ){
    float n = ridgedNoise( p * freq, ridgeOffset );
    n     *= n;
    sum   += n*amp*prev;
    prev  = n;
    freq  *= lacunarity;
    amp   *= gain;
  }
  return sum;
}

//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dRidgedMF( vec2 p )
{
  return dRidgedMF( p, 1.0f, 4, 2.0f, 0.5f );
}
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dRidgedMF( vec2 p, float ridgeOffset )
{
  return dRidgedMF( p, ridgeOffset, 4, 2.0f, 0.5f );
}
//! Returns a 2D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec3 dRidgedMF( vec2 p, float ridgeOffset, int octaves, float lacunarity, float gain )
{
  vec3 sum = vec3( 0.0f );
  float freq  = 1.0;
  float amp = 0.5;
  vec3 prev  = vec3( 1.0f );
  
  for( int i = 0; i < octaves; i++ ){
    vec3 n = ridgeOffset - abs( dnoise( p * freq ) );
    n     *= n;
    sum   += n*amp*prev;
    prev  = n;
    freq  *= lacunarity;
    amp   *= gain;
  }
  return sum;
}


//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec3 p )
{
  return ridgedMF( p, 1.0f, 4, 2.0f, 0.5f );
}
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec3 p, float ridgeOffset )
{
  return ridgedMF( p, ridgeOffset, 4, 2.0f, 0.5f );
}
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise in the range [-1,1]
float ridgedMF( vec3 p, float ridgeOffset, int octaves, float lacunarity, float gain )
{
  float sum = 0;
  float freq  = 1.0;
  float amp = 0.5;
  float prev  = 1.0;
  
  for( int i = 0; i < octaves; i++ ){
    float n = ridgedNoise( p * freq, ridgeOffset );
    n     *= n;
    sum   += n*amp*prev;
    prev  = n;
    freq  *= lacunarity;
    amp   *= gain;
  }
  return sum;
}
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dRidgedMF( vec3 p )
{
  return dRidgedMF( p, 1.0f, 4, 2.0f, 0.5f );
}
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dRidgedMF( vec3 p, float ridgeOffset )
{
  return dRidgedMF( p, ridgeOffset, 4, 2.0f, 0.5f );
}
//! Returns a 3D Ridged Multi-Fractal sum of Simplex Noise with Derivatives in the range [-1,1]
vec4 dRidgedMF( vec3 p, float ridgeOffset, int octaves, float lacunarity, float gain )
{
  vec4 sum = vec4( 0.0f );
  float freq  = 1.0;
  float amp = 0.5;
  vec4 prev  = vec4( 1.0f );
  
  for( int i = 0; i < octaves; i++ ){
    vec4 n = ridgeOffset - abs( dnoise( p * freq ) );
    n     *= n;
    sum   += n*amp*prev;
    prev  = n;
    freq  *= lacunarity;
    amp   *= gain;
  }
  return sum;
}


/*
// IQ cos noise
// https://www.shadertoy.com/view/MtsSRf
// Created by Beautypi/2015
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0

float cosNoise( in vec2 p )
{
    return 0.5*( sin(p.x) + sin(p.y) );
}
*/

/* 
// IQ Simplex 2D
// https://www.shadertoy.com/view/Msf3WH
// Created by inigo quilez - iq/2013
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.

// Simplex Noise (http://en.wikipedia.org/wiki/Simplex_noise), a type of gradient noise
// that uses N+1 vertices for random gradient interpolation instead of 2^N as in regular
// latice based Gradient Noise.

vec2 hash( vec2 p )
{
    p = vec2( dot(p,vec2(127.1,311.7)),
              dot(p,vec2(269.5,183.3)) );

    return -1.0 + 2.0*fract(sin(p)*43758.5453123);
}

float noise( in vec2 p )
{
    const float K1 = 0.366025404; // (sqrt(3)-1)/2;
    const float K2 = 0.211324865; // (3-sqrt(3))/6;

    vec2 i = floor( p + (p.x+p.y)*K1 );
    
    vec2 a = p - i + (i.x+i.y)*K2;
    vec2 o = (a.x>a.y) ? vec2(1.0,0.0) : vec2(0.0,1.0); //vec2 of = 0.5 + 0.5*vec2(sign(a.x-a.y), sign(a.y-a.x));
    vec2 b = a - o + K2;
    vec2 c = a - 1.0 + 2.0*K2;

    vec3 h = max( 0.5-vec3(dot(a,a), dot(b,b), dot(c,c) ), 0.0 );

    vec3 n = h*h*h*h*vec3( dot(a,hash(i+0.0)), dot(b,hash(i+o)), dot(c,hash(i+1.0)));

    return dot( n, vec3(70.0) );
    
}

/* IQ Value Noise 2D
// https://www.shadertoy.com/view/lsf3WH
// Created by inigo quilez - iq/2013
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.

// Value Noise (http://en.wikipedia.org/wiki/Value_noise), not to be confused with Perlin's
// Noise, is probably the simplest way to generate noise (a random smooth signal with 
// mostly all its energy in the low frequencies) suitable for procedural texturing/shading,
// modeling and animation.
//
// It produces lowe quality noise than Gradient Noise (https://www.shadertoy.com/view/XdXGW8)
// but it is slightly faster to compute. When used in a fractal construction, the blockyness
// of Value Noise gets qcuikly hidden, making it a very popular alternative to Gradient Noise.
//
// The princpiple is to create a virtual grid/latice all over the plane, and assign one
// random value to every vertex in the grid. When querying/requesting a noise value at
// an arbitrary point in the plane, the grid cell in which the query is performed is
// determined (line 30), the four vertices of the grid are determined and their random
// value fetched (lines 35 to 38) and then bilinearly interpolated (lines 35 to 38 again)
// with a smooth interpolant (line 31 and 33).


float hash( vec2 p )
{
    float h = dot(p,vec2(127.1,311.7));
    
    return -1.0 + 2.0*fract(sin(h)*43758.5453123);
}

float noise( in vec2 p )
{
    vec2 i = floor( p );
    vec2 f = fract( p );
    
    vec2 u = f*f*(3.0-2.0*f);

    return mix( mix( hash( i + vec2(0.0,0.0) ), 
                     hash( i + vec2(1.0,0.0) ), u.x),
                mix( hash( i + vec2(0.0,1.0) ), 
                     hash( i + vec2(1.0,1.0) ), u.x), u.y);
}

// ----------------------------------------------- */

/*
// IQ Value Noise 2D with derivatives
// https://www.shadertoy.com/view/MdX3Rr
// Created by inigo quilez - iq/2013
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.

#define SC (250.0)

// value noise, and its analytical derivatives
vec3 noised( in vec2 x )
{
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f*f*(3.0-2.0*f);
    float a = texture(iChannel0,(p+vec2(0.5,0.5))/256.0,-100.0).x;
    float b = texture(iChannel0,(p+vec2(1.5,0.5))/256.0,-100.0).x;
    float c = texture(iChannel0,(p+vec2(0.5,1.5))/256.0,-100.0).x;
    float d = texture(iChannel0,(p+vec2(1.5,1.5))/256.0,-100.0).x;
    return vec3(a+(b-a)*u.x+(c-a)*u.y+(a-b-c+d)*u.x*u.y,
                6.0*f*(1.0-f)*(vec2(b-a,c-a)+(a-b-c+d)*u.yx));
} 
*/

/*
// IQ Value Noise 3D
// https://www.shadertoy.com/view/4sfGzS#
// Created by inigo quilez - iq/2013
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.


// Fast 3D (value) noise by using two cubic-smooth bilinear interpolations in a LUT, 
// which is much faster than its hash based (purely procedural) counterpart.
//
// Note that instead of fetching from a grey scale texture twice at an offset of (37,17)
// pixels, the green channel of the texture is a copy of the red channel offset that amount
// (thx Dave Hoskins for the suggestion to try this)

//#define USE_PROCEDURAL

//===============================================================================================
//===============================================================================================
//===============================================================================================

#ifdef USE_PROCEDURAL
float hash( float n ) { return fract(sin(n)*753.5453123); }
float noise( in vec3 x )
{
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f*f*(3.0-2.0*f);
    
    float n = p.x + p.y*157.0 + 113.0*p.z;
    return mix(mix(mix( hash(n+  0.0), hash(n+  1.0),f.x),
                   mix( hash(n+157.0), hash(n+158.0),f.x),f.y),
               mix(mix( hash(n+113.0), hash(n+114.0),f.x),
                   mix( hash(n+270.0), hash(n+271.0),f.x),f.y),f.z);
}
#else
float noise( in vec3 x )
{
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f*f*(3.0-2.0*f);
    
    vec2 uv = (p.xy+vec2(37.0,17.0)*p.z) + f.xy;
    vec2 rg = texture( iChannel0, (uv+0.5)/256.0, -100.0 ).yx;
    return mix( rg.x, rg.y, f.z );
}
#endif

*/

/* 
// IQ Gradient Noise 2D
// https://www.shadertoy.com/view/XdXGW8
// Created by inigo quilez - iq/2013
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.

// Gradient Noise (http://en.wikipedia.org/wiki/Gradient_noise), not to be confused with
// Value Noise, and neither with Perlin's Noise (which is one form of Gradient Noise)
// is probably the most convenient way to generate noise (a random smooth signal with 
// mostly all its energy in the low frequencies) suitable for procedural texturing/shading,
// modeling and animation.
//
// It produces smoother and higher quality than Value Noise, but it's of course slighty more
// expensive.
//
// The princpiple is to create a virtual grid/latice all over the plane, and assign one
// random vector to every vertex in the grid. When querying/requesting a noise value at
// an arbitrary point in the plane, the grid cell in which the query is performed is
// determined (line 32), the four vertices of the grid are determined and their random
// vectors fetched (lines 37 to 40). Then, the position of the current point under 
// evaluation relative to each vertex is doted (projected) with that vertex' random
// vector, and the result is bilinearly interpolated (lines 37 to 40 again) with a 
// smooth interpolant (line 33 and 35).

vec2 hash( vec2 p )
{
    p = vec2( dot(p,vec2(127.1,311.7)),
              dot(p,vec2(269.5,183.3)) );

    return -1.0 + 2.0*fract(sin(p)*43758.5453123);
}

float noise( in vec2 p )
{
    vec2 i = floor( p );
    vec2 f = fract( p );
    
    vec2 u = f*f*(3.0-2.0*f);

    return mix( mix( dot( hash( i + vec2(0.0,0.0) ), f - vec2(0.0,0.0) ), 
                     dot( hash( i + vec2(1.0,0.0) ), f - vec2(1.0,0.0) ), u.x),
                mix( dot( hash( i + vec2(0.0,1.0) ), f - vec2(0.0,1.0) ), 
                     dot( hash( i + vec2(1.0,1.0) ), f - vec2(1.0,1.0) ), u.x), u.y);
}
*/
// END MadNoise.glsl

vec4 materialColorForPixel( vec2 texCoord )
{
float red = 1;
float green = 1;
float blue = 1;
float transmission = 1;
vec3 color;	
	
	color = vec3(1,1,1);
	
	
    #if defined(Gel_IS_R01_Light_Bastard_Amber)
    red = 1;
	green = .78;
	blue = .65;
	transmission = .44;
	
    #elif defined(Gel_IS_R02_Bastard_Amber)
	red = 1;
	green = 0.75;
	blue = .63;
	transmission = .28;

	#elif defined(Gel_IS_R03_Dark_Bastard_Amber)
	red = 1;
	green = 0.62;
	blue = .47;
	transmission = .38;

    #elif defined(Gel_IS_R04_Medium_Bastard_Amber)
	red = .99;
	green = 0.62;
	blue = .49;
	transmission = .44;
	
	#elif defined(Gel_IS_R05_Rose_Tint)
	red = 1;
	green = 0.75;
	blue = .82;
	transmission = .2;
	
	#elif defined(Gel_IS_R06_No_Color_Straw)
	red = .99;
	green = 1;
	blue = .84;
	transmission = .08;

	#elif defined(Gel_IS_R07_Pale_Yellow)
	red = 1;
	green = 1;
	blue = .69;
	transmission = .04;

	
	#elif defined(Gel_IS_R08_Pale_Gold)
	red = .99;
	green = 0.72;
	blue = .31;
	transmission = .14;

	
	#elif defined(Gel_IS_R09_Pale_Amber_Gold)
	red = .99;
	green = 0.72;
	blue = .31;
	transmission = .26;
	
	#elif defined(Gel_IS_R10_Medium_Yellow)
	red = 1;
	green = 1;
	blue = .13;
	transmission = .08;
	
	#elif defined(Gel_IS_R11_Light_Straw)
	red = .99;
	green = 0.8;
	blue = .14;
	transmission = .18;
	
	#elif defined(Gel_IS_R12_Straw)
	red = .94;
	green = 1;
	blue = 0;
	transmission = .12;
	
	
	#elif defined(Gel_IS_R13_Straw_Tint)
	red = 1;
	green = 0.78;
	blue = .45;
	transmission = .22;
	
	#elif defined(Gel_IS_R14_Medium_Straw)
	red = 1;
	green = 0.67;
	blue = .19;
	transmission = .32;
	
	#elif defined(Gel_IS_R15_Deep_Straw)
	red = .97;
	green = 0.58;
	blue = 0;
	transmission = .35;
	
	#elif defined(Gel_IS_R16_Light_Amber)
	red = 1;
	green = 0.38;
	blue = 0;
	transmission = .32;
	
	#elif defined(Gel_IS_R17_Light_Flame)
	red = 0.94;
	green = 0.25;
	blue = 0.13;
	transmission = 0.44;
	
	#elif defined(Gel_IS_R18_Flame)
	red = .94;
	green = 0.06;
	blue = 0;
	transmission = 0.44;
	
	
	#elif defined(Gel_IS_R19_Fire)
	red = 1;
	green = 0.2;
	blue = .2;
	transmission = .80;
	
	#elif defined(Gel_IS_R20_Medium_Amber)
	red = .99;
	green = 0.55;
	blue = .26;
	transmission = .46;
	
	#elif defined(Gel_IS_R21_Golden_Amber)
	red = .93;
	green = 0.38;
	blue = .01;
	transmission = .57;

	#elif defined(Gel_IS_R22_Deep_Amber)
	red = .99;
	green = 0.25;
	blue = .19;
	transmission = .74;

	#elif defined(Gel_IS_R23_Orange)
	red = .99;
	green = 0.42;
	blue = .26;
	transmission = .68;

	#elif defined(Gel_IS_R24_Scarlet)
	red = .75;
	green = 0;
	blue = 0;
	transmission = .78;

	#elif defined(Gel_IS_R25_Orange_Red)
	red = 1;
	green = 0;
	blue = 0;
	transmission = .86;

	#elif defined(Gel_IS_R26_Light_Red)
	red = .62;
	green = 0;
	blue = 0;
	transmission = .84;

	#elif defined(Gel_IS_R27_Medium_Red)
	red = .38;
	green = 0;
	blue = 0;
	transmission = .96;

	#elif defined(Gel_IS_R30_Light_Salmon_Pink)
	red = .1;
	green = 0.4;
	blue = .35;
	transmission = .56;

	#elif defined(Gel_IS_R31_Salmon_Pink)
	red = .1;
	green = 0.39;
	blue = .53;
	transmission = .54;

	#elif defined(Gel_IS_R32_Medium_Salmon_Pink)
	red = .99;
	green = 0;
	blue = .22;
	transmission = .72;
	
	#elif defined(Gel_IS_R33_No_Color_Pink)
	red = 1;
	green = 0.5;
	blue = .63;
	transmission = .35;

	#elif defined(Gel_IS_R34_Flesh_Pink)
	red = 1;
	green = 0.13;
	blue = .25;
	transmission = .55;

	#elif defined(Gel_IS_R35_Light_Pink)
	red = 1;
	green = 0.64;
	blue = .69;
	transmission = .34;

	#elif defined(Gel_IS_R36_Medium_Pink)
	red = .91;
	green = 0.36;
	blue = .54;
	transmission = .54;

	#elif defined(Gel_IS_R37_Pale_Rose_Pink)
	red = 1;
	green = 0.5;
	blue = .69;
	transmission = .44;
	
	
	#elif defined(Gel_IS_R38_Light_Rose)
	red = 1;
	green = 0.38;
	blue = .69;
	transmission = .51;

	#elif defined(Gel_IS_R40_Light_Salmon)
	red = 1;
	green = 0;
	blue = 0;
	transmission = .66;

	#elif defined(Gel_IS_R41_Salmon)
	red = .94;
	green = 0;
	blue = .6;
	transmission = .76;

	#elif defined(Gel_IS_R42_Deep_Salmon)
	red = .56;
	green = 0;
	blue = 0;
	transmission = .92;

	#elif defined(Gel_IS_R43_Deep_Pink)
	red = 1;
	green = 0;
	blue = .44;
	transmission = .72;

	#elif defined(Gel_IS_R44_Middle_Rose)
	red = .87;
	green = 0;
	blue = .44;
	transmission = .74;

	#elif defined(Gel_IS_R45_Rose)
	red = .56;
	green = 0;
	blue = .13;
	transmission = .92;

	#elif defined(Gel_IS_R46_Magenta)
	red = .38;
	green = 0;
	blue = 0;
	transmission = .84;

	#elif defined(Gel_IS_R47_Light_Rose_Purple)
	red = .25;
	green = 0;
	blue = .25;
	transmission = .84;

	#elif defined(Gel_IS_R48_Rose_Purple)
	red = .72;
	green = 0.01;
	blue = .72;
	transmission = .84;

	#elif defined(Gel_IS_R49_Medium_Purple)
	red = .44;
	green = 0;
	blue = .31;
	transmission = .96;

	#elif defined(Gel_IS_R50_Mauve)
	red = .44;
	green = 0;
	blue = 0;
	transmission = .86;

	#elif defined(Gel_IS_R51_Surprise_Pink)
	red = 1;
	green = 0.5;
	blue = 1;
	transmission = .46;

	#elif defined(Gel_IS_R52_Light_Lavender)
	red = .69;
	green = 0.6;
	blue = .94;
	transmission = .74;

	#elif defined(Gel_IS_R53_Pale_Lavender)
	red = .75;
	green = 0.75;
	blue = 1;
	transmission = .36;

	#elif defined(Gel_IS_R54_Special_Lavender)
	red = .75;
	green = 0.63;
	blue = 1;
	transmission = .5;

	#elif defined(Gel_IS_R55_Lilac)
	red = .43;
	green = 0.31;
	blue = 1;
	transmission = .37;

	#elif defined(Gel_IS_R56_Gypsy_Lavender)
	red = .25;
	green = 0;
	blue = .5;
	transmission = .96;

	#elif defined(Gel_IS_R57_Lavender)
	red = .25;
	green = 0;
	blue = .5;
	transmission = .76;

	#elif defined(Gel_IS_R58_Deep_Lavender)
	red = .25;
	green = 0;
	blue = .5;
	transmission = .90;

	#elif defined(Gel_IS_R59_Indigo)
	red = .19;
	green = 0;
	blue = .31;
	transmission = .98;

	#elif defined(Gel_IS_R60_No_Color_Blue)
	red = .5;
	green = 0.75;
	blue = 1;
	transmission = .38;

	#elif defined(Gel_IS_R61_Mist_Blue)
	red = .31;
	green = 0.75;
	blue = .82;
	transmission = .34;

	#elif defined(Gel_IS_R62_Booster_Blue)
	red = .31;
	green = 0.56;
	blue = .75;
	transmission = .66;

	#elif defined(Gel_IS_R63_Pale_Blue)
	red = .06;
	green = 0.56;
	blue = .75;
	transmission = .44;

	#elif defined(Gel_IS_R64_Light_Steel_Blue)
	red = 0;
	green = 0.31;
	blue = .94;
	transmission = .74;

	#elif defined(Gel_IS_R65_Daylight_Blue)
	red = 0;
	green = 0.25;
	blue = 1;
	transmission = .65;

	#elif defined(Gel_IS_R66_Cool_Blue)
	red = 0;
	green = 0.75;
	blue = .75;
	transmission = .33;

	#elif defined(Gel_IS_R67_Light_Sky_Blue)
	red = 0;
	green = 0.38;
	blue = .1;
	transmission = .74;

	#elif defined(Gel_IS_R68_Sky_Blue)
	red = 0;
	green = 0;
	blue = .82;
	transmission = .86;

	#elif defined(Gel_IS_R69_Brilliant_Blue)
	red = 0;
	green = 0.25;
	blue = .87;
	transmission = .82;

	#elif defined(Gel_IS_R70_Nile_Blue)
	red = .06;
	green = 0.63;
	blue = .69;
	transmission = .55;

	#elif defined(Gel_IS_R71_Sea_Blue)
	red = 0;
	green = 0.5;
	blue = .56;
	transmission = .7;

	#elif defined(Gel_IS_R72_Azure_Blue)
	red = 0;
	green = 0.63;
	blue = .81;
	transmission = .56;

	#elif defined(Gel_IS_R73_Peacock_Blue)
	red = .06;
	green = 0.56;
	blue = .56;
	transmission = .72;

	#elif defined(Gel_IS_R74_Night_Blue)
	red = 0;
	green =0;
	blue = .69;
	transmission = .96;

	#elif defined(Gel_IS_R76_Light_Green_Blue)
	red = 0;
	green = 0.5;
	blue = .56;
	transmission = .91;

	#elif defined(Gel_IS_R77_Green_Blue)
	red = 0;
	green = 0.5;
	blue = .87;
	transmission = .91;

	#elif defined(Gel_IS_R78_Trudy_Blue)
	red = .13;
	green = 0.6;
	blue = .69;
	transmission = .81;

	#elif defined(Gel_IS_R79_Bright_Blue)
	red = 0;
	green = 0;
	blue = .82;
	transmission = .92;

	#elif defined(Gel_IS_R80_Primary_Blue)
	red = 0;
	green = 0;
	blue = .5;
	transmission = .91;

	#elif defined(Gel_IS_R81_Urban_Blue)
	red = .14;
	green = 0;
	blue = .79;
	transmission = .90;

	#elif defined(Gel_IS_R82_Surprise_Blue)
	red = .6;
	green = 0;
	blue = .44;
	transmission = .94;

	#elif defined(Gel_IS_R83_Medium_Blue)
	red = 0;
	green = 0;
	blue = .38;
	transmission = .96;

	#elif defined(Gel_IS_R84_Zephyr_Blue)
	red = .12;
	green = 0;
	blue = .64;
	transmission = .86;

	#elif defined(Gel_IS_R85_Deep_Blue)
	red = 0;
	green = 0;
	blue = .38;
	transmission = .97;

	#elif defined(Gel_IS_R86_Pea_Green)
	red = 0;
	green = 0.56;
	blue = 0;
	transmission = .44;

	#elif defined(Gel_IS_R87_Pale_Yellow_Green)
	red = .75;
	green = 1;
	blue = .5;
	transmission = .15;

	#elif defined(Gel_IS_R89_Moss_Green)
	red = 0;
	green = .48;
	blue = 0;
	transmission = .55;

	#elif defined(Gel_IS_R90_Dark_Yellow_Green)
	red = .06;
	green = 0.37;
	blue = 0;
	transmission = .87;

	#elif defined(Gel_IS_R91_Primary_Green)
	red = 0;
	green = 0.25;
	blue = 0;
	transmission = 93;

	#elif defined(Gel_IS_R92_Turquoise)
	red = 0;
	green = 0.75;
	blue = .5;
	transmission = .41;

	#elif defined(Gel_IS_R93_Blue_Green)
	red = 0;
	green = 0.69;
	blue = .38;
	transmission = .65;

	#elif defined(Gel_IS_R94_Kelly_Green)
	red = .16;
	green = 0.53;
	blue = .41;
	transmission = .75;

	#elif defined(Gel_IS_R95_Medium_Blue_Green)
	red = 0;
	green = 0.38;
	blue = .31;
	transmission = .85;

	#elif defined(Gel_IS_R96_Lime)
	red = .75;
	green = 1;
	blue = 0;
	transmission = 2;

	#elif defined(Gel_IS_R97_Light_Grey)
	red = .75;
	green = 0.75;
	blue = .75;
	transmission = .5;

	#elif defined(Gel_IS_R98_Medium_Grey)
	red = .44;
	green = 0.44;
	blue = .44;
	transmission = .25;

	#elif defined(Gel_IS_R99_Chocolate)
	red = .56;
	green = 0.44;
	blue = .38;
	transmission = .65;

	#elif defined(Gel_IS_R304_Pale_Apricot)
	red = 1;
	green = 0.63;
	blue = .5;
	transmission = .21;

	#elif defined(Gel_IS_R305_Rose_Gold)
	red = 1;
	green = 0.5;
	blue = .38;
	transmission = .25;

	#elif defined(Gel_IS_R312_Canary)
	red = .99;
	green = 0.87;
	blue = .35;
	transmission = .15;

	#elif defined(Gel_IS_R317_Apricot)
	red = .94;
	green = 0.06;
	blue = 0;
	transmission = .49;

	#elif defined(Gel_IS_R321_Soft_Golden_Amber)
	red = .87;
	green = 0.13;
	blue = 0;
	transmission = .61;

	#elif defined(Gel_IS_R337_True_Pink)
	red = 1;
	green = 0.54;
	blue = .77;
	transmission = .45;

	#elif defined(Gel_IS_R339_Broadway_Pink)
	red = 1;
	green = 0;
	blue = .56;
	transmission = .45;

	#elif defined(Gel_IS_R342_Rose_Pink)
	red = .81;
	green = 0;
	blue = .31;
	transmission = .84;

	#elif defined(Gel_IS_R344_Follies_Pink)
	red = .88;
	green = 0;
	blue = .5;
	transmission = .79;

	#elif defined(Gel_IS_R355_Pale_Violet)
	red = .25;
	green = 0.13;
	blue = .63;
	transmission = .80;

	#elif defined(Gel_IS_R356_Middle_Lavender)
	red = .68;
	green = 0.21;
	blue = 1;
	transmission = .73;

	#elif defined(Gel_IS_R357_Royal_Lavender)
	red = .19;
	green = 0.0;
	blue = .44;
	transmission = .95;

	#elif defined(Gel_IS_R358_Rose_Indigo)
	red = .13;
	green = 0;
	blue = .31;
	transmission = .95;

	#elif defined(Gel_IS_R359_Medium_Violet)
	red = .06;
	green = 0;
	blue = .38;
	transmission = .95;

	#elif defined(Gel_IS_R378_Alice_Blue)
	red = .31;
	green = 0;
	blue = .82;
	transmission = .85;

	#elif defined(Gel_IS_R383_Sapphire_Blue)
	red = .1;
	green = 0;
	blue = .51;
	transmission = .96;

	#elif defined(Gel_IS_R385_Royal_Blue)
	red = 0;
	green = 0;
	blue = .31;
	transmission = .96;

	#elif defined(Gel_IS_R388_Gaslight_Green)
	red = .0;
	green = 0.88;
	blue = .0;
	transmission = .24;

	#elif defined(Gel_IS_R389_Chroma_Green)
	red = 0;
	green = 0.5;
	blue = 0;
	transmission = .6;

	#elif defined(Gel_IS_R397_Pale_Grey)
	red = .88;
	green = 0.88;
	blue = .88;
	transmission = .3;	

	#elif defined(Gel_IS_L02_Rose_Pink)
	red = 0.85;
	green = 0;
	blue = 0.57;
	transmission = .67;

	#elif defined(Gel_IS_L03_Lavender_Tint)
	red = 0.86;
	green = 0.69;
	blue = 0.1;
	transmission = .25;

	#elif defined(Gel_IS_L04_Medium_Bastard_Amber)
	red = 1;
	green = 0.49;
	blue = 0.25;
	transmission = .36;

	#elif defined(Gel_IS_L07_Pale_Yellow)
	red = 1;
	green = 1;
	blue = 0.62;
	transmission = .15;

	#elif defined(Gel_IS_L08_Dark_Salmon)
	red = 1;
	green = 0.15;
	blue = 0.11;
	transmission = .65;

	#elif defined(Gel_IS_L09_Pale_Amber_Gold)
	red = 1;
	green = 0.63;
	blue = 0.25;
	transmission = .29;

	#elif defined(Gel_IS_L10_Medium_Yellow)
	red = 1;
	green = 0.86;
	blue = 0;
	transmission = .13;

	#elif defined(Gel_IS_L13_Straw_Tint)
	red = 1;
	green = 0.71;
	blue = 0.38;
	transmission = .28;

	#elif defined(Gel_IS_L15_Deep_Straw)
	red = 0.99;
	green = 0.51;
	blue = 0;
	transmission = .39;

	#elif defined(Gel_IS_L19_Fire)
	red = 0.99;
	green = 0;
	blue = 0.03;
	transmission = .81;

	#elif defined(Gel_IS_L20_Medium_Amber)
	red = 0.1;
	green = 0.61;
	blue = 0.42;
	transmission = .49;

	#elif defined(Gel_IS_L21_Gold_Amber)
	red = 0.99;
	green = 0.36;
	blue = 0.06;
	transmission = .69;

	#elif defined(Gel_IS_L22_Dark_Amber)
	red = 0.87;
	green = 0.13;
	blue = 0.13;
	transmission = .76;

	#elif defined(Gel_IS_L24_Scarlet)
	red = 0.87;
	green = 0;
	blue = 0;
	transmission = .81;

	#elif defined(Gel_IS_L26_Bright_Red)
	red = 0.79;
	green = 0;
	blue = 0;
	transmission = .91;

	#elif defined(Gel_IS_L27_Medium_Red)
	red = 0.26;
	green = 0;
	blue = 0.03;
	transmission = .96;
	
	#elif defined(Gel_IS_L35_Light_Pink)
	red = 1;
	green = 0.36;
	blue = 0.51;
	transmission = .39;

	#elif defined(Gel_IS_L36_Mesium_Pink)
	red = 1;
	green = 0.38;
	blue = 0.52;
	transmission = .67;

	#elif defined(Gel_IS_L46_Dark_Magenta)
	red = 0.38;
	green = 0;
	blue = 0;
	transmission = .94;

	#elif defined(Gel_IS_L48_Rose_Purple)
	red = 0.38;
	green = 0;
	blue = 0.36;
	transmission = .85;

	#elif defined(Gel_IS_L52_Light_Lavender)
	red = 0.39;
	green = 0;
	blue = 0.68;
	transmission = .55;

	#elif defined(Gel_IS_L53_Paler_Lavender)
	red = 0.64;
	green = 0.75;
	blue = 1;
	transmission = .38;

	#elif defined(Gel_IS_L58_Lavender)
	red = 0.25;
	green = 0;
	blue = 0.5;
	transmission = .91;

	#elif defined(Gel_IS_L61_Mist_Blue)
	red = 0.35;
	green = 0.86;
	blue = 0.98;
	transmission = .38;

	#elif defined(Gel_IS_L63_Pale_Blue)
	red = 0;
	green = 0.63;
	blue = 0.87;
	transmission = .46;

	#elif defined(Gel_IS_L68_Sky_Blue)
	red = 0;
	green = 0;
	blue = 0.58;
	transmission = .87;

	#elif defined(Gel_IS_L79_Just_Blue)
	red = 0.04;
	green = 0.04;
	blue = 0.60;
	transmission = .94;

	#elif defined(Gel_IS_L85_Deeper_Blue)
	red = 0;
	green = 0;
	blue = 0.26;
	transmission = .97;

	#elif defined(Gel_IS_L89_Moss_Green)
	red = 0;
	green = 0.62;
	blue = 0;
	transmission = .70;

	#elif defined(Gel_IS_L90_Dark_Yellow_Green)
	red = 0.02;
	green = 0.24;
	blue = 0;
	transmission = .89;
	
	#elif defined(Gel_IS_L101_Yellow)
	red = 0.1;
	green = 0.75;
	blue = 0.0;
	transmission = .2;
	
	#elif defined(Gel_IS_L102_Light_Amber)
	red = 0.98;
	green = 0.82;
	blue = 0.07;
	transmission = .25;

	#elif defined(Gel_IS_L103_Straw)
	red = 0.1;
	green = 0.87;
	blue = 0.71;
	transmission = .18;

	#elif defined(Gel_IS_L104_Deep_Amber)
	red = 0.98;
	green = 0.64;
	blue = 0.13;
	transmission = .36;

	#elif defined(Gel_IS_L105_Orange)
	red = 0.99;
	green = 0.47;
	blue = 0.01;
	transmission = .59;

	#elif defined(Gel_IS_L106_Primary_Red)
	red = 0.5;
	green = 0;
	blue = 0;
	transmission = .91;

	#elif defined(Gel_IS_L107_Light_Rose)
	red = 1;
	green = 0.31;
	blue = 0.43;
	transmission = .52;

	#elif defined(Gel_IS_L109_Light_Salman)
	red = 0.95;
	green = 0.4;
	blue = 0.4;
	transmission = .45;

	#elif defined(Gel_IS_L110_Middle_Rose)
	red = 1;
	green = 0.41;
	blue = 0.66;
	transmission = .53;

	#elif defined(Gel_IS_L111_Dark_Pink)
	red = 0.93;
	green = 0.22;
	blue = 0.59;
	transmission = .68;
	
	#elif defined(Gel_IS_L113_Magenta)
	red = 0.69;
	green = 0;
	blue = 0;
	transmission = .89;

	#elif defined(Gel_IS_L115_Peacock_Blue)
	red = 0.08;
	green = 0.61;
	blue = 0.55;
	transmission = .65;

	#elif defined(Gel_IS_L116_Medium_Blue_Green)
	red = 0;
	green = 0.31;
	blue = 0.13;
	transmission = .81;

	#elif defined(Gel_IS_L117_Steel_Blue)
	red = 0;
	green = 0.87;
	blue = 1;
	transmission = .45;

	#elif defined(Gel_IS_L118_Light_Blue)
	red = 0.07;
	green = 0.46;
	blue = 1;
	transmission = .76;

	#elif defined(Gel_IS_L119_Dark_Blue)
	red = 0;
	green = 0.06;
	blue = 0.5;
	transmission = .97;

	#elif defined(Gel_IS_L120_Deep_Blue)
	red = 0.14;
	green = 0.11;
	blue = 0.46;
	transmission = .99;

	#elif defined(Gel_IS_L121_Lee_Green)
	red = 0;
	green = 0.75;
	blue = 0;
	transmission = .36;

	#elif defined(Gel_IS_L122_Fern_Green)
	red = 0;
	green = 0.91;
	blue = 0.0;
	transmission = .48;

	#elif defined(Gel_IS_L124_Dark_Green)
	red = 0.0;
	green = 0.64;
	blue = 0.0;
	transmission = .69;


	#elif defined(Gel_IS_L126_Mauve)
	red = 0.38;
	green = 0;
	blue = 0.44;
	transmission = .96;

	#elif defined(Gel_IS_L127_Smokey_Pink)
	red = 0.44;
	green = 0.19;
	blue = 0.25;
	transmission = .88;

	#elif defined(Gel_IS_L128_Bright_Pink)
	red = 0.8;
	green = 0.07;
	blue = 0.45;
	transmission = .86;

	#elif defined(Gel_IS_L130_Clear)
	red = 1;
	green = 1;
	blue = 1;
	transmission = .05;

	#elif defined(Gel_IS_L132_Medium_Blue)
	red = 0;
	green = 0;
	blue = 0.75;
	transmission = .91;

	#elif defined(Gel_IS_L134_Golden_Amber)
	red = 0.1;
	green = 0.45;
	blue = 0.27;
	transmission = .62;

	#elif defined(Gel_IS_L135_Deep_Golden_Amber)
	red = 0.62;
	green = 0.13;
	blue = 0.13;
	transmission = .81;

	#elif defined(Gel_IS_L136_Pale_Lavender)
	red = 0.69;
	green = 0.5;
	blue = 0.87;
	transmission = .57;

	#elif defined(Gel_IS_L137_Special_Lavender)
	red = 0.33;
	green = 0.16;
	blue = 0.81;
	transmission = .74;

	#elif defined(Gel_IS_L138_Pale_Green)
	red = 0.5;
	green = 1;
	blue = 0.13;
	transmission = .20;

	#elif defined(Gel_IS_L139_Primary_Green)
	red = 0;
	green = 0.31;
	blue = 0;
	transmission = .85;

	#elif defined(Gel_IS_L141_Bright_Blue)
	red = 0;
	green = 0.19;
	blue = 0.82;
	transmission = .82;

	#elif defined(Gel_IS_L142_Pale_Violet)
	red = 0.19;
	green = 0;
	blue = 0.82;
	transmission = .82;

	#elif defined(Gel_IS_L143_Pale_Navy_Blue)
	red = 0;
	green = 0.53;
	blue = 0.59;
	transmission = .84;

	#elif defined(Gel_IS_L144_No_Colour_Blue)
	red = 0;
	green = 0.44;
	blue = 0.87;
	transmission = .68;

	#elif defined(Gel_IS_L147_Apricot)
	red = 1;
	green = 0.46;
	blue = 0.28;
	transmission = .47;

	#elif defined(Gel_IS_L148_Bright_Rose)
	red = 0.87;
	green = 0.01;
	blue = 0.38;
	transmission = .86;

	#elif defined(Gel_IS_L151_Gold_Tint)
	red = 1;
	green = 0.73;
	blue = 0.66;
	transmission = .31;

	#elif defined(Gel_IS_L152_Pale_Gold)
	red = 1;
	green = 0.79;
	blue = 0.68;
	transmission = .29;

	#elif defined(Gel_IS_L153_Pale_Salmon)
	red = 1;
	green = 0.65;
	blue = 0.72;
	transmission = .35;
	

	#elif defined(Gel_IS_L154_Pale_Rose)
	red = 1;
	green = 0.8;
	blue = 0.75;
	transmission = .27;

	#elif defined(Gel_IS_L156_Chocolate)
	red = 0.47;
	green = 0.36;
	blue = 0.36;
	transmission = .74;

	#elif defined(Gel_IS_L157_Pink)
	red = 0.88;
	green = 0;
	blue = 0.31;
	transmission = .64;

	#elif defined(Gel_IS_L158_Deep_Orange)
	red = 0.99;
	green = 0.37;
	blue = 0.16;
	transmission = .70;

	#elif defined(Gel_IS_L159_No_Color_Straw)
	red = 0.1;
	green = 0.1;
	blue = 0.79;
	transmission = .11;

	#elif defined(Gel_IS_L161_Slate_Blue)
	red = 0.06;
	green = 0.19;
	blue = 0.56;
	transmission = .75;

	#elif defined(Gel_IS_L162_Bastard_Amber)
	red = 1;
	green = 0.63;
	blue = 0.5;
	transmission = .22;

	#elif defined(Gel_IS_L164_Flame_Red)
	red = 0.89;
	green = 0;
	blue = 0;
	transmission = .82;

	#elif defined(Gel_IS_L165_Daylight_Blue)
	red = 0;
	green = 0.25;
	blue = 1;
	transmission = .8;

	#elif defined(Gel_IS_L166_Pale_Red)
	red = 0.92;
	green = 0.01;
	blue = 0.40;
	transmission = .75;

	#elif defined(Gel_IS_L170_Deep_Lavender)
	red = 0.71;
	green = 0;
	blue = 0.86;
	transmission = .74;

	#elif defined(Gel_IS_L174_Dark_Steel_Blue)
	red = 0;
	green = 0.27;
	blue = 0.99;
	transmission = .70;

	#elif defined(Gel_IS_L176_Loving_Amber)
	red = 0.94;
	green = 0.44;
	blue = 0.38;
	transmission = .50;

	#elif defined(Gel_IS_L179_Chrome_Orange)
	red = 0.1;
	green = 0.49;
	blue = 0.18;
	transmission = .46;

	#elif defined(Gel_IS_L180_Dark_Lavender)
	red = 0.44;
	green = 0;
	blue = 0.87;
	transmission = .93;

	#elif defined(Gel_IS_L181_Congo_Blue)
	red = 0.05;
	green = 0.02;
	blue = 0.44;
	transmission = .99;

	#elif defined(Gel_IS_L182_Light_Red)
	red = 0.56;
	green = 0;
	blue = 0;
	transmission = .89;

	#elif defined(Gel_IS_L183_Moonlight_Blue)
	red = 0.13;
	green = 0.38;
	blue = 1;
	transmission = .81;

	#elif defined(Gel_IS_L184_Cosmetic_Peach)
	red = 1;
	green = 0.94;
	blue = 0.87;
	transmission = .43;

	#elif defined(Gel_IS_L185_Cosmetic_Burgundy)
	red = 0.75;
	green = 0.62;
	blue = 0.63;
	transmission = .48;

	#elif defined(Gel_IS_L186_Cosmetic_Silver_Rose)
	red = 1;
	green = 0.63;
	blue = 0.81;
	transmission = .49;

	#elif defined(Gel_IS_L187_Cosmetic_Rouge)
	red = 1;
	green = 0.61;
	blue = 0.53;
	transmission = .46;

	#elif defined(Gel_IS_L188_Cosmetic_Highlight)
	red = 1;
	green = .82;
	blue = 0.78;
	transmission = .44;

	#elif defined(Gel_IS_L189_Cosmetic_Silver_Moss)
	red = 0.84;
	green = 1;
	blue = 0.71;
	transmission = .39;

	#elif defined(Gel_IS_L190_Cosmetic_Emerald)
	red = 1;
	green = 0.96;
	blue = 0.84;
	transmission = .40;

	#elif defined(Gel_IS_L191_Cosmetic_Aqua_Blue)
	red = 0.38;
	green = 1;
	blue = 0.87;
	transmission = .47;

	#elif defined(Gel_IS_L192_Flesh_Pink)
	red = 0.87;
	green = 0.13;
	blue = 0.38;
	transmission = .65;

	#elif defined(Gel_IS_L193_Rosy_Gold)
	red = 1;
	green = 0.32;
	blue = 0.4;
	transmission = .64;

	#elif defined(Gel_IS_L194_Surprise_Pink)
	red = 0.38;
	green = 0.25;
	blue = 0.75;
	transmission = .78;

	#elif defined(Gel_IS_L195_Zenith_Blue)
	red = 0;
	green = 0.06;
	blue = 0.38;
	transmission = .97;

	#elif defined(Gel_IS_L196_True_Blue)
	red = 0;
	green = 0.25;
	blue = 1;
	transmission = .73;

	#elif defined(Gel_IS_L197_Alice_Blue)
	red = 0.13;
	green = 0.25;
	blue = 0.75;
	transmission = .90;

	#elif defined(Gel_IS_L328_Follies_Pink)
	red = 0.8;
	green = 0;
	blue = 0.17;
	transmission = .80;

	#elif defined(Gel_IS_L332_Special_Rose_Pink)
	red = 0.76;
	green = 0;
	blue = 0.29;
	transmission = .89;
	
	
	#elif defined(Gel_IS_L343_Special_Medium_Lavender)
	red = 0.13;
	green = 0;
	blue = 0.5;
	transmission = .94;


	#elif defined(Gel_IS_L344_Violet)
	red = 0.13;
	green = 0.13;
	blue = 0.75;
	transmission = .80;
	

	#elif defined(Gel_IS_L353_Lighter_Blue)
	red = 0.11;
	green = 0.53;
	blue = 0.86;
	transmission = .59;

	#elif defined(Gel_IS_L354_Special_Steel_Blue)
	red = 0;
	green = 0.87;
	blue = 0.87;
	transmission = .61;

	#elif defined(Gel_IS_L363_Special_Medium_Blue)
	red = 0;
	green = 0;
	blue = 0.38;
	transmission = .96;

	#elif defined(Gel_IS_G105_Antique_Rose)
	red = 0.74;
	green = 0.98;
	blue = 0.58;
	transmission = .42;

	#elif defined(Gel_IS_G110_Dark_Rose)
	red = 0.91;
	green = 0.13;
	blue = 0.64;
	transmission = .78;
	
	
	#elif defined(Gel_IS_G120_Bright_Pink)
	red = 0.93;
	green = 0.24;
	blue = 0.58;
	transmission = .79;
	
	#elif defined(Gel_IS_G130_Rose)
	red = 0.95;
	green = 0.35;
	blue = 0.60;
	transmission = .64;
	
	#elif defined(Gel_IS_G140_Dark_Magenta)
	red = 0.73;
	green = 0.05;
	blue = 0.64;
	trans = .90;
	
	#elif defined(Gel_IS_G150_Pink_Punch)
	red = 0.75;
	green = 0;
	blue = 0.38;
	transmission = .73;
	
	#elif defined(Gel_IS_G155_Light_Pink)
	red = 0.98;
	green = 0.67;
	blue = 0.82;
	transmission = .29;
	
	#elif defined(Gel_IS_G160_Chorus_Pink)
	red = 0.99;
	green = 0.64;
	blue = 0.82;
	transmission = .38;
	
	#elif defined(Gel_IS_G170_Flesh_Pink)
	red = 0.98;
	green = 0.40;
	blue = 0.71;
	transmission = .53;
	
	#elif defined(Gel_IS_G180_Cherry)
	red = 0.98;
	green = 0.11;
	blue = 0.37;
	transmission = .73;
	
	#elif defined(Gel_IS_G190_Cold_Pink)
	red = 0.99;
	green = 0.55;
	blue = 0.68;
	transmission = .49;
	
	#elif defined(Gel_IS_G195_Nyph_Pink)
	red = 0.99;
	green = 0.57;
	blue = 0.72;
	transmission = .47;
	
	#elif defined(Gel_IS_G220_Pink_Magenta)
	red = 0.81;
	green = 0.02;
	blue = 0.29;
	transmission = .82;
	
	#elif defined(Gel_IS_G235_Pink_Red)
	red = 0.98;
	green = 0.21;
	blue = 0.28;
	transmission = .82;
	
	#elif defined(Gel_IS_G245_Light_Red)
	red = 0.82;
	green = 0.02;
	blue = 0.08;
	transmission = .87;
	
	#elif defined(Gel_IS_G250_Medium_Red_XT)
	red = 0.45;
	green = 0;
	blue = 0.06;
	transmission = .92;
	
	#elif defined(Gel_IS_G260_Rosy_Amber)
	red = 0.99;
	green = 0.49;
	blue = 0.60;
	transmission = .50;
	
	#elif defined(Gel_IS_G270_Red_Orange)
	red = 0.44;
	green = 0;
	blue = 0;
	transmission = .83;
	
	#elif defined(Gel_IS_G280_Fire_Red)
	red = 1;
	green = 0.04;
	blue = 0.04;
	transmission = .74;
	
	#elif defined(Gel_IS_G290_Fire_Orange)
	red = 0.90;
	green = 0.07;
	blue = 0;
	transmission = .72;
	
	#elif defined(Gel_IS_G305_French_Rose)
	red = 1;
	green = 0.59;
	blue = 0.67;
	transmission = .30;
	
	#elif defined(Gel_IS_G315_Autumn_Glory)
	red = 0.99;
	green = 0.28;
	blue = 0.24;
	transmission = .63;
	
	#elif defined(Gel_IS_G320_Peach)
	red = 0.99;
	green = 0.33;
	blue = 0.15;
	transmission = .53;
	
	#elif defined(Gel_IS_G323_Indian_Summer)
	red = 1;
	green = 0.13;
	blue = 0.13;
	transmission = .54;
	
	#elif defined(Gel_IS_G325_Bastard_Amber)
	red = 1;
	green = 0.68;
	blue = 0.59;
	transmission = .28;
	
	#elif defined(Gel_IS_G330_Sepia)
	red = 0.71;
	green = 0.41;
	blue = 0.43;
	transmission = .63;
	
	#elif defined(Gel_IS_G335_Coral)
	red = 0.62;
	green = 0;
	blue = 0;
	transmission = .56;
	
	#elif defined(Gel_IS_G340_Light_Bastard_Amber)
	red = 0.1;
	green = 0.82;
	blue = 0.65;
	transmission = .22;
	
	#elif defined(Gel_IS_G343_Honey)
	red = 0.44;
	green = 0.06;
	blue = 0;
	transmission = .38;
	
	#elif defined(Gel_IS_G345_Deep_Amber)
	red = 1;
	green = 0;
	blue = 0;
	transmission = .59;
	
	#elif defined(Gel_IS_G350_Dark_Amber)
	red = 0.99;
	green = 0.40;
	blue = 0.15;
	transmission = .49;
	
	#elif defined(Gel_IS_G360_Amber_Blush)
	red = 0.94;
	green = 0.81;
	blue = 0.70;
	transmission = .27;
	
	#elif defined(Gel_IS_G363_Sand)
	red = 0.1;
	green = 0.87;
	blue = 0.69;
	transmission = .15;
	
	#elif defined(Gel_IS_G364_Pale_Honey)
	red = 0.87;
	green = 0.58;
	blue = 0.25;
	transmission = .18;
	
	#elif defined(Gel_IS_G365_Warm_Straw)
	red = 0.94;
	green = 0.81;
	blue = 0.70;
	transmission = .21;
	
	#elif defined(Gel_IS_G370_Spice)
	red = 0.44;
	green = 0.31;
	blue = 0.31;
	transmission = .79;
	
	#elif defined(Gel_IS_G375_Flame)
	red = 0.99;
	green = 0.48;
	blue = 0.21;
	transmission = .28;
	
	#elif defined(Gel_IS_G380_Golden_Tan)
	red = 0.49;
	green = 0.32;
	blue = 0.27;
	transmission = .64;
	
	#elif defined(Gel_IS_G385_Light_Amber)
	red = 0.99;
	green = 0.71;
	blue = 0.53;
	transmission = .23;
	
	#elif defined(Gel_IS_G390_Walnut)
	red = 0.21;
	green = 0.15;
	blue = 0.16;
	transmission = .89;
	
	#elif defined(Gel_IS_G420_Medium_Amber)
	red = 0.99;
	green = 0.79;
	blue = 0.38;
	transmission = .29;
	
	#elif defined(Gel_IS_G440_Very_Light_Straw)
	red = 1;
	green = 0.91;
	blue = 0.73;
	transmission = .17;
	
	#elif defined(Gel_IS_G450_Saffron)
	red = 0.90;
	green = 0.62;
	blue = 0.09;
	transmission = .17;
	
	#elif defined(Gel_IS_G460_Mellow_Yellow)
	red = 0.97;
	green = 0.99;
	blue = 0.32;
	transmission = .17;
	
	#elif defined(Gel_IS_G470_Pale_Gold)
	red = 0.94;
	green = 1;
	blue = 0.22;
	transmission = .13;
	
	#elif defined(Gel_IS_G480_Medium_Yellow)
	red = 0.96;
	green = 0.92;
	blue = 0.11;
	transmission = .12;
	
	#elif defined(Gel_IS_G510_No_Color_Straw)
	red = 0.99;
	green = 0.98;
	blue = 0.73;
	transmission = .10;
	
	#elif defined(Gel_IS_G520_New_Straw)
	red = 0.78;
	green = 1;
	blue = 0.65;
	transmission = .15;
	
	#elif defined(Gel_IS_G535_Lime)
	red = 0.38;
	green = 1;
	blue = 0.54;
	transmission = .14;
	
	#elif defined(Gel_IS_G540_Pale_Green)
	red = 0.57;
	green = 1;
	blue = 0.36;
	transmission = .25;
	
	#elif defined(Gel_IS_G570_Light_Green_Yellow)
	red = 0.1;
	green = 0.89;
	blue = 0.4;
	transmission = .54;
	
	#elif defined(Gel_IS_G650_Grass_Green)
	red = 0;
	green = 0.42;
	blue = 0;
	transmission = .94;
	
	#elif defined(Gel_IS_G655_Rich_Green)
	red = 0;
	green = 0.05;
	blue = 0;
	transmission = .88;
	
	#elif defined(Gel_IS_G660_Medium_Green)
	red = 0;
	green = 0.7;
	blue = 0.02;
	transmission = .64;
	
	#elif defined(Gel_IS_G680_Kelly_Green)
	red = 0.15;
	green = 0.71;
	blue = 0.44;
	transmission = .65;
	
	#elif defined(Gel_IS_G685_Pistachio)
	red = 0;
	green = 0.17;
	blue = 0.06;
	transmission = .70;
	
	#elif defined(Gel_IS_G690_Bluegrass)
	red = 0;
	green = 0.22;
	blue = 0.13;
	transmission = .83;
	
	#elif defined(Gel_IS_G710_Blue_Green)
	red = 0.23;
	green = 0.46;
	blue = 0.38;
	transmission = .86;
	
	#elif defined(Gel_IS_G720_Light_Steel_Blue)
	red = 0.47;
	green = 0.89;
	blue = 1;
	transmission = .44;
	
	#elif defined(Gel_IS_G725_Princess_Blue)
	red = 0;
	green = 0.35;
	blue = 0.44;
	transmission = .68;
	
	#elif defined(Gel_IS_G730_Azure_Blue)
	red = 0;
	green = 0.4;
	blue = 0.48;
	transmission = .73;
	
	#elif defined(Gel_IS_G740_Off_Blue)
	red = 0;
	green = 0.65;
	blue = 0.90;
	transmission = .83;
	
	#elif defined(Gel_IS_G750_Nile_Blue)
	red = 0;
	green = 0.51;
	blue = 0.66;
	transmission = .86;
	
	#elif defined(Gel_IS_G760_Aqua_Blue)
	red = 0.13;
	green = 0.44;
	blue = 0.47;
	transmission = .86;
	
	#elif defined(Gel_IS_G770_Christel_Blue)
	red = 0.18;
	green = 0.60;
	blue = 0.64;
	transmission = .81;
	
	#elif defined(Gel_IS_G780_Shark_Blue)
	red = 0.21;
	green = 0.69;
	blue = 0.75;
	transmission = .73;
	
	#elif defined(Gel_IS_G790_Electric_Blue)
	red = 0.41;
	green = 0.62;
	blue = 1;
	transmission = .60;
	
	#elif defined(Gel_IS_G810_Moon_Blue)
	red = 0;
	green = 0.24;
	blue = 0.69;
	transmission = .89;
	
	#elif defined(Gel_IS_G815_Moody_Blue)
	red = 0;
	green = 0.2;
	blue = 0.42;
	transmission = .8;
	
	#elif defined(Gel_IS_G820_Full_Light_Blue)
	red = 0.58;
	green = 0.73;
	blue = 1;
	transmission = .50;
	
	#elif defined(Gel_IS_G830_North_Sky_Blue)
	red = 0.86;
	green = 0.78;
	blue = 1;
	transmission = .49;
	
	#elif defined(Gel_IS_G835_Aztec_Blue)
	red = 0.0;
	green = 0.0;
	blue = 0.36;
	transmission = .94;
	
	#elif defined(Gel_IS_G840_Steel_Blue)
	red = 0.37;
	green = 0;
	blue = 0.98;
	transmission = .81;
	
	#elif defined(Gel_IS_G842_Whisper_Blue)
	red = 0;
	green = 0.54;
	blue = 1;
	transmission = .56;
	
	#elif defined(Gel_IS_G845_Cobalt)
	red = 0;
	green = 0;
	blue = 0.35;
	transmission = .96;
	
	#elif defined(Gel_IS_G847_City_Blue)
	red = 0;
	green = 0;
	blue = 0.38;
	transmission = .87;
	
	#elif defined(Gel_IS_G848_Bonus_Blue)
	red = 0;
	green = 0;
	blue = 0.42;
	transmission = .86;
	
	#elif defined(Gel_IS_G850_Blue_Primary)
	red = 0.25;
	green = 0;
	blue = 0.67;
	transmission = .95;
	
	#elif defined(Gel_IS_G860_Sky_Blue)
	red = 0.6;
	green = 0.35;
	blue = 1;
	transmission = .72;
	
	#elif defined(Gel_IS_G870_Winter_Blue)
	red = 0;
	green = 0.83;
	blue = 0.1;
	transmission = .24;
	
	#elif defined(Gel_IS_G880_Daylight_Blue)
	red = 0.35;
	green = 0;
	blue = 0.93;
	transmission = .78;
	
	#elif defined(Gel_IS_G882_Southern_Sky)
	red = 0;
	green = 0.11;
	blue = 0.28;
	transmission = .76;
	
	#elif defined(Gel_IS_G885_Blue_Ice)
	red = 0;
	green = 0.52;
	blue = 0.63;
	transmission = .40;
	
	#elif defined(Gel_IS_G888_Blue_Belle)
	red = 0.0;
	green = 0.09;
	blue = 0.22;
	transmission = .69;
	
	#elif defined(Gel_IS_G890_Dark_Sky_Blue)
	red = 0.01;
	green = 0.04;
	blue = 0.53;
	transmission = .97;
	
	#elif defined(Gel_IS_G905_Dark_Blue)
	red = 0;
	green = 0;
	blue = 0.42;
	transmission = .99;
	
	#elif defined(Gel_IS_G910_Alice_Blue)
	red = 0.06;
	green = 0;
	blue = 0.39;
	transmission = .89;
	
	#elif defined(Gel_IS_G915_Twilight)
	red = 0.05;
	green = 0.00;
	blue = 0.36;
	transmission = .96;
	
	#elif defined(Gel_IS_G920_Pale_Lavender)
	red = 0.95;
	green = 0.86;
	blue = 1;
	transmission = .37;
	
	#elif defined(Gel_IS_G925_Cosmic_Blue)
	red = 0;
	green = 0;
	blue = 0.05;
	transmission = .98;
	
	#elif defined(Gel_IS_G930_Real_Congo_Blue)
	red = 0.0;
	green = 0.0;
	blue = 1;
	transmission = .98;
	
	#elif defined(Gel_IS_G940_Light_Purple)
	red = 0.03;
	green = 0.10;
	blue = 0.75;
	transmission = .80;
	
	#elif defined(Gel_IS_G945_Royal_Purple)
	red = 0.27;
	green = 0.01;
	blue = 0.42;
	transmission = .98;
	
	#elif defined(Gel_IS_G948_African_Violet)
	red = 0.05;
	green = 0;
	blue = 0.13;
	transmission = .96;
	
	#elif defined(Gel_IS_G950_Purple)
	red = 0.25;
	green = 0.01;
	blue = 0.38;
	transmission = .93;
	
	#elif defined(Gel_IS_G960_Medium_Lavender)
	red = 0.54;
	green = 0.02;
	blue = 0.82;
	transmission = .78;
	
	#elif defined(Gel_IS_G970_Special_Lavender)
	red = 0.69;
	green = 0.13;
	blue = 0.98;
	transmission = .68; 	
	
	#elif defined(Gel_IS_G980_Surprise_Pink)
	red = 0.88;
	green = 0.67;
	blue = 0.99;
	transmission = .48;
	
	#elif defined(Gel_IS_G990_Dark_Lavender)
	red = 0.41;
	green = 0.2;
	blue = 0.62;
	transmission = .85;
	
	#elif defined(Gel_IS_G995_Orchid)
	red = 0.14;
	green = 0;
	blue = 0.11;
	transmission = .94;

	
	
	#endif

		
		
		
		
		
		
		
	#if defined(lightSource_IS_40W_Tungsten_2600k)
			color = vec3(1,0.7725,.5607);		
	#elif defined(lightSource_IS_100W_Tungsten_2850k)
			color = vec3(1,0.8392,0.6666);
	#elif defined(lightSource_IS_575W_HPL_3200k)
			color = vec3(1,0.945,0.8784);
	#elif defined(lightSource_IS_Carbon_Arc_5200k)
			color = vec3(1,0.98,0.9568);
	#elif defined(lightSource_IS_Direct_Sunlight_6000k)
			color = vec3(1,1,1);
	#elif defined(lightSource_IS_Mercury_Vapor)
			color = vec3(0.84705,0.968627,1);	
	#elif defined(lightSource_IS_Sodium_Vapor)
			color = vec3(1,0.8196,0.6980);
	#elif defined(lightSource_IS_Metal_Halide)
			color = vec3(0.949,0.988235,1);	
	#elif defined(lightSource_IS_High_Pressure_Sodium)
			color = vec3(1,0.71764,0.298039);
	#elif defined(lightSource_IS_Warm_Flourescent)
			color = vec3(1,0.956862,0.898039);
	#elif defined(lightSource_IS_Standard_Flourescent)
			color = vec3(0.956862,1,0.98039);	
	#elif defined(lightSource_IS_Cool_White_Flourescent)
			color = vec3(0.83137,0.921568,1);
	#elif defined(lightSource_IS_Full_Spectrum_Flourescent)
			color = vec3(1,0.95686,0.94901);
	#elif defined(lightSource_IS_Black_Light)
			color = vec3(0.654901,0,1);	
	#endif	

		
		
		
	color = mix(vec3(red,green,blue),color,0.5);
	
	
	
    #if defined(mode_IS_Solid)
    transmission = 1;
	#endif

	
	
	return vec4(color,transmission);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
