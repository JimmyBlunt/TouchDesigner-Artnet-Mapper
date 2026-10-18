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
uniform vec4 uMMParam001; // native input: mat_color
vec4 mat_color = uMMParam001;
uniform vec4 uMMParam002; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_reverse
bool mat_reverse = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_speed
float mat_speed = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_offset
float mat_offset = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_strob
float mat_strob = uMMParam006.x;
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

#define clamp01(x) clamp(x, 0.0, 1.0)
#define mad(x, a, b) ((x) * (a) + (b))
#define rsqrt(x) inversesqrt(x)

vec3 GammaEncode(vec3 x) {return pow(x, vec3(1.0 / 2.2));}


float SDFtoMask(float sdf)
{
   return sdf / length(vec2(dFdx(sdf), dFdy(sdf))) * 1.2;
}

float Hash(float v)
{
    return fract(sin(v) * 43758.5453);
}

float Hash(vec2 v)
{
    return Hash(v.y + v.x * 12.9898);
}

float Hash(vec3 v)
{
    return Hash(v.y + v.x * 12.9898 + v.z * 33.7311);
}


float Pow2(float v){return v * v;}
float Pow3(float v){return v * v * v;}
float Pow4(float v){return Pow2(Pow2(v));}
float Pow8(float v){return Pow2(Pow4(v));}
float Pow16(float v){return Pow4(Pow4(v));}
float Pow32(float v){return Pow16(Pow2(v));}

float SqrLen(vec2 v){return dot(v, v);}
float SqrLen(vec3 v){return dot(v, v);}
float SqrLen(vec4 v){return dot(v, v);}










#define HASHSCALE1 .1031
#define HASHSCALE3 vec3(.1031, .1030, .0973)
#define HASHSCALE4 vec4(1031, .1030, .0973, .1099)

