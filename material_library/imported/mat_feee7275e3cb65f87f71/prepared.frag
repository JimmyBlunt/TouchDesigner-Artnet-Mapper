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

uniform vec4 uMMParam000; // native input: mouse
vec2 mouse = uMMParam000.xy;
uniform vec4 uMMParam001; // native input: mat_zoom
float mat_zoom = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_reverse
bool mat_reverse = uMMParam003.x > 0.5;
uniform vec4 uMMParam004; // native input: mat_speed
float mat_speed = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_offset
float mat_offset = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_strob
float mat_strob = uMMParam006.x;
float mat_time = uTDTime * (mat_speed);

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

float iTime = mat_time - mat_offset * 10;

float iGlobalTime = mat_time - mat_offset * 10;






uniform float startRandom;
uniform vec2 touch;



#define MODEL_ROTATION vec2(.3, .25)
#define CAMERA_ROTATION vec2(.5, .5)




#define MOUSE_CONTROL 1












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

float smax(float a, float b, float r) {
    float m = max(a, b);
    if ((-a < r) && (-b < r)) {
        return max(m, -(r - sqrt((r+a)*(r+a) + (r+b)*(r+b))));
    } else {
        return m;
    }
}









vec3 facePlane;
vec3 uPlane;
vec3 vPlane;

int Type=5;
vec3 nc;
vec3 pab;
vec3 pbc;
vec3 pca;

void initIcosahedron() {
    float cospin=cos(PI/float(Type)), scospin=sqrt(0.75-cospin*cospin);
    nc=vec3(-0.5,-cospin,scospin);
    pbc=vec3(scospin,0.,0.5);
    pca=vec3(0.,scospin,cospin);
    pbc=normalize(pbc); pca=normalize(pca);
  pab=vec3(0,0,1);

    facePlane = pca;
    uPlane = cross(vec3(1,0,0), facePlane);
    vPlane = vec3(1,0,0);
}

void pModIcosahedron(inout vec3 p) {
    p = abs(p);
    pReflect(p, nc, 0.);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.);
}







const float sqrt3 = 1.7320508075688772;
const float i3 = 0.5773502691896258;

const mat2 cart2hex = mat2(1, 0, i3, 2. * i3);
const mat2 hex2cart = mat2(1, 0, -.5, .5 * sqrt3);

#define PHI (1.618033988749895)
#define TAU 6.283185307179586

struct TriPoints {
  vec2 a;
    vec2 b;
    vec2 c;
    vec2 center;
    vec2 ab;
    vec2 bc;
    vec2 ca;
};

TriPoints closestTriPoints(vec2 p) {
    vec2 pTri = cart2hex * p;
    vec2 pi = floor(pTri);
    vec2 pf = fract(pTri);

    float split1 = step(pf.y, pf.x);
    float split2 = step(pf.x, pf.y);

    vec2 a = vec2(split1, 1);
    vec2 b = vec2(1, split2);
    vec2 c = vec2(0, 0);

    a += pi;
    b += pi;
    c += pi;

    a = hex2cart * a;
    b = hex2cart * b;
    c = hex2cart * c;

    vec2 center = (a + b + c) / 3.;

  vec2 ab = (a + b) / 2.;
    vec2 bc = (b + c) / 2.;
    vec2 ca = (c + a) / 2.;

    return TriPoints(a, b, c, center, ab, bc, ca);
}






struct TriPoints3D {
  vec3 a;
    vec3 b;
    vec3 c;
  vec3 center;
    vec3 ab;
    vec3 bc;
    vec3 ca;
};

vec3 intersection(vec3 n, vec3 planeNormal, float planeOffset) {
    float denominator = dot(planeNormal, n);
    float t = (dot(vec3(0), planeNormal ) + planeOffset) / -denominator;
    return n * t;
}





float faceRadius = 0.3819660112501051;


vec2 icosahedronFaceCoordinates(vec3 p) {
    vec3 pn = normalize(p);
    vec3 i = intersection(pn, facePlane, -1.);
    return vec2(dot(i, uPlane), dot(i, vPlane));
}


vec3 faceToSphere(vec2 facePoint) {
  return normalize(facePlane + (uPlane * facePoint.x) + (vPlane * facePoint.y));
}

TriPoints3D geodesicTriPoints(vec3 p, float subdivisions) {
    
    vec2 uv = icosahedronFaceCoordinates(p);

    
  float uvScale = subdivisions / faceRadius / 2.;
    TriPoints points = closestTriPoints(uv * uvScale);

    
    vec3 a = faceToSphere(points.a / uvScale);
    vec3 b = faceToSphere(points.b / uvScale);
    vec3 c = faceToSphere(points.c / uvScale);
    vec3 center = faceToSphere(points.center / uvScale);
    vec3 ab = faceToSphere(points.ab / uvScale);
    vec3 bc = faceToSphere(points.bc / uvScale);
    vec3 ca = faceToSphere(points.ca / uvScale);

    return TriPoints3D(a, b, c, center, ab, bc, ca);
}







