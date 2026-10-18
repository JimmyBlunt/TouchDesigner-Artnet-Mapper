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

uniform vec4 uMMParam000; // native input: speed
float speed = uMMParam000.x;
uniform vec4 uMMParam001; // native input: scale
float scale = uMMParam001.x;
uniform vec4 uMMParam002; // native input: kontrast
float kontrast = uMMParam002.x;
uniform vec4 uMMParam003; // native input: parallaxX
float parallaxX = uMMParam003.x;
uniform vec4 uMMParam004; // native input: parallaxY
float parallaxY = uMMParam004.x;
float animation_time = uTDTime * (speed);
























































 
#define clouds_volsteps 8
#define clouds_stepsize 0.190
 
#define clouds_zoom 3.900
#define clouds_tile   0.450
 
#define clouds_distfading 0.560
#define clouds_saturation 0.400

#define cloud 0.2

float triangle(float x, float a)
{
    float output2 = 2.0*abs(  2.0*  ( (x/a) - floor( (x/a) + 0.5) ) ) - 1.0;
    return output2;
}
 

float field(in vec3 p) {
    float strength = 7. + .03 * log(1.e-6 + fract(sin(animation_time) * 4373.11));
    float accum = 0.;
    float prev = 0.;
    float tw = 0.;
    

    for (int i = 0; i < 6; ++i) {
        float mag = dot(p, p);
        p = abs(p) / mag + vec3(-.5, -.8 + 0.1*sin(animation_time*0.2 + 2.0), -1.1+0.3*cos(animation_time*0.15));
        float w = exp(-float(i) / 7.);
        accum += w * exp(-strength * pow(abs(mag - prev), 2.3));
        tw += w;
        prev = mag;
    }
    return max(0., 5. * accum / tw - .7);

}

vec4 materialColorForPixel(vec2 texCoord)
{
    
    vec2 uv = vec2(0.5,0.5) + (texCoord-vec2(0.5,0.5)) * scale;
               
    float a_xz = 0.9;
    float a_yz = -.6;
    float a_xy = 0.9 + animation_time*0.04;
        
    mat2 rot_xz = mat2(cos(a_xz),sin(a_xz),-sin(a_xz),cos(a_xz));   
    mat2 rot_yz = mat2(cos(a_yz),sin(a_yz),-sin(a_yz),cos(a_yz));       
    mat2 rot_xy = mat2(cos(a_xy),sin(a_xy),-sin(a_xy),cos(a_xy));
        
    vec3 dir=vec3(uv*clouds_zoom,1.);
 
    vec3 from=vec3(0.0, 0.0,0.0);
    
    from.x -= (parallaxX)*scale;
    from.y -= (parallaxY)*scale;
    
    vec3 forward = vec3(0.,0.,1.);
                
    from.z += 0.003*animation_time;
    
    dir.xy*=rot_xy;
    forward.xy *= rot_xy;

    dir.xz*=rot_xz;
    forward.xz *= rot_xz;

    dir.yz*= rot_yz;
    forward.yz *= rot_yz;
    
    from.xy*=-rot_xy;
    from.xz*=rot_xz;
    from.yz*= rot_yz;
     
    
    float zooom = (animation_time-3311.)*0.01;
    from += forward* zooom;
    float sampleShift = (0.5+0.5*sin( zooom )) * clouds_stepsize;
     
    float zoffset = -sampleShift;
    sampleShift /= clouds_stepsize; 

    
    float s=0.24;
    float s3 = s + clouds_stepsize/2.0;
    vec3 v=vec3(0.);
    float t3 = 0.0;

    vec3 backCol2 = vec3(0.);
    for (int r=0; r<clouds_volsteps; r++) {
        vec3 p3=(from+(s3+zoffset)*dir )* (1.9/clouds_zoom);
        
        p3 = abs(vec3(clouds_tile)-mod(p3,vec3(clouds_tile*2.))); 
        
        #ifdef cloud
        t3 = field(p3);
        #endif
    
        float fade = pow(clouds_distfading,max(0.,float(r)-sampleShift));
        
        backCol2 += 0.75 * vec3(t3 ) * fade;
        
        s+=clouds_stepsize;
        s3 += clouds_stepsize;        
    }
               
    v=mix(vec3(length(v)),v,clouds_saturation); 
    
    #ifdef cloud
    backCol2 *= cloud;
    #endif
    
    vec4 color = vec4(backCol2, 1.0);
    color.rgb = pow(color.rgb + vec3(kontrast*0.05),vec3(kontrast));
    return color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
