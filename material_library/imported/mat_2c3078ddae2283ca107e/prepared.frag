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
float mat_time = uTDTime * (mat_speed);














#define PI 3.14159265359




float smooth_clamp(float x, float m, float n) {
    if(x>m) return x;

    
    
    
    
    
    
    
    
    
    
    float a = 2.0*n-m;
    float b = 2.0*m-3.0*n;
    float t = x/m;
    return (a*t+b)*t*t+n;

    
    
}




float exp_impulse(float x, float s, float h) {
    float k = s*x;
    float j = h*k;
    
    return j*exp(1.0-k);

    
    
    
}




float acc_to_const_v(float x, float a, float t) {
    
    
    
    if (2.0*a*x < t) return a*pow(x,2.0);

    
    
    return t*x-(a*pow(t/(2.0*a),2.0));

    
    
}




float sin_bounce(float x, float f, float h) {
    float k = PI*(f*x-1.0);
    return h*sin(k)/k;
}



float light_falloff(float r, float a, float b) {
    r = abs(r);
    return 1.0/(1.0+a*r+b*pow(r,2.0));

    
}




float trunc_falloff(float r, float m) {
    if (r < 0.0) return 1.0;
    if (r > m) return 0.0;
    r /= m;
    return (r-2.0)*r+1.0;
}



float p_wave(float x, float k) {
    return -pow(abs(2.0*x-1.0),1.0/k)+1.0;

    
    
    
    
    
}



float p_bell(float x, float k) {
    return pow(4.0*x*(1.0-x),k);

    
    
    
    
    
}




float p_curve(float x, float a, float b) {
    
    
    
    float k = pow(a+b,a+b)/(pow(a,a)*pow(b,b));

    
    
    return k*pow(x,a)*pow(1.0-x,b);
}



float flatten(float x, float k) {
    float a = 0.5*pow(abs(2.0*x-1.0),k)+0.5;
    return x>0.5?a:1.0-a;
}


float contrast(float x, float k) {
    float a = 0.5*pow(2.0*((x<0.5)?x:1.0-x),k);
    return (x<0.5)?a:1.0-a;
}



float tonemap(float x, float k) {
    return x*(1.0+k)/(1.0+k*x);

    
}











float gaussian(float x, float a, float b, float c) {
    return a*exp(-pow(x-b,2.0)/2.0*c*c);
}




float cubic_pulse(float x, float c, float w) {
    x = abs(x - c);
    if (x > w) return 0.0;
    x /= w;
    return 1.0-x*x*(3.0-2.0*x);
}


float plot(vec2 st, float pct) {
    return smoothstep(pct-0.02, pct, st.y) - smoothstep(pct, pct+0.02, st.y);
}


float plot_v2(vec2 st, float pct) {
    return cubic_pulse(st.y, pct, 0.02);
}

float shaping_func(ivec2 cell_coord, float x) {
    return    cell_coord==ivec2(0,0) ? smooth_clamp(x, 0.95, 0.50)
            : cell_coord==ivec2(1,0) ? exp_impulse(x, 8.0, 0.2)
            : cell_coord==ivec2(2,0) ? acc_to_const_v(x, 4.0, 2.0)
            : cell_coord==ivec2(3,0) ? sin_bounce(x, 8.0, 1.)
            : cell_coord==ivec2(0,1) ? light_falloff(x, 2.0, 5.0)
            : cell_coord==ivec2(1,1) ? trunc_falloff(x, 0.5)
            : cell_coord==ivec2(2,1) ? p_wave(x, 5.0)
            : cell_coord==ivec2(3,1) ? p_bell(x, 5.0)
            : cell_coord==ivec2(0,2) ? p_curve(x, 0.7, 1.5)
            : cell_coord==ivec2(1,2) ? flatten(x, 3.0)
            : cell_coord==ivec2(2,2) ? contrast(x, 3.0)
            : cell_coord==ivec2(3,2) ? tonemap(x, 10.0)
            : cell_coord==ivec2(0,3) ? gaussian(x, 1.0, 0.5, 10.0)
            : cell_coord==ivec2(1,3) ? cubic_pulse(x, 0.5, 1.0)
            : cell_coord==ivec2(2,3) ? 0.0
            : 1.0;
}

vec4 materialColorForPixel( vec2 texCoord )
{
    float column = 4.0;
    float row = 4.0;
    
    vec2 st = texCoord;
	st.y = 1.-st.y;
    st.x *= column;
    st.y *= row;
    ivec2 coord = ivec2(st);
    st = mod(st, 1.0); 

    float y = shaping_func(coord, st.x);
    float pct = plot_v2(st, y);

    vec3 bg_color = vec3(y);
    vec3 plot_color = vec3(1.0,float(coord.y)/(row-1.0),float(coord.x)/(column-1.0));
    vec3 color = (1.0-pct)*bg_color + pct*plot_color;

    float circle_radius = 0.05;
    float cell_num = mod(mat_time, column*row); 
    float cell_x = mod(cell_num, column); 
    float cell_y = (cell_num-cell_x)/row; 
    ivec2 circle_coord = ivec2(int(cell_x), int(cell_y));
    float time_x = mod(mat_time, 1.0);

    float circle_y = shaping_func(coord, time_x);
    float circle_pct = float(length(vec2(time_x, circle_y)-st) <= circle_radius);

    vec3 circle_color = vec3(1.0-circle_y);
    color = (1.0-circle_pct)*color + circle_pct*circle_color;

    return vec4(color, 1.0);

}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
