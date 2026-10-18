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

const int mat_mode = 1;
#define mat_mode_IS_Filled
uniform vec4 uMMParam001; // native input: mat_waveform_thickness
float mat_waveform_thickness = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_waveform_smooth
float mat_waveform_smooth = uMMParam002.x;
uniform vec4 uMMParam003; // native input: mat_time_scale
float mat_time_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_waveform_amplitude
float mat_waveform_amplitude = uMMParam004.x;
#define mat_waveform sTD2DInputs[0]






















































vec4 materialColorForPixel(vec2 texCoord)
{
    float width = mat_waveform_thickness * mat_waveform_thickness;

    #if defined(mat_mode_IS_Lost)
        float posY = 0.5;
        posY += (IMG_NORM_PIXEL(mat_waveform,vec2(texCoord.x*mat_time_scale,0)).r * mat_waveform_amplitude) / 6;
        posY += (IMG_NORM_PIXEL(mat_waveform,vec2(texCoord.x*mat_time_scale - 1.0/mat_waveform_size.x,0)).r * mat_waveform_amplitude) / 6;
        posY += (IMG_NORM_PIXEL(mat_waveform,vec2(texCoord.x*mat_time_scale + 1.0/mat_waveform_size.x,0)).r * mat_waveform_amplitude) / 6;
        float value = smoothstep(width,0,abs(texCoord.y-posY))*4;
    #else 
        float posY1 = 0.5 + (IMG_NORM_PIXEL(mat_waveform,vec2(texCoord.x*mat_time_scale,0)).r * mat_waveform_amplitude);
        float posY2 = 0.5 + (IMG_NORM_PIXEL(mat_waveform,vec2((texCoord.x+width)*mat_time_scale,0)).r * mat_waveform_amplitude);

        float minY = min(posY1,posY2)-1./800.;
        float maxY = max(posY1,posY2)+1./800.;
        float centerY = (minY+maxY)/2;

        float value;
        if (texCoord.y>=centerY)
            value = 1-smoothstep(maxY+(0.99999-mat_waveform_smooth)*width,maxY+width,texCoord.y);
        else
            value = 1-smoothstep(minY-(0.99999-mat_waveform_smooth)*width,minY-width,texCoord.y);
    #endif

    return vec4(vec3(value),1);
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
