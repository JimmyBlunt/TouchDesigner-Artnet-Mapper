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
uniform vec4 uMMParam008; // native input: mat_distort
float mat_distort = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_height
float mat_height = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_iterations
int mat_iterations = int(round(uMMParam010.x));
uniform vec4 uMMParam011; // native input: mat_speed
float mat_speed = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam012.x > 0.5;
uniform vec4 uMMParam013; // native input: mat_reverse
bool mat_reverse = uMMParam013.x > 0.5;
uniform vec4 uMMParam014; // native input: mat_offset
float mat_offset = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_offset_scale
float mat_offset_scale = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_strob
float mat_strob = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_restart
int mat_restart = int(round(uMMParam017.x));
uniform vec4 uMMParam018; // native input: mat_luma_to_alpha
bool mat_luma_to_alpha = uMMParam018.x > 0.5;
uniform vec4 uMMParam019; // native input: mat_luma_sensitivity
float mat_luma_sensitivity = uMMParam019.x;
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
    uv *= mat_scale;

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






















































#define ROW_OFFSET



#define SHAPE 2


#define FACE_DECO



#define DOUBLE_SPIRAL
















#if SHAPE == 2
#ifndef ROW_OFFSET
#define ROW_OFFSET
#endif
#endif

#ifdef ROW_OFFSET
#if SHAPE >= 1
const vec2 rDim = vec2(1, 2.*.8660254);
#else
const vec2 rDim = vec2(1, 2);
#endif
#else
const vec2 rDim = vec2(1, 2);
#endif


vec2 scale = vec2(1./8.);


#define FAR 20.



float objID;



mat2 rot2(in float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }


float hash21(vec2 p){

    








    

    
    
    return fract(sin(dot(p, vec2(27.617, 57.743)))*43758.5453);

}














float opExtrusion(in float sdf, in float pz, in float h){

    vec2 w = vec2( sdf, abs(pz) - h );
    return min(max(w.x, w.y), 0.) + length(max(w, 0.));

    





}

#if SHAPE == 2


float sHexS(in vec2 p, float r, in float sf){

      
      
      
      const vec3 k = vec3(.5, -.8660254, .57735); 

      
      p = abs(p);
      p -= 2.*min(dot(k.xy, p), 0.)*k.xy;

      r -= sf;
      
      
      
      
      return length(p - vec2(r, clamp(p.y, -k.z*r, k.z*r)))*sign(p.x - r) - sf;

}
#endif




float hm(in vec2 p){

     return (sin(6.2831*(p.y*2. + p.x) + mat_time*2.)*.5 + .5);

    
    
    
    
    

}


float sBoxS(in vec2 p, in vec2 b, in float sf){

  vec2 d = abs(p) - b + sf;
  return min(max(d.x, d.y), 0.) + length(max(d, 0.)) - sf;
}



vec2 gP;


float tempR;







vec4 blocks(vec3 q3){



    
    vec2 l = scale;
    vec2 s = scale*2.;
    #if SHAPE == 2 
    vec2 hSc = vec2(1);
    #elif SHAPE == 1 
    #ifdef ROW_OFFSET
    vec2 hSc = vec2(1);
    #endif
    #endif



    float minSc = min(scale.x, scale.y);

    
    float d = 1e5;
    
    vec2 p, ip;

    
    vec2 id = vec2(0);

    
    #ifdef ROW_OFFSET
    
    vec2[4] ps4 = vec2[4](vec2(-.25, .25), vec2(.25), vec2(.5, -.25), vec2(0, -.25));
    #else
    vec2[4] ps4 = vec2[4](vec2(-.25, .25), vec2(.25), vec2(.25, -.25), vec2(-.25));
    #endif

    float data = 0.; 

    int i;

    for(int i = 0; i<4; i++){


        
        p = q3.xy;
        ip = floor(p/s - ps4[i]); 

        
        vec2 idi = (ip + .5 + ps4[i])*s;

        p -= idi; 


        
        
        vec2 index = mod(idi, rDim.yx)/rDim.yx;

        
        
        float h = hm(index)*tempR*.1;


        #if SHAPE == 2
        
        float di2D = sHexS(p, minSc/1.732 - .0035, .015);
        #elif SHAPE == 1
        
        #ifdef ROW_OFFSET
        float di2D = length(p) - minSc/1.732 + .0035;
        #else
        float di2D = length(p) - l.x/2. + .0035;
        #endif
        #else
        
        float di2D = sBoxS(p, l/2. - .0035, .02);
        #endif



        #ifdef HOLES
        
        di2D = max(di2D, -(di2D + minSc/3.));
        #endif

        
        float di = opExtrusion(di2D, (q3.z + h - 1.), h + 1.);



        
        
        


        #ifdef RAISED
        
        di += di2D*.5*tempR;
        #endif

        #ifdef RIDGES
        
        di += smoothstep(-.5, .5, sin(di2D/minSc*6.2831*3.))*.01;
        #endif




        
        
        if(di<d){
            d = di;
            id = idi;
            
            data = di2D;

            gP = p;
        }

    }

    
    return vec4(d, id, data);
}







