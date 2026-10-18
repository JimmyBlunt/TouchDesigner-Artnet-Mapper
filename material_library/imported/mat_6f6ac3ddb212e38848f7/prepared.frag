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
uniform vec4 uMMParam001; // native input: mat_distortion
float mat_distortion = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_color_shift
float mat_color_shift = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_zoom
float mat_zoom = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_frequency
float mat_frequency = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_glow
float mat_glow = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_orbit_speed
float mat_orbit_speed = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_planet_size
float mat_planet_size = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_bg_gradient_angle
float mat_bg_gradient_angle = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_bg_star_density
float mat_bg_star_density = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_color_1
vec4 mat_color_1 = uMMParam010;
uniform vec4 uMMParam011; // native input: mat_color_2
vec4 mat_color_2 = uMMParam011;
uniform vec4 uMMParam012; // native input: mat_bg_color_1
vec4 mat_bg_color_1 = uMMParam012;
uniform vec4 uMMParam013; // native input: mat_bg_color_2
vec4 mat_bg_color_2 = uMMParam013;
float mat_time = uTDTime * (mat_speed);






























































































































#define MAX_STEPS 100
#define MAX_DIST 100.
#define SURF_DIST .001

float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float getNoise(vec3 p) {
    return fract(sin(dot(p, vec3(12.9898, 78.233, 45.5432))) * 43758.5453);
}

float getDistortion(vec3 p) {
    return sin(p.x * mat_frequency + mat_time) * 
           sin(p.y * mat_frequency + mat_time) * 
           sin(p.z * mat_frequency + mat_time) * mat_distortion;
}

float getDist(vec3 p) {
    float sphere = sdSphere(p, mat_planet_size);
    float distortion = getDistortion(p);
    return sphere + distortion;
}

float rayMarch(vec3 ro, vec3 rd) {
    float dO = 0.;
    for(int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * dO;
        float dS = getDist(p);
        dO += dS;
        if(dO > MAX_DIST || abs(dS) < SURF_DIST) break;
    }
    return dO;
}

vec3 getNormal(vec3 p) {
    float d = getDist(p);
    vec2 e = vec2(.001, 0);
    vec3 n = d - vec3(
        getDist(p - e.xyy),
        getDist(p - e.yxy),
        getDist(p - e.yyx)
    );
    return normalize(n);
}

vec3 getRayDirection(vec2 uv, vec3 p, vec3 l, float z) {
    vec3 f = normalize(l - p),
        r = normalize(cross(vec3(0, 1, 0), f)),
        u = cross(f, r),
        c = f * z,
        i = c + uv.x * r + uv.y * u;
    return normalize(i);
}

float star(vec2 uv, float flare) {
    float d = length(uv);
    float m = .05 / d;
    float rays = max(0., 1. - abs(uv.x * uv.y * 1000.));
    m += rays * flare;
    return m;
}

vec3 starField(vec2 uv) {
    vec3 col = vec3(0);
    vec2 gv = fract(uv * 100.) - 0.5;
    vec2 id = floor(uv * 100.);
    
    for(int y = -1; y <= 1; y++) {
        for(int x = -1; x <= 1; x++) {
            vec2 offs = vec2(x, y);
            float n = getNoise(vec3(id + offs, mat_time * 0.1));
            float size = fract(n * 345.32);
            float star = star(gv - offs - vec2(n, fract(n * 34.)) + 0.5, smoothstep(0.9, 1., size) * 0.6);
            vec3 color = sin(vec3(0.2, 0.3, 0.9) * fract(n * 2345.2) * 123.2) * 0.5 + 0.5;
            color = color * vec3(1, 0.1, 1. + size);
            star *= sin(mat_time * 3. + n * 6.2831) * 0.5 + 1.;
            col += star * size * color;
        }
    }
    return col * mat_bg_star_density;
}

vec4 materialColorForPixel(vec2 texCoord) {
    vec2 uv = texCoord;
    uv.y = 1.0 - uv.y;
    vec2 originalUV = uv;
    uv = (uv * 2.0 - 1.0) / mat_zoom;
    
    float orbit = mat_time * mat_orbit_speed;
    vec3 ro = vec3(sin(orbit) * 3.0, cos(orbit) * 1.5, cos(orbit) * 3.0);
    vec3 rd = getRayDirection(uv, ro, vec3(0, 0, 0), 1.);

    float d = rayMarch(ro, rd);
    
    vec3 bgGradient = mix(mat_bg_color_1.rgb, mat_bg_color_2.rgb, 
                          dot(originalUV - 0.5, vec2(cos(radians(mat_bg_gradient_angle)), 
                                                     sin(radians(mat_bg_gradient_angle)))) + 0.5);
    vec3 stars = starField(originalUV);
    vec3 backgroundColor = bgGradient + stars;
    
    if(d >= MAX_DIST) {
        return vec4(backgroundColor, 1.0);
    }
    
    vec3 p = ro + rd * d;
    vec3 n = getNormal(p);
    
    vec3 color = 0.5 + 0.5 * cos(mat_time * 0.5 + p.xyx + vec3(0, 2, 4));
    color += mat_color_shift * sin(mat_time * 0.1 + p.y * 10.0);
    
    float fresnel = pow(1.0 + dot(rd, n), 3.0);
    color += vec3(mat_color_1.rgb) * fresnel * 0.5;

    
    color += vec3(mat_color_2.rgb) * (1.0 / (d * d + 0.1)) * mat_glow;

    
    color = pow(color, vec3(1.2));

    
    color = mix(color, vec3(mat_color_1.rgb), color.r * 0.5);
    color = mix(color, vec3(mat_color_2.rgb), color.b * 0.5);

    
    color = mix(backgroundColor, color, smoothstep(MAX_DIST - 5.0, MAX_DIST - 10.0, d));

    return vec4(color, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
