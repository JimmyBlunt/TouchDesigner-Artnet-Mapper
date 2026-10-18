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

uniform vec4 uMMParam000; // native input: mat_speed
float mat_speed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_scale
float mat_scale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_mix
float mat_mix = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_height
float mat_height = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_zoom
float mat_zoom = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_bump
float mat_bump = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_bump_power
float mat_bump_power = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_offset
vec2 mat_offset = uMMParam007.xy;
uniform vec4 uMMParam008; // native input: mat_light
vec2 mat_light = uMMParam008.xy;
uniform vec4 uMMParam009; // native input: mat_light_z
float mat_light_z = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_specular
float mat_specular = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_fresnel
float mat_fresnel = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_attenuation
float mat_attenuation = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_diff_color
vec4 mat_diff_color = uMMParam013;
uniform vec4 uMMParam014; // native input: mat_spec_color
vec4 mat_spec_color = uMMParam014;
uniform vec4 uMMParam015; // native input: mat_fre_color
vec4 mat_fre_color = uMMParam015;
uniform vec4 uMMParam016; // native input: mat_brightness
float mat_brightness = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_contrast
float mat_contrast = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_tint
vec4 mat_tint = uMMParam018;
uniform vec4 uMMParam019; // native input: mat_invert
bool mat_invert = uMMParam019.x > 0.5;
float mat_time = uTDTime * (mat_speed);
#define mat_tex_1 sTD2DInputs[0]
#define mat_tex_2 sTD2DInputs[1]

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

const float PRECISION  = 0.001;
const float MAX_DISTANCE = 20.;


float zoom(vec3 p, sampler2D stex)
{
	float o = 0.;
	float s;

    const float L = 5.; 
	for (float i = 0.; i<L; i++){
	
        
		s = fract((i - mat_time*2.)/L);
        
        
        float expS = exp2(s*L)/8.;
        o += texture(stex, p.xy*expS + i*.9).x * (.5 - abs(s-.5))*8./L;
	}

	return o;
}


float map(vec3 p){

	float bump = sin(length(p.xy*4.)+mat_bump*PI*2.);
	float tex = mix(
					mix(texture(mat_tex_1, p.xy).x, pow(zoom(p, mat_tex_1),1.4),mat_zoom),
			  		mix(texture(mat_tex_2, p.xy).x, pow(zoom(p, mat_tex_2),1.4),mat_zoom),
				mat_mix);

	return 1. - p.z - tex*mat_height*0.1 - bump*0.1*mat_bump_power;
 
}


float intersect( in vec3 ro, in vec3 rd )
{
	float h= PRECISION * 2.0;
    float t = 0.0;
	float maxd = MAX_DISTANCE;
    float sid = -1.0;
    for( int i=0; i<10; i++ )
    {
        if( abs(h)<PRECISION||t>maxd ) break;
        t += h;
	    h = map( ro+rd*t );
    }
    return t;
}

vec3 calcNormal( in vec3 pos )
{
    vec3  eps = vec3(PRECISION,0.0,0.0);
    vec3 nor;
    nor.x = map(pos+eps.xyy) - map(pos-eps.xyy);
    nor.y = map(pos+eps.yxy) - map(pos-eps.yxy);
    nor.z = map(pos+eps.yyx) - map(pos-eps.yyx);
    return normalize(nor);
}

float calcAO( in vec3 pos, in vec3 nor )
{
	float occ = 0.0;
    float sca = 1.0;
    for( int i=0; i<5; i++ )
    {
        float hr = 0.01 + 0.12*float(i)/4.0;
        vec3 aopos =  nor * hr + pos;
        float dd = map( aopos );
        occ += -(dd-hr)*sca;
        sca *= 0.95;
    }
    return clamp( 1.0 - 3.0*occ, 0.0, 1.0 );    
}

float sss(vec3 p, vec3 l , float d){
	return smoothstep(0.,1.,map(p+l*d)/d);
} 


float curve(in vec3 p){
    const float eps = 0.0225, amp = 7.5, ampInit = 0.525;

    vec2 e = vec2(-1., 1.)*eps;
    
    float t1 = map(p + e.yxx), t2 = map(p + e.xxy);
    float t3 = map(p + e.xyx), t4 = map(p + e.yyy);
    
    return clamp((t1 + t2 + t3 + t4 - 4.*map(p))*amp + ampInit, 0., 1.);
}

vec4 materialColorForPixel( vec2 texCoord )
{
	vec2 uv = texCoord - 0.5;
	uv *= mat_scale;
	uv += vec2(-mat_offset.x, mat_offset.y);
	
	vec3 color;

	vec3 rd = normalize(vec3(uv, 1.));
    
    
    vec3 ro = vec3(0.);  
    
	
    float surf = intersect(ro,rd);

  	
    vec3 pos = ro + surf * rd;
    vec3 nor = calcNormal(pos);

    
    vec3 lp = ro + vec3(mat_light.x, -mat_light.y, mat_light_z);
    vec3 ld = (lp - pos);
    
    float lDist = max(length(ld), 0.001); 							
    float atten = mix(1.,1./(1. + lDist * 0.25), mat_attenuation); 	

    ld /= lDist; 
    
    float diff = max(dot(ld, nor), 0.); 
    float spec = pow(max( dot( reflect(-ld, nor), -rd ), 0.0 ), 32.) * mat_specular; 
    float fre = clamp(dot(nor, rd) + 1., .0, 1.) * mat_fresnel; 

    color = (mat_diff_color.xyz * (diff + .5) + mat_spec_color.xyz * spec * 2.) + mat_fre_color.xyz * pow(fre, 3.)*5.;
    
	
	float ao = calcAO(pos, nor);

    float crv = curve(pos); 
    crv = smoothstep(0., 1., crv) * .5 + crv * .25 + .25; 
    
	color *= (atten * crv * ao);

	
    color = mix(vec3(0.5), color, mat_contrast);

    
    color += vec3(mat_brightness);

	
	color *= mat_tint.rgb;

	
	color = mix(color, vec3(1.0) - color, float(mat_invert));
		
	return vec4(color,1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