vec2 cMul(vec2 z, vec2 w){ return mat2(z, -z.y, z.x)*w; }

vec2 cInv(vec2 z){ return vec2(z.x, -z.y)/dot(z, z); }

vec2 cDiv(vec2 z, vec2 w){ return cMul(z, cInv(w)); }

vec2 cLog(vec2 z){ return vec2(log(length(z)), atan(z.y, z.x)); }





vec2 caTanh(vec2 z, float sc) {

    
    
    return cLog(cDiv(vec2(sc, 0) + z, vec2(sc, 0) - z));
}





vec4 gID;



float map(vec3 p){


    
    float fl = -p.z + .01;

    
    

    
    
    

    
    vec2 z = rot2(-sin(mat_time/3.)*.65)*p.xy; 
    
    
    const float sc = 1.5; 
    float r = min(length(z - vec2(sc, 0)), length(z - vec2(-sc, 0)));
    tempR = r;
    z = caTanh(-z, sc)/6.2831;


    #ifdef DOUBLE_SPIRAL
    vec2 z2 = rot2(-cos(mat_time/3.)*.65*2.)*p.xy;
    
    
    float sc2 = .75 * mat_distort;
    float r2 = min(length(z2.xy - vec2(sc2, 0)), length(z2.xy - vec2(-sc2, 0)));
    tempR = min(tempR, r2);
    z += caTanh(z2, sc2)/6.2831;
    #endif

    
    
    tempR = smoothstep(.1, .5, tempR) * mat_height;

    
    z.y = fract(z.y + mat_time*.1);
    
    z = cMul(rDim, z);

    
    

    
    p.xy = z;

    


    
    vec4 d4 = blocks(p);
    gID = d4; 


    
    objID = d4.x < fl? 0. : 1.;

    
    return min(d4.x, fl);

}


float trace(in vec3 ro, in vec3 rd){

    
    float t = 0., d;

    for(int i = 0; i<mat_iterations; i++){

        d = map(ro + rd*t);
        
        
        if(abs(d)<.001 || t>FAR) break; 

        t += d*.8;
    }

    return min(t, FAR);
}



vec3 getNormal(in vec3 p, float t) {
    const vec2 e = vec2(.001, 0);
    return normalize(vec3(map(p + e.xyy) - map(p - e.xyy), map(p + e.yxy) - map(p - e.yxy),
                          map(p + e.yyx) - map(p - e.yyx)));
}




float softShadow(vec3 ro, vec3 lp, vec3 n, float k){

    
    const int maxIterationsShad = 32;

    ro += n*.0015; 
    vec3 rd = lp - ro; 

    float shade = 1.;
    float t = 0.;
    float end = max(length(rd), .0001);
    
    rd /= end;

    
    
    for (int i = 0; i<maxIterationsShad; i++){

        float d = map(ro + rd*t);
        shade = min(shade, k*d/t);
        
        
        t += clamp(d, .01, .1);


        
        if (d<0. || t>end) break;
    }

    
    
    
    return max(shade, 0.);
}




float calcAO(vec3 p, vec3 n){

    float occ = 1.; 
    float ds = .01; 
    float k = .05/ds;  
    float dst = ds*2.; 

    for(int i = 0; i<5; i++){
        occ -= (dst - map(p + n*dst))*k;
        dst += ds;
        k *= .5;
    }

    return clamp(occ, 0., 1.);
}

vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    #ifdef ROW_OFFSET
    #if SHAPE >= 1
    scale *= vec2(2./1.732, 1);
    #endif
    #endif

    
    
    vec3 ro = vec3(0, -1, -2.2); 
    vec3 lk = ro + vec3(0, .1, .25); 

    
    vec3 lp = ro + vec3(-.5, 1, 1);

    
    float FOV = 1.333 * mat_fov; 
    vec3 fwd = normalize(lk-ro);
    vec3 rgt = normalize(vec3(fwd.z, 0., -fwd.x ));
    
    
    
    vec3 up = cross(fwd, rgt);
    
    
    vec3 rd = normalize(uv.x*rgt + uv.y*up + fwd/FOV);

    
    rd.xy *= rot2( sin(mat_time)/32. );



    
    float t = trace(ro, rd);

    
    vec4 svGID = gID;

    
    float svObjID = objID;

    
    float svTempR = tempR;

    
    vec2 svP = gP;


    
    vec3 col = vec3(0);

    
    if(t < FAR){


        
        vec3 sp = ro + rd*t;
        vec3 sn = getNormal(sp, t);

                
        vec3 ld = lp - sp;
        
        float lDist = max(length(ld), .001);

        
        ld /= lDist;


        
        float sh = softShadow(sp, lp, sn, 16.);
        float ao = calcAO(sp, sn); 

        
        float atten = 1./(1. + lDist*.05);

        
        float diff = max( dot(sn, ld), 0.);
        

        
        float spec = pow(max(dot(reflect(ld, sn), rd ), 0.), 32.);

        
        float fre = pow(clamp(1. - abs(dot(sn, rd))*.5, 0., 1.), 2.);

        
        
        
        float Schlick = pow( 1. - max(dot(rd, normalize(rd + ld)), 0.), 5.);
        float freS = mix(.15, 1., Schlick);  


        
        vec3 texCol = vec3(.6);
        
        if(svObjID<.5){

            
            vec2 index = mod(svGID.yz, rDim.yx)/rDim.yx;
            

            
            vec3 col1 = .5 + .45*cos(6.2831*index.y + vec3(0, 1, 2)*2.);
            vec3 col2 = .5 + .45*cos(6.2831*index.y + 3.14159/2.5 + vec3(0, 1, 2)*1.35);
            texCol = col1;
            
            
            
            


            
            
            
            
            #if 1
            float di2D = svGID.w;
            float tmp = map(sp - vec3(3./450., 0, 0)); 
            float di2DX = gID.w; 
            tmp = map(sp - vec3(0, 3./450., 0)); 
            float di2DY = gID.w; 
            
            

            vec3 dF = (vec3(di2DX, di2DY, 1e5) - di2D); 
            
            float sf = length(dF.xy); 
            #else
            
            float sf = fwidth(svGID.w);
            #endif


            #ifdef VERT_LINES
            
            #if SHAPE == 2
            const float aNum = 6.;
            vec2 z = rot2(3.14159/aNum)*svP;
            
            #else
            const float aNum = 4.;
            vec2 z = svP;
            #endif
            float a = mod(atan(z.x, z.y), 6.2831)/6.2831;
            a = (floor(a*aNum) + .5)/aNum;
            z *= rot2(a*6.2831);
            texCol = mix(texCol, vec3(0), (1. - smoothstep(0., sf, abs(z.x) - .001))*.95);
            #endif


            #ifdef FACE_DECO
            float rim = .04;
            #ifdef ROW_OFFSET
            #if SHAPE >= 1
            rim /= .8660254;
            #endif
            #endif
            texCol = mix(texCol, vec3(0), (1. - smoothstep(0., sf, svGID.w + rim))*.95);
            texCol = mix(texCol, col2, (1. - smoothstep(0., sf, svGID.w + rim + .005)));
            #endif


            
            float h = hm(index); 
            float lw = .0035;
            float dS = abs(svGID.w) - lw/2.; 
            texCol = mix(texCol, texCol/3., (1. - smoothstep(0., sf, dS)));
            dS = max(dS, abs(sp.z + h*.1*svTempR*2.) - lw/2.); 
            texCol = mix(texCol, vec3(0), (1. - smoothstep(0., sf, dS))*.95);


        }
        else {

            
            texCol = vec3(.05);
        }


        
        col = texCol*(diff*sh + .3 + vec3(.25, .5, 1)*fre*0. + vec3(1, .97, .92)*spec*freS*2.*sh);

        
        col *= ao*atten;


    }


    
    out_color = vec4(sqrt(max(col, 0.)), 1);


    
    if (mat_luma_to_alpha && mat_luma_mode == 0) {
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 2.) - mat_luma_threshold * 4. - 1.;
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
        out_color.a = mat_luma(out_color * mat_luma_sensitivity * 2.) - mat_luma_threshold * 4. - 1.;
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
