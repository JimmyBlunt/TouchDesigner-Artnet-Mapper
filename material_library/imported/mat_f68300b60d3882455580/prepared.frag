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
uniform vec4 uMMParam001; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_reverse
bool mat_reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_offset
float mat_offset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_strob
float mat_strob = uMMParam005.x;
float mat_time = uTDTime * (mat_speed);

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

float iTime = mat_time - mat_offset * 10;

#define HorizontalAmplitude     0.30
#define VerticleAmplitude       0.20
#define HorizontalSpeed         0.90
#define VerticleSpeed           1.50
#define ParticleMinSize         1.76
#define ParticleMaxSize         1.61
#define ParticleBreathingSpeed      0.30
#define ParticleColorChangeSpeed    0.70
#define ParticleCount           2.0
#define ParticleColor1          vec3(9.0, 5.0, 3.0)
#define ParticleColor2          vec3(1.0, 3.0, 9.0)


float hash( float x )
{
    return fract( sin( x ) * 43758.5453 );
}

float noise( vec2 uv )  
{
    vec3 x = vec3( uv.xy, 0.0 );

    vec3 p = floor( x );
    vec3 f = fract( x );

    f = f*f*(3.0 - 2.0*f);

    float offset = 57.0;

    float n = dot( p, vec3(1.0, offset, offset*2.0) );

    return mix( mix(    mix( hash( n + 0.0 ),       hash( n + 1.0 ), f.x ),
                        mix( hash( n + offset),     hash( n + offset+1.0), f.x ), f.y ),
                mix(    mix( hash( n + offset*2.0), hash( n + offset*2.0+1.0), f.x),
                        mix( hash( n + offset*3.0), hash( n + offset*3.0+1.0), f.x), f.y), f.z);
}

float snoise( vec2 uv )
{
    return noise( uv ) * 2.0 - 1.0;
}


float perlinNoise( vec2 uv )
{
    float n =       noise( uv * 1.0 )   * 128.0 +
                noise( uv * 2.0 )   * 64.0 +
                noise( uv * 4.0 )   * 32.0 +
                noise( uv * 8.0 )   * 16.0 +
                noise( uv * 16.0 )  * 8.0 +
                noise( uv * 32.0 )  * 4.0 +
                noise( uv * 64.0 )  * 2.0 +
                noise( uv * 128.0 ) * 1.0;

    float noiseVal = n / ( 1.0 + 2.0 + 4.0 + 8.0 + 16.0 + 32.0 + 64.0 + 128.0 );
    noiseVal = abs(noiseVal * 2.0 - 1.0);

    return  noiseVal;
}

float fBm( vec2 uv, float lacunarity, float gain )
{
    float sum = 0.0;
    float amp = 10.0;

    for( int i = 0; i < 2; ++i )
    {
        sum += ( perlinNoise( uv ) ) * amp;
        amp *= gain;
        uv *= lacunarity;
    }

    return sum;
}

vec3 particles( vec2 pos )
{

    vec3 c = vec3( 0, 0, 0 );

    float noiseFactor = fBm( pos, 0.01, 0.1);

    for( float i = 1.0; i < ParticleCount+1.0; ++i )
    {
        float cs = cos( iTime * HorizontalSpeed * (i/ParticleCount) + noiseFactor ) * HorizontalAmplitude;
        float ss = sin( iTime * VerticleSpeed   * (i/ParticleCount) + noiseFactor ) * VerticleAmplitude;
        vec2 origin = vec2( cs , ss );

        float t = sin( iTime * ParticleBreathingSpeed * i ) * 0.5 + 0.5;
        float particleSize = mix( ParticleMinSize, ParticleMaxSize, t );
        float d = clamp( sin( length( pos - origin )  + particleSize ), 0.0, particleSize);

        float t2 = sin( iTime * ParticleColorChangeSpeed * i ) * 0.5 + 0.5;
        vec3 color = mix( ParticleColor1, ParticleColor2, t2 );
        c += color * pow( d, 10.0 );
    }

    return c;
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;
    vec3 finalColor = particles( sin( abs(uv) ) );


    return vec4( finalColor, 1.0 );

}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
