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
uniform vec4 uMMParam001; // native input: mat_rotate
float mat_rotate = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: mat_shift_scale
float mat_shift_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_shift_type
int mat_shift_type = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_orbit
vec2 mat_orbit = uMMParam007.xy;
uniform vec4 uMMParam008; // native input: mat_thick
float mat_thick = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_corner
float mat_corner = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_shadow
float mat_shadow = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_iterations
int mat_iterations = int(round(uMMParam011.x));
uniform vec4 uMMParam012; // native input: mat_speed
float mat_speed = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam013.x > 0.5;
uniform vec4 uMMParam014; // native input: mat_reverse
bool mat_reverse = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: mat_offset
float mat_offset = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_offset_scale
float mat_offset_scale = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_strob
float mat_strob = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_restart
int mat_restart = int(round(uMMParam018.x));
uniform vec4 uMMParam019; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam020.x;
const int mat_luma_mode = 0;
#define mat_luma_mode_IS_Before_Color_Controls
uniform vec4 uMMParam022; // native input: mat_brightness
float mat_brightness = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_contrast
float mat_contrast = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_saturation
float mat_saturation = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_hue_shift
float mat_hue_shift = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_invert
bool mat_invert = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam027.x > 0.5;
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

float mat_time = mat_time_source - mat_offset * 8. * mat_offset_scale;

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
}

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

vec2 mirrorUV(vec2 uv) {
    uv += vec2(0.5);
    if (mat_mirror_x) {
        if (uv.x > 0.5)   {
            uv.x = 1.0-uv.x;
        }
    }
    if (mat_mirror_y) {
        if (uv.y > 0.5) {
            uv.y = 1.0-uv.y;
        }
    }
    uv -= vec2(0.5);
    return uv;
}

