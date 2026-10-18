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
uniform vec4 uMMParam008; // native input: mat_pattern1
float mat_pattern1 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_pattern2
float mat_pattern2 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_thickness
float mat_thickness = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_lines
float mat_lines = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_shadow1
float mat_shadow1 = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_shadow2
float mat_shadow2 = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_ring
float mat_ring = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_ring_pattern
float mat_ring_pattern = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_ring_shadow
float mat_ring_shadow = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_shading1
float mat_shading1 = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_shading2
float mat_shading2 = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_shading3
float mat_shading3 = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_speed
float mat_speed = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam021.x > 0.5;
uniform vec4 uMMParam022; // native input: mat_reverse
bool mat_reverse = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_offset
float mat_offset = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_offset_scale
float mat_offset_scale = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_strob
float mat_strob = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_restart
int mat_restart = int(round(uMMParam026.x));
uniform vec4 uMMParam027; // native input: mat_brightness
float mat_brightness = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_contrast
float mat_contrast = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_saturation
float mat_saturation = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_hue_shift
float mat_hue_shift = uMMParam030.x;
uniform vec4 uMMParam031; // native input: mat_invert
bool mat_invert = uMMParam031.x > 0.5;
uniform vec4 uMMParam032; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam032.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);







































































































































































































































































































#extension GL_ARB_shader_bit_encoding: enable

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

float mat_time = (mat_time_source - mat_offset * 8. * mat_offset_scale) * 4.;

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
    uv *= mat_scale * 2.;

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






























































































#define TAU     6.28318531


mat2 rot2(in float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }




















float hash21(vec2 f){

    uvec2 p = floatBitsToUint(f);
    p = 1664525U*(p>>1U^p.yx);
    return float(1103515245U*(p.x^(p.y>>3U)))/float(0xffffffffU);
}

void swap(inout int a, inout int b){ int tmp = a; a = b; b = tmp; }









float floorSm(float x, float c) {

    float ix = floor(x); x -= ix;
    return (pow(x, c) - pow(1.- x, c))/2. + ix;
}


















#ifdef PENTAGON
const int N = 5;    
const int Q = 4;    
#else
const int N = 3;    
const int Q = 8;    
#endif

float count; 








vec3 initDomain(){

    
    
    
    

    
    
    
    
    
    
    

    
    
    
    
    

    






















    
    
    
    
    
    
    
    
    
    
    
    
    

    float piDivN = PI/float(N), piDivQ = piDivN + PI/float(Q) - PI/2.;

    
    vec2 trig1 = vec2(cos(piDivN), sin(piDivN));
    vec2 trig2 = vec2(cos(piDivQ), sin(piDivQ));

    
    
    
    float dist = trig1.x - trig2.x*trig1.y/trig2.y;
    float rad = length(vec2(dist, 0.) - trig1);

    float d = max(dist*dist - rad*rad, 0.);

    
    
    
    return vec3(dist, rad, 1)/sqrt(d);

    






}










vec2 transform(vec2 p, vec2 circ) {


    
    
    
    

    float ia = (floor(atan(p.x, p.y)/TAU*float(N)) + .5)/float(N);
    
    
    
    vec2 vert = rot2(ia*TAU)*vec2(0, circ.x);

    
    float rSq = circ.y*circ.y;

    
    
    
    
    
    vec2 pc = p - vert;
    float lSq = dot(pc, pc);

    
    
    
    if(lSq<rSq){

        p = pc*rSq/lSq + vert;

        
        
        p = rot2(TAU/float(N)*(count + float(Q)))*p;


        
        
        count++;

    }

    return p;
}







