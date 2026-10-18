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
uniform vec4 uMMParam001; // native input: mat_iterations
int mat_iterations = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: mat_scale
float mat_scale = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_offset
vec2 mat_offset = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: mat_brightness
float mat_brightness = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_contrast
float mat_contrast = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_tint
vec4 mat_tint = uMMParam006;
uniform vec4 uMMParam007; // native input: mat_invert
bool mat_invert = uMMParam007.x > 0.5;
float mat_animation_time = uTDTime * (mat_speed);

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

#define SHADED 0
#define FOG 0
#define NOISE 3 
#define VARIANT 2

const vec3 skyColor = 0.*vec3(.7,.8,1.); const float skyTrsp = .5;
const vec3 sunColor = vec3(1.,.7,.1)*10.;   
const vec3 lightDir = vec3(.94,.24,.24); 
const vec3 ambient  = vec3(.2,0.,0.), 
           diffuse  = vec3(.8);






const mat3 m = mat3( 0.00,  0.80,  0.60,
           		    -0.80,  0.36, -0.48,
             		-0.60, -0.48,  0.64 );

float mat_hash( float n ) {
    return fract(sin(n)*43758.5453);
}

float mat_noise( in vec3 x ) { 
    vec3 p = floor(x);
    vec3 f = fract(x);

    f = f*f*(3.-2.*f);

    float n = p.x + p.y*57. + 113.*p.z;

    float res = mix(mix(mix( mat_hash(n+  0.), mat_hash(n+  1.),f.x),
                        mix( mat_hash(n+ 57.), mat_hash(n+ 58.),f.x),f.y),
                    mix(mix( mat_hash(n+113.), mat_hash(n+114.),f.x),
                        mix( mat_hash(n+170.), mat_hash(n+171.),f.x),f.y),f.z);
    return res;
}

float mat_fbm( vec3 p ) { 
    float f;
    f  = 0.5000*mat_noise( p ); p = m*p*2.02;
    f += 0.2500*mat_noise( p ); p = m*p*2.03;
    f += 0.1250*mat_noise( p ); p = m*p*2.01;
    f += 0.0625*mat_noise( p );
    return f;
}



vec3 mat_hash13( float n ) {
    return fract(sin(n+vec3(0.,12.345,124))*43758.5453);
}
float mat_hash31( vec3 n ) {
    return mat_hash(n.x+10.*n.y+100.*n.z);
}
vec3 mat_hash33( vec3 n ) {
    return mat_hash13(n.x+10.*n.y+100.*n.z);
}

vec4 mat_worley( vec3 p ) {
    vec4 d = vec4(1e15);
    vec3 ip = floor(p);
    for (float i=-1.; i<2.; i++)
   	 	for (float j=-1.; j<2.; j++)
            for (float k=-1.; k<2.; k++) {
                vec3 p0 = ip+vec3(i,j,k),
                      c = mat_hash33(p0)+p0-p;
                float d0 = dot(c,c);
                if      (d0<d.x) { d.yzw=d.xyz; d.x=d0; }
                else if (d0<d.y) { d.zw =d.yz ; d.y=d0; }
                else if (d0<d.z) { d.w  =d.z  ; d.z=d0; }
                else if (d0<d.w) {              d.w=d0; }   
            }
    return sqrt(d);
}


float mat_i_grad=.2/2., mat_i_scale = 5., mat_i_thresh=.5; 


float mat_tweaknoise( vec3 p , bool step) {
    float d1 = smoothstep(mat_i_grad/2.,-mat_i_grad/2.,length(p)-.5),
          d2 = smoothstep(mat_i_grad/1.,-mat_i_grad/1.,abs(p.z)-.5),
          d=d1;
#if NOISE==1 
    float v = mat_fbm(mat_i_scale*p);
#elif NOISE==2 
    float v = (.9-mat_i_scale*mat_worley(mat_i_scale*p).x);
#elif NOISE>=3 
  #if VARIANT==0
    d = (1.-d1)*d2; 
  #elif VARIANT==2
    d=d2;
  #endif
    if (d<0.5) return 0.;
    mat_i_grad=.8, mat_i_scale = 10., mat_i_thresh=.5+.5*(cos(.5*mat_animation_time)+.36*cos(.5*3.*mat_animation_time))/1.36;
    vec4 w=mat_i_scale*mat_worley(mat_i_scale*p-vec3(0.,0.,3.*mat_animation_time)); 
    float v=1.-1./(1./(w.z-w.x)+1./(w.a-w.x)); 
#endif
    
    return (true)? smoothstep(mat_i_thresh-mat_i_grad/2.,mat_i_thresh+mat_i_grad/2.,v*d) : v*d;
}



float shadedNormal( vec3 p, float v ) {
    float epsL = 0.01;
#if 1
    float dx = (mat_tweaknoise(p+epsL*lightDir,false)-mat_tweaknoise(p-epsL*lightDir,false))/(2.*epsL);
#else 
    float dx = (mat_tweaknoise(p+epsL*lightDir,false)-v)/epsL;
#endif
    return clamp(-dx*mat_i_grad/mat_i_scale/v, 0.,1.); 
    
}


vec4 materialColorForPixel( vec2 texCoord )
{
	
	vec2 uv = texCoord;

    
    vec2 mouse=mat_offset;
    if (mouse.x+mouse.y==0.) mouse.xy=vec2(0.5);

    
    float theta = (mouse.x*2. - 1.)*PI;
    float phi = (mouse.y - .5)*PI;
 
    float t=3.*mat_animation_time,B=.07; theta += B*cos(t); phi += B*sin(t);


    vec3 cameraPos =vec3(sin(theta)*cos(phi),sin(phi),cos(theta)*cos(phi));   
    vec3 cameraTarget = vec3(0.);
    vec3 ww = normalize( cameraPos - cameraTarget );
    vec3 uu = normalize(cross( vec3(0.,1.,0.), ww ));
    vec3 vv = normalize(cross(ww,uu));
    vec2 q = 2.*(uv -vec2(.9,.5));
    vec3 rayDir = normalize( q.x*uu + q.y*vv -1.5*ww );

    
    vec3 col=vec3(0.);
 	float transp=1., epsC=.01/2.;
    float l = .5;
    vec3 p=cameraPos+l*rayDir, p_=p;
    
    for (int i=0; i<mat_iterations; i++) { 
        float Aloc = mat_tweaknoise(p*mat_scale,true); 
        if (Aloc>0.01) {
            

            float a = 2.*PI*float(i)/200.; vec3 c = .5+.5*cos(a+vec3(0.,2.*PI/3.,-2.*PI/3.)+mat_animation_time);

 	        col += transp*c*Aloc;
            
            col = clamp(col,0.,1.); 
   		    transp *= 1.-Aloc;
	        if (transp<.001) break;
        }
 
        p += epsC*rayDir;
    }           

	
	
	vec3 color = col+ transp*skyColor;

	
    color = mix(vec3(0.5), color, mat_contrast);
    
    color += vec3(mat_brightness);
	
	color *= mat_tint.rgb;
	
	color = mix(color, vec3(1.0)-color,float(mat_invert));
		
	vec4 final_color = vec4(color,1.0);	
	return final_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
