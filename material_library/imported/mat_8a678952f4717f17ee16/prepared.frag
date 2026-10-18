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

uniform vec4 uMMParam000; // native input: mat_offset
vec2 mat_offset = uMMParam000.xy;
uniform vec4 uMMParam001; // native input: mat_number
float mat_number = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_tint
vec4 mat_tint = uMMParam002;
uniform vec4 uMMParam003; // native input: mat_invert
bool mat_invert = uMMParam003.x > 0.5;
















float segment(vec2 uv, bool On) {
	return (On) ?  (1.-smoothstep(0.08,0.09+float(On)*0.02,abs(uv.x)))*
			       (1.-smoothstep(0.46,0.47+float(On)*0.02,abs(uv.y)+abs(uv.x)))
		        : 0.;
}

float digit(vec2 uv,int num) {
	float seg= 0.;
    seg += segment(uv.yx+vec2(-1., 0.),num!=-1 && num!=1 && num!=4                    );
	seg += segment(uv.xy+vec2(-.5,-.5),num!=-1 && num!=1 && num!=2 && num!=3 && num!=7);
	seg += segment(uv.xy+vec2( .5,-.5),num!=-1 && num!=5 && num!=6                    );
   	seg += segment(uv.yx+vec2( 0., 0.),num!=-1 && num!=0 && num!=1 && num!=7          );
	seg += segment(uv.xy+vec2(-.5, .5),num==0 || num==2 || num==6 || num==8           );
	seg += segment(uv.xy+vec2( .5, .5),num!=-1 && num!=2                              );
    seg += segment(uv.yx+vec2( 1., 0.),num!=-1 && num!=1 && num!=4 && num!=7          );	
	return seg;
}

float showNum(vec2 uv,int nr, bool zeroTrim) { 
	if (abs(uv.x)>2.*1.5 || abs(uv.y)>1.2) return 0.;

	if (nr<0) {
		nr = -nr;
		if (uv.x>1.5) {
			uv.x -= 2.;
			return segment(uv.yx,true); 
		}
	}
	
	if (uv.x>0.) {
		nr /= 10; if (nr==0 && zeroTrim) nr = -1;
		uv -= vec2(.75,0.);
	} else {
		uv += vec2(.75,0.); 
		nr = int(mod(float(nr),10.));
	}

	return digit(uv,nr);
}

float dots(vec2 uv, int dot) { 
	float point0 = float(dot/2),
		  point1 = float(dot)-2.*point0; 
	uv.y -= .5;	float l0 = 1.-point0+length(uv); if (l0<.13) return (1.-smoothstep(.11,.13,l0));
	uv.y += 1.;	float l1 = 1.-point1+length(uv); if (l1<.13) return (1.-smoothstep(.11,.13,l1));
	return 0.;
}


#define STEPX .875
#define STEPY 1.5
float _offset=0.; 


bool display(vec2 pos, float scale, float offset, int number, int dot, vec2 uv) { 

	uv = (uv-pos)/scale*2.; 
    uv.x = .5-uv.x + STEPX*offset;
	uv.y -= 1.;
	
	float seg = showNum(uv,number,false);
	offset += 2.;
	
	if (dot>0) {
		uv.x += STEPX*offset; 
		offset += 2.;
	}


	_offset = offset;
	return (seg>0.);
}


bool display(vec2 pos, float scale, float offset, float val,vec2 uv) { 
	if (display( pos, scale, 0., int(val), 1,uv)) return true;
    if (display( pos, scale, _offset, int(fract(abs(val))*100.), 0,uv)) return true;
	return false;
}

vec4 materialColorForPixel( vec2 texCoord )
{
	
	vec2 uv = texCoord;
	
	uv *= 2.;
	uv += vec2(-mat_offset.x,mat_offset.y-1.);
	uv.y *= -1;

	
	vec2 pos ; 
	float scale = 0.5;
	vec3 color = vec3( 0.);
	
	pos = vec2(0.3,0.25);   
	if (display( pos, scale, 0., (mat_number),uv)) { color = vec3(1.); }

	
	color *= mat_tint.rgb;
	
	color = mix(color, vec3(1.0)-color,float(mat_invert));
		
	vec4 final_color = vec4(color,1.0);	
	return final_color;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
