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

uniform vec4 uMMParam000; // native input: One
float One = uMMParam000.x;
uniform vec4 uMMParam001; // native input: Two
float Two = uMMParam001.x;
uniform vec4 uMMParam002; // native input: Three
float Three = uMMParam002.x;
uniform vec4 uMMParam003; // native input: Four
float Four = uMMParam003.x;
uniform vec4 uMMParam004; // native input: Five
float Five = uMMParam004.x;
uniform vec4 uMMParam005; // native input: Six
float Six = uMMParam005.x;
uniform vec4 uMMParam006; // native input: Seven
float Seven = uMMParam006.x;
uniform vec4 uMMParam007; // native input: Eight
float Eight = uMMParam007.x;
uniform vec4 uMMParam008; // native input: Nine
float Nine = uMMParam008.x;
uniform vec4 uMMParam009; // native input: Ten
float Ten = uMMParam009.x;
uniform vec4 uMMParam010; // native input: Eleven
float Eleven = uMMParam010.x;
uniform vec4 uMMParam011; // native input: Twelve
float Twelve = uMMParam011.x;































#define PI 3.1415926535897932384626433832795

const int MAX_ITER = 100;
const float LIMIT = 0.001;

struct Material {
    vec3 color;
    float specular;
    float diffuse;
    float ambient;
    float shininess;
};
struct Surface{
    float depth;
    Material mat;
};

struct Final{
    Surface s;
    int iterations;
};

mat3x3 rotate(vec3 angle) {
    return mat3(
    cos(angle.y)*cos(angle.z), cos(angle.z)*sin(angle.x)*sin(angle.y)-cos(angle.x)*sin(angle.z), cos(angle.x)*cos(angle.z)*sin(angle.y)+sin(angle.x)*sin(angle.z),
    cos(angle.y)*sin(angle.z), cos(angle.x)*cos(angle.z)+sin(angle.x)*sin(angle.y)*sin(angle.z), -cos(angle.z)*sin(angle.x)+cos(angle.x)*sin(angle.y)*sin(angle.z),
    -sin(angle.y), cos(angle.y)*sin(angle.x), cos(angle.x)*cos(angle.y));
}

Surface opSmoothUnion(Surface d1, Surface d2, float k) {
    float d = clamp(0.5 + 0.5*(d2.depth-d1.depth)/k, 0.0, One);
    Material material = Material(mix(d2.mat.color, d1.mat.color, d), mix(d2.mat.specular, d1.mat.specular, d), mix(d2.mat.diffuse, d1.mat.diffuse, d), mix(d2.mat.ambient, d1.mat.ambient, d), mix(d2.mat.shininess, d1.mat.shininess, d));
    Surface s = Surface(mix(d2.depth, d1.depth, d) - k*d*(1.0-d), material);
    return s;
}

Surface sfJoin(Surface d1, Surface d2) {
    if(d1.depth < d2.depth)
    return d1;
    else
    return d2;
}

Surface sdSphere(vec3 p, float r, vec3 offset, Material mat)
{
    return Surface(length(p-offset)-r, mat);
}


vec3 position(float xSpeed, float ySpeed, float zSpeed, float time) {
    float x = (2./PI)*(asin(sin((2.*PI/xSpeed) * time)));
    float y = (1.5/PI)*(asin(sin((2.*PI/ySpeed) * time)));
    float z = (1./PI)*(asin(sin((2.*PI/zSpeed) * time)));
    return vec3(x, y, z);
}




Surface sdScene(vec3 p) {
    float time = TIME/Four;
    Surface d = Surface(100., Material(vec3(0.), 0., 0., 0., 0.));
    
    Material sphere1 = Material(vec3(Five, Six, Seven), 0.25, 0.5, 0.15, 10.);
    for (float  i = 0.; i < 15.; i++){
        vec3 po = position(float(.4 / sin(i)), float(.3 / sin(i)), float(.2 / sin(i)), time) * 5.;
        d = opSmoothUnion(d, sdSphere(p, 1., po, sphere1), 1.);
    }
    return d;
}

vec3 normal(vec3 p){ 
    vec2 e = vec2(1.0, -1.0) * 0.0005;
    return normalize(
    e.xyy * sdScene(p + e.xyy).depth +
    e.yyx * sdScene(p + e.yyx).depth +
    e.yxy * sdScene(p + e.yxy).depth +
    e.xxx * sdScene(p + e.xxx).depth);
}




Final rayMarch(vec3 o, vec3 d){
    Surface sur;
    Surface sc;
    int iter = 0;
    for (int i = 0; i < MAX_ITER; i++){
        sc = sdScene(o + d*sur.depth);
        sur.depth += sc.depth;
        sur.mat = sc.mat;
        if (sc.depth < LIMIT || sur.depth > 100.){
            iter = (i);
            break;
        }
    }
    return Final(sur, iter);
}






float shadowMarch(vec3 p, vec3 lPos, float intensity){
    float depth = LIMIT * 2.;
    Surface sc;

    vec3 dir = normalize(lPos - p);

    
    sc = sdScene(p + depth * dir);
    depth += sc.depth;
    if (sc.depth < LIMIT) return 1.;

    for (int i = 1; i < MAX_ITER; i++) {
        sc  = sdScene(p + depth * dir);
        depth += sc.depth;
        if (sc.depth < LIMIT){
            return 1.-intensity;
        }
    }
    return 1.;
}








vec3 phongLightning(vec3 p, vec3 lPos, vec3 N, vec3 RD, Material m){
    vec3 L = normalize(lPos - p);
    vec3 ambient = m.color * m.ambient * Eleven;
    vec3 diffuse = m.diffuse * clamp(dot(L, N), Twelve, 1.) * m.color;
    vec3 specular = m.specular * pow(clamp(-dot(reflect(L, N), -RD), 0., 1.), m.shininess) * vec3(1.);
    specular = vec3(max(specular.x, 0.), max(specular.y, 0.), max(specular.z, 0.));

    return ambient + diffuse + specular;
}

vec4 materialColorForPixel(vec2 texCoord)
 {

    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy - 0.5;
    uv.x = uv.x * RENDERSIZE.x / RENDERSIZE.y;
    
    vec3 rayOrigin = vec3(1.0, 1.0, 5.);
    vec3 rayDir = normalize(vec3(uv, -1.));
    vec3 light = vec3(cos(TIME) * 10., 10., sin(TIME) * 10.);
    Final f = rayMarch(rayOrigin, rayDir);
    Surface d = f.s;
    if (d.depth < 100.){ 
        vec3 p = rayOrigin + rayDir * d.depth;
        vec3 N = normal(p);
        vec3 col = phongLightning(p, light, N, rayDir, d.mat);
        return vec4(col, Three);
    } else {
        vec3 col = vec3(0.) + vec3(Eight, Nine, Ten) * float(f.iterations);
        return vec4(col, Two); 
    }
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
