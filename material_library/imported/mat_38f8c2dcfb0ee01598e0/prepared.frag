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
uniform vec4 uMMParam007; // native input: mat_water_level
float mat_water_level = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_water_edge_level
float mat_water_edge_level = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_beach_level
float mat_beach_level = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_beach_edge_level
float mat_beach_edge_level = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_grass_level
float mat_grass_level = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_terrain_level
float mat_terrain_level = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_smooth
float mat_smooth = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_smooth2
float mat_smooth2 = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_speed
float mat_speed = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_reverse
bool mat_reverse = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: mat_offset
float mat_offset = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_offset_scale
float mat_offset_scale = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_strob
float mat_strob = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_restart
int mat_restart = int(round(uMMParam021.x));
uniform vec4 uMMParam022; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_luma_threshold
float mat_luma_threshold = uMMParam024.x;
const int mat_luma_mode = 0;
#define mat_luma_mode_IS_Before_Color_Controls
uniform vec4 uMMParam026; // native input: mat_brightness
float mat_brightness = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_contrast
float mat_contrast = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_saturation
float mat_saturation = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_hue_shift
float mat_hue_shift = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_invert
bool mat_invert = uMMParam030.x > 0.5;
uniform vec4 uMMParam031; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam031.x > 0.5;
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
    uv *= mat_scale * 0.75;

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







































#define TRIANGLE_PATTERN


#define GRASS


mat2 rot2(in float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }



float hash21(vec2 p){ return fract(sin(dot(p, vec2(141.13, 289.97)))*43758.5453); }



vec2 hash22(vec2 p) {

    
    
    
    
    float n = sin(dot(p, vec2(41, 289)));
    

    
    p = fract(vec2(262144, 32768)*n);
    return sin(p*6.2831853 + mat_time);

}



float n2D3G( in vec2 p ){

    vec2 i = floor(p); p -= i;

    vec4 v;
    v.x = dot(hash22(i), p);
    v.y = dot(hash22(i + vec2(1, 0)), p - vec2(1, 0));
    v.z = dot(hash22(i + vec2(0, 1)), p - vec2(0, 1));
    v.w = dot(hash22(i + 1.), p - 1.);

#if 1
    
    p = p*p*p*(p*(p*6. - 15.) + 10.);
#else
    
    p = p*p*(3. - 2.*p);
#endif

    return mix(mix(v.x, v.y, p.x), mix(v.z, v.w, p.x), p.y);
    
}



float isoFunction(in vec2 p){ return n2D3G(p/4. + .07); }



float distLine(vec2 a, vec2 b){


    b = a - b;
    float h = clamp(dot(a, b)/dot(b, b), 0., 1.);
    return length(a - b*h);
}



float distEdge(vec2 a, vec2 b){

    



    return dot((a + b)*.5, normalize((b - a).yx*vec2(-1, 1)) );
    

}




vec2 inter(in vec2 p1, in vec2 p2, float v1, float v2, float isovalue){

    
    
    
    
    
    
    
    
    
    return mix(p1, p2, (isovalue - v1)/(v2 - v1)*.75 + .25/2.);

    
    

    
    
    
}


int isoLine(vec3 n3, vec2 ip0, vec2 ip1, vec2 ip2, float isovalue, float i,
          inout vec2 p0, inout vec2 p1){


    
    p0 = vec2(1e5), p1 = vec2(1e5);

    
    
    
    
    
    
    

    
    
    
    
    int iTh = 0;
    
    
    if(n3.x>isovalue) iTh += 4;
    if(n3.y>isovalue) iTh += 2;
    if(n3.z>isovalue) iTh += 1;


    
    
    if(iTh == 1 || iTh == 6){ 

        p0 = inter(ip1, ip2, n3.y, n3.z, isovalue); 
        p1 = inter(ip2, ip0, n3.z, n3.x, isovalue); 

    }
    else if(iTh == 2 || iTh == 5){ 

        p0 = inter(ip0, ip1, n3.x, n3.y, isovalue); 
        p1 = inter(ip1, ip2, n3.y, n3.z, isovalue); 

    }
    else if(iTh == 3 || iTh == 4){ 

        p0 = inter(ip0, ip1, n3.x, n3.y, isovalue); 
        p1 = inter(ip2, ip0, n3.z, n3.x, isovalue); 

    }


    
    
    
    if(iTh>=4 && iTh<=6){ vec2 tmp = p0; p0 = p1; p1 = tmp; }

    
    
    
    if(i == 0.){ vec2 tmp = p0; p0 = p1; p1 = tmp; }


    
    return iTh;


}