float sdBezier(vec2 pos, vec2 A, vec2 B, vec2 C){

    
    
    
    
    

    vec2 a = B - A;
    vec2 b = A - 2.0*B + C;
    vec2 c = a * 2.0;
    vec2 d = A - pos;

     
    
    float kk = 1./max(dot(b,b), 1e-6); 
    float kx = kk * dot(a,b);
    float ky = kk * (2.0*dot(a,a)+dot(d,b)) / 3.0;
    float kz = kk * dot(d,a);

    float res = 0.0;

    float p = ky - kx*kx;
    float p3 = p*p*p;
    float q = kx*(2.0*kx*kx - 3.0*ky) + kz;
    float h = q*q + 4.0*p3;

    if(h >= 0.0)
    {
        h = sqrt(h);
        vec2 x = (vec2(h, -h) - q) / 2.0;
        vec2 uv = sign(x)*pow(abs(x), vec2(1.0/3.0));
        float t = uv.x + uv.y - kx;
        t = clamp( t, 0.0, 1.0 );

        
        vec2 qos = d + (c + b*t)*t;
        res = length(qos);
    }
    else
    {
        float z = sqrt(-p);
        float v = acos( q/(p*z*2.0) ) / 3.0;
        float m = cos(v);
        float n = sin(v)*1.732050808;
        vec3 t = vec3(m + m, -n - m, n - m) * z - kx;
        t = clamp( t, 0.0, 1.0 );

        
        vec2 qos = d + (c + b*t.x)*t.x;
        float dis = dot(qos,qos);

        res = dis;

        qos = d + (c + b*t.y)*t.y;
        dis = dot(qos,qos);
        res = min(res,dis);

        qos = d + (c + b*t.z)*t.z;
        dis = dot(qos,qos);
        res = min(res,dis);

        res = sqrt( res );
    }

    return res;
}







float doSeg(vec2 p, vec4 a, vec4 b, float r){

    
    vec2 mid = (a.xy + b.xy)/2.; 

    
    
    float l = length(b.xy - a.xy)*1.732/6.; 

    
    
    
    
    
    if(abs(length(b.zw - a.zw))<.01) l = r;

    
    
    mid += (a.zw + b.zw)/2.*l;

    
    
    
    float b1 = sdBezier(p, a.xy, a.xy + a.zw*l, mid);
    float b2 = sdBezier(p, mid, b.xy + b.zw*l, b.xy);

    
    return min(b1, b2);
}





float Polygon(vec2 p, float vertices, float radius){

    float segmentAngle = TAU/vertices;

    float angleRadians = atan(p.x, p.y);
    float repeat = mod(angleRadians, segmentAngle) - segmentAngle/2.;
    float inradius = radius*cos(segmentAngle/2.);
    float circle = length(p);
    return cos(repeat)*circle - inradius;

}


