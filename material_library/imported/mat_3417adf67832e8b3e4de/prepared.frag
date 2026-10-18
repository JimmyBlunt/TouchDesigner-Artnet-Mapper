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
uniform vec4 uMMParam007; // native input: mat_fov
float mat_fov = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_shell_scale
float mat_shell_scale = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_height
float mat_height = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_glow
float mat_glow = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_edge
float mat_edge = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_background
float mat_background = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_iterations
int mat_iterations = int(round(uMMParam013.x));
uniform vec4 uMMParam014; // native input: mat_speed
float mat_speed = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_reverse
bool mat_reverse = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_offset
float mat_offset = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_offset_scale
float mat_offset_scale = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_strob
float mat_strob = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_restart
int mat_restart = int(round(uMMParam020.x));
uniform vec4 uMMParam021; // native input: mat_spin_speed
float mat_spin_speed = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_spin_bpm_sync
bool mat_spin_bpm_sync = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_spin_reverse
bool mat_spin_reverse = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_spin_offset
float mat_spin_offset = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_spin_offset_scale
float mat_spin_offset_scale = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_spin_strob
float mat_spin_strob = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_spin_restart
int mat_spin_restart = int(round(uMMParam027.x));
uniform vec4 uMMParam028; // native input: mat_brightness
float mat_brightness = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_contrast
float mat_contrast = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_saturation
float mat_saturation = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_hue_shift
float mat_hue_shift = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_invert
bool mat_invert = uMMParam032.x > 0.5;
uniform vec4 uMMParam033; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam033.x > 0.5;
uniform vec4 uMMParam034; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam035.x;
const int mat_luma_mode = 1;
#define mat_luma_mode_IS_After_Color_Controls
uniform vec4 uMMParam037; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam037.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_spin_time_source = uTDTime * (mat_spin_speed);

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
#define MM_LIBRARY_lerp(x,y,t) mix( x, y, t )

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

float mat_time = (mat_time_source - mat_offset * 8. * mat_offset_scale) * 0.25;
float mat_spin_time = (mat_spin_time_source - mat_spin_offset * 32. * mat_spin_offset_scale) * 0.25;

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
    uv *= mat_scale * 2.5;

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






float vmax(vec3 v) {
    return max(max(v.x, v.y), v.z);
}

float fPlane(vec3 p, vec3 n, float distanceFromOrigin) {
    return dot(p, n) + distanceFromOrigin;
}


float fBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, vec3(0))) + vmax(min(d, vec3(0)));
}




void pR(inout vec2 p, float a) {
    p = cos(a)*p + sin(a)*vec2(p.y, -p.x);
}


float pReflect(inout vec3 p, vec3 planeNormal, float offset) {
    float t = dot(p, planeNormal)+offset;
    if (t < 0.) {
        p = p - (2.*t)*planeNormal;
    }
    return sign(t);
}




int Type=5;

vec3 nc,pab,pbc,pca;
void initIcosahedron() {
    float cospin=cos(PI/float(Type)), scospin=sqrt(0.75-cospin*cospin);
    nc=vec3(-0.5,-cospin,scospin);
    pab=vec3(0.,0.,1.);
    pbc=vec3(scospin,0.,0.5);
    pca=vec3(0.,scospin,cospin);
    pbc=normalize(pbc); pca=normalize(pca);
}


vec3 bToC(vec3 A, vec3 B, vec3 C, vec3 barycentric) {
    return barycentric.x * A + barycentric.y * B + barycentric.z * C;
}

vec3 pModIcosahedron(inout vec3 p, int subdivisions) {
    p = abs(p);
    pReflect(p, nc, 0.);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.);

    if (subdivisions > 0) {

        vec3 A = pbc;
        vec3 C = reflect(A, normalize(cross(pab, pca)));
        vec3 B = reflect(C, normalize(cross(pbc, pca)));

        vec3 n;

        

        vec3 p1 = bToC(A, B, C, vec3(.5, .0, .5));
        vec3 p2 = bToC(A, B, C, vec3(.5, .5, .0));
        n = normalize(cross(p1, p2));
        pReflect(p, n, 0.);

        if (subdivisions > 1) {

            

            A = reflect(A, n);
            B = p1;
            C = p2;

            

            p1 = bToC(A, B, C, vec3(.5, .0, .5));
            p2 = bToC(A, B, C, vec3(.5, .5, .0));
            n = normalize(cross(p1, p2));
            pReflect(p, n, 0.);


            

            p2 = bToC(A, B, C, vec3(.0, .5, .5));
            p1 = bToC(A, B, C, vec3(.5, .5, .0));
            n = normalize(cross(p1, p2));
            pReflect(p, n, 0.);
        }
    }

    return p;
}

vec3 pRoll(inout vec3 p) {
    
    float s = 5.;
    float d = 0.01;
    float a = sin(mat_time * s) * d;
    float b = cos(mat_time * s) * d;
    pR(p.xy, a);
    pR(p.xz, a + b);
    pR(p.yz, b);
    return p;
}