vec2 transformUV(vec2 uv) {

    if (mat_lock_aspect) {
        uv.x *= RENDERSIZE.x / RENDERSIZE.y;
    }
    uv *= mat_scale * 1.75;

    uv = mirrorUV(uv);

    vec2 uv_shift = mat_shift_amount * mat_shift_scale;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    if (mat_shift_type == 0) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, -1. * 2*PI*(mat_rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    
    if (mat_shift_type == 1) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    return uv;
}


#define LOOP_DURATION 8.
#define MOVE_COUNT 6.
#define TIME_OFFSET .3


vec4 moves[6] = vec4[6](
    vec4(1,0,0, 2.),
    vec4(0,1,0, -1.),
    vec4(0,-1,0, -3.),
    vec4(0,0,-1, 2.),
    vec4(0,-1,0, -1.),
    vec4(0,1,0, -3.)
);





#define QUATERNION_IDENTITY vec4(0, 0, 0, 1)





vec4 qmul(vec4 q1, vec4 q2) {
    return vec4(
        q2.xyz * q1.w + q1.xyz * q2.w + cross(q1.xyz, q2.xyz),
        q1.w * q2.w - dot(q1.xyz, q2.xyz)
    );
}



vec3 rotate_vector(vec3 v, vec4 r) {
    vec4 r_c = r * vec4(-1, -1, -1, 1);
    return qmul(r, qmul(vec4(v, 0), r_c)).xyz;
}


vec4 rotate_angle_axis(float angle, vec3 axis) {
    float sn = sin(angle * 0.5);
    float cs = cos(angle * 0.5);
    return vec4(axis * sn, cs);
}

vec4 q_conj(vec4 q) {
    return vec4(-q.x, -q.y, -q.z, q.w);
}

vec4 q_slerp(vec4 a, vec4 b, float t) {
    
    if (length(a) == 0.0) {
        if (length(b) == 0.0) {
            return QUATERNION_IDENTITY;
        }
        return b;
    } else if (length(b) == 0.0) {
        return a;
    }

    float cosHalfAngle = a.w * b.w + dot(a.xyz, b.xyz);

    if (cosHalfAngle >= 1.0 || cosHalfAngle <= -1.0) {
        return a;
    } else if (cosHalfAngle < 0.0) {
        b.xyz = -b.xyz;
        b.w = -b.w;
        cosHalfAngle = -cosHalfAngle;
    }

    float blendA;
    float blendB;
    if (cosHalfAngle < 0.99) {
        
        float halfAngle = acos(cosHalfAngle);
        float sinHalfAngle = sin(halfAngle);
        float oneOverSinHalfAngle = 1.0 / sinHalfAngle;
        blendA = sin(halfAngle * (1.0 - t)) * oneOverSinHalfAngle;
        blendB = sin(halfAngle * t) * oneOverSinHalfAngle;
    } else {
        
        blendA = 1.0 - t;
        blendB = t;
    }

    vec4 result = vec4(blendA * a.xyz + blendB * b.xyz, blendA * a.w + blendB * b.w);
    if (length(result) > 0.0) {
        return normalize(result);
    }
    return QUATERNION_IDENTITY;
}

vec2 rand(vec2 n) {
    return fract(sin(n) * 43758.5453123) * 2. - 1.;
}

vec2 srand(vec2 n, float hard) {
    vec2 nf = floor(n);
    vec2 nc = ceil(n);
    return mix(rand(nf), rand(nc), smoothstep(.5 * hard, 1. - .5 * hard, fract(n)));
}

vec2 mainSound( in int samp, float time )
{
    time += TIME_OFFSET;
    
    float index = floor((time + .05) / LOOP_DURATION * MOVE_COUNT);
    float moveIndex = mod(index - 1., MOVE_COUNT);
    float turns = abs(moves[int(moveIndex)].w);
    float volume = pow(turns / 3., 1.5);

    float t = mod(time, LOOP_DURATION);
    t = mod(t, LOOP_DURATION / MOVE_COUNT);
    vec2 s = srand(vec2(t * 2.5, t * 2. + .02) * 1000., .0) * exp(-100. * t);
    s += sin(vec2(t * 5000.) / mix(1.1, 1., rand(vec2(index+.2)).x) / (1. + t * .5)) * exp(-30. * t) * .1;

    return s * volume;
}









void pR(inout vec2 p, float a) {
    p = cos(a)*p + sin(a)*vec2(p.y, -p.x);
}

float vmin(vec3 v) {
    return min(min(v.x, v.y), v.z);
}

float vmax(vec3 v) {
    return max(max(v.x, v.y), v.z);
}

float fBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, vec3(0))) + vmax(min(d, vec3(0)));
}

float smin(float a, float b, float k){
    float f = clamp(0.5 + 0.5 * ((a - b) / k), 0., 1.);
    return (1. - f) * a + f  * b - f * (1. - f) * k;
}

float smax(float a, float b, float k) {
    return -smin(-a, -b, k);
}



float range(float vmin, float vmax, float value) {
  return clamp((value - vmin) / (vmax - vmin), 0., 1.);
}

float almostIdentity(float x) {
    return x*x*(2.0-x);
}

float circularOut(float t) {
  return sqrt((2.0 - t) * t);
}



vec3 pal( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d ) {
    return a + b*cos( 6.28318*(c*t+d) );
}

vec3 spectrum(float n) {
    return pal( n, vec3(0.5,0.5,0.5),vec3(0.5,0.5,0.5),vec3(1.0,1.0,1.0),vec3(0.0,0.33,0.67) );
}


vec3 erot(vec3 p, vec3 ax, float ro) {
  return mix(dot(ax,p)*ax, p, cos(ro))+sin(ro)*cross(ax,p);
}







bool lightingPass;
float time;

void applyMomentum(inout vec4 q, float time, int i, vec4 move) {

    float turns = move.w;
    vec3 axis = move.xyz;

    float duration = abs(turns);
    float rotation = PI / 2. * turns * .75;

    float start = float(i + 1);
    float t = time * MOVE_COUNT;
    float ramp = range(start, start + duration, t);
    float angle = circularOut(ramp) * rotation;
    vec4 q2 = rotate_angle_axis(angle, axis);
    q = qmul(q, q2);
}