vec3 pal( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d ) {
    return a + b*cos( 6.28318*(c*t+d) );
}

vec3 spectrum(float n) {
    return pal( n, vec3(0.5,0.5,0.5),vec3(0.5,0.5,0.5),vec3(1.0,1.0,1.0),vec3(0.0,0.33,0.67) );
}






mat3 sphericalMatrix(float theta, float phi) {
    float cx = cos(theta);
    float cy = cos(phi);
    float sx = sin(theta);
    float sy = sin(phi);
    return mat3(
        cy, -sy * -sx, -sy * cx,
        0, cx, sx,
        sy, cy * -sx, cy * cx
    );
}

mat3 mouseRotation(bool enable, vec2 xy) {
    if (enable) {
        

        vec2 mouse = touch.xy;

        if (mouse.x != 0. && mouse.y != 0.) {
            xy.x = mouse.x;
            xy.y = mouse.y;
        }
    }
    float rx, ry;

    rx = (xy.y + .5) * PI;
    ry = (-xy.x) * 2. * PI;

    return sphericalMatrix(rx, ry);
}

mat3 modelRotation() {
    mat3 m = mouseRotation(MOUSE_CONTROL==1, MODEL_ROTATION);
    return m;
}

mat3 cameraRotation() {
    mat3 m = mouseRotation(MOUSE_CONTROL==2, CAMERA_ROTATION);
    return m;
}






const float SCENE_DURATION = 6.;
const float CROSSFADE_DURATION = 2.;

struct HexSpec {
    float roundTop;
    float roundCorner;
  float height;
    float thickness;
    float gap;
};

HexSpec newHexSpec(float subdivisions) {
  return HexSpec(
        .05 / subdivisions,
        .1 / subdivisions,
        2.,
        2.,
        .005
    );
}



float animSubdivisions1() {
  return mix(2.4, 3.4, cos(iTime * PI) * .5 + .5);
}

HexSpec animHex1(vec3 hexCenter, float subdivisions) {
    HexSpec spec = newHexSpec(subdivisions);

    float offset = iTime * 3. * PI;
    offset -= subdivisions;
    float blend = dot(hexCenter, pca);
    blend = cos(blend * 30. + offset) * .5 + .5;
    spec.height = mix(1.75, 2., blend);

    spec.thickness = spec.height;

    return spec;
}



float animSubdivisions2() {
    return mix(1., 2.3, sin(iTime * PI/2.) * .5 + .5);
}


HexSpec animHex2(vec3 hexCenter, float subdivisions) {
    HexSpec spec = newHexSpec(subdivisions);

    float blend = hexCenter.y;
    spec.height = mix(1.6, 2., sin(blend * 10. + iTime * PI) * .5 + .5);

    spec.roundTop = .02 / subdivisions;
    spec.roundCorner = .09 / subdivisions;
    spec.thickness = spec.roundTop * 4.;
    spec.gap = .01;

    return spec;
}



float animSubdivisions3() {
  return 5.;
}

HexSpec animHex3(vec3 hexCenter, float subdivisions) {
    HexSpec spec = newHexSpec(subdivisions);

    float blend = acos(dot(hexCenter, pab)) * 10.;
    blend = cos(blend + iTime * PI) * .5 + .5;
    spec.gap = mix(.01, .4, blend) / subdivisions;

    spec.thickness = spec.roundTop * 2.;

  return spec;
}



float sineInOut(float t) {
  return -0.5 * (cos(PI * t) - 1.0);
}

float transitionValues(float a, float b, float c) {
    #ifdef LOOP
        #if LOOP == 1
            return a;
        #endif
        #if LOOP == 2
            return b;
        #endif
        #if LOOP == 3
            return c;
        #endif
    #endif
    float t = iTime / SCENE_DURATION;
    float scene = floor(mod(t, 3.));
    float blend = fract(t);
    float delay = (SCENE_DURATION - CROSSFADE_DURATION) / SCENE_DURATION;
    blend = max(blend - delay, 0.) / (1. - delay);
    blend = sineInOut(blend);
    float ab = mix(a, b, blend);
    float bc = mix(b, c, blend);
    float cd = mix(c, a, blend);
    float result = mix(ab, bc, min(scene, 1.));
    result = mix(result, cd, max(scene - 1., 0.));
    return result;
}

