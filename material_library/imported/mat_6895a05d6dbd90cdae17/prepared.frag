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

uniform vec4 uMMParam000; // native input: mat_iterations
int mat_iterations = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_speed
float mat_speed = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_dens
float mat_dens = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_abb
float mat_abb = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_fov
float mat_fov = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_offset
vec2 mat_offset = uMMParam005.xy;
uniform vec4 uMMParam006; // native input: mat_ambColor
vec4 mat_ambColor = uMMParam006;
uniform vec4 uMMParam007; // native input: mat_color
float mat_color = uMMParam007.x;
float mat_time = uTDTime * (mat_speed);
#define texture_graff sTD2DInputs[0]


































#define MAX_DIST 10.
#define SURF_DIST .001
#define PI 3.14156

#define S smoothstep
#define T mat_time

mat2 Rot(float a) {
    float s=sin(a), c=cos(a);
    return mat2(c, -s, s, c);
}

float sdBox(vec3 p, vec3 s) {
    p = abs(p)-s;
	return length(max(p, 0.))+min(max(p.x, max(p.y, p.z)), 0.);
}
float sdRoundBox( vec3 p, vec3 b, float r )
{
  vec3 q = abs(p) - b;
  return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0) - r;
}
float sdOctahedron( vec3 p, float s)
{
  p = abs(p);
  return (p.x+p.y+p.z-s)*0.57735027;
}















float GetDist(vec3 p) {



	p.xz *= Rot(PI*0.25-T+2.37);
	p.yx *= Rot(PI*0.25+T+0.56);
	p = abs(abs(p+0.2))-0.5;
	float d = sdOctahedron(p, 1.2);
	p.xy *= Rot(PI*0.25+T);
	p.yz *= Rot(PI*0.25-T);
	d = min(d,sdOctahedron(p-0.3, 1.2));
    
    return d*0.9;
}

float RayMarch(vec3 ro, vec3 rd, float side) {
	float dO=0.;
    
    for(int i=0; i<mat_iterations; i++) {
    	vec3 p = ro + rd*dO;
        float dS = GetDist(p)*side;
        dO += dS;
        if(dO>MAX_DIST || abs(dS)<SURF_DIST) break;
    }
    
    return dO;
}

vec3 GetNormal(vec3 p) {
	float d = GetDist(p);
    vec2 e = vec2(.0002, 0);
    
    vec3 n = d - vec3(
        GetDist(p-e.xyy),
        GetDist(p-e.yxy),
        GetDist(p-e.yyx));
    
    return normalize(n);
}

vec3 GetRayDir(vec2 uv, vec3 p, vec3 l, float z) {
    vec3 f = normalize(l-p),
        r = normalize(cross(vec3(0,1,0), f)),
        u = cross(f,r),
        c = f*z,
        i = c + uv.x*r + uv.y*u,
        d = normalize(i);
    return d;
}

vec2 getSphUv(in vec3 r)
{
	float theta = acos(r.y) / -PI;
	float phi = atan( -r.z, r.x) / -PI * 0.5f;

	return vec2(phi,theta);
}

vec4 materialColorForPixel( vec2 texCoord )
{

   vec2 uv = texCoord *2. -1.;
	vec2 m = mat_offset;

    vec3 ro = vec3(0, 3, -3);
    ro.yz *= Rot(-m.y*3.14+1.);
    ro.xz *= Rot(-m.x*6.2831);
    
    vec3 rd = GetRayDir(uv, ro, vec3(0,0.,0), mat_fov);
    vec3 col = vec3(0.2,0.2,0.3)* (1. - length(uv)); 


    float d = RayMarch(ro, rd, 1.); 
    
    float IOR = 1.45; 
    
    if(d<MAX_DIST) {
        vec3 p = ro + rd * d; 
        vec3 n = GetNormal(p); 
        vec3 r = reflect(rd, n);
        
        vec3 rdIn = refract(rd, n, 1./IOR); 
        
        vec3 pEnter = p - n*SURF_DIST*3.;
        float dIn = RayMarch(pEnter, rdIn, -1.); 
        
        vec3 pExit = pEnter + rdIn * dIn; 
        vec3 nExit = -GetNormal(pExit); 
        
        vec3 rdOut = vec3(0.);
		vec3 reflTex = vec3(0.);

   		float abb = .05*mat_abb;
        
        
        rdOut = refract(rdIn, nExit, IOR-abb);
        if(dot(rdOut, rdOut)==0.) rdOut = reflect(rdIn, nExit);
        reflTex.r = texture(texture_graff, getSphUv(rdOut)).r;
        
        
        rdOut = refract(rdIn, nExit, IOR);
        if(dot(rdOut, rdOut)==0.) rdOut = reflect(rdIn, nExit);
        reflTex.g =  texture(texture_graff, getSphUv(rdOut)).g;
        
        
        rdOut = refract(rdIn, nExit, IOR+abb);
        if(dot(rdOut, rdOut)==0.) rdOut = reflect(rdIn, nExit);
        reflTex.b =  texture(texture_graff, getSphUv(rdOut)).b;
        
        float dens = mat_dens;
        float optDist = exp(-dIn*dens);
        
        reflTex = reflTex*optDist;

		float fresnel = pow(1.+dot(rd,n),5.);
		vec3 rfl = texture(texture_graff, getSphUv(reflect(rd,n))).rgb;
	
		col = reflTex;
		col += mat_ambColor.rgb;
		
		col = mix(col, rfl, fresnel);

		col += fract(rdOut)*mat_color;
		col *= vec3(dot(vec3(0.25,0.6,0.15),(vec3(step(vec3(0.5), fract(rdOut*1.))))));
    }
    
	return vec4(col,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