void applyMove(inout vec3 p, int i, vec4 move) {

    float turns = move.w;
    vec3 axis = move.xyz;

    float rotation = PI / 2. * turns;

    float start = float(i);
    float t = time * MOVE_COUNT;
    float ramp = range(start, start + 1., t);
    ramp = pow(almostIdentity(ramp), 2.5);
    float angle = ramp * rotation;

    bool animSide = vmax(p * -axis) > 0.;
    if (animSide) {
        angle = 0.;
    }

    p = erot(p, axis, angle) ;
}

vec4 momentum(float time) {
    vec4 q = QUATERNION_IDENTITY;
    applyMomentum(q, time, 5, moves[5]);
    applyMomentum(q, time, 4, moves[4]);
    applyMomentum(q, time, 3, moves[3]);
    applyMomentum(q, time, 2, moves[2]);
    applyMomentum(q, time, 1, moves[1]);
    applyMomentum(q, time, 0, moves[0]);
    return q;
}

vec4 momentumLoop(float time) {
    vec4 q;

    
    q = momentum(3.);
    q = q_conj(q);
    q = q_slerp(QUATERNION_IDENTITY, q, time);

    
    q = qmul(momentum(time + 1.), q);

    
    q = qmul(momentum(time), q);

    return q;
}






vec4 mapBox(vec3 p) {

    
    pR(p.xy, step(0., -p.z) * PI / -2.);
    pR(p.xz, step(0., p.y) * PI);
    pR(p.yz, step(0., -p.x) * PI * 1.5);

    
    vec3 face = step(vec3(vmax(abs(p))), abs(p)) * sign(p);
    float faceIndex = max(vmax(face * vec3(0,1,2)), vmax(face * -vec3(3,4,5)));
    vec3 col = spectrum(faceIndex / 6. + .1 + .5);

    
    float thick = .033 * mat_thick;
    float d = length(p + vec3(.1,.02,.05)) - .4;
    d = max(d, -d - thick);

    
    vec3 ap = abs(p);
    float l = sqrt(sqrt(1.) / 3.);
    vec3 plane = cross(abs(face), normalize(vec3(1)));
    float groove = max(-dot(ap.yzx, plane), dot(ap.zxy, plane));
    d = smax(d, -abs(groove), .01);

    float gap = .005;

    
    float r = .05 * mat_corner;
    float cut = -fBox(abs(p) - (1. + r + gap), vec3(1.)) + r;
    d = smax(d, -cut, thick / 2.);

    
    float opp = vmin(abs(p)) + gap;
    opp = max(opp, length(p) - 1.);
    if (opp < d) {
        return vec4(opp, vec3(-1));
    }

    return vec4(d, col * .4);
}

vec4 map(vec3 p) {

    vec2 orbit = mat_orbit;
    
    
    

    pR(p.yz, (orbit.y * 2. + 1.) * 2.);
    pR(p.xz, (orbit.x * 2. + 1.) * 4.);


    
    pR(p.xz, time * PI * 2.);
    
    

    vec4 q = momentumLoop(time);
    p = rotate_vector(p, q);

    applyMove(p, 5, moves[5]);
    applyMove(p, 4, moves[4]);
    applyMove(p, 3, moves[3]);
    applyMove(p, 2, moves[2]);
    applyMove(p, 1, moves[1]);
    applyMove(p, 0, moves[0]);

    return mapBox(p);
}






mat3 calcLookAtMatrix( in vec3 ro, in vec3 ta, in float roll )
{
    vec3 ww = normalize( ta - ro );
    vec3 uu = normalize( cross(ww,vec3(sin(roll),cos(roll),0.0) ) );
    vec3 vv = normalize( cross(uu,ww));
    return mat3( uu, vv, ww );
}


vec3 calcNormal(vec3 p)
{
    const float h = 0.001;
    
    vec3 n = vec3(0.0);
    for( int i=0; i<4; i++ )
    {
        vec3 e = 0.5773*(2.0*vec3((((i+3)>>1)&1),((i>>1)&1),(i&1))-1.0);
        n += e*map(p+e*h).x;
    }
    return normalize(n);
}




