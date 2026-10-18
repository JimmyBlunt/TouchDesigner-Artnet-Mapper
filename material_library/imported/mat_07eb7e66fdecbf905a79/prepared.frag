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






























































































float iTime = mat_time - mat_offset * 10;
#define TWO_PI 6.28318530718
#define rotate(a) mat2(cos(a), sin(a), -sin(a), cos(a))
#define spiral(u, a, r, t, d) abs(sin(t + r * length(u) + a * (d * atan(u.y, u.x))))
#define flower(u, a, r, t) spiral(u, a, r, t, 1.) * spiral(u, a, r, t, -1.)
#define sinp(a) .5 + sin(a) * .5
#define polar(a, t) a * vec2(cos(t), sin(t))


vec4 materialColorForPixel(vec2 texCoord) {

    vec2 st = texCoord - vec2(0.5);

    st *= mat_zoom;

    st = rotate(iTime / 8.) * st;

    vec3 col;
    vec2 o = vec2(cos(iTime / 4.1), sin(iTime / 2.));

    float t = -.001*iTime;
    vec2 mp = 1.+4.*mouse.xy;

    for (int i = 0; i < 10; i++) {
        for (float i = 0.; i < TWO_PI; i += TWO_PI / 16.) {
            t += .6 * flower(vec2(st + polar(1., i)), 6.+mp.x, (4.4+mp.y) *
                             sinp(iTime / 2.), iTime / 4.);
        }
    col[i] = sin(5. * t + length(st) * 8. * sinp(t));
  }

  return vec4(mix(col, vec3(1., .7, 0.), col.r), 1.0);


}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
