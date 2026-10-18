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

uniform vec4 uMMParam000; // native input: mat_one
float mat_one = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_two
float mat_two = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_three
float mat_three = uMMParam002.x;
#define iChannel0 sTD2DInputs[0]




























#define AA 2

float hash( in float n )
{
    return fract(sin(n)*43758.5453);
}
float noise( in vec2 p )
{
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    float n = i.x + i.y*57.0;
    return mix(mix( hash(n+ 0.0), hash(n+ 1.0),f.x),
               mix( hash(n+57.0), hash(n+58.0),f.x),f.y);
}

vec2 map( in vec2 p, in float time )
{
    for( int i=0; i<4; i++ )
    {
    	float a = (noise(p*1.5)*6.2831 + time);
		p += 0.1*vec2( cos(a), sin(a) );
    }
    return p;
}

float height( in vec2 p, in vec2 q )
{
    float h = dot(p-q,p-q);
    h += 0.005*IMG_NORM_PIXEL(iChannel0,mod(9.75*(p+q),1.0)).x;
    return h;
}

vec4 materialColorForPixel( vec2 texCoord ) {



    float time = mat_one*TIME;
    
    vec3 tot = vec3(0.0);
	#if AA>1
    for( int m=0; m<AA; m++ )
    for( int n=0; n<AA; n++ )
    {
        vec2 o = vec2(float(m),float(n)) / float(AA) - 0.5;
        vec2 p = (mat_three*(texCoord.xy));
		#else    
        vec2 p = (mat_three*texCoord.xy);
		#endif
        
        vec2 q = map(p,time*mat_one);
        
        float w = 10.0*q.x;
        float u = floor(w);
        float f = fract(w);
        vec3  col = vec3(0.7,0.55,0.5) + 0.3*cos(3.0*u+vec3(0.0,1.5,2.0));
        
        
        float sha = smoothstep(0.0,mat_two,f)-smoothstep(1.0-fwidth(w),1.0,f);
        
        
 		vec2  eps = vec2(2.0,0.0);
		float l2c = height(q,p);
        float l2x = height(map(p+eps.xy,time),p) - l2c;
        float l2y = height(map(p+eps.yx,time),p) - l2c;
        vec3  nor = normalize( vec3( l2x, eps.x, l2y ) );
            
        
        col *= 0.3+0.7*sha;
        col *= 0.8+0.2*vec3(1.0,0.9,0.3)*dot(nor,vec3(0.7,0.3,0.7));
        col += 0.3*pow(nor.y,20.0)*sha;
        col *= 7.5*l2c;
        tot += col;
	#if AA>1
    }
    tot /= float(AA*AA);
	#endif
	return vec4(tot, 1.0 );
}




void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