HexSpec transitionHexSpecs(HexSpec a, HexSpec b, HexSpec c) {
    float roundTop = transitionValues(a.roundTop, b.roundTop, c.roundTop);
    float roundCorner = transitionValues(a.roundCorner, b.roundCorner, c.roundCorner);
  float height = transitionValues(a.height, b.height, c.height);
    float thickness = transitionValues(a.thickness, b.thickness, c.thickness);
    float gap = transitionValues(a.gap, b.gap, c.gap);
  return HexSpec(roundTop, roundCorner, height, thickness, gap);
}






const vec3 FACE_COLOR = vec3(.9,.9,1.);
const vec3 BACK_COLOR = vec3(.1,.1,.15);
const vec3 BACKGROUND_COLOR = vec3(.0, .005, .03);

struct Model {
    float dist;
    vec3 albedo;
    float glow;
};

Model hexModel(
    vec3 p,
    vec3 hexCenter,
    vec3 edgeA,
    vec3 edgeB,
    HexSpec spec
) {
    float d;

    float edgeADist = dot(p, edgeA) + spec.gap;
    float edgeBDist = dot(p, edgeB) - spec.gap;
    float edgeDist = smax(edgeADist, -edgeBDist, spec.roundCorner);

    float outerDist = length(p) - spec.height;
    d = smax(edgeDist, outerDist, spec.roundTop);

    float innerDist = length(p) - spec.height + spec.thickness;
    d = smax(d, -innerDist, spec.roundTop);

    vec3 color;

    float faceBlend = (spec.height - length(p)) / spec.thickness;
    faceBlend = clamp(faceBlend, 0., 1.);
    color = mix(FACE_COLOR, BACK_COLOR, step(.5, faceBlend));

    vec3 edgeColor = spectrum(dot(hexCenter, pca) * 5. + length(p) + .8);
  float edgeBlend = smoothstep(-.04, -.005, edgeDist);
    color = mix(color, edgeColor, edgeBlend);

    return Model(d, color, edgeBlend);
}


Model opU( Model m1, Model m2 ){
    if (m1.dist < m2.dist) {
        return m1;
    } else {
        return m2;
    }
}

Model geodesicModel(vec3 p) {

    pModIcosahedron(p);

    float subdivisions = transitionValues(
        animSubdivisions1(),
        animSubdivisions2(),
        animSubdivisions3()
     );
  TriPoints3D points = geodesicTriPoints(p, subdivisions);

  vec3 edgeAB = normalize(cross(points.center, points.ab));
  vec3 edgeBC = normalize(cross(points.center, points.bc));
    vec3 edgeCA = normalize(cross(points.center, points.ca));

    Model model, part;
    HexSpec spec;

spec = transitionHexSpecs(
        animHex1(points.b, subdivisions),
        animHex2(points.b, subdivisions),
        animHex3(points.b, subdivisions)
    );
    part = hexModel(p, points.b, edgeAB, edgeBC, spec);
    model = part;

  spec = transitionHexSpecs(
        animHex1(points.c, subdivisions),
        animHex2(points.c, subdivisions),
        animHex3(points.c, subdivisions)
    );
    part = hexModel(p, points.c, edgeBC, edgeCA, spec);
    model = opU(model, part);

  spec = transitionHexSpecs(
        animHex1(points.a, subdivisions),
        animHex2(points.a, subdivisions),
        animHex3(points.a, subdivisions)
    );
    part = hexModel(p, points.a, edgeCA, edgeAB, spec);
    model = opU(model, part);

  return model;
}

Model map( vec3 p ){
    mat3 m = modelRotation();
    p *= m;
    #ifndef LOOP
      pR(p.xz, iTime * PI/16.);
    #endif
    Model model = geodesicModel(p);
    return model;
}






vec3 doLighting(Model model, vec3 pos, vec3 nor, vec3 ref, vec3 rd) {
    vec3 lightPos = normalize(vec3(.5,.5,-1.));
    vec3 backLightPos = normalize(vec3(-.5,-.3,1));
    vec3 ambientPos = vec3(0,1,0);

    vec3  lig = lightPos;
    float amb = clamp((dot(nor, ambientPos) + 1.) / 2., 0., 1.);
    float dif = clamp( dot( nor, lig ), 0.0, 1.0 );
    float bac = pow(clamp(dot(nor, backLightPos), 0., 1.), 1.5);
    float fre = pow( clamp(1.0+dot(nor,rd),0.0,1.0), 2.0 );

    vec3 lin = vec3(0.0);
    lin += 1.20 * dif * vec3(.9);
    lin += 0.80 * amb * vec3(.5, .7, .8);
    lin += 0.30 * bac * vec3(.25);
    lin += 0.20 * fre * vec3(1);

    vec3 albedo = model.albedo;
    vec3 col = mix(albedo * lin, albedo, model.glow);

    return col;
}







