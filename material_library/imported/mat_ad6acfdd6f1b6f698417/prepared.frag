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

uniform vec4 uMMParam000; // native input: mat_speed
float mat_speed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_scale
float mat_scale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_smoothness
float mat_smoothness = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_simplify
float mat_simplify = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_mx
float mat_mx = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_my
float mat_my = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_mz
float mat_mz = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_invert
bool mat_invert = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: mat_backgroundColor
vec4 mat_backgroundColor = uMMParam008;
uniform vec4 uMMParam009; // native input: mat_foregroundColor
vec4 mat_foregroundColor = uMMParam009;
uniform vec4 uMMParam010; // native input: mat_brightness
float mat_brightness = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_contrast
float mat_contrast = uMMParam011.x;
float mat_time = uTDTime * (mat_speed);






























const float PI = 3.1415926535897932384626433832795;

int Seed = 70; 

float  ofs = .0001; 


#define hash44(p) fract(18.5453 * sin(p * mat4(127.1, 311.7, 269.5, 183.3, 421.1, 547.6, 231.3, 298.4, 87.6, 123.4, 356.1, 654.3, 765.1, 876.4, 132.5, 234.8)))
#define disp(p) ( -ofs + (1.0 + 2.0 * ofs) * hash44(p) )


#define hash31(p) fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453123)


float noise3d(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);

    float v = mix(
                mix(
                    mix(hash31(i + vec3(0, 0, 0)), hash31(i + vec3(1, 0, 0)), f.x),
                    mix(hash31(i + vec3(0, 1, 0)), hash31(i + vec3(1, 1, 0)), f.x), f.y),
                mix(
                    mix(hash31(i + vec3(0, 0, 1)), hash31(i + vec3(1, 0, 1)), f.x),
                    mix(hash31(i + vec3(0, 1, 1)), hash31(i + vec3(1, 1, 1)), f.x), f.y), f.z);
    
    return 1.0 - abs(2.0 * v - 1.0);
}



mat3 rot3(float angle) {
    float c = cos(angle), s = sin(angle);
    return mat3(
        c, -s, 0,
        s,  c, 0,
        0,  0, 1
    );
}



vec3 poor_mans_fbm33(vec3 p) {
    vec3 v = vec3(0.0);
    float a = 0.5;
    mat3 R = rot3(0.37);
    for (int i = 0; i < 6; i++, p *= 2.0, a /= 2.0) {
        p = R * p;
        
        float n = noise3d(p);
        float nn = n*n;
        v += a * vec3(n,nn,nn*n);
    }
    return v;
}


float voronoi4D_edge_distance(vec4 u) 
{
	
	vec3 Movement_3D = vec3(mat_mx,mat_my,mat_mz); 

    
    u.w *= 0.1;
    u.w = 1.0 - 2.0 * abs(fract(u.w + 0.5) - 0.5);
    u.w *= 0.99;
    
    
    u.w += float(Seed); 
    u.xyz += Movement_3D*mat_time; 
    
    
    vec4 iu = floor(u);
    float m = 1e9, m2 = 1e9;
    vec4 P, P2;
    
    vec4 iu_offset = iu - 0.5;
    vec4 p, o, r;
    float d;
    
    
    for (int k = 0; k < 6; k++) {
        p = iu_offset + vec4(k & 1, (k >> 1) & 1, (k >> 2) & 1, (k >> 3) & 1); 
        o = disp(p);  
        r = p - u + o;
        d = dot(r, r);

        if (d < m) {
            m2 = m;
            P2 = P;
            m = d;
            P = r;
        } else if (d < m2 && dot(P - r, P - r) > 1e-5) {
            m2 = d;
            P2 = r;
        }
    }
    
    
    if (m2 < 1e9) {
        m2 = 0.5 * dot((P + P2), normalize(P2 - P));
    }

    return m2;
}

vec3 uvToCartesian3D(vec2 uv) {
    
    float theta = uv.x * 2.0 * 3.14159265359; 
    float phi = uv.y * 3.14159265359; 
    
    float x = sin(phi) * cos(theta);
    float y = sin(phi) * sin(theta);
    float z = cos(phi);
    return vec3(x, y, z);
}

vec4 materialColorForPixel( vec2 texCoord )
{

	vec2 uv = texCoord.xy;
    vec3 pos = uvToCartesian3D(uv);
	pos *= mat_scale;
	vec3 f33=poor_mans_fbm33(pos/mat_smoothness);

	vec3 coo = mix(pos,f33,vec3(mat_simplify));
	float G = voronoi4D_edge_distance(vec4(coo, mat_time*0.45+0.334));

    
    G += mat_brightness;
    
    G = mix(0.5, G, mat_contrast);
	G = clamp(G,0.,1.);

	if (mat_invert) G = 1 - G;

	vec3 color = mix( mat_backgroundColor.rgb, mat_foregroundColor.rgb, G );


	vec4 col = vec4(color,1.);
	return col;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
