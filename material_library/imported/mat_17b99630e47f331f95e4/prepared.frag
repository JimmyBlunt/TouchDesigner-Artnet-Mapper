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
float mat_time = uTDTime * (mat_speed);















#define PI 3.141592
#define BALLS 16.

mat2 rotate2d(float a) {
  return mat2(cos(a), -sin(a), sin(a), cos(a));
}

vec4 materialColorForPixel( vec2 texCoord )
{

	vec2 uv = texCoord;
  uv.x -= .5;
  uv.y -= .5;

	uv *= mat_scale;
 
  uv *= 100.;
  float dist = length((uv));
  vec4 fragColor = vec4(0.);

  for (float i = 0.; i < BALLS; i++) {
    uv.y += .5 * (i / 20.) * cos(uv.y / 1000. + mat_time / 4.) + sin(uv.x / 50. - mat_time / 2.)*0.1;
    uv.x += .5 * (i) * sin(uv.x / 300. + mat_time / 6.) * sin(uv.y / 50. + mat_time / 5.)*0.1;
    float t = .01 * dist * (i) * PI / BALLS * (5. + 1.);
    vec2 p = 8. * vec2(-1. * cos(t), 1. * sin(t / 6.));
    p /= sin(PI * sin(uv.x / 10.) * cos(uv.y / 11.));
    vec3 col = cos(vec3(0, 1, -1) * PI * 2. / 3. + PI * (mat_time / 5. + float(i) / 5.)) * 0.5 + 0.5;
    fragColor += vec4(float(i) * .2 / length(uv - p * 0.9) * col, 1.);
  }


	return fragColor;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
