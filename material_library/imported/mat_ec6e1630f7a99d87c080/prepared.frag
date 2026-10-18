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
uniform vec4 uMMParam001; // native input: mat_height
float mat_height = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_spectrum_radius
float mat_spectrum_radius = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_smoothness
float mat_smoothness = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_shininess
float mat_shininess = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_ao_strength
float mat_ao_strength = uMMParam005.x;
uniform vec4 uMMParam006; // native input: mat_noise_scale
float mat_noise_scale = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_noise_strength
float mat_noise_strength = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_noise_speed
float mat_noise_speed = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_camera_height
float mat_camera_height = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_focal_length
float mat_focal_length = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_base_color
vec4 mat_base_color = uMMParam011;
uniform vec4 uMMParam012; // native input: mat_specular_color
vec4 mat_specular_color = uMMParam012;
uniform vec4 uMMParam013; // native input: mat_background_color
vec4 mat_background_color = uMMParam013;
float mat_noise_time = uTDTime * (mat_noise_speed);
#define waveformFFT sTD2DInputs[0]






























#define MAX_STEPS 100
#define MAX_DIST 100.0
#define SURF_DIST 0.01

vec3 hash3(vec3 p) {
    p = vec3(dot(p, vec3(127.1, 311.7, 74.7)),
             dot(p, vec3(269.5, 183.3, 246.1)),
             dot(p, vec3(113.5, 271.9, 124.6)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

float noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(dot(hash3(i + vec3(0.0, 0.0, 0.0)), f - vec3(0.0, 0.0, 0.0)),
                       dot(hash3(i + vec3(1.0, 0.0, 0.0)), f - vec3(1.0, 0.0, 0.0)), u.x),
                   mix(dot(hash3(i + vec3(0.0, 1.0, 0.0)), f - vec3(0.0, 1.0, 0.0)),
                       dot(hash3(i + vec3(1.0, 1.0, 0.0)), f - vec3(1.0, 1.0, 0.0)), u.x), u.y),
               mix(mix(dot(hash3(i + vec3(0.0, 0.0, 1.0)), f - vec3(0.0, 0.0, 1.0)),
                       dot(hash3(i + vec3(1.0, 0.0, 1.0)), f - vec3(1.0, 0.0, 1.0)), u.x),
                   mix(dot(hash3(i + vec3(0.0, 1.0, 1.0)), f - vec3(0.0, 1.0, 1.0)),
                       dot(hash3(i + vec3(1.0, 1.0, 1.0)), f - vec3(1.0, 1.0, 1.0)), u.x), u.y), u.z);
}

float getHeight(vec2 p) {
    float freq = length(p) * 0.1;
    vec4 spectrum = texture(waveformFFT, vec2(freq, 0.0));
    return spectrum.r * mat_height;
}

float getDist(vec3 p) {
    vec2 uv = p.xz * mat_scale;
    float height = getHeight(uv);
    float noiseValue = noise(p * mat_noise_scale * 10 + vec3(0, mat_noise_time, 0)) * mat_noise_strength;
    return p.y - height - noiseValue;
}

vec3 getNormal(vec3 p) {
    float d = getDist(p);
    vec2 e = vec2(0.01, 0);
    vec3 n = d - vec3(
        getDist(p - e.xyy),
        getDist(p - e.yxy),
        getDist(p - e.yyx)
    );
    return normalize(n);
}

float rayMarch(vec3 ro, vec3 rd) {
    float dO = 0.0;
    for(int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * dO;
        float dS = getDist(p) * mat_smoothness;
        dO += dS;
        if(dO > MAX_DIST || abs(dS) < SURF_DIST) break;
    }
    return dO;
}

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float calcAO(vec3 p, vec3 n) {
    float occ = 0.0;
    float sca = 1.0;
	 const int mat_ao_steps = 5;
    for(int i = 0; i < int(mat_ao_steps); i++) {
        float h = 0.01 + 0.12 * float(i) / mat_ao_steps;
        float d = getDist(p + h * n);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ * mat_ao_strength, 0.0, 1.0);
}

vec4 materialColorForPixel(vec2 texCoord) {
    vec2 uv = texCoord;
    uv.y = 1.0 - uv.y;
    uv = (uv - 0.5) * 2.0;

    vec3 ro = vec3(0, mat_camera_height, -3);
    vec3 lookAt = vec3(0, 0, 0);
    vec3 forward = normalize(lookAt - ro);
    vec3 right = normalize(cross(vec3(0, 1, 0), forward));
    vec3 up = cross(forward, right);
    vec3 rd = normalize(uv.x * right + uv.y * up + mat_focal_length * forward);

    float d = rayMarch(ro, rd);
    vec3 p = ro + rd * d;
    vec3 n = getNormal(p);
    vec3 light = normalize(vec3(1, 2, -2));

    float distFromCenter = length(p.xz);
    float spectrumMask = smoothstep(mat_spectrum_radius + 0.1, mat_spectrum_radius - 0.1, distFromCenter);

    float dif = dot(n, light) * 0.5 + 0.5;
    vec3 diffuse = dif * mat_base_color.rgb;

    vec3 viewDir = normalize(ro - p);
    vec3 reflectDir = reflect(-light, n);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), mat_shininess);
    vec3 specular = mat_specular_color.rgb * spec;

    float ao = calcAO(p, n);
    vec3 col = (diffuse + specular) * spectrumMask * ao;

    col += noise(p * mat_noise_scale * 20.0 + vec3(0, mat_noise_time, 0)) * mat_noise_strength * 0.5;

    col = mix(col, mat_background_color.rgb, 1.0 - exp(-0.0005 * d * d));

    return vec4(col, 1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
