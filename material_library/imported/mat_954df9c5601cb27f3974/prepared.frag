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
uniform vec4 uMMParam001; // native input: u_bands
int u_bands = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: u_waves
float u_waves = uMMParam002.x;
uniform vec4 uMMParam003; // native input: u_scale
float u_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: u_scaleDiff
float u_scaleDiff = uMMParam004.x;
uniform vec4 uMMParam005; // native input: u_density
float u_density = uMMParam005.x;
uniform vec4 uMMParam006; // native input: u_densityDiff
float u_densityDiff = uMMParam006.x;
uniform vec4 uMMParam007; // native input: u_overlap
float u_overlap = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_shift
vec2 mat_shift = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_speed
float mat_speed = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam010.x > 0.5;
uniform vec4 uMMParam011; // native input: mat_reverse
bool mat_reverse = uMMParam011.x > 0.5;
uniform vec4 uMMParam012; // native input: mat_offset
float mat_offset = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_strob
float mat_strob = uMMParam013.x;
uniform vec4 uMMParam014; // native input: u_color1
vec4 u_color1 = uMMParam014;
uniform vec4 uMMParam015; // native input: u_color2
vec4 u_color2 = uMMParam015;
uniform vec4 uMMParam016; // native input: u_color3
vec4 u_color3 = uMMParam016;
uniform vec4 uMMParam017; // native input: u_color4
vec4 u_color4 = uMMParam017;
uniform vec4 uMMParam018; // native input: mat_alpha
float mat_alpha = uMMParam018.x;
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

float mat_time = mat_time_source - mat_offset * 10.;













vec4 mat_permute(vec4 x) {
  return mod((34.0 * x + 1.0) * x, 289.0);
}







vec2 mat_cellular2x2(vec2 P) {
#define K 0.142857142857 
#define K2 0.0714285714285 
#define jitter 0.8 
    vec2 Pi = mod(floor(P), 289.0);
    vec2 Pf = fract(P);
    vec4 Pfx = Pf.x + vec4(-0.5, -1.5, -0.5, -1.5);
    vec4 Pfy = Pf.y + vec4(-0.5, -0.5, -1.5, -1.5);
    vec4 p = mat_permute(Pi.x + vec4(0.0, 1.0, 0.0, 1.0));
    p = mat_permute(p + Pi.y + vec4(0.0, 0.0, 1.0, 1.0));
    vec4 ox = mod(p, 7.0)*K+K2;
    vec4 oy = mod(floor(p*K),7.0)*K+K2;
    vec4 dx = Pfx + jitter*ox;
    vec4 dy = Pfy + jitter*oy;
    vec4 d = dx * dx + dy * dy; 
    
#if 0
    
    d.xy = min(d.xy, d.zw);
    d.x = min(d.x, d.y);
    return d.xx; 
#else
    
    d.xy = (d.x < d.y) ? d.xy : d.yx; 
    d.xz = (d.x < d.z) ? d.xz : d.zx;
    d.xw = (d.x < d.w) ? d.xw : d.wx;
    d.y = min(d.y, d.z);
    d.y = min(d.y, d.w);
    return sqrt(d.xy);
#endif
}






#define QUARTERPI 0.785398163397448
#define HALFPI 1.57079632679489661923

#define TWOPI 6.28318530717958647692

float matGetBand(vec2 st, float src)
{
    
    float bandCount = float(u_bands);
    float bandSize = 1.0 / bandCount;
    float band = floor(src/bandSize);
    return band;
}
float matGetBandColor(float band)
{
   
    float bandCount = float(u_bands);
    float bandColor = band * (1.0/(bandCount-1.0));
    return bandColor;
}
vec2 matGetBandRange(float band, float overlap)
{
    
    float bandCount = float(u_bands);
    float bandSize = (1.0/bandCount);
    float c1 = band * bandSize;
    float c2 = (band+1.0) * bandSize;
    if (band > 0.0)           c1 -= (bandSize * overlap);
    if (band < bandCount-1.0) c2 += (bandSize * overlap);
    return vec2(c1,c2);
}
float matGetBandStep(vec2 range,float a)
{
    float bandStep = smoothstep( range.x, range.y, a ); 
    if (range.y < 0.99)
    {
        bandStep = bandStep * 2.0 - 1.0;    
        bandStep = 1.0 - abs(bandStep);     
    }
    return bandStep;
}








vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale * 2.;

    vec2 shift = mat_shift;
    shift += vec2(0.5);
    shift.x = 1. - shift.x;
    shift -= vec2(0.5);

    uv += shift;

    vec2 st = uv;
    vec3 source = vec3(uv.x);
    float src = source.x;

    vec3 tex = vec3(0.);


    float gray = (tex.x + tex.y + tex.z) / 3.0;
    float a = gray;


    a = dot(st,st)-mat_time*0.05;
    a = abs(sin(a*3.1415*u_waves));
    
    




    vec3 color = vec3(0);

    
    
    
    for (float band = 0.0 ; band < 4.0 ; band++)
    {
        
        
        
        vec2 bandRange = matGetBandRange( band, u_overlap );
        if ( a >= bandRange.x && a <= bandRange.y )
        {
            float bandStep = matGetBandStep( bandRange, a );
            
            float dens = abs(u_density) - (band * u_densityDiff);
            float scale = abs(u_scale) - (band * u_scaleDiff);
            vec2 st2 = st + vec2(-mat_time*0.038) * (band+1.0);
            vec2 F = mat_cellular2x2( st2 * scale );
            
            float n = 1.0 - step( bandStep, F.x*dens );

            if ( band == 0.0 )  color = max(color, n * u_color1.xyz );
            if ( band == 1.0 )  color = max(color, n * u_color2.xyz );
            if ( band == 2.0 )  color = max(color, n * u_color3.xyz );
            if ( band > 2.0 )   color = max(color, n * u_color4.xyz );
        }
    }

    
    
    
    
    
    

    
    
    
    
    
    
    
    
    
    

    float alpha = 1.;

    if (color == vec3(0.)) {
        alpha = mat_alpha;
    }

    out_color = vec4(color, alpha);







    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
