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

uniform vec4 uMMParam000; // native input: mat_zoom
float mat_zoom = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam001.x > 0.5;
uniform vec4 uMMParam002; // native input: mat_reverse
bool mat_reverse = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_speed
float mat_speed = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_offset
float mat_offset = uMMParam004.x;
uniform vec4 uMMParam005; // native input: mat_strob
float mat_strob = uMMParam005.x;
float mat_time = uTDTime * (mat_speed);














































































#define R mat2(cos(1.57*vec4(0,3,1,0)    

float adjusted_time(float m_time, float m_decay, float m_release)
{

    float adj_time;

    if (m_time < m_decay) {
        adj_time = 1;
    } else {
        
        adj_time = (m_time - m_decay) * 1 / (1 - m_decay);
        if (m_time < m_release) {
            adj_time = 1 - adj_time * 1 / m_release;
        } else {
            adj_time = 0;
        }
    }

    return adj_time;

}


vec4 materialColorForPixel( vec2 texCoord ) {


	vec2 U = texCoord;

	vec4 O = vec4(1.0, 1.0, 1.0, 1.0);

	U *= mat_zoom;

    U *= 10;

	float adj_time = mat_time;
	adj_time = adj_time - mat_offset;



	

	



	



	

    
  
  

    
    
     U = abs( R+adj_time)) * ( U - R-1.25))*ceil( R+1.25))*U/3.2 -.5 )*3.2 )  );

    
    O = smoothstep(.5, .4, max(min(U.x,U.y),max(U.x,U.y)-1.) ) +O-O;   
	return O;
}






void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
