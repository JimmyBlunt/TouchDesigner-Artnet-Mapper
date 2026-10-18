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
uniform vec4 uMMParam008; // native input: mat_cube_scale
float mat_cube_scale = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_size
float mat_size = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_min_size
float mat_min_size = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_pad_factor
float mat_pad_factor = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_break_chance
float mat_break_chance = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_cycle
float mat_cycle = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_seed
float mat_seed = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_iterations
int mat_iterations = int(round(uMMParam015.x));
uniform vec4 uMMParam016; // native input: mat_explode_amp
float mat_explode_amp = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_explode_factor1
float mat_explode_factor1 = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_explode_factor2
float mat_explode_factor2 = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_explode_mod1
float mat_explode_mod1 = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_explode_mod2
float mat_explode_mod2 = uMMParam020.x;
uniform vec4 uMMParam021; // native input: mat_explode_mod3
float mat_explode_mod3 = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_explode_mod4
float mat_explode_mod4 = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_explode_animate
bool mat_explode_animate = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_explode_speed
float mat_explode_speed = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_explode_bpm_sync
bool mat_explode_bpm_sync = uMMParam025.x > 0.5;
uniform vec4 uMMParam026; // native input: mat_explode_reverse
bool mat_explode_reverse = uMMParam026.x > 0.5;
uniform vec4 uMMParam027; // native input: mat_explode_offset
float mat_explode_offset = uMMParam027.x;
uniform vec4 uMMParam028; // native input: mat_explode_offset_scale
float mat_explode_offset_scale = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_explode_strob
float mat_explode_strob = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_explode_restart
int mat_explode_restart = int(round(uMMParam030.x));
uniform vec4 uMMParam031; // native input: mat_rot_speed
float mat_rot_speed = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_rot_bpm_sync
bool mat_rot_bpm_sync = uMMParam032.x > 0.5;
uniform vec4 uMMParam033; // native input: mat_rot_reverse
bool mat_rot_reverse = uMMParam033.x > 0.5;
uniform vec4 uMMParam034; // native input: mat_rot_offset
float mat_rot_offset = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_rot_offset_scale
float mat_rot_offset_scale = uMMParam035.x;
uniform vec4 uMMParam036; // native input: mat_rot_strob
float mat_rot_strob = uMMParam036.x;
uniform vec4 uMMParam037; // native input: mat_rot_restart
int mat_rot_restart = int(round(uMMParam037.x));
uniform vec4 uMMParam038; // native input: mat_lighting
float mat_lighting = uMMParam038.x;
uniform vec4 uMMParam039; // native input: mat_shadow
float mat_shadow = uMMParam039.x;
uniform vec4 uMMParam040; // native input: mat_brightness
float mat_brightness = uMMParam040.x;
uniform vec4 uMMParam041; // native input: mat_contrast
float mat_contrast = uMMParam041.x;
uniform vec4 uMMParam042; // native input: mat_saturation
float mat_saturation = uMMParam042.x;
uniform vec4 uMMParam043; // native input: mat_hue_shift
float mat_hue_shift = uMMParam043.x;
uniform vec4 uMMParam044; // native input: mat_invert
bool mat_invert = uMMParam044.x > 0.5;
uniform vec4 uMMParam045; // native input: mat_back_color
vec4 mat_back_color = uMMParam045;
uniform vec4 uMMParam046; // native input: mat_back_grad
bool mat_back_grad = uMMParam046.x > 0.5;
uniform vec4 uMMParam047; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam047.x > 0.5;
float mat_explode_time_source = uTDTime * (mat_explode_speed);
float mat_rot_time_source = uTDTime * (mat_rot_speed);

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

float mat_explode_time = mat_explode_time_source - mat_explode_offset * 4. * mat_explode_offset_scale;
float mat_rot_time = mat_rot_time_source - mat_rot_offset * 2. * PI * mat_rot_offset_scale;

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
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

    vec2 uv_shift = mat_shift_amount * mat_shift_scale / 2.;
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














float MDIST = 350.0;
float STEPS = 128.0;
#define rot(a) mat2(cos(a),sin(a),-sin(a),cos(a))
#define pmod(p,x) (mod(p,x)-0.5*(x))


