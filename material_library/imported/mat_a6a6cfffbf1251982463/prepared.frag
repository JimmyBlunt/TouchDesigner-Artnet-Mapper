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

uniform vec4 uMMParam000; // native input: mat_speedx
float mat_speedx = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_speedy
float mat_speedy = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_density
float mat_density = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_direction
vec2 mat_direction = uMMParam003.xy;
float mat_timex = uTDTime * (mat_speedx);
float mat_timey = uTDTime * (mat_speedy);






















		vec2 mod289(vec2 x) {
		  return x - floor(x * (1.0 / 289.0)) * 289.0;
		}

		vec3 mod289(vec3 x) {
		  	return x - floor(x * (1.0 / 289.0)) * 289.0;
		}
		
		vec4 mod289(vec4 x) {
		  	return x - floor(x * (1.0 / 289.0)) * 289.0;
		}
		
		vec3 permute(vec3 x) {
		  return mod289(((x*34.0)+1.0)*x);
		}

		vec4 permute(vec4 x) {
		  return mod((34.0 * x + 1.0) * x, 289.0);
		}

		vec4 taylorInvSqrt(vec4 r)
		{
		  	return 1.79284291400159 - 0.85373472095314 * r;
		}
		
		float snoise(vec2 v)
		{
				const vec4 C = vec4(0.211324865405187,0.366025403784439,-0.577350269189626,0.024390243902439);
				vec2 i  = floor(v + dot(v, C.yy) );
				vec2 x0 = v -   i + dot(i, C.xx);
				
				vec2 i1;
				i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
				vec4 x12 = x0.xyxy + C.xxzz;
				x12.xy -= i1;
				
				i = mod289(i); 
				vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
					+ i.x + vec3(0.0, i1.x, 1.0 ));
				
				vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
				m = m*m ;
				m = m*m ;
				
				vec3 x = 2.0 * fract(p * C.www) - 1.0;
				vec3 h = abs(x) - 0.5;
				vec3 ox = floor(x + 0.5);
				vec3 a0 = x - ox;
				
				m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
				
				vec3 g;
				g.x  = a0.x  * x0.x  + h.x  * x0.y;
				g.yz = a0.yz * x12.xz + h.yz * x12.yw;

				return 130.0 * dot(m, g);		
		}
		
		float cellular2x2(vec2 P)
		{
				#define K 0.142857142857 
				#define K2 0.0714285714285 
				#define jitter 0.8 
				
				vec2 Pi = mod(floor(P), 289.0);
				vec2 Pf = fract(P);
				vec4 Pfx = Pf.x + vec4(-0.5, -1.5, -0.5, -1.5);
				vec4 Pfy = Pf.y + vec4(-0.5, -0.5, -1.5, -1.5);
				vec4 p = permute(Pi.x + vec4(0.0, 1.0, 0.0, 1.0));
				p = permute(p + Pi.y + vec4(0.0, 0.0, 1.0, 1.0));
				vec4 ox = mod(p, 7.0)*K+K2;
				vec4 oy = mod(floor(p*K),7.0)*K+K2;
				vec4 dx = Pfx + jitter*ox;
				vec4 dy = Pfy + jitter*oy;
				vec4 d = dx * dx + dy * dy; 
				
				
				
				d.xy = min(d.xy, d.zw);
				d.x = min(d.x, d.y);
				return d.x; 
		}

		float fbm(vec2 p) {
 		   float f = 0.0;
    		float w = 0.5;
    		for (int i = 0; i < 5; i ++) {
						f += w * snoise(p);
						p *= 2.;
						w *= 0.5;
    		}
    		return f;
		}
vec4 materialColorForPixel( vec2 texCoord )
{

		float speed=2.0;
				
				vec2 uv = texCoord.xy*2.-1.;
									
				vec2 GA = vec2(0.);
				GA.x-=mat_timex*mat_direction.x;
				GA.y+=mat_timey*mat_direction.y;
		
				float F1=0.0,mm_material_F2=0.0,mm_material_F3=0.0,mm_material_F4=0.0,F5=0.0,N1=0.0,N2=0.0,N3=0.0,N4=0.0,N5=0.0;
				float A=0.0,A1=0.0,A2=0.0,A3=0.0,A4=0.0,A5=0.0;

				
				A = 0.5; 

				
				F1 = 1.0-cellular2x2((uv+(GA*0.1))*8.0*mat_density);	
				A1 = 1.0-(A*1.0);
				N1 = smoothstep(0.998,1.0,F1)*1.0*A1;	

				mm_material_F2 = 1.0-cellular2x2((uv+(GA*0.2))*6.0*mat_density);	
				A2 = 1.0-(A*0.8);
				N2 = smoothstep(0.995,1.0,mm_material_F2)*0.85*A2;				

				mm_material_F3 = 1.0-cellular2x2((uv+(GA*0.4))*4.0*mat_density);	
				A3 = 1.0-(A*0.6);
				N3 = smoothstep(0.99,1.0,mm_material_F3)*0.65*A3;				

				mm_material_F4 = 1.0-cellular2x2((uv+(GA*0.6))*3.0*mat_density);	
				A4 = 1.0-(A*1.0);
				N4 = smoothstep(0.98,1.0,mm_material_F4)*0.4*A4;				

				F5 = 1.0-cellular2x2((uv+(GA))*1.2*mat_density);	
				A5 = 1.0-(A*1.0);
				N5 = smoothstep(0.98,1.0,F5)*0.25*A5;				
								
				float Snowout=N5+N4+N3+N2+N1;
				
				vec4 col = vec4(Snowout*0.9, Snowout, Snowout*1.1, 1.0);

	return col;
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
