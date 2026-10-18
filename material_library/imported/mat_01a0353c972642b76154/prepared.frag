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

uniform vec4 uMMParam000; // native input: mat_zoom
float mat_zoom = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_focal_length
float mat_focal_length = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_bpmsync
bool mat_bpmsync = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_reverse
bool mat_reverse = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_speed
float mat_speed = uMMParam004.x;
uniform vec4 uMMParam005; // native input: bpm_offset
float bpm_offset = uMMParam005.x;
uniform vec4 uMMParam006; // native input: bpm_strob
float bpm_strob = uMMParam006.x;
float mat_animation_time = uTDTime * (mat_speed);














































































float adjusted_time(float m_time, float m_decay, float m_release)
{

    float adj_time;

    if (m_time < m_decay) {
        adj_time = 1;
    } else {
        
        adj_time = (m_time - m_decay) * 1 / (1 - m_decay);
        if (m_time < m_release) {
            adj_time = 1 - adj_time * 1 / m_release;
        } else {
            adj_time = 0;
        }
    }

    return adj_time;
}

vec3 iResolution = vec3(RENDERSIZE, 1.);

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

void pR(inout vec2 p, float a) {
    p = cos(a)*p + sin(a)*vec2(p.y, -p.x);
}

vec2 pMod2(inout vec2 p, vec2 size) {
    vec2 c = floor((p + size*0.5)/size);
    p = mod(p + size*0.5,size) - size*0.5;
    return c;
}

float smax(float a, float b, float r) {
    vec2 u = max(vec2(r + a,r + b), vec2(0));
    return min(-r, max (a, b)) + length(u);
}

float fTorus(vec3 p, float smallRadius, float largeRadius) {
    return length(vec2(length(p.xz) - largeRadius, p.y)) - smallRadius;
}







vec3 pal( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d ) {
    return a + b*cos( 6.28318*(c*t+d) );
}

vec3 spectrum(float n) {
    return pal( n, vec3(0.5,0.5,0.5),vec3(0.5,0.5,0.5),vec3(1.0,1.0,1.0),vec3(0.0,0.33,0.67) );
}









vec4 inverseStereographic(vec3 p) {
    float r = length(p);
    vec4 p4 = vec4(2.*p,1.-r*r)*1./(1.+r*r);
    return p4;
}

float fTorus(vec4 p4, out vec2 uv) {

    
    float d = length(p4.xy) / length(p4.zw) - 1.;

    if (d > 0.) {
        
        
        
        d = 1. - length(p4.zw) / length(p4.xy);
    }

    
    
    
    d /= PI;

    
    uv = (vec2(
        atan(p4.y, p4.x),
        atan(p4.z, p4.w)
    ) / PI) * .5 + .5;

    return d;
}





















float fixDistance(vec3 p, float d, float threshold) {
    d *= PI;

    float od = d;
    float sn = sign(d);

    d = abs(d);
    d = d * dot(p, p) / 4.2;
    if (d > 1.) {
        d = pow(d, .5);
        d = (d - 1.) * 1.8 + 1.;
    }
    d *= sn;

    if (abs(d) < threshold) {
        d = od / PI;
    }

    return d;
}


vec2 modelUv;
bool hitDebugTorus = false;

float map(vec3 p, float time) {

    #ifdef DEBUG
        if (p.x < 0.) {
            hitDebugTorus = true;
            return abs(fTorus(p.xzy, 1.002, 1.4163));
        }
    #endif

    vec4 p4 = inverseStereographic(p);

    
    
    
    pR(p4.zy, time * -PI / 2.);

    
    pR(p4.xw, time * -PI / 2.);

    vec2 uv;
    float d = fTorus(p4, uv);
    modelUv = uv;

    #ifdef DEBUG
        d = abs(d);
        d = fixDistance(p, d, 1.);
        return d;
    #endif

    
    
    vec3 pp = p;
    float uvScale = 2.25; 
    p = vec3(uv * uvScale, d);

    

    float n = 10.;
    float repeat = uvScale / n;

    p.xy += repeat / 2.;
    pMod2(p.xy, vec2(repeat));

    d = length(p.xy) - repeat * .4;
    d = smax(d, abs(p.z) - .013, .01);

    d = fixDistance(pp, d, .01);

    return d;
}

bool hitDebugPlane = false;

float mapDebug(vec3 p, float time) {
    float d = map(p, time);
    #ifndef DEBUG
        return d;
    #endif
    float plane = min(abs(p.z), abs(p.y));
    hitDebugPlane = plane < abs(d);
    return d;
    
}






vec3 calcNormal(vec3 p, float time) {
  vec3 eps = vec3(.0001,0,0);
  vec3 n = vec3(
    map(p + eps.xyy, time) - map(p - eps.xyy, time),
    map(p + eps.yxy, time) - map(p - eps.yxy, time),
    map(p + eps.yyx, time) - map(p - eps.yyx, time)
  );
  return normalize(n);
}

mat3 calcLookAtMatrix(vec3 ro, vec3 ta, vec3 up) {
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww,up));
    vec3 vv = normalize(cross(uu,ww));
    return mat3(uu, vv, ww);
}

const float ITER = 400.;
const float MAX_DIST = 12.;


vec4 materialColorForPixel( vec2 texCoord ) {




	float adj_time = mat_animation_time;
	



	

	



	

    



    


    vec3 camPos = vec3(1.8, 5.5, -5.5);
    vec3 camTar = vec3(.1,0,.1);
    vec3 camUp = vec3(-1,0,-1.5);
    mat3 camMat = calcLookAtMatrix(camPos, camTar, camUp);

    float focalLength = 2.4 * mat_focal_length;
    

	vec2 p =  vec2(texCoord.x - 0.5, texCoord.y - 0.5);

	p *= mat_zoom;

    

    



    vec3 rayDirection = normalize(camMat * vec3(p, focalLength));
    vec3 rayOrigin = camPos;
    vec3 rayPosition = rayOrigin;
    float rayLength = 0.;

    float distance = 0.;
    vec3 color = vec3(0);

    for (float i = 0.; i < ITER; i++) {
        rayLength += distance;
        rayPosition = rayOrigin + rayDirection * rayLength;
        distance = mapDebug(rayPosition, adj_time);

        if (distance < .001) {
            vec3 normal = calcNormal(rayPosition, adj_time);
            color = vec3(dot(normalize(vec3(1,.5,0)), normal) * .5 + .5);

            #ifdef DEBUG
                if (hitDebugPlane) {
                    
                    float d = map(rayPosition, adj_time);
                    color = vec3(mod(abs(d) * 10., 1.));
                    color *= spectrum(abs(d));
                    color = mix(color, vec3(1), step(0., -d) * .25);
                } else if ( ! hitDebugTorus) {
                    
                    float repeat = 1. / 20.;
                    pMod2(modelUv, vec2(repeat));
                    color -= color * vec3(0,1,0) * smoothstep(0., .001, abs(modelUv.x) - repeat * .4);
                    color -= color * vec3(1,0,0) * smoothstep(0., .001, abs(modelUv.y) - repeat * .4);
                }
            #endif

            break;
        }

        if (rayLength > MAX_DIST) {
            break;
        }
    }

    #ifndef DEBUG
        float fog = pow(smoothstep(7.25, MAX_DIST, rayLength), .25);
        color = mix(color, vec3(0), fog);
        color = spectrum((color.r * 2. - 1.) * .2 + .4);
        color *= mix(1., .025, fog);
    #endif

    color = pow(color, vec3(1. / 2.2)); 
    return vec4(color, 1);



}






void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