vec3 pal( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d ){
    return a + b*cos(2.*PI*(c*t+d));
}
float h21 (vec2 a) {
    return fract(sin(dot(a.xy,vec2(12.9898,78.233)))*43758.5453123);
}
float h11 (float a) {
    return fract(sin((a)*12.9898)*43758.5453123);
}
float box(vec3 p, vec3 b){
    vec3 d = abs(p)-b;
    return max(d.x,max(d.y,d.z));
}

float ebox( vec3 p, vec3 b ){
  vec3 q = abs(p) - b;
  return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0);
}

float swave(float x, float a){
    return (sin(mat_explode_mod4*x*PI/3.-PI/2. + (mat_explode_mod3 - 1.))/sqrt(a*a+sin(x*PI/3.-PI/2.)*sin(x*PI/3.-PI/2.)) / mat_explode_factor2 +1./sqrt(a*a+1.) * mat_explode_factor1)*0.5;
}
vec3 rdg = vec3(0);
float nsdf = 0.;
vec2 blocks(vec3 p, vec3 scl, vec3 rd){
    vec3 po = p;
    float t = mat_explode_time;

    if (!mat_explode_animate) {
        t = 0.;
    }

    bvec3 isEdge = bvec3(true);
    vec3 dMin = vec3(-0.5) * scl;
    vec3 dMax = vec3(0.5) * scl;
    vec3 dMini = dMin;
    vec3 dMaxi = dMax;

    float id = 0.;
    float seed = floor(t/4.);

    float MIN_SIZE = 0.5 * mat_min_size;
    float ITERS = float(mat_iterations);
    float PAD_FACTOR = 1.01 * mat_pad_factor;
    float BREAK_CHANCE = 0.2 * mat_break_chance;

    vec3 dim = dMax - dMin;
    
    for (float i = 0.; i < ITERS; i++) {

        vec3 divHash = vec3(
            h21( vec2( i + id, seed )),
            h21( vec2( i + id + 2.44, seed )),
            h21( vec2( i + id + 7.83, seed ))
        );
        if(i==0.0){
        divHash = vec3(0.49,0.5,.51) * mat_cycle;
        }
        if(i>0.){
            vec3 center = -(dMin + dMax)/2.0;

            vec3 cs = vec3(0.3) * (mat_seed + 1.);
            divHash = clamp(divHash,vec3(cs*sign(center)),vec3(1.0-cs*sign(-center)));

        }
        vec3 divide = divHash * dim + dMin;
        divide = clamp(divide, dMin + MIN_SIZE * PAD_FACTOR , dMax - MIN_SIZE * PAD_FACTOR );
        vec3 minAxis = min(abs(dMin - divide), abs(dMax - divide));

        float minSize = min( minAxis.x, min( minAxis.y, minAxis.z ) );
        bool smallEnough = minSize < MIN_SIZE;

        bool willBreak = false;
        if (i  > 0. && h11( id ) < BREAK_CHANCE ) { willBreak = true; }
        if (smallEnough && i  > 0.) { willBreak = true; }
        if( willBreak ) {
            break;
        }

        dMax = mix( dMax, divide, step( p, divide ));
        dMin = mix( divide, dMin, step( p, divide ));

        float pad = 0.01;
        if(dMaxi.x>dMax.x+pad&&dMini.x<dMin.x-pad)isEdge.x=false;
        if(dMaxi.y>dMax.y+pad&&dMini.y<dMin.y-pad)isEdge.y=false;
        if(dMaxi.z>dMax.z+pad&&dMini.z<dMin.z-pad)isEdge.z=false;

        vec3 diff = mix( -divide, divide, step( p, divide));
        id = length(diff + 1.0);

        dim = dMax - dMin;
    }
    float volume = dim.x*dim.y*dim.z;
    vec3 center = (dMin + dMax)/2.0;
    float b = 0.;



    if(any(isEdge)) {
        float expand;

        
        
        
        
        


        expand = (1.0+(3.0-h11(id)*3.)*swave(t*3.0+h11(id)*1.5 * mat_explode_mod2,0.17 * mat_explode_mod1)) * mat_explode_amp;


        if(isEdge.x){
        center.x*=expand;
        }
        else if(isEdge.y){
        center.y*=expand;
        }
        else if(isEdge.z){
        center.z*=expand;
        }
    }
    vec3 edgeAxis = mix(dMin, dMax, step(0.0, rd));
    vec3 dAxis = abs(p - edgeAxis) / (abs(rd) + 1E-4);
    float dEdge = min(dAxis.x,min(dAxis.y,dAxis.z));
    b= dEdge;

    vec3 d = abs(center);
    dim-=0.4 / mat_size;
    float a = ebox(p-center,dim*0.5)-0.2;

    if(!any(isEdge)){
        a=b;

        nsdf =5.;
    }
    else nsdf = a;
    a = min(a, b);

    id = h11(id)*1000.0;

    return vec2(a,id);
}