const float MAX_TRACE_DISTANCE = 8.; 
const float INTERSECTION_PRECISION = .001; 
const int NUM_OF_TRACE_STEPS = 20;
const float FUDGE_FACTOR = .9; 

struct CastRay {
    vec3 origin;
    vec3 direction;
};

struct Ray {
    vec3 origin;
    vec3 direction;
    float len;
};

struct Hit {
    Ray ray;
    Model model;
    vec3 pos;
    bool isBackground;
    vec3 normal;
    vec3 color;
};

vec3 calcNormal( in vec3 pos ){
    vec3 eps = vec3( 0.001, 0.0, 0.0 );
    vec3 nor = vec3(
        map(pos+eps.xyy).dist - map(pos-eps.xyy).dist,
        map(pos+eps.yxy).dist - map(pos-eps.yxy).dist,
        map(pos+eps.yyx).dist - map(pos-eps.yyx).dist );
    return normalize(nor);
}

Hit raymarch(CastRay castRay){

    float currentDist = INTERSECTION_PRECISION * 2.0;
    Model model;

    Ray ray = Ray(castRay.origin, castRay.direction, 0.);

    for( int i=0; i< NUM_OF_TRACE_STEPS ; i++ ){
        if (currentDist < INTERSECTION_PRECISION || ray.len > MAX_TRACE_DISTANCE) {
            break;
        }
        model = map(ray.origin + ray.direction * ray.len);
        currentDist = model.dist;
        ray.len += currentDist * FUDGE_FACTOR;
    }

    bool isBackground = false;
    vec3 pos = vec3(0);
    vec3 normal = vec3(0);
    vec3 color = vec3(0);

    if (ray.len > MAX_TRACE_DISTANCE) {
        isBackground = true;
    } else {
        pos = ray.origin + ray.direction * ray.len;
        normal = calcNormal(pos);
    }

    return Hit(ray, model, pos, isBackground, normal, color);
}






void shadeSurface(inout Hit hit){

    vec3 color = BACKGROUND_COLOR;

    if (hit.isBackground) {
        hit.color = color;
        return;
    }

    vec3 ref = reflect(hit.ray.direction, hit.normal);

#ifdef DEBUG
        color = hit.normal * 0.5 + 0.5;
    #else
        color = doLighting(
            hit.model,
            hit.pos,
            hit.normal,
            ref,
            hit.ray.direction
        );
    #endif

    hit.color = color;
}

vec3 render(Hit hit){
    shadeSurface(hit);
  return hit.color;
}







mat3 calcLookAtMatrix( in vec3 ro, in vec3 ta, in float roll )
{
    vec3 ww = normalize( ta - ro );
    vec3 uu = normalize( cross(ww,vec3(sin(roll),cos(roll),0.0) ) );
    vec3 vv = normalize( cross(uu,ww));
    return mat3( uu, vv, ww );
}

void doCamera(out vec3 camPos, out vec3 camTar, out float camRoll, in float iTime, in vec2 mouse) {
    float dist = 5.5;
    camRoll = 0.;
    camTar = vec3(0,0,0);
    camPos = vec3(0,0,-dist);
    camPos *= cameraRotation();
    camPos += camTar;
}







const float GAMMA = 2.2;

vec3 gamma(vec3 color, float g) {
    return pow(color, vec3(g));
}

vec3 linearToScreen(vec3 linearRGB) {
    return gamma(linearRGB, 1.0 / GAMMA);
}

vec4 materialColorForPixel(vec2 texCoord) {

    vec2 uv = texCoord - vec2(0.5);

    uv *= mat_zoom;

    



    #ifdef LOOP
        #if LOOP == 1
            iTime = mod(iTime, 2.);
        #endif
        #if LOOP == 2
            iTime = mod(iTime, 4.);
        #endif
        #if LOOP == 3
            iTime = mod(iTime, 2.);
      #endif
    #endif

    initIcosahedron();

    vec2 p = uv;

    

    vec2 m = touch.xy;

    vec3 camPos = vec3( 0., 0., 2.);
    vec3 camTar = vec3( 0. , 0. , 0. );
    float camRoll = 0.;

    
    doCamera(camPos, camTar, camRoll, iGlobalTime, m);

    
    mat3 camMat = calcLookAtMatrix( camPos, camTar, camRoll );  

    
    vec3 rd = normalize( camMat * vec3(p.xy,2.0) ); 
    if(length(p)<.85){
    Hit hit = raymarch(CastRay(camPos, rd));

    vec3 color = render(hit);

    #ifndef DEBUG
        
    #endif

    return vec4(color,1.0);
    } else {
     return vec4(BACKGROUND_COLOR,1) ;
    }

}






void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