vec2 mouseInversion(vec2 p){

    
    


    vec2 m = mat_orbit;
    
    
    if(length(m) < 1e-3) m += 1e-3;
    
    if(abs(m.x)>.98*.7071 || abs(m.y)>.98*.7071) m *= .98;

    
    
    
    float k = 1./dot(m, m);
    vec2 invCtr = k*m;
    float t = (k - 1.)/dot(p -invCtr, p - invCtr);
    p = t*p + (1. - t)*invCtr;
    p.x = -p.x; 

    return p;

}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec2 uv_orig = uv;



    
    
    
    


    #ifdef HALF_PLANE
    
    const float sc = 4.;
    uv.y += sc/2. + 1.;
    uv /= dot(uv, uv)/sc;
    uv.y -= 1.;
    #else
    
    
    uv *= 1.05;
    #endif

    
    vec2 p = uv;

    
    
    p = mouseInversion(p);

    
    p = rot2(mat_time/16.)*p;


    
    
    count = 0.;

    
    
    
    
    
    vec3 domInfo = initDomain();


    
    
    
    
    
    
    
    
    
    
    
    
    for(int i=0; i<24; i++){
        p = transform(p, domInfo.xy);
    }

    
    
    
    
    
    
    
    
    if(length(p)> 1.) p /= dot(p, p);


    
    
    
    p /= (domInfo.z);

    
    
    float sf = .015 * mat_shading1;
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    float shape = Polygon(p, float(N), .8 * mat_pattern2);


    
    vec2 vp[N];
    float ln[N];

    
    
    const int N2 = N*2;
    vec4 mp[N2];
    int shuff[N2];

    float vert = 1e5;
    vec2 v0 = vec2(0, 1);

    for(int i = 0; i<N; i++){
        vert = min(vert, length(p - v0) - .09);
        vp[i] = v0;
        v0 = rot2(TAU/float(N))*v0;
    }

    
    
    vec2 rp = rot2(float(count + 2.)*TAU/float(N))*(p);
    float angl = mod(atan(rp.x, rp.y), TAU)*float(N2)/TAU;
    float triSeg = (floorSm(angl, .1) + .5)/float(N2);
    vec3 oCol = .55 + .45*cos(triSeg*TAU + vec3(0, 1, 2));
    
    
    
    
    


    
    
    

    
    vec3 col = vec3(1, .99, .98);

    
    col = mix(col, vec3(0), 1. - smoothstep(0., sf, shape));
    col = mix(col, oCol, 1. - smoothstep(0., sf, shape + .04 * mat_shadow2));
    
    col = mix(col, vec3(0), 1. - smoothstep(0., sf, vert));
    


    
    
    float sLength = length(vp[0] - vp[1]);


    for(int i = 0; i<N; i++){

        
        shuff[i*2] = i*2;
        shuff[i*2 + 1] = i*2 + 1;

        
        
        
        vec2 mpi = mix(vp[i], vp[(i + 1)%N], .5 * mat_pattern1);
        vec2 tangenti = normalize(mpi - vp[i]);
        
        
        
        
        
        
        
        
        

        
        mp[i*2].xy = mpi - tangenti*sLength/6.;
        mp[i*2 + 1].xy = mpi + tangenti*sLength/6.;

        
        
        mp[i*2].zw = tangenti.yx*vec2(1, -1);
        mp[i*2 + 1].zw = tangenti.yx*vec2(1, -1);

    }


    
    
    
    
    
    
    
    
    
    for(int i = N2 - 1; i>0; i--){

        
        if(i >= N2) continue;

        
        float fi = float(i);

        
        
        
        float rs = hash21(vec2(count) + domInfo.xy + domInfo.z + fi/float(N2));

        
        
        
        int j = int(floor(rs*(fi + .9999)));
        swap(shuff[i], shuff[j]);

        

    }


    for(int i = 0; i<N; i++){

        
        int j = shuff[i*2], jp1 = shuff[i*2 + 1];

        
        
        
        
        
        
        float lnOff = sLength/4.; 
        ln[i] = doSeg(p, mp[j], mp[jp1], lnOff) - .105 * pow(mat_thickness,0.75);

        
        
        
        

    }


    
    
    float ringBlend = smoothstep(0., .235, abs(length(uv) - 1.) - .1);
    float pat2 = abs(fract(shape*16.) - .5)*2. - .05; 
    col = mix(col, vec3(0), ringBlend*(1. - smoothstep(0., .5, pat2))*.7 * mat_shading2);

     for(int i = 0; i<N; i++){

         
         

         
         pat2 = abs(fract(ln[i]*16. + .5) - .5)*2. - .05;
         pat2 = mix(1., 0., ringBlend*(1. - smoothstep(0., .5, pat2))*.7 * mat_lines);

         
         vec3 bgC = col;
         col = mix(col, vec3(0), (1. - smoothstep(0., sf*5., ln[i]))*.3 * mat_shadow1);
         col = mix(col, vec3(0), (1. - smoothstep(0., sf, ln[i])));
         col = mix(col, mix(bgC*1.2, vec3(1, .97, .26), .85)*pat2,
                   1. - smoothstep(0., sf, ln[i] + .04));
         col = mix(col, col*1.3, (1. - smoothstep(0., sf, ln[i] + .085)));

    }

    
    
    
    

    
    uv*= rot2(mat_time/16.);
    float lu = length(uv); 
    float ring = abs(lu - 1.)/mat_ring - .05; 

    
    float ang = atan(uv.x, uv.y)/TAU;
    float pat = abs(fract(ang*72.) - .5)*2. * mat_ring_pattern;
    pat = smoothstep(0., sf, pat - .125);

    

    col = mix(col, vec3(0), (1. - smoothstep(0., sf*5., ring-.01))*.6 * mat_ring_shadow);
    col = mix(col, vec3(0), (1. - smoothstep(0., sf/2., ring)));
    col = mix(col, vec3(1, .99, .98)*pat*.35 + .65, 1. - smoothstep(0., .005, ring + .02));
    ring = max(ring + .02, lu - .995);
    col = mix(col, vec3(.4)*pat, (1. - smoothstep(0., sf/3., ring)));


    
    col = mix(col, min( mix(col, vec3(1)*dot(col, vec3(.299, .587, .114) * mat_shading3),
                   min(lu*.7, 1.))*1.15, 1.),  1. - smoothstep(0., sf, 1.05 - lu));

    








    out_color = vec4(sqrt(max(col, 0.)), 1.);

    
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


    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
