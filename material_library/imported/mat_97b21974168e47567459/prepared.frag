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

uniform vec4 uMMParam000; // native input: anim1_level
float anim1_level = uMMParam000.x;
uniform vec4 uMMParam001; // native input: anim1_repeat
int anim1_repeat = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: anim1_speed
float anim1_speed = uMMParam002.x;
uniform vec4 uMMParam003; // native input: anim1_reverse
bool anim1_reverse = uMMParam003.x > 0.5;
const int anim1_shape = 0;
#define anim1_shape_IS_Serpentine
uniform vec4 uMMParam005; // native input: anim1_smoothness
float anim1_smoothness = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_anim1_restart
int mat_anim1_restart = int(round(uMMParam006.x));
uniform vec4 uMMParam007; // native input: anim2_level
float anim2_level = uMMParam007.x;
uniform vec4 uMMParam008; // native input: anim2_repeat
int anim2_repeat = int(round(uMMParam008.x));
uniform vec4 uMMParam009; // native input: anim2_speed
float anim2_speed = uMMParam009.x;
uniform vec4 uMMParam010; // native input: anim2_reverse
bool anim2_reverse = uMMParam010.x > 0.5;
const int anim2_shape = 0;
#define anim2_shape_IS_Serpentine
uniform vec4 uMMParam012; // native input: anim2_smoothness
float anim2_smoothness = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_anim2_restart
int mat_anim2_restart = int(round(uMMParam013.x));
uniform vec4 uMMParam014; // native input: repeat_y
int repeat_y = int(round(uMMParam014.x));
uniform vec4 uMMParam015; // native input: offset
float offset = uMMParam015.x;
uniform vec4 uMMParam016; // native input: random_offset
bool random_offset = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: bpmsync
bool bpmsync = uMMParam017.x > 0.5;
float anim1_time = uTDTime * (anim1_speed);
float anim2_time = uTDTime * (anim2_speed);

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

float mat_hash( vec2 p ) {
    return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);
}

vec4 materialColorForPixel(vec2 texCoord)
{
	int cellId = int(texCoord.y * repeat_y);

    float normalizedCellId; 
    if (random_offset)
        normalizedCellId = mat_hash(vec2(0,cellId) * 0.5);
    else
        normalizedCellId = float(cellId) / repeat_y; 

	float out_value = 1;

	if (anim1_level > 0) {
		float pixelPos = fract(texCoord.x*anim1_repeat);
		float anim_pos = fract(anim1_time - offset * normalizedCellId); 
		float smoothness = anim1_smoothness;

		#if defined(anim1_shape_IS_Serpentine)
			float diff = abs(pixelPos-anim_pos);
			float value = smoothstep(0.25*(1-smoothness),0.25*(1+smoothness),min(diff,1-diff));
		#elif defined(anim1_shape_IS_Fill)
			float diff = (1-anim_pos)*(1+smoothness)-pixelPos;
			float value = smoothstep(0,smoothness+0.000001,diff);
		#elif defined(anim1_shape_IS_Fill_Sin)
			float diff = pixelPos-(1+sin(anim_pos*2*PI))*(1+smoothness)/2;
			float value = smoothstep(0,smoothness+0.000001,-diff);
		#elif defined(anim1_shape_IS_Chase)
			float diff = abs(pixelPos-0.5-sin(anim_pos*2*PI)/4);
			float value = 1-smoothstep(0.25*(1-smoothness),0.25*(1+smoothness),diff);
		#elif defined(anim1_shape_IS_Centered)
			float diff = abs(pixelPos-0.5)-anim_pos*(1+smoothness)/2;
			float value = smoothstep(0,smoothness+0.000001,-diff);
		#elif defined(anim1_shape_IS_Centered_Sin)
			float diff = abs(pixelPos-0.5) - (1+sin((anim_pos - offset * normalizedCellId)*2*PI))*(1+smoothness)/4;
			float value = smoothstep(0,smoothness+0.000001,-diff);
		#elif defined(anim1_shape_IS_Flow)
			int lineID = int(texCoord.x*anim1_repeat);
        	float startStroke = (1+cos(anim_pos*2*PI+1234.341*mat_hash(vec2(0,lineID) * 0.5)))/2;
        	float endStroke = (1+cos(anim_pos*2*PI+1234.341*mat_hash(vec2(0,lineID+1) * 0.5)))/2;
			float value = mix(startStroke,endStroke,pixelPos);
		#else 
			int lineID = int(texCoord.x*anim1_repeat);
			float value = cos(anim1_time*2*PI - offset * normalizedCellId+10*lineID);
			float cutValue = value<0?1:0;
			value = mix(cutValue,value,smoothness);
		#endif

		out_value = mix(out_value, out_value * value, anim1_level);
	}

	if (anim2_level > 0) {
		float pixelPos = fract(texCoord.x*anim2_repeat);
		float anim_pos = fract(anim2_time - offset * normalizedCellId); 
		float smoothness = anim2_smoothness;

		#if defined(anim2_shape_IS_Serpentine)
			float diff = abs(pixelPos-anim_pos);
			float value = smoothstep(0.25*(1-smoothness),0.25*(1+smoothness),min(diff,1-diff));
		#elif defined(anim2_shape_IS_Fill)
			float diff = (1-anim_pos)*(1+smoothness)-pixelPos;
			float value = smoothstep(0,smoothness+0.000001,diff);
		#elif defined(anim2_shape_IS_Fill_Sin)
			float diff = pixelPos-(1+sin(anim_pos*2*PI))*(1+smoothness)/2;
			float value = smoothstep(0,smoothness+0.000001,-diff);
		#elif defined(anim2_shape_IS_Chase)
			float diff = abs(pixelPos-0.5-sin(anim_pos*2*PI)/4);
			float value = 1-smoothstep(0.25*(1-smoothness),0.25*(1+smoothness),diff);
		#elif defined(anim2_shape_IS_Centered)
			float diff = abs(pixelPos-0.5)-anim_pos*(1+smoothness)/2;
			float value = smoothstep(0,smoothness+0.000001,-diff);
		#elif defined(anim2_shape_IS_Centered_Sin)
			float diff = abs(pixelPos-0.5) - (1+sin((anim_pos - offset * normalizedCellId)*2*PI))*(1+smoothness)/4;
			float value = smoothstep(0,smoothness+0.000001,-diff);
		#elif defined(anim2_shape_IS_Flow)
			int lineID = int(texCoord.x*anim2_repeat);
        	float startStroke = (1+cos(anim_pos*2*PI+1234.341*mat_hash(vec2(0,lineID) * 0.5)))/2;
        	float endStroke = (1+cos(anim_pos*2*PI+1234.341*mat_hash(vec2(0,lineID+1) * 0.5)))/2;
			float value = mix(startStroke,endStroke,pixelPos);
		#else 
			int lineID = int(texCoord.x*anim2_repeat);
			float value = cos(anim2_time*2*PI - offset * normalizedCellId+10*lineID);
			float cutValue = value<0?1:0;
			value = mix(cutValue,value,smoothness);
		#endif

		out_value = mix(out_value, out_value * value, anim2_level);
	}

	return vec4(vec3(out_value),1);
}



void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
