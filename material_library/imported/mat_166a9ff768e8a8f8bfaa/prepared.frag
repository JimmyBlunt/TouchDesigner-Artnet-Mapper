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
uniform vec4 uMMParam001; // native input: mat_complex
int mat_complex = int(round(uMMParam001.x));
uniform vec4 uMMParam002; // native input: mat_outline
bool mat_outline = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_distort
float mat_distort = uMMParam003.x;
float mat_time = uTDTime * (mat_speed);

















float df;

#define pal(a,b,c,d,e) (a + (b)*sin((c)*(d) + e))

vec3 add(float da, float db, vec3 cola, vec3 colb, float method){
    vec3 colo = vec3(0);
    
    float aa = smoothstep(df,0.,db);
    
    if (method == 0.){
        colo = mix(cola,colb,aa);
    }
    return colo;
}

mat2 rot(float angle){
    return mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
}
#define xor(a,b,c) min(max(a,-(b)), max(-(a) + c,b))


vec4 materialColorForPixel( vec2 texCoord )
{
    vec2 p = (texCoord *2. - 1.)*0.7;
    vec2 uv = p;
    
    float env = pow(abs(sin(mat_time*0.5)),0.3)*sign(sin(mat_time*0.5 ))*0.5 + 0.5 ;   
    
    p += vec2(sin(mat_time + sin(mat_time*0.4))*0.04,sin(mat_time*0.6 - sin(mat_time*0.4))*0.04);
    
    p *= 1. + env;
    df = dFdx(p.x);
    
    vec3 col = vec3(0.01,0.4,0.91);
    
    col += sin(p.xyy + sin(mat_time + length(p))*0.4)*0.5;
      
    float d = 10e4;  
    vec3 colo = vec3(0);

  #define TP(P) (floor(T) + pow(fract(T),P))

    float T = mat_time - 14.;
    for(float i = 0.; i < mat_complex; i++){
        float env = sin(TP(5. + sin(i)*2.));
        env = pow(abs(env),4.)*sign(env);
        T += mat_distort;
        p.x += 0. + env*0.004;
        p *= rot(sin(TP(2.)*0.001)*0.41);
        float ld = length(p) - .2 - sin(i*1.4 + sin(T)*0.2)*0.4;
        vec3 c = pal(0.5,.5,vec3(3,2.1,1.5),1.,i + p.x);
        
        if(sin(i *0.4) < -0.4){
            ld = xor(ld,-(p.y) - .5*sin(i + T*0.13 ),.4);
            
        }
        if(sin(i *0.4) > 0.1){
            ld = abs(ld - 0.1*sin(i + TP(5.)));
        }
            
        colo = add(d,ld,colo,c,0.);
        
        
        d = xor(d,ld,-0. - sin(i)*0.1);
        
        if(mat_outline)d = min(d,ld);
    }

    col = add(10.,d + 0.01,col,colo,0.);       
      
    col = mix(1. - col,col, env);    
    col *= smoothstep(1.,0.,dot(uv,uv)*0.7);
    
    col = mix(col,smoothstep(0.,1.,col),0.6);
    
    col = pow(col,vec3(0.454545));

	return vec4(col,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