vec3 lerp(vec3 a, vec3 b, float s) {
    return a + (b - a) * s;
}

float face(vec3 p) {
    
    vec3 rn = normalize(lerp(pca, vec3(0,0,1), 0.5));
    p = reflect(p, rn);
    return  min(
        fPlane(p, vec3(0,0,-1), -1.4),
        length(p + vec3(0,0,1.4)) - 0.02
    );
}

vec3 planeNormal(vec3 p) {
    
    vec3 rn = normalize(lerp(pca, vec3(0,0,1), 0.5));
    return reflect(p, rn);
}



 #define t1 mat_time*1.5
 #define t2 mat_time/2.
 #define t3 mat_spin_time/2.
 #define t4 mat_spin_time/2.
 #define t5 mat_time/8.
 #define t6 mat_time/16.


float inner(vec3 p) {
    p += vec3(0.,0.,2.);
    pR(p.xy, t1);
    pR(p.zy, t2);
    return fBox(p, vec3(.5,.1,.2));
}

float exampleModelC(vec3 p) {
    pR(p.xy, t3);
    pR(p.yz, t4);
     pModIcosahedron(p, 2);
     pR(p.xy, t5);
     pR(p.yz, t6);
    pModIcosahedron(p, 1);
    p = planeNormal(p) * mat_fov;
    float b = inner(p);
    return b;
}

float exampleModel(vec3 p) {
    
    return exampleModelC(p);
}

vec3 doBackground(vec3 rayVec) {
    return vec3(.13) * mat_background;
}




float MAX_TRACE_DISTANCE = 200.0 * mat_edge;           
const float INTERSECTION_PRECISION = 0.001   ;     
int NUM_OF_TRACE_STEPS = mat_iterations;




vec2 opU( vec2 d1, vec2 d2 ){

    return (d1.x<d2.x) ? d1 : d2;

}





vec2 map( vec3 p ){
    vec2 res = vec2(exampleModel(p) ,1.);
    return res;
}



vec2 calcIntersection( in vec3 ro, in vec3 rd ){


    float h =  INTERSECTION_PRECISION*2.0;
    float t = 0.0;
    float res = -1.0;
    float id = -1.;

    for( int i=0; i< NUM_OF_TRACE_STEPS ; i++ ){

        if( h < INTERSECTION_PRECISION || t > MAX_TRACE_DISTANCE ) break;
        vec2 m = map( ro+rd*t );
        h = m.x;
        t += h;
        id = m.y;

    }

    if( t < MAX_TRACE_DISTANCE ) res = t;
    if( t > MAX_TRACE_DISTANCE ) id =-1.0;

    return vec2( res , id );

}





mat3 calcLookAtMatrix( in vec3 ro, in vec3 ta, in float roll )
{
    vec3 ww = normalize( ta - ro );
    vec3 uu = normalize( cross(ww,vec3(sin(roll),cos(roll),0.0) ) );
    vec3 vv = normalize( cross(uu,ww));
    return mat3( uu, vv, ww );
}

void doCamera(out vec3 camPos, out vec3 camTar, in float time, in vec2 mouse) {

    camPos = vec3(0.0,0.0,22.0);

    camTar = vec3(0);
}




vec3 calcNormal( in vec3 pos ){

    vec3 eps = vec3( 0.001, 0.0, 0.0 );
    vec3 nor = vec3(
        map(pos+eps.xyy).x - map(pos-eps.xyy).x,
        map(pos+eps.yxy).x - map(pos-eps.yxy).x,
        map(pos+eps.yyx).x - map(pos-eps.yyx).x );
    return normalize(nor);
}




vec3 render( vec2 res , vec3 ro , vec3 rd ){


  vec3 color = doBackground(rd);

    if (res.y == 2.) {
        return vec3(0.987,0.257,1.000);
    }

  if( res.y > -.5 ){

    vec3 pos = ro + rd * res.x;
    vec3 norm = calcNormal( pos );
    vec3 ref = reflect(rd, norm);
    color = norm * 0.5 + 0.5;
    float split = 1. - dot(pos, norm);
    float light = dot(ref, normalize(vec3(0,1,1)));
    light *= clamp((1.-split), 0., 1.);
    color *= split * 0.8 * mat_glow;
    color = clamp(color, vec3(0), vec3(1));
    color += light * 0.5;
    

  }

  return color;
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    initIcosahedron();

    vec2 p = uv;
    

    vec2 m = vec2(1.);
    vec3 ro = vec3( 0., 0., 2.);
    vec3 ta = vec3( 0. , 0. , 0. );


    
    doCamera(ro, ta, mat_time, m);

    
    mat3 camMat = calcLookAtMatrix( ro, ta, 0.0 );  

    
    vec3 rd = normalize( camMat * vec3(p.xy,20.) ) * mat_shell_scale; 
    vec2 res = calcIntersection( ro , rd  ) * mat_height;

    vec3 color = render( res , ro , rd );

    out_color = vec4(color,1.0);


    
    if (mat_luma_to_alpha && mat_luma_mode == 0) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
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
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 4.) - mat_luma_threshold * 4.;
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