vec3 simplexContour(vec2 p){



    
    const float gSc = 8.;
    p *= gSc;


    
    vec2 oP = p;

    
    p += vec2(n2D3G(p*3.5), n2D3G(p*3.5 + 7.3))*.015;



    

    vec2 s = floor(p + (p.x + p.y)*.36602540378); 

    p -= s - (s.x + s.y)*.211324865; 

    
    float i = p.x < p.y? 1. : 0.; 
    vec2 ioffs = vec2(1. - i, i);

    
    vec2 ip0 = vec2(0), ip1 = ioffs - .2113248654, ip2 = vec2(.577350269);


    
    vec2 ctr = (ip0 + ip1 + ip2)/3.; 
    
    ip0 -= ctr; ip1 -= ctr; ip2 -= ctr; p -= ctr;



    
    
    vec3 n3;
    n3.x = isoFunction(s);
    n3.y = isoFunction(s + ioffs);
    n3.z = isoFunction(s + 1.);


    
    float d = 1e5, d2 = 1e5, d3 = 1e5, d4 = 1e5, d5 = 1e5;


    
    float isovalue = 0.;

    
    
    vec2 p0, p1;

    
    int iTh = isoLine(n3, ip0, ip1, ip2, isovalue, i, p0, p1);

    
    
    d = min(d, distEdge(p - p0, p - p1));



    

    
    if(iTh == 7){ 

        
        
                  

        
        d = 0.;
    }



    
    d3 = min(d3, distLine((p - p0), (p - p1)));
    
    d4 = min(d4, min(length(p - p0), length(p - p1)));





    
    
    
    float tri = min(min(distLine(p - ip0, p - ip1), distLine(p - ip1, p - ip2)),
                  distLine(p - ip2, p - ip0)) / mat_smooth2;

    
    d5 = min(d5, tri);


    
    
    d5 = min(d5, length(p) - .02);

    
    #ifdef TRIANGULATE_CONTOURS
    vec2 oldP0 = p0;
    vec2 oldP1 = p1;

    
    float td = (iTh>0 && iTh<7)? 1. : 0.;

    
    if(iTh==3 || iTh==5 || iTh==6){

        
        vec2 pt = p0;
        if(i==1.) pt = p1;
        d5 = min(d5, distLine((p - pt), (p - ip0)));
        d5 = min(d5, distLine((p - pt), (p - ip1)));
        d5 = min(d5, distLine((p - pt), (p - ip2)));
    }
    #endif
    


    
    isovalue = -.15;

    
    int iTh2 = isoLine(n3, ip0, ip1, ip2, isovalue, i, p0, p1);

    
    
    d2 = min(d2, distEdge(p - p0, p - p1));

    
    float oldD2 = d2;

    if(iTh2 == 7) d2 = 0.;
    if(iTh == 7) d2 = 1e5;
    d2 = max(d2, -d);


    
    d3 = min(d3, distLine((p - p0), (p - p1)));
    
    d4 = min(d4, min(length(p - p0), length(p - p1)));

    d4 -= .075;
    d3 -= .0125;

    
    #ifdef TRIANGULATE_CONTOURS
    

    
    

    
    float td2 = (iTh2>0 && iTh2<7)? 1. : 0.;


    if(td==1. && td2==1.){
        
        

        
        d5 = min(d5, distLine(p - p0, p - oldP0));
        d5 = min(d5, distLine(p - p0, p - oldP1));
        d5 = min(d5, distLine(p - p1, p - oldP1));

        
        if(oldD2>0.){
            vec2 pt = p0;
            if(i==1.) pt = p1;
            d5 = min(d5, distLine(p - pt, p - ip0));
            d5 = min(d5, distLine(p - pt, p - ip1));
            d5 = min(d5, distLine(p - pt, p - ip2));
        }
    }
    else if(td==1. && td2==0.){

        

        
        vec2 pt = oldP0;
        if(i==1.) pt = oldP1;
        d5 = min(d5, distLine(p - pt, p - ip0));
        d5 = min(d5, distLine(p - pt, p - ip1));
        d5 = min(d5, distLine(p - pt, p - ip2));
    }
    else if(td==0. && td2==1.){

        

        
        vec2 pt = p0;
        if(i==1.) pt = p1;
        d5 = min(d5, distLine(p - pt, p - ip0));
        d5 = min(d5, distLine(p - pt, p - ip1));
        d5 = min(d5, distLine(p - pt, p - ip2));
    }

    #endif
    


    
    
    d /= gSc;
    d2 /= gSc;
    d3 /= gSc;
    d4 /= gSc;
    d5 /= gSc;



    

    
    vec3 col = vec3(1, .85, .6);

    
    float sf = .004 * mat_smooth;

    
    if(d>0. && d2>0.) col = mat_water_level*vec3(1, 1.8, 3)*.45;
     
    if(d>0.) col = mix(col, mat_water_edge_level*vec3(1, 1.85, 3)*.3, (1. - smoothstep(0., sf, d2 - .012)));

    
    col = mix(col, mat_beach_level*vec3(1.1, .85, .6),  (1. - smoothstep(0., sf, d2)));
    
    col = mix(col, mat_beach_edge_level*vec3(1.5, .9, .6)*.6, (1. - smoothstep(0., sf, d - .012)));

    #ifdef GRASS
    
    col = mix(col, mat_grass_level*vec3(1, .8, .6)*vec3(.7, 1., .75)*.95, (1. - smoothstep(0., sf, d)));
    #else
    
    col = mix(col, mat_terrain_level*vec3(1, .82, .6)*.95, (1. - smoothstep(0., sf, d)));
    #endif




    
    if(d2>0.) col *= (abs(dot(n3, vec3(1)))*1.25 + 1.25)/2.;
    else col *= max(2. - (dot(n3, vec3(1)) + 1.45)/1.25, 0.);

    
    
    


    
    #ifdef TRIANGULATE_CONTOURS
    
    #endif
    

    
    #ifdef TRIANGLE_PATTERN
    
    float pat = abs(fract(tri*12.5 + .4) - .5)*2.;
    col *= pat*.425 + .75;
    #endif
    




    
    col = mix(col, vec3(0), (1. - smoothstep(0., sf, d5))*.95);



    
    col = mix(col, vec3(0), (1. - smoothstep(0., sf, d3)));


    
    col = mix(col, vec3(0), (1. - smoothstep(0., sf, d4)));
    col = mix(col, vec3(1), (1. - smoothstep(0., sf, d4 + .005)));



    
    
    
    
    
    
    
    
    
    
    
    
    
    
    vec2 q = oP*1.5;
    
    
    col = min(col, 1.);
    
    float gr = sqrt(dot(col, vec3(.299, .587, .114)))*1.25;
    
    float ns = (n2D3G(q*4.*vec2(1./3., 3))*.64 + n2D3G(q*8.*vec2(1./3., 3))*.34)*.5 + .5;
    
    ns = gr - ns;
    
    
    q *= rot2(3.14159/3.);
    float ns2 = (n2D3G(q*4.*vec2(1./3., 3))*.64 + n2D3G(q*8.*vec2(1./3., 3))*.34)*.5 + .5;
    ns2 = gr - ns2;
    
    
    
    ns = smoothstep(0., 1., min(ns, ns2)); 
    
    
    col = mix(col, col*(ns + .35), .4);
    
    
    
    
    
    
    


    










    
    
    
    


    
    return col;


}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    
    vec2 p = rot2(3.14159/12.)*uv + vec2(.8660254, .5)*mat_time/16.;

    
    vec3 col = simplexContour(p);

    
    
    
    
    

    
    out_color = vec4(sqrt(max(col, 0.)), 1);


    
    if (mat_luma_to_alpha && mat_luma_mode == 0) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity) - mat_luma_threshold * 4. - 1.;
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
        out_color.a = mat_luma(out_color * mat_luma_sensitivity);
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
