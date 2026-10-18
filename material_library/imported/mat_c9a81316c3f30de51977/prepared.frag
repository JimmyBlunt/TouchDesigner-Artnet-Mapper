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
uniform vec4 uMMParam002; // native input: mat_hq
bool mat_hq = uMMParam002.x > 0.5;
uniform vec4 uMMParam003; // native input: mat_offset
vec2 mat_offset = uMMParam003.xy;
uniform vec4 uMMParam004; // native input: mat_A
vec4 mat_A = uMMParam004;
uniform vec4 uMMParam005; // native input: mat_B
vec4 mat_B = uMMParam005;
uniform vec4 uMMParam006; // native input: mat_contrast
float mat_contrast = uMMParam006.x;
float mat_time = uTDTime * (mat_speed);
#define mat_tex sTD2DInputs[0]

























vec4 noise(float p){return texture(mat_tex,vec2(p*float(1.0/256.0),.0));}
vec4 noise(vec2 p){return texture(mat_tex,p*vec2(1.0/256.0));}
vec4 noise(vec3 p){float m = mod(p.z,1.0);float s = p.z-m; float sprev = s-1.0;if (mod(s,2.0)==1.0) { s--; sprev++; m = 1.0-m; };return mix(texture(mat_tex,p.xy*vec2(1.0/256.0) + noise(sprev).yz*21.421),texture(mat_tex,p.xy*vec2(1.0/256.0) + noise(s).yz*14.751),m);}
vec4 noise(vec4 p){float m = mod(p.w,1.0);float s = p.w-m; float sprev = s-1.0;if (mod(s,2.0)==1.0) { s--; sprev++; m = 1.0-m; };return mix(noise(p.xyz+noise(sprev).wyx*3531.123420),	noise(p.xyz+noise(s).wyx*4521.5314),	m);}


mat2 rotate_2D(float a){float sa = sin(a); float ca = cos(a); return mat2(ca,sa,-sa,ca);}
mat3 rotate_x(float a){float sa = sin(a); float ca = cos(a); return mat3(1.,.0,.0,    .0,ca,sa,   .0,-sa,ca);}
mat3 rotate_y(float a){float sa = sin(a); float ca = cos(a); return mat3(ca,.0,sa,    .0,1.,.0,   -sa,.0,ca);}
mat3 rotate_z(float a){float sa = sin(a); float ca = cos(a); return mat3(ca,sa,.0,    -sa,ca,.0,  .0,.0,1.);}

const float toffs = -152.0;
float t;


float density(vec3 p)
{
	vec4 d = noise(p*.25)*noise(p.xz*.044)*noise(p.xy*.067)*noise(p.yz*.21);
	float fd = dot(d,vec4(1.4));
	fd = fd*fd*fd*fd*fd;
	
	return max(.0,fd);
}

vec4 materialColorForPixel( vec2 texCoord )
{

    t = mat_time*0.1 + toffs;
    
    vec2 uv = texCoord *2. -1.;
	uv *= mat_scale;
	vec2 m =mat_offset;
	
	mat3 rotmat = rotate_y((t-toffs)*.07+m.x+0.2)*rotate_x((t-toffs)*.031+m.y+0.2);
	
	vec3 p = vec3(.0,.0,-30.0); p*=rotmat;
	p += vec3(sin(t),cos(t),sin(t*.25)*29.0+t*7.0-22.0-4.0/((t-toffs)*.01+0.01));
	
	vec3 d = normalize(vec3(uv*(sin(t*.17)*.2+0.8),1.0-length(uv)*.2));
	d*=rotmat;
	
	
	float a = .0;
	float ai = .0;
	vec3 color = vec3(.0);


	for (int i=0; i<50 + int(mat_hq)*50; i++)
	{
		
		p+=d*.3;

		vec3 n = noise(p.xz*.25+vec2(t*.1)).xyz*12.0*noise(p.zy*.1+vec2(t*.1)).xyz;

		float de = density(p+n);
		a += de; 
		a = min(1.0,a); 
		vec4 c2 = noise(p.yz*.03).xyzw;
		c2.xyz = c2.xxx;
		vec3 c = c2.xyz*1.7;
		
		float occ = min((de-density(p+vec3(0.7+n))),1.0);

		color += max(.0,occ)*(1.0-a)*c;

		if (a>1.0) break; 
	}

	color *= 4.*pow(mat_contrast,4.);
	color = min(color,vec3(1.));
	color = mix(mat_A.rgb,mat_B.rgb,color);

	return vec4(color,1.);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
