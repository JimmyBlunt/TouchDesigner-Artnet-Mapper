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
uniform vec4 uMMParam001; // native input: mat_shadow
float mat_shadow = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_zoom
float mat_zoom = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_tilex
int mat_tilex = int(round(uMMParam003.x));
uniform vec4 uMMParam004; // native input: mat_tiley
int mat_tiley = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: mat_mirrorx
bool mat_mirrorx = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_mirrory
bool mat_mirrory = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_color1
vec4 mat_color1 = uMMParam007;
uniform vec4 uMMParam008; // native input: mat_color2
vec4 mat_color2 = uMMParam008;
float mat_time = uTDTime * (mat_speed);












































   






















#define ANIMATE
#define TWO_PI 6.28318530718

vec2 hash2( vec2 p )
{
    
    

    
    return fract(sin(vec2(dot(p,vec2(127.1,311.7)),dot(p,vec2(269.5,183.3))))*43758.5453);
}

vec3 voronoi( in vec2 x )
{
    vec2 n = floor(x);
    vec2 f = fract(x);

    
    
    
    vec2 mg, mr;

    float md = 8.0;
    for( int j=-1; j<=1; j++ )
    for( int i=-1; i<=1; i++ )
    {
        vec2 g = vec2(float(i),float(j));
        vec2 o = hash2( n + g );
        
        o = 0.5 + 0.5*sin( mat_time + TWO_PI * o );
        
        vec2 r = g + o - f;
        float d = dot(r,r);

        if( d<md )
        {
            md = d;
            mr = r;
            mg = g;
        }
    }

    
    
    
    md = 8.0;
    for( int j=-2; j<=2; j++ )
    for( int i=-2; i<=2; i++ )
    {
        vec2 g = mg + vec2(float(i),float(j));
        vec2 o = hash2( n + g );
        
        o = 0.5 + 0.5*sin( mat_time + TWO_PI * o );
        
        vec2 r = g + o - f;

        if( dot(mr-r,mr-r)>0.00001 )
        md = min( md, dot( 0.5*(mr+r), normalize(r-mr) ) );
    }

    return vec3( md, mr );
}

vec4 materialColorForPixel( vec2 texCoord )
{
	
	float boundx = 1. / mat_tilex;
	bool mirrorx = mat_mirrorx && mod(floor( texCoord.x / boundx ), 2.0) == 0.0;
	float boundedx = mod( texCoord.x, boundx );

	float boundy = 1. / mat_tiley;
	bool mirrory = mat_mirrory && mod(floor( texCoord.y / boundy ), 2.0) == 0.0;
	float boundedy = mod( texCoord.y, boundy );
    vec2 p = vec2(  mirrorx ? boundx - boundedx : boundedx , mirrory ? boundy - boundedy : boundedy ); 

    vec3 c = voronoi( mat_zoom * p );

    
    vec3 col = vec3(mat_color2.r, mat_color2.g, mat_color2.b); 
    
    col = mix( vec3(mat_color1.r,mat_color1.g,mat_color1.b), col, smoothstep( 0.05, 0.05 + mat_shadow / 0.2 * .25, c.x ) );
    
    
    
    

    return vec4(col,1.0);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