vec3 map(vec3 p){
    float t = mat_rot_time;
    vec3 po = p;
    vec2 a = vec2(1);

    vec3 scl = vec3(10.) * mat_cube_scale;
    vec3 rd2 = rdg;

    p.xz*=rot(t);
    rd2.xz*=rot(t);
    p.xy*=rot(PI/4.);
    rd2.xy*=rot(PI/4.);
    a = blocks(p,scl,rd2)+0.01;

    a.x = max(box(p,vec3(scl*2.0)),a.x);

    return vec3(a,nsdf);
}
vec3 norm(vec3 p){
    vec2 e = vec2(0.01,0.);
    return normalize(map(p).x-vec3(
    map(p-e.xyy).x,
    map(p-e.yxy).x,
    map(p-e.yyx).x));
}



vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    vec3 col = vec3(0);
    vec3 ro = vec3(0,3.5,-20)*2.;

    vec2 orbit = mat_orbit;

    orbit += vec2(0.5);
    orbit.y = 1.-orbit.y;
    orbit -= vec2(0.5);

    ro.yz*=rot(2.0*orbit.y);
    ro.zx*=rot(-7.0*orbit.x);

    ro.xz*=rot(-PI/4.);
    vec3 lk = vec3(0,0.,0);
    vec3 f = normalize(lk-ro);
    vec3 r = normalize(cross(vec3(0,1,0),f));
    vec3 rd = normalize(f*(0.99)+uv.x*r+uv.y*cross(f,r));
    rdg = rd;
    vec3 p = ro;
    float dO = 0.;
    vec3 d = vec3(0);
    bool hit = false;
    for(float i = 0.; i<STEPS; i++){
        p = ro+rd*dO;
        d = map(p);
        dO+=d.x;
        if(abs(d.x)<0.0001||i==STEPS-1.){
            hit = true;
            break;
        }
        if(d.x>MDIST){
            dO=MDIST;
            break;
        }
    }
    if(hit){
        vec3 ld = normalize(vec3(0.,1.,0));
        vec3 n = norm(p);
        vec3 r = reflect(rd,n);
        vec3 e = vec3(0.5);
        vec3 al = pal(fract(d.y)*0.8-0.15,e*1.4,e,e*2.0,vec3(0,0.33,0.66)) * mat_lighting;
        col = al;


        float shadow = 1. * 1./mat_shadow;

    #ifdef USE_SHADOWS
        rdg = ld;
        for(float h = 0.09; h<10.0;){
            vec3 dd = map(p+ld*h+n*0.2);
            if(dd.x<0.001){shadow = 0.3; break;}
            
            h+=dd.x;
        }
    #endif

        
        float spec = length(sin(r*5.)*.5+.5)/sqrt(3.);
        float fres = 1.-abs(dot(rd,n))*0.9;

        float diff = length(sin(n*2.)*.5+.65)/sqrt(3.);

        #define AO(a,n,p) smoothstep(-a,a,map(p+n*a).z)
        float ao = AO(0.3,n,p)*AO(.5,n,p)*AO(.9,n,p);
        col = al*diff+pow(spec,5.0)*fres*shadow;
        col*=pow(ao,0.2);
        col*=max(shadow,0.7);
    }
    
    
    
    

    col = pow(col,vec3(0.9));

    out_color = vec4(col,1.0);

    
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

    vec4 back_color = mat_back_color;
    if (mat_back_grad) {
        back_color *= (1.0-length(uv)*0.5);
    }
    out_color = mix(out_color,back_color,pow(clamp(dO/MDIST,0.,1.),2.0));

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
