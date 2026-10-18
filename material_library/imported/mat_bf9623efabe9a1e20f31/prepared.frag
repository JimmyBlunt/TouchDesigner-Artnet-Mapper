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
uniform vec4 uMMParam001; // native input: mat_rotate
float mat_rotate = uMMParam001.x;
uniform vec4 uMMParam002; // native input: slide_x
float slide_x = uMMParam002.x;
uniform vec4 uMMParam003; // native input: slide_y
float slide_y = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam004.x > 0.5;
uniform vec4 uMMParam005; // native input: mat_reverse
bool mat_reverse = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_speed
float mat_speed = uMMParam006.x;
uniform vec4 uMMParam007; // native input: mat_offset
float mat_offset = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_strob
float mat_strob = uMMParam008.x;
uniform vec4 uMMParam009; // native input: complexity_a
int complexity_a = int(round(uMMParam009.x));
uniform vec4 uMMParam010; // native input: mod_a
float mod_a = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mod_b
float mod_b = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mod_c
float mod_c = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mod_d
float mod_d = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mod_e
float mod_e = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mod_f
float mod_f = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mod_g
float mod_g = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mod_h
float mod_h = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mod_i
float mod_i = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mod_j
float mod_j = uMMParam019.x;
float mat_time = uTDTime * (mat_speed);






















































































































#define PI 3.14159265359

float mat_iTime = mat_time - mat_offset;

vec2 mat_rotate2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}





















vec2 sc,y,e=vec2(.000035,-.000035);
float t,tt=0.,b,bb=0.,g1=0.,g2=0.;
vec3 np,bp;

float mat_bo(vec3 p,vec3 r){vec3 q=abs(p)-r;return max(max(q.x,q.y),q.z);}
float mat_cy(vec3 p,float r){p.y=0.;return length(p)-r;}
float mat_cz(vec3 p,float r){p.z=0.;return length(p)-r;}
mat2 mat_r2(float r){return mat2(cos(r),sin(r),-sin(r),cos(r));}
vec2 mat_fb(vec3 p,vec3 m, float s)
{
  p.xz*=mat_r2(s)*mod_g;
  p.xy*=mat_r2(s+bb*1.4)*mod_h;
  vec2 h,t=vec2(mat_bo(abs(p)-vec3(0,0,1),mod_i*vec3(2.2,0.3,0.7)),m.x);
  t.x=min(.6*mat_cy(abs(abs(p)-vec3(0.5,0,0))-vec3(0.5,0,1),0.1),t.x);
  if(m.x<6.) g2+=0.1/(0.1+pow(abs(t.x),2.));
  h=vec2(mat_bo(abs(p)-vec3(0,0,1),vec3(2.0,0.5,0.5)),m.y);
  t=(t.x<h.x)?t:h;
  h=vec2(mat_bo(p,vec3(1.8,0.2,2.8)),m.z);
  t=(t.x<h.x)?t:h;
  t.x*=0.7;
  return t;
}
float mat_noise(vec3 p){
  vec3 ip=floor(p),s=vec3(7,157,113);
  p-=ip; vec4 h=vec4(0,s.yz,s.y+s.z)+dot(ip,s);
  p=p*p*(3.-2.*p);
  h=mix(fract(sin(h)*43758.5),fract(sin(h+s.x)*43758.5),p.x);
  h.xy=mix(h.xz,h.yw,p.y);
  return mix(h.x,h.y,p.z);
}
vec2 mp( vec3 p ) 
{
  b=sin(p.z-tt*10.)*0.1*mod_a;
  np=p;
  for(int i=0;i<complexity_a;i++){
    np=abs(np)-vec3(2.5,1.7,0)*mod_e;
    np.xy*=mat_r2(cos(p.y*0.05)*0.5)*mod_f;
    np.xz*=mat_r2(20.);
  }
  vec2 h,t=mat_fb(np,vec3(5,3,6),b);
  bp=np;bp.yz*=mat_r2(.785);bp=abs(bp*0.5*mod_b)-vec3(3.2*mod_d);
  np.xz*=mat_r2(b);
  np.xy*=mat_r2(b+bb*1.4);
  h=mat_fb(bp,vec3(7,8,9),0.1);
  h.x*=2.0;
  t=(t.x<h.x)?t:h;
  h=vec2(mat_cz(p,0.5-b),8)*mod_c;
  h.x=min(length(p)-6.+b,h.x);
  g1+=0.1/(0.1+pow(abs(h.x),2.));
  t=(t.x<h.x)?t:h;
  return t;
}
vec2 tr( vec3 ro, vec3 rd )
{
  vec2 h,t=vec2(0.1);
  for(int i=0;i<128;i++){
    h=mp(ro+rd*t.x);
    if(h.x<.0001||t.x>50.) break;
    t.x+=h.x;t.y=h.y;
  }
  if(t.x>50.) t.x=0.;
  return t;
}

vec4 materialColorForPixel( vec2 texCoord ) {
      

      vec2 uv = texCoord;

      uv = mat_rotate2D(uv,PI*mat_rotate);
      uv -= 0.5;


      uv.x -= slide_x;
      uv.y -= slide_y;

    


      



      uv *= mat_zoom;

      tt=mod(mat_iTime,100.);
        bb=0.5+clamp(sin(tt),-0.5,0.5);
      vec3 ro=vec3(cos(tt*0.5)*15.,sin(tt*0.5)*15.,-20),
      cw=normalize(vec3(0)-ro),cu=normalize(cross(cw,vec3(0,1,0))),cv=normalize(cross(cu,cw)),
      rd=mat3(cu,cv,cw)*normalize(vec3(uv,.5)),
      co,fo,ld=normalize(vec3(0,0.5,-0.5));
      co=fo=vec3(.04)*(1.-(length(uv)-.2));
      sc=tr(ro,rd);t=sc.x;

      if(t>0.){
          
          vec3 po=ro+rd*t,no=normalize(e.xyy*mp(po+e.xyy).x+e.yyx*mp(po+e.yyx).x+e.yxy*mp(po+e.yxy).x+e.xxx*mp(po+e.xxx).x),
          
          al=vec3(1,0.05,0);
          float dif=max(0.,dot(no,ld)),
          aor=t/50.,ao=exp2(-2.*pow(max(0.,1.-mp(po+no*aor).x/aor),2.)),
          fr=pow(1.+dot(no,rd),4.),
          spo=exp(1.+3.*mat_noise(np/vec3(.1,.2,.4)));
          
          if(sc.y<5.) al=vec3(0);
          if(sc.y>5.) al=vec3(1);
          if(sc.y>6.) {al=vec3(0.1,0.5,0.9);spo=exp(1.+3.*mat_noise(bp/vec3(.1,.2,.4))); no*=(1.+.6*ceil(cos(bp*4.)));no=normalize(no);}
          if(sc.y>7.) {al=vec3(0);}
          if(sc.y>8.) {al=vec3(1);}

          vec3 sss=vec3(0.5)*smoothstep(0.,1.,mp(po+ld*0.4).x/0.4),
          sp=vec3(0.5)*pow(max(dot(reflect(-ld,no),-rd),0.),spo);
          co=mix(sp+al*(.8*ao+0.2)*(dif+sss),fo,fr);
          co=mix(co,fo,1.-exp(-.0001*t*t*t));
      }
      co+=g1*0.3;
        co+=vec3(1,0.05,0)*g2*(0.004*bb);
      return vec4(pow(co,vec3(0.45)),1);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