vec2 iSphere( in vec3 ro, in vec3 rd, float r )
{
    vec3 oc = ro;
    float b = dot( oc, rd );
    float c = dot( oc, oc ) - r*r;
    float h = b*b - c;
    if( h<0.0 ) return vec2(-1.0);
    h = sqrt(h);
    return vec2(-b-h, -b+h );
}


float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax )
{
    float res = 1.0;

    
    
    vec2 bound = iSphere(ro, rd, .55);
    tmax = min(tmax, bound.y);

    float t = mint;
    float ph = 1e10;

    for( int i=0; i<100; i++ )
    {
        vec4 hit = map( ro + rd*t );
        float h = hit.x;
        if (hit.y > 0.) { 
            res = min( res, 10.0*h/t );
        }
        t += h;
        if( res<0.0001 || t>tmax ) break;

    }

    return clamp( res, 0.0, 1.0 );
}

vec3 render(vec2 p) {

    vec3 col = vec3(.02,.01,.025) * 0.;

    

    vec3 camPos = vec3(0,0,2.);
    mat3 camMat = calcLookAtMatrix( camPos, vec3(0,0,-1), 0.);
    vec3 rd = normalize( camMat * vec3(p.xy, 2.8) );
    vec3 pos = camPos;

    vec2 bound = iSphere(pos, rd, .55);
    if (bound.x < 0.) {
        return col;
    }

    lightingPass = false;
    float rayLength = bound.x;
    float dist = 0.;
    bool background = true;
    vec4 res;

    for (int i = 0; i < mat_iterations; i++) {
        rayLength += dist;
        pos = camPos + rd * rayLength;
        res = map(pos);
        dist = res.x;

        if (abs(dist) < .001) {
            background = false;
            break;
        }

        if (rayLength > bound.y) {
            break;
        }
    }

    
    

    lightingPass = true;

    if ( ! background) {

        col = res.yzw;
        vec3 nor = calcNormal(pos);
        vec3 lig = normalize(vec3(-.33,.3,.25));
        vec3 lba = normalize( vec3(.5, -1., -.5) );
        vec3 hal = normalize( lig - rd );
        float amb = sqrt(clamp( 0.5+0.5*nor.y, 0.0, 1.0 ));
        float dif = clamp( dot( nor, lig ), 0.0, 1.0 );
        float bac = clamp( dot( nor, lba ), 0.0, 1.0 )*clamp( 1.0-pos.y,0.0,1.0);
        float fre = pow( clamp(1.0+dot(nor,rd),0.0,1.0), 2.0 );

        
        
        if( dif > .001) dif *= softshadow( pos, lig, 0.001, .9 );

        float occ = 1.;

        float spe = pow( clamp( dot( nor, hal ), 0.0, 1.0 ),16.0)*
            dif *
            (0.04 + 0.96*pow( clamp(1.0+dot(hal,rd),0.0,1.0), 5.0 ));

        vec3 lin = vec3(0.0);
        lin += 2.80*dif*vec3(1.30,1.00,0.70);
        lin += 0.55*amb*vec3(0.40,0.60,1.15)*occ;
        lin += 1.55*bac*vec3(0.25,0.25,0.25)*occ*vec3(2,0,1);
        lin += 0.25*fre*vec3(1.00,1.00,1.00)*occ;

        col = col*lin;
        col += 5.00*spe*vec3(1.10,0.90,0.70);
    }

    return col;
}

float vmul(vec2 v) {
    return v.x * v.y;
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    float mTime = (mat_time + TIME_OFFSET) / LOOP_DURATION;

    vec3 col = vec3(0);

    time = mod(mTime, 1.);
    vec2 p = uv;
    col += render(p);

    col = pow( col, vec3(0.4545) * mat_shadow );

    out_color = vec4(col, 1.);

    
    if (mat_luma_to_alpha && mat_luma_mode == 0) {
        if (mat_luma(out_color.rgb) < mat_luma_threshold) {
            out_color.a = 0.;
        }
    }

    
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

    
    if (mat_luma_to_alpha && mat_luma_mode == 1) {
        if (mat_luma(out_color.rgb) < mat_luma_threshold) {
            out_color.a = 0.;
        }
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
