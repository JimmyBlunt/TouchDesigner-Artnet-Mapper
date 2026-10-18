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
int mat_scale = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: mat_grid
int mat_grid = int(round(uMMParam001.x));

















vec2 ran2( vec2 p ) 
{
	return fract(sin(vec2(dot(p,vec2(127.1,311.7)),
			  			  dot(p,vec2(269.5,183.3))))
                 			* 43758.5453123);
}

float TileCell(vec2 tc, int grid, float seed)
{
    vec2 p   = tc * float(grid);
    vec2 ftc = fract(p);
    vec2 itc = floor(p);
    float m  = 1.0;
    
    for(int i = -1; i < 2; i++)
    {
        for(int j = -1; j < 2; j++)
        {
            vec2 n = vec2(i,j);
            vec2 q = itc + n;
            
            if(q.x == -1.0)q.x = float(grid-1);
            else if(q.x == float(grid))q.x = 0.0;
                
            if(q.y == -1.0)q.y =float(grid-1);
            else if(q.y == float(grid))q.y = 0.0;

            vec2 rp 	= ran2(q * seed);
            vec2 diff 	= n + rp - ftc;
            float dist 	= length(diff);
            m 			= min(m,dist);
        }
    } 
    
    return pow(1.0 - m,1.0);
}


vec4 materialColorForPixel( vec2 texCoord )
{

	vec2 uv 	= texCoord;
	uv *= float(mat_scale);
	uv = fract(uv);
 
    float c 	= TileCell(uv,mat_grid,1.0);
	return vec4(c,c,c,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