float Hash11I(float p ){vec3 p3 = fract(vec3(p     ) * HASHSCALE1); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.x    + p3.y   ) * p3.z   );}
float Hash12I(vec2  p ){vec3 p3 = fract(vec3(p.xyx ) * HASHSCALE1); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.x    + p3.y   ) * p3.z   );}
float Hash13I(vec3  p3){     p3 = fract(    (p3    ) * HASHSCALE1); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.x    + p3.y   ) * p3.z   );}
vec2  Hash21I(float p ){vec3 p3 = fract(vec3(p     ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xx   + p3.yz  ) * p3.zy  );}
vec2  Hash22I(vec2  p ){vec3 p3 = fract(vec3(p.xyx ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xx   + p3.yz  ) * p3.zy  );}
vec2  Hash23I(vec3  p3){     p3 = fract(    (p3    ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xx   + p3.yz  ) * p3.zy  );}
vec3  Hash31I(float p ){vec3 p3 = fract(vec3(p     ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xxy  + p3.yzz ) * p3.zyx );}
vec3  Hash32I(vec2  p ){vec3 p3 = fract(vec3(p.xyx ) * HASHSCALE3); p3 += dot(p3, p3.yxz  + 19.19); return fract((p3.xxy  + p3.yzz ) * p3.zyx );}
vec3  Hash33I(vec3  p3){     p3 = fract(    (p3    ) * HASHSCALE3); p3 += dot(p3, p3.yxz  + 19.19); return fract((p3.xxy  + p3.yxx ) * p3.zyx );}
vec4  Hash41I(float p ){vec4 p4 = fract(vec4(p     ) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}
vec4  Hash42I(vec2  p ){vec4 p4 = fract(vec4(p.xyxy) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}
vec4  Hash43I(vec3  p ){vec4 p4 = fract(vec4(p.xyzx) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}
vec4  Hash44I(vec4  p4){     p4 = fract(    (p4    ) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}

#undef HASHSCALE1
#undef HASHSCALE3
#undef HASHSCALE4




#define HASHSCALE1 443.8975
#define HASHSCALE3 vec3(443.897, 441.423, 437.195)
#define HASHSCALE4 vec4(443.897, 441.423, 437.195, 444.129)

float Hash11F(float p ){vec3 p3 = fract(vec3(p     ) * HASHSCALE1); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.x    + p3.y   ) * p3.z   );}
float Hash12F(vec2  p ){vec3 p3 = fract(vec3(p.xyx ) * HASHSCALE1); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.x    + p3.y   ) * p3.z   );}
float Hash13F(vec3  p3){     p3 = fract(    (p3    ) * HASHSCALE1); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.x    + p3.y   ) * p3.z   );}
vec2  Hash21F(float p ){vec3 p3 = fract(vec3(p     ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xx   + p3.yz  ) * p3.zy  );}
vec2  Hash22F(vec2  p ){vec3 p3 = fract(vec3(p.xyx ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xx   + p3.yz  ) * p3.zy  );}
vec2  Hash23F(vec3  p3){     p3 = fract(    (p3    ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xx   + p3.yz  ) * p3.zy  );}
vec3  Hash31F(float p ){vec3 p3 = fract(vec3(p     ) * HASHSCALE3); p3 += dot(p3, p3.yzx  + 19.19); return fract((p3.xxy  + p3.yzz ) * p3.zyx );}
vec3  Hash32F(vec2  p ){vec3 p3 = fract(vec3(p.xyx ) * HASHSCALE3); p3 += dot(p3, p3.yxz  + 19.19); return fract((p3.xxy  + p3.yzz ) * p3.zyx );}
vec3  Hash33F(vec3  p3){     p3 = fract(    (p3    ) * HASHSCALE3); p3 += dot(p3, p3.yxz  + 19.19); return fract((p3.xxy  + p3.yxx ) * p3.zyx );}
vec4  Hash41F(float p ){vec4 p4 = fract(vec4(p     ) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}
vec4  Hash42F(vec2  p ){vec4 p4 = fract(vec4(p.xyxy) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}
vec4  Hash43F(vec3  p ){vec4 p4 = fract(vec4(p.xyzx) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}
vec4  Hash44F(vec4  p4){     p4 = fract(    (p4    ) * HASHSCALE4); p4 += dot(p4, p4.wzxy + 19.19); return fract((p4.xxyz + p4.yzzw) * p4.zywx);}

#undef HASHSCALE1
#undef HASHSCALE3
#undef HASHSCALE4














float EvalIntensityCurve(vec2 id, float time)
{
    time += Hash(id.yx * 1.733);
    

    float mat_time = floor(time);
    float fTime = fract(time);

    float h = Hash(vec3(id, mat_time));
    

    
    
    h *= h;
    h *= h;

    float falloff = 1.0 - Pow2(fTime * 2.0 - 1.0);

    


    {
        float f = 100.0;
        float d = 1.0 / (exp2(f) - 1.0);

        falloff = mad(exp2(falloff * f), d, -d);
    }
    

    
    

    return h * falloff*1.0;
}

float GlowKern1(float x, float s)
{
    float rx = sqrt(x);

    return (exp(-s * rx) * s) / (2.0 * rx);
}

float GlowKern2(float x, float s)
{
    float rx = sqrt(x);

    return s / (2.0 * Pow2(1.0 + s * rx) * rx);
}

float GlowKern3(float x, float s)
{
    return s / Pow3(1.0 + s * x);
}

float GlowKern4(float x, float c)
{
    return c * rsqrt(x * Pow3(x + c)) * 0.5;
}

float CurveU(float x, float u)
{
    return (u - u * x) / (u + x);
}

float EvalGlow3(vec2 uv, vec2 off, float time)
{
    vec2 iUV = floor(uv) + off;
    vec2 fUV = fract(uv) - off;

    vec2 fUV2 = fUV * 2.0 - 1.0;

    float dist2 = SqrLen(fUV2);

    float l = length(fUV2);
    l = max(0.0, l - 0.7);
    float glow = 0.0;
    
    
    glow = GlowKern3(l, 1.2);
  
    

    glow = clamp01(glow);

    glow *= clamp01(1.0 - Pow2(l*0.25));

    return EvalIntensityCurve(iUV.xy, time) * glow;
}


float PlotDot(vec2 sp, vec2 dp, float dr)
{
    float v = length(sp - dp);

    float d = v - dr;
    
    d /= length(vec2(dFdx(v), dFdy(v)));
    
    d = clamp01(1.0 - d * 1.2);

    return d;
}

float EvalGlyph(vec2 uv, vec2 off, float time)
{
    vec2 iUV = floor(uv) + off;
    vec2 fUV = fract(uv) - off;

    vec2 fUV2 = fUV * 2.0 - 1.0;

    float distToCenter = length(fUV2);

    float gMask = distToCenter - 0.75;
          gMask = SDFtoMask(gMask);
          gMask = clamp01(1.0 - gMask);

    gMask = PlotDot(fUV2, vec2(0.0), 0.75);

    return EvalIntensityCurve(iUV.xy, time) * gMask;
}


vec3 EvalTile(vec2 uv, vec2 off, float time)
{
    vec2 iUV = floor(uv) + off;
    vec2 fUV = fract(uv) - off;

    

    vec3 blue1 = mat_color.rgb;

    float nTime = time*50.0;
    float time2 = floor(nTime);
    float fTime = fract(nTime);

    float n0 = Hash(vec3(uv, time2));
    float n1 = Hash(vec3(uv, time2 + 1.0));

    

    float glyph = EvalGlyph(uv, off, time);

    float glow = 0.0;

    for(float i = -2.0; i <= 2.0; ++i)
    for(float j = -2.0; j <= 2.0; ++j)
    {
        glow += EvalGlow3(uv, off + vec2(i, j), time);
    }


    return vec3(mix(glow, glyph, 0.94)).xxx * blue1 * 32.0;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);
    uv *= mat_scale * 50.;

    float time = mat_time * 0.1;



    vec3 outCol = vec3(1.0, 1.0, 1.0);

    outCol = vec3(0.0);

    outCol = EvalTile(uv, vec2(0.0), time);

    

    
    
    out_color = vec4(GammaEncode(clamp01(outCol.xyz)), 1.0);


    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
