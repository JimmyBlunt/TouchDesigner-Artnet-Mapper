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

uniform vec4 uMMParam000; // native input: mat_position
float mat_position = uMMParam000.x;
const int mat_spectrum = 0;
#define mat_spectrum_IS_Custom_gradient
uniform vec4 uMMParam002; // native input: mat_custom_start
vec4 mat_custom_start = uMMParam002;
uniform vec4 uMMParam003; // native input: mat_custom_end
vec4 mat_custom_end = uMMParam003;
#define tex_visible_wavelength sTD2DInputs[0]
#define tex_temperature sTD2DInputs[1]
#define tex_sun sTD2DInputs[2]
#define tex_rayleigh_scattering sTD2DInputs[3]

// BEGIN MadSDF.glsl
/*
MadMapper Signed Distance Field Glsl Library

Copyright (c) 2016, Garage Cube, All rights reserved.
Copyright (c) 2016, Simon Geilfus, All rights reserved.

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

// Options
//______________________________________________

//#define SDF_ANTIALIASING_NONE
//#define SDF_ANTIALIASING_MEDIUM
//#define SDF_ANTIALIASING_HIGH

// Defaut to SDF_ANTIALIASING_HIGH if nothing specified
#if ! defined( SDF_ANTIALIASING_NONE ) && ! defined( SDF_ANTIALIASING_MEDIUM ) && ! defined( SDF_ANTIALIASING_HIGH )
    #define SDF_ANTIALIASING_HIGH
#endif

#if defined( SDF_ANTIALIASING_MEDIUM ) && ! defined( SDF_ANTIALIASING_MEDIUM_DIST_SCALE )
    #define SDF_ANTIALIASING_MEDIUM_DIST_SCALE 850.0
#endif

// 2D Primitives
//______________________________________________

//! Returns the signed distance of a circle
float circle( vec2 p, float radius );
//! Returns the signed distance of a circle
float circle( vec2 p, vec2 center, float radius );
//! Returns the signed distance of a box
float rectangle( vec2 p, float radius );
//! Returns the signed distance of a box
float rectangle( vec2 p, vec2 size );
//! Returns the signed distance of a box
float rectangle( vec2 p, vec2 center, float radius );
//! Returns the signed distance of a box
float rectangle( vec2 p, vec2 center, vec2 size );
//! Returns the signed distance of a rounded box
float roundedRectangle( vec2 p, vec2 size, float cornerRadius );
//! Returns the signed distance of a rounded box
float roundedRectangle( vec2 p, vec2 center, vec2 size, float cornerRadius );
//! Returns the signed distance of a triangle
float triangle( vec2 p, float radius );
//! Returns the signed distance of a triangle
float triangle( vec2 p, vec2 center, float radius );
//! Returns the signed distance of an hexagon
float hexagon( vec2 p, float radius );
//! Returns the signed distance of an hexagon
float hexagon( vec2 p, vec2 center, float radius );
//! Returns the signed distance of a line
float line( vec2 p, vec2 start, vec2 end, float width );
//! Returns the signed distance of an arc
float arc( vec2 p, float radius, float angle, float width );

// Colors
//______________________________________________
//! Returns the colored inner distance field
vec3 fill( vec3 a, vec3 b, float dist );
//! Returns the colored inner distance field
vec4 fill( vec4 a, vec4 b, float dist );
//! Returns the colored border of the distance field
vec3 stroke( vec3 a, vec3 b, float dist, float width );
//! Returns the colored border of the distance field
vec4 stroke( vec4 a, vec4 b, float dist, float width );
//! Returns the colored blurred border of the distance field
vec3 glow( vec3 color, float dist, float width );
//! Returns the colored blurred border of the distance field
vec4 glow( vec4 color, float dist, float width );

// 2D Transforms
//______________________________________________

//! Returns a translated position
vec2 translate( vec2 p, vec2 t );
//! Returns a rotated position
vec2 rotate( vec2 p, float a );
//! Returns a transformed position
vec2 transform( vec2 p, mat2 m );

// 2D Domain and Distance Operations
//______________________________________________

//! Returns the repeated position every offset
vec2 repeat( vec2 p, vec2 offset );
//! Returns the repeated position every offset with the ID for the current cell
vec2 repeat( vec2 p, vec2 offset, out vec2 cellId );
//! Returns the repeated position with an offset between each a of size b
vec2 repeat( vec2 p, vec2 offset, vec2 a, vec2 b );
//! Returns the repeated position with an offset between each a of size b with the ID for the current cell
vec2 repeat( vec2 p, vec2 offset, vec2 a, vec2 b, out vec2 cellId );
//! Returns the repeated position radially each angle
vec2 repeatRadial( vec2 p, float angle );
//! Returns the repeated position radially each angle with the ID for the current cell
vec2 repeatRadial( vec2 p, float angle, out vec2 cellId );
//! Returns the repeated position radially each angle starting at angleOffset
vec2 repeatRadial( vec2 p, float angle, float angleOffset );
//! Returns the repeated position radially each angle starting at angleOffset with the ID for the current cell
vec2 repeatRadial( vec2 p, float angle, float angleOffset, out vec2 cellId );

//! Returns the union of two signed distance field
float blend( float d1, float d2 );
//! Returns the smooth blend of two signed distance field
float smoothBlend( float d1, float d2, float k );
//! Returns the subtraction of a signed distance field by another signed distance field 
float subtract( float d1, float d2 );
//! Returns the intersection of two signed distance field
float intersect( float d1, float d2 );


// Implementation
//______________________________________________

//! Returns the signed distance of a circle
float circle( vec2 p, float radius )
{
    return length( p ) - radius;
}

//! Returns the signed distance of a circle
float circle( vec2 p, vec2 center, float radius )
{
    return length( p - center ) - radius;
}

//! Returns the signed distance of a box
float rectangle( vec2 p, float radius )
{
    vec2 d = abs( p ) - vec2( radius );
    return min( max( d.x, d.y ), 0.0 ) + length( max( d, 0.0 ) );
}

//! Returns the signed distance of a box
float rectangle( vec2 p, vec2 size )
{
    vec2 d = abs( p ) - size;
    return min( max( d.x, d.y ), 0.0 ) + length( max( d, 0.0 ) );
}

//! Returns the signed distance of a box
float rectangle( vec2 p, vec2 center, float radius )
{
    vec2 d = abs( p - center ) - vec2( radius );
    return min( max( d.x, d.y ), 0.0 ) + length( max( d, 0.0 ) );
}

//! Returns the signed distance of a box
float rectangle( vec2 p, vec2 center, vec2 size )
{
    vec2 d = abs( p - center ) - size;
    return min( max( d.x, d.y ), 0.0 ) + length( max( d, 0.0 ) );
}

//! Returns the signed distance of a rounded box
float roundedRectangle( vec2 p, vec2 size, float cornerRadius )
{
  return length( max( abs( p ) - size + cornerRadius, 0.0 ) ) - cornerRadius;
}

//! Returns the signed distance of a rounded box
float roundedRectangle( vec2 p, vec2 center, vec2 size, float cornerRadius )
{
  return length( max( abs( p - center ) - size + cornerRadius, 0.0 ) ) - cornerRadius;
}

//! Returns the signed distance of a triangle
float triangle( vec2 p, float radius )
{
    return max( abs( p ).x * 0.866025 + p.y * 0.5, -p.y ) - radius * 0.5;
}

//! Returns the signed distance of a triangle
float triangle( vec2 p, vec2 center, float radius )
{
    p = p - center;
    return max( abs( p ).x * 0.866025 + p.y * 0.5, -p.y ) - radius * 0.5;
}

//! Returns the signed distance of an hexagon
float hexagon( vec2 p, float radius )
{
    vec2 absP = abs(p);
    return max((absP.x*0.866025+absP.y*0.5),absP.y) - radius;
}
//! Returns the signed distance of an hexagon
float hexagon( vec2 p, vec2 center, float radius )
{
    p = p - center;
    vec2 absP = abs(p);
    return max((absP.x*0.866025+absP.y*0.5),absP.y) - radius;
}

//! Returns the signed distance of a line
float line( vec2 p, vec2 start, vec2 end, float width )
{
    vec2 dir = start - end;
    float lngth = length(dir);
    dir /= lngth;
    vec2 proj = max(0.0, min(lngth, dot((start - p), dir))) * dir;
    return length( (start - p) - proj ) - (width / 2.0);
}

//! Returns the signed distance of an arc
float arc( vec2 p, float radius, float angle, float width )
{
    width   *= 0.5;
    radius  -= width;
    vec2 n  = vec2(cos( angle ), sin( angle ));
    return max( -( abs( p ).x * n.x + p.y * n.y ), abs( circle( p, radius ) ) - width );
}

// Colors
//______________________________________________

float fillDist( float dist )
{
#if defined( SDF_ANTIALIASING_NONE )
    return step( dist, 0.0 );
#elif defined( SDF_ANTIALIASING_MEDIUM )
    return clamp( -dist * SDF_ANTIALIASING_MEDIUM_DIST_SCALE, 0.0, 1.0 );
#elif defined( SDF_ANTIALIASING_HIGH )
    //return smoothstep( fwidth( dist ), 0.0, dist );
    float aa = length( vec2( dFdx( dist ), dFdy( dist ) ) );
    return smoothstep( aa, -aa, dist );
#endif
}
float strokeDist( float dist, float width )
{
#if defined( SDF_ANTIALIASING_NONE )
    float s = max( -dist - width, dist );
    return step( s, 0.0 );
#elif defined( SDF_ANTIALIASING_MEDIUM )
    dist = dist * SDF_ANTIALIASING_MEDIUM_DIST_SCALE;
    width = width * SDF_ANTIALIASING_MEDIUM_DIST_SCALE;
    return clamp( - dist, 0.0, 1.0 ) - clamp( - dist - width, 0.0, 1.0 );
#elif defined( SDF_ANTIALIASING_HIGH )
    //float s = max( dist - width, -dist );
    //return smoothstep( fwidth( s ), 0.0, s );    
    float aa = length( vec2( dFdx( -dist ), dFdy( -dist ) ) );
    return 1.0f - ( smoothstep( aa, -aa, -dist ) + smoothstep( -aa, aa, -dist - width ) );
#endif
}

vec3 fill( vec3 a, vec3 b, float dist ) 
{
    return mix( a, b, fillDist( dist ) );
}
vec4 fill( vec4 a, vec4 b, float dist ) 
{
    return mix( a, b, fillDist( dist ) );
}
vec3 stroke( vec3 a, vec3 b, float dist, float width ) 
{
    return mix( a, b, strokeDist( dist, width ) );
}
vec4 stroke( vec4 a, vec4 b, float dist, float width ) 
{
    return mix( a, b, strokeDist( dist, width ) );
}
vec3 glow( vec3 color, float dist, float width ) 
{
    return color * ( 1.0 - smoothstep( -width, width, abs( dist ) ) );
}
vec4 glow( vec4 color, float dist, float width ) 
{
    return color * ( 1.0 - smoothstep( -width, width, abs( dist ) ) );
}

// Transforms
//______________________________________________

//! Returns a translated position
vec2 translate( vec2 p, vec2 t )
{
    return p - t;
}
//! Returns a rotated position
vec2 rotate( vec2 p, float a )
{
    mat2 m = mat2(cos(a), -sin(a), sin(a), cos(a));
    return p * m;
}
//! Returns a transformed position
vec2 transform( vec2 p, mat2 m )
{
    return p * m;
}

// 2D Domain and Distance Operations
//______________________________________________

//! Returns the repeated position every offset
vec2 repeat( vec2 p, vec2 offset )
{
    return mod( p, offset ) - 0.5 * offset;
}

//! Returns the repeated position every offset with the ID for the current cell
vec2 repeat( vec2 p, vec2 offset, out vec2 cellId )
{
    cellId = floor( p / offset );
    return mod( p, offset ) - 0.5 * offset;
}

//! Returns the repeated position with an offset between each a of size b
vec2 repeat( vec2 p, vec2 offset, vec2 a, vec2 b )
{
    p += mod( floor( p / offset ).yx, b ) * a;
    return mod( p, offset ) - 0.5 * offset;
}

//! Returns the repeated position with an offset between each a of size b with the ID for the current cell
vec2 repeat( vec2 p, vec2 offset, vec2 a, vec2 b, out vec2 cellId )
{
    p += mod( floor( p / offset ).yx, b ) * a;
    cellId = floor( p / offset );
    return mod( p, offset ) - 0.5 * offset;
}

//! Returns the repeated position radially each angle
vec2 repeatRadial( vec2 p, float angle )
{
    float a = atan( p.y, p.x ) + angle * 0.5;
    float r = length( p );
    a       = mod( a, angle ) - angle * 0.5;
    return vec2( cos( a ), sin( a ) ) * r;      
}

//! Returns the repeated position radially each angle with the ID for the current cell
vec2 repeatRadial( vec2 p, float angle, out vec2 cellId )
{
    float a = atan( p.y, p.x ) + angle * 0.5;
    float r = length( p );
    cellId  = vec2( floor( a / angle ) );    
    a       = mod( a, angle ) - angle * 0.5;
    return vec2( cos( a ), sin( a ) ) * r;    
}

//! Returns the repeated position radially each angle starting at angleOffset
vec2 repeatRadial( vec2 p, float angle, float angleOffset )
{
    float a = angleOffset + atan( p.y, p.x ) + angle * 0.5;
    float r = length( p );
    a       = mod( a, angle ) - angle * 0.5;
    return vec2( cos( a ), sin( a ) ) * r;    
}

//! Returns the repeated position radially each angle starting at angleOffset with the ID for the current cell
vec2 repeatRadial( vec2 p, float angle, float angleOffset, out vec2 cellId )
{
    float a = angleOffset + atan( p.y, p.x ) + angle * 0.5;
    float r = length( p );
    cellId  = vec2( floor( a / angle ) );   
    a       = mod( a, angle ) - angle * 0.5;
    return vec2( cos( a ), sin( a ) ) * r;    
}

//! Returns the union of two signed distance field
float blend( float d1, float d2 )
{
    return min( d1, d2 );
}

float smin( float a, float b, float k )
{
    float h = clamp( 0.5+0.5*(b-a)/k, 0.0, 1.0 );
    return mix( b, a, h ) - k*h*(1.0-h);
}
//! Returns the smooth blend of two signed distance field
float smoothBlend( float d1, float d2, float k )
{
    return smin( d1, d2, k );
}
//! Returns the subtraction of a signed distance field by another signed distance field 
float subtract( float d1, float d2 )
{
    return max(d1, -d2);
}
//! Returns the intersection of two signed distance field
float intersect( float d1, float d2 )
{
    return max(d1, d2);
}



// END MadSDF.glsl


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

float plot(vec2 st, float pct, float w){
  return smoothstep( pct-w*.5, pct, st.y) - smoothstep( pct, pct+w*.5, st.y);
}

vec4 materialColorForPixel( vec2 texCoord )
{
	
	float thickness = 0.005;
	vec2 uv = texCoord;
	vec3 black = vec3(0.);

	
	vec3 solidColor = vec3(0.);
	vec3 gradientColor = vec3(0.);

    #if defined(mat_spectrum_IS_Visible_wavelength)
		solidColor = texture(tex_visible_wavelength, vec2(mat_position, 0.)).rgb;
		gradientColor = texture(tex_visible_wavelength, uv).rgb;
    #elif defined(mat_spectrum_IS_Temperature)
		solidColor = texture(tex_temperature, vec2(mat_position, 0.)).rgb;
		gradientColor = texture(tex_temperature, uv).rgb;
	 #elif defined(mat_spectrum_IS_Sun)
		solidColor = texture(tex_sun, vec2(mat_position, 0.)).rgb;
		gradientColor = texture(tex_sun, uv).rgb;
	 #elif defined(mat_spectrum_IS_Rayleigh_scattering)
		solidColor = texture(tex_rayleigh_scattering, vec2(mat_position, 0.)).rgb;
		gradientColor = texture(tex_rayleigh_scattering, uv).rgb;
	#else
		solidColor = mix(mat_custom_start, mat_custom_end, mat_position).rgb;
		gradientColor = mix(mat_custom_start, mat_custom_end, uv.x).rgb;
    #endif

	
	float solidSDF = rectangle(uv, vec2(0., 0.125), vec2(1., 0.125));
	vec3 solid = fill(black, solidColor, solidSDF);

	
	float gradientSDF = rectangle(uv, vec2(0., 0.25 + 0.125),vec2(1., 0.125));
	vec3 gradient = fill(black, gradientColor, gradientSDF);

	
	vec2 gradientLinePos = vec2(uv.x-mat_position, uv.y);
	float gradientLineSDF = line(gradientLinePos, vec2(0., 0.25+thickness*.5), vec2(0., 0.5-thickness*.5), thickness);
	vec3 gradientLine = fill(black, vec3(1.), gradientLineSDF);

	
	float y = 1. - pow(cos(PI * uv.x - PI*.5), 2.) * .48;
	float functionLine = plot(uv, y, thickness);

	
	vec2 functionCirclePos = vec2(mat_position,  1. - pow(cos(PI * mat_position - PI*.5), 2.) * .48);
	float functionCircleSDF = circle(uv, functionCirclePos, 0.02);
	vec3 functionCircle = fill(black, vec3(1.), functionCircleSDF);

	
	vec3 col = solid + gradient + gradientLine + functionLine + functionCircle;

	return vec4(col, 1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
