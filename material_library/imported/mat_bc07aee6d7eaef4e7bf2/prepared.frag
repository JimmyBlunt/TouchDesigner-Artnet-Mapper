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

uniform vec4 uMMParam000; // native input: restart
int restart = int(round(uMMParam000.x));
uniform vec4 uMMParam001; // native input: line_width
float line_width = uMMParam001.x;
uniform vec4 uMMParam002; // native input: smoothness
float smoothness = uMMParam002.x;
uniform vec4 uMMParam003; // native input: repeat
int repeat = int(round(uMMParam003.x));
uniform vec4 uMMParam004; // native input: line_rotate
float line_rotate = uMMParam004.x;
uniform vec4 uMMParam005; // native input: bpmsync
bool bpmsync = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: bpm_phase_sync
bool bpm_phase_sync = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: reverse
bool reverse = uMMParam007.x > 0.5;
uniform vec4 uMMParam008; // native input: speed
float speed = uMMParam008.x;
uniform vec4 uMMParam009; // native input: bpm_offset
float bpm_offset = uMMParam009.x;
uniform vec4 uMMParam010; // native input: bpm_offset_alt
float bpm_offset_alt = uMMParam010.x;
uniform vec4 uMMParam011; // native input: bpm_strob
float bpm_strob = uMMParam011.x;
uniform vec4 uMMParam012; // native input: decay
float decay = uMMParam012.x;
uniform vec4 uMMParam013; // native input: release
float release = uMMParam013.x;
uniform vec4 uMMParam014; // native input: strobe_on
bool strobe_on = uMMParam014.x > 0.5;
uniform vec4 uMMParam015; // native input: strobe_div
int strobe_div = int(round(uMMParam015.x));
uniform vec4 uMMParam016; // native input: strobe_offset
float strobe_offset = uMMParam016.x;
uniform vec4 uMMParam017; // native input: strobe_audio_enable
bool strobe_audio_enable = uMMParam017.x > 0.5;
uniform vec4 uMMParam018; // native input: strobe_audio_thresh
float strobe_audio_thresh = uMMParam018.x;
uniform vec4 uMMParam019; // native input: bass_level
float bass_level = uMMParam019.x;
uniform vec4 uMMParam020; // native input: medium_level
float medium_level = uMMParam020.x;
uniform vec4 uMMParam021; // native input: treble_level
float treble_level = uMMParam021.x;
uniform vec4 uMMParam022; // native input: master_scale
float master_scale = uMMParam022.x;
const int animation = 2;
#define animation_IS_Single
uniform vec4 uMMParam024; // native input: rotate
float rotate = uMMParam024.x;
uniform vec4 uMMParam025; // native input: post_rotate
float post_rotate = uMMParam025.x;
const int mirror_x = 0;
#define mirror_x_IS_None
uniform vec4 uMMParam027; // native input: slide_x
float slide_x = uMMParam027.x;
const int mirror_y = 0;
#define mirror_y_IS_None
uniform vec4 uMMParam029; // native input: slide_y
float slide_y = uMMParam029.x;
uniform vec4 uMMParam030; // native input: border_x
float border_x = uMMParam030.x;
uniform vec4 uMMParam031; // native input: border_y
float border_y = uMMParam031.x;
uniform vec4 uMMParam032; // native input: front_edge_mode
int front_edge_mode = int(round(uMMParam032.x));
uniform vec4 uMMParam033; // native input: back_edge_mode
int back_edge_mode = int(round(uMMParam033.x));
uniform vec4 uMMParam034; // native input: alternate_edges
bool alternate_edges = uMMParam034.x > 0.5;
uniform vec4 uMMParam035; // native input: cells_x
int cells_x = int(round(uMMParam035.x));
uniform vec4 uMMParam036; // native input: cells_y
int cells_y = int(round(uMMParam036.x));
uniform vec4 uMMParam037; // native input: offset
float offset = uMMParam037.x;
uniform vec4 uMMParam038; // native input: random_offset
bool random_offset = uMMParam038.x > 0.5;
uniform vec4 uMMParam039; // native input: alternate_offset
bool alternate_offset = uMMParam039.x > 0.5;
uniform vec4 uMMParam040; // native input: alternate_direction
bool alternate_direction = uMMParam040.x > 0.5;
uniform vec4 uMMParam041; // native input: strobe_level
float strobe_level = uMMParam041.x;
uniform vec4 uMMParam042; // native input: strob_bpmsync
bool strob_bpmsync = uMMParam042.x > 0.5;
uniform vec4 uMMParam043; // native input: strob_reverse
bool strob_reverse = uMMParam043.x > 0.5;
uniform vec4 uMMParam044; // native input: strob_speed
float strob_speed = uMMParam044.x;
uniform vec4 uMMParam045; // native input: strob_bpm_offset
float strob_bpm_offset = uMMParam045.x;
uniform vec4 uMMParam046; // native input: strob_bpm_strob
float strob_bpm_strob = uMMParam046.x;
uniform vec4 uMMParam047; // native input: strob_decay
float strob_decay = uMMParam047.x;
uniform vec4 uMMParam048; // native input: strob_release
float strob_release = uMMParam048.x;
uniform vec4 uMMParam049; // native input: strob_shape
int strob_shape = int(round(uMMParam049.x));
uniform vec4 uMMParam050; // native input: foregroundColor
vec4 foregroundColor = uMMParam050;
uniform vec4 uMMParam051; // native input: backgroundColor
vec4 backgroundColor = uMMParam051;
uniform vec4 uMMParam052; // native input: brightness
float brightness = uMMParam052.x;
uniform vec4 uMMParam053; // native input: grad_level
float grad_level = uMMParam053.x;
const int grad_type = 0;
#define grad_type_IS_Auto_Color_Cycle
uniform vec4 uMMParam055; // native input: grad_color_count
int grad_color_count = int(round(uMMParam055.x));
uniform vec4 uMMParam056; // native input: grad_color1
vec4 grad_color1 = uMMParam056;
uniform vec4 uMMParam057; // native input: grad_color2
vec4 grad_color2 = uMMParam057;
uniform vec4 uMMParam058; // native input: grad_color3
vec4 grad_color3 = uMMParam058;
uniform vec4 uMMParam059; // native input: grad_color4
vec4 grad_color4 = uMMParam059;
uniform vec4 uMMParam060; // native input: grad_color5
vec4 grad_color5 = uMMParam060;
uniform vec4 uMMParam061; // native input: grad_color6
vec4 grad_color6 = uMMParam061;
uniform vec4 uMMParam062; // native input: grad_color7
vec4 grad_color7 = uMMParam062;
uniform vec4 uMMParam063; // native input: grad_color8
vec4 grad_color8 = uMMParam063;
uniform vec4 uMMParam064; // native input: grad_color9
vec4 grad_color9 = uMMParam064;
uniform vec4 uMMParam065; // native input: grad_color10
vec4 grad_color10 = uMMParam065;
uniform vec4 uMMParam066; // native input: grad_bpmsync
bool grad_bpmsync = uMMParam066.x > 0.5;
uniform vec4 uMMParam067; // native input: grad_bpm_phase_sync
bool grad_bpm_phase_sync = uMMParam067.x > 0.5;
uniform vec4 uMMParam068; // native input: grad_reverse
bool grad_reverse = uMMParam068.x > 0.5;
uniform vec4 uMMParam069; // native input: grad_speed
float grad_speed = uMMParam069.x;
uniform vec4 uMMParam070; // native input: grad_offset
float grad_offset = uMMParam070.x;
uniform vec4 uMMParam071; // native input: grad_strob
float grad_strob = uMMParam071.x;
uniform vec4 uMMParam072; // native input: grad_decay
float grad_decay = uMMParam072.x;
uniform vec4 uMMParam073; // native input: grad_release
float grad_release = uMMParam073.x;
uniform vec4 uMMParam074; // native input: mat_anim2_shape
int mat_anim2_shape = int(round(uMMParam074.x));
uniform vec4 uMMParam075; // native input: grad_repeat
int grad_repeat = int(round(uMMParam075.x));
uniform vec4 uMMParam076; // native input: grad_rotate
float grad_rotate = uMMParam076.x;
uniform vec4 uMMParam077; // native input: grad_scale
float grad_scale = uMMParam077.x;
uniform vec4 uMMParam078; // native input: grad_size
float grad_size = uMMParam078.x;
uniform vec4 uMMParam079; // native input: grad_curve
float grad_curve = uMMParam079.x;
uniform vec4 uMMParam080; // native input: grad_mode
int grad_mode = int(round(uMMParam080.x));
uniform vec4 uMMParam081; // native input: grad_match_offset
bool grad_match_offset = uMMParam081.x > 0.5;
uniform vec4 uMMParam082; // native input: grad_match_direction
bool grad_match_direction = uMMParam082.x > 0.5;
uniform vec4 uMMParam083; // native input: grad_match_tilt
bool grad_match_tilt = uMMParam083.x > 0.5;
float animation_time = uTDTime * (speed);
float strob_time = uTDTime * (strob_speed);
float grad_time = uTDTime * (grad_speed);
#define spectrum sTD2DInputs[0]
#define spectrum_16_decay sTD2DInputs[1]

// BEGIN MadCommon.glsl
/*
MadCommon Glsl Library

Copyright (c) 2016, Garage Cube, All rights reserved.
Copyright (c) 2016, Simon Geilfus, All rights reserved.

Portions of code from Romain Dura see corresponding licence

Redistribution and use in source and binary forms, with or without modification, are permitted provided that
the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and
 the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
 the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
*/

//! Constants
#define PI 3.1415926535897932384626433832795

//! Returns the luminance of a RGB color
float luma( vec3 color );

//! Returns the luminance of a RGB color
float luminance( vec3 color );

//! Luminance based rgb8/linear conversion
vec3 linearToRgb( vec3 color, vec3 range );

//! Luminance based rgb8/linear conversion
vec3 rgbToLinear( vec3 color, vec3 range );

//! Contrast, saturation, brightness, For all settings: 1.0 = 100% 0.5=50% 1.5 = 150%
vec3 applyContrastSaturationBrightness( vec3 color, float contrast, float saturation, float brightness );

//! Returns HSV values for RGB input color
vec3 rgb2hsv( vec3 color );

//! Returns RGB values for HSV input color
vec3 hsv2rgb( vec3 color );

//! Returns the Hue value for RGB input color
float rgb2hue( vec3 color );

//! Usefull shortcuts
#define saturate(x) clamp( x, 0.0, 1.0 )
#define lerp(x,y,t) mix( x, y, t )

// Implementation

// Luminance
float luma( vec3 color )
{
    // Rec 709 Coefficients
    return dot( color, vec3( 0.2126729, 0.7151522, 0.0721750 ) );
}
float luminance( vec3 color )
{
    return dot( color, vec3( 0.299, 0.587, 0.114 ) );
}

// Luminance based rgb8/linear conversion
vec3 linearToRgb( vec3 color, vec3 range )
{
    return ( color ) / ( vec3( 1.0 ) - vec3( luminance( color ) ) / range );
}

vec3 rgbToLinear( vec3 color, vec3 range )
{
    return ( color ) / ( vec3( 1.0 ) + vec3( luminance( color ) ) / range );
}

// RGB <-> HSV Conversion functions
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    //vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    //vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    vec4 p = c.g < c.b ? vec4(c.bg, K.wz) : vec4(c.gb, K.xy);
    vec4 q = c.r < p.x ? vec4(p.xyw, c.r) : vec4(c.r, p.yzx);
    
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float rgb2hue(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return abs(q.z + (q.w - q.y) / (6.0 * d + e));
}

/*
** Copyright (c) 2012, Romain Dura romain@shazbits.com
** 
** Permission to use, copy, modify, and/or distribute this software for any 
** purpose with or without fee is hereby granted, provided that the above 
** copyright notice and this permission notice appear in all copies.
** 
** THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES 
** WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF 
** MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY 
** SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES 
** WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN 
** ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR 
** IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/


/*
** Contrast, saturation, brightness
** Code of this function is from TGM's shader pack
** http://irrlicht.sourceforge.net/phpBB2/viewtopic.php?t=21057
*/

// For all settings: 1.0 = 100% 0.5=50% 1.5 = 150%
vec3 applyContrastSaturationBrightness( vec3 color, float contrast, float saturation, float brightness )
{
    // Increase or decrease theese values to adjust r, g and b color channels seperately
    const float AvgLumR = 0.5;
    const float AvgLumG = 0.5;
    const float AvgLumB = 0.5;
    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    
    vec3 AvgLumin = vec3(AvgLumR, AvgLumG, AvgLumB);
    vec3 brtColor = color * brightness;
    vec3 intensity = vec3(dot(brtColor, LumCoeff));
    vec3 satColor = mix( intensity, brtColor, saturation );
    vec3 conColor = mix( AvgLumin, satColor, contrast );
    return conColor;
}
// END MadCommon.glsl

#define TWO_PI 6.28318530718



float hash( vec2 p ) {
    return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);
}

vec2 rotate2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}









float adjusted_time(float time, float decay, float release)
{

    float adjusted_time;

    if (time < decay) {
        adjusted_time = 1;
    } else {
        
        adjusted_time = (time - decay) * 1 / (1 - decay);
        if (time < release) {
            adjusted_time = 1 - adjusted_time * 1 / release;
        } else {
            adjusted_time = 0;
        }
    }

    return adjusted_time;

}

vec4 materialColorForPixel(vec2 texCoord)
{

    float audio_value = 0.0;
    float bass_value = 0.3 * master_scale * bass_level * IMG_NORM_PIXEL(spectrum,vec2(0.17,0)).r;
    float medium_value = 0.3 * master_scale * medium_level * IMG_NORM_PIXEL(spectrum,vec2(0.5,0)).r;
    float treble_value = 0.3 * master_scale * treble_level * IMG_NORM_PIXEL(spectrum,vec2(0.83,0)).r;
    audio_value += bass_value;
    audio_value += medium_value;
    audio_value += treble_value;


	if (line_width==0) return vec4(0,0,0,1);


	
	#if defined(mirror_x_IS_Mirror_All)
		if (texCoord.x > 0.5) {
			texCoord.x = 1.0-texCoord.x;
		}
	#endif


    #if defined(mirror_y_IS_Mirror_All)
        if (texCoord.y > 0.5) {
            texCoord.y = 1.0-texCoord.y;
        }
    #endif

    texCoord.x -= slide_x;
    texCoord.y -= slide_y;

	
	texCoord = rotate2D(texCoord,PI*rotate);

	float pixelPos=mod(texCoord.x*cells_x,1);
	vec2 cellId = vec2(int(texCoord.x * cells_x), int(texCoord.y * cells_y));

    float normalizedCellId; 
    if (random_offset)
        normalizedCellId = hash(cellId * 0.5);
    else
        normalizedCellId = (cellId.x + cellId.y*cells_x) / (cells_x*cells_y); 


    float animation_time_strobed = animation_time;

    bool adjusted_strobe_on = strobe_on;

    if (strobe_audio_enable && strobe_on) {

        if (audio_value < strobe_audio_thresh) {
            adjusted_strobe_on = false;
        }

    }


    if (adjusted_strobe_on) {
        
        
        

        animation_time_strobed = (round(strobe_div * animation_time_strobed) + strobe_offset) / strobe_div;

        
    }


	float adjusted_bpm_pos;
	float adjusted_animation_time = mod(animation_time_strobed + bpm_offset + bpm_offset_alt,1);
	float adjusted_offset = offset;
	float adjusted_grad_time = grad_time;
	float adjusted_line_rotate = line_rotate;
	float adjusted_grad_offset = grad_offset;

	
	if (alternate_direction) {
		if (mod(texCoord.y, 2.0/cells_y) > 1.0/(cells_y)) {
			adjusted_animation_time = 1-adjusted_animation_time;

			if (grad_match_direction) {
				adjusted_grad_time = 1-grad_time;
			}
		}
	}

	
	if (alternate_offset) {
		if (mod(texCoord.y, 2.0/cells_y) > 1.0/(cells_y)) {
			adjusted_offset = 0.0;
		}

		adjusted_bpm_pos = mod(adjusted_animation_time - adjusted_offset,1);

		if (grad_match_offset) {
			adjusted_grad_offset -= adjusted_offset;
		}


	} else {

		adjusted_bpm_pos = mod(adjusted_animation_time - adjusted_offset * normalizedCellId,1);

		adjusted_grad_offset -= adjusted_offset * normalizedCellId;
		
		
		
		
	}

	
	#if defined(mirror_x_IS_Mirror_Shape)

		if (texCoord.x > 0.5) {
			adjusted_bpm_pos = 1-adjusted_bpm_pos;
			
			adjusted_line_rotate =1-adjusted_line_rotate;
		}
	#endif

    #if defined(mirror_y_IS_Mirror_Shape)

        if (texCoord.y > 0.5) {
            adjusted_bpm_pos = 1-adjusted_bpm_pos;
            
            adjusted_line_rotate =1-adjusted_line_rotate;
        }
    #endif

    adjusted_bpm_pos = adjusted_time(adjusted_bpm_pos, decay, release);


	float strob_adjusted_bpm_pos = mod(strob_time + strob_bpm_offset,1); 


    strob_adjusted_bpm_pos = adjusted_time(strob_adjusted_bpm_pos, strob_decay, strob_release);


    if (strob_shape == 0) { 
        strob_adjusted_bpm_pos = strob_adjusted_bpm_pos;
    } else if (strob_shape == 1) { 
        strob_adjusted_bpm_pos = 1-strob_adjusted_bpm_pos;
    } else { 
        strob_adjusted_bpm_pos = (1+sin((-0.25+strob_adjusted_bpm_pos)*2*PI))/2;
    }

	float widthValue = 1.0;
	float minSmoothness = 0.001 * repeat;
    float finalSmoothness = minSmoothness + smoothness/2;
    float halfFinalWidth = line_width * widthValue / 2;

	float a = (adjusted_line_rotate) * PI;
	float edge_adjustment = mod(texCoord.y, 2.0/cells_y) * cos(a);

	float value;

	#if defined(animation_IS_Cross)

		edge_adjustment = 0.0; 
		value = smoothstep(line_width,line_width*(1-smoothness),abs(pixelPos-adjusted_bpm_pos - edge_adjustment));
		value += smoothstep(line_width,line_width*(1-smoothness),abs((1-pixelPos)-adjusted_bpm_pos - edge_adjustment));
	#elif defined(animation_IS_Centered_Filled)
		value = smoothstep(0,-smoothness,(2*abs(0.5-pixelPos)-adjusted_bpm_pos-edge_adjustment));
	#elif defined(animation_IS_Single)

		float dist=fract((pixelPos  - adjusted_bpm_pos - edge_adjustment) *repeat + halfFinalWidth) - halfFinalWidth;

		
		dist *= (1-2*minSmoothness);

		int back_orig = back_edge_mode;
		int front_orig = front_edge_mode;

		int adjusted_front_edge_mode = front_edge_mode;
		int adjusted_back_edge_mode = back_edge_mode;

		if (alternate_edges && (mod(texCoord.y, 2.0/cells_y) > 1.0/(cells_y))) {
			adjusted_front_edge_mode = back_orig;
			adjusted_back_edge_mode = front_orig;
		}

		if (dist>0) {
			if (adjusted_back_edge_mode==0) {
				value=1-smoothstep(halfFinalWidth-finalSmoothness,halfFinalWidth,dist);
			} else if (adjusted_back_edge_mode==1) {
				value=halfFinalWidth;
			} else {
				value=1-dist;
			}

		} else {

			if (adjusted_front_edge_mode==0) {
				value=1-smoothstep(-halfFinalWidth+finalSmoothness,-halfFinalWidth,dist);
			} else if (adjusted_front_edge_mode==1) {
				value=-halfFinalWidth;
			} else {
				value=1-dist;
			}


			
		}

    #elif defined(animation_IS_Fill_Up)
        float diff = surf_anim1_limit*anim_pos-(1-pixelPos/surf_anim1_limit);
        

        
        value = step(diff,0);

    #elif defined(animation_IS_Fill_Down)     
        float diff = adjusted_bpm_pos-pixelPos;
        value = step(diff,0);

    #elif defined(animation_IS_Empty_Up)
        float diff = (1-pixelPos)-adjusted_bpm_pos;
        value = smoothstep(0,0,-diff);


    #elif defined(animation_IS_Empty_Down)     
        float diff = pixelPos-adjusted_bpm_pos;
        value = step(diff,0);

    #elif defined(animation_IS_Fill_Sin_Up)

        float diff = pixelPos-(1+sin(adjusted_bpm_pos*2*PI))/2;
        value = step(diff,0);

    #elif defined(animation_IS_Fill_Sin_Down) 
        float diff = (1+sin(adjusted_bpm_pos*2*PI))/2-pixelPos;
        value = step(diff,0);

    #elif defined(animation_IS_Chase)
        
        
        


        float diff = abs(pixelPos-0.5-sin(adjusted_bpm_pos*2*PI)/4);
        value = step(min(diff,diff),0.25*(line_width+0.5));


    #elif defined(animation_IS_Centered)
            float diff = abs(pixelPos-0.5);
            float value = step(diff,line_width*adjusted_bpm_pos/2);

    #elif defined(animation_IS_Centered_Sin)
        float diff = abs(pixelPos-0.5);
        value = step(diff,(1+sin(adjusted_bpm_pos*2*PI))/4);






	#elif defined(animation_IS_Filled)
		
		value = smoothstep(0,-smoothness,pixelPos-adjusted_bpm_pos);

    #else 

        value = 1.0;
	#endif


    
    
    

    if ((mod(texCoord.y, 2.0/cells_y) < border_y / 2.) || (mod(texCoord.y, 2.0/cells_y) > 1. - border_y / 2.)) {
        value = 0.0;
    }

    if ((mod(texCoord.x, 2.0/cells_x) < border_x / 2.) || (mod(texCoord.x, 2.0/cells_x) > 1. - border_x / 2.)) {
        value = 0.0;
    }





	vec4 backColor = vec4(backgroundColor.rgb * brightness, backgroundColor.a);
	vec4 frontColor = vec4(foregroundColor.rgb * brightness, foregroundColor.a);
	

    adjusted_grad_time = mod(adjusted_grad_time - grad_offset, 1);

    adjusted_grad_time = adjusted_time(adjusted_grad_time, grad_decay, grad_release);



	float angle = (grad_rotate) * 2*PI / 360;
    float sin_factor = sin(angle);
    float cos_factor = cos(angle);
    vec2 uv = ((texCoord-vec2(0.5)) * mat2(cos_factor, sin_factor, -sin_factor, cos_factor));
    float color_pos;
    if (grad_mode==0)
        color_pos = uv.x;
    else
        color_pos = -length(uv);
    color_pos *= pow(grad_scale,3) + grad_size*grad_size;
	color_pos = fract(color_pos);
    
	

    color_pos += adjusted_grad_time;

	if (grad_match_tilt) {
		color_pos -= edge_adjustment;
	}
	color_pos = fract(color_pos*grad_repeat);
	
    

    vec4 colors[10];
    colors[0] = grad_color1;
    colors[1] = grad_color2;
    colors[2] = grad_color3;
    colors[3] = grad_color4;
    colors[4] = grad_color5;

	colors[5] = grad_color6;
    colors[6] = grad_color7;
    colors[7] = grad_color8;
    colors[8] = grad_color9;
    colors[9] = grad_color10;

    float stepSize = 1.0/grad_color_count;
    int stepId = int(color_pos/stepSize);
    

	
	
	

	vec4 color;

	#if defined(grad_type_IS_Auto_Color_Cycle)
		color = vec4(hsv2rgb(vec3(color_pos, 1.0, 1.0)), 1.0);
	#elif defined(grad_type_IS_Custom_Gradient)
		color = mix(colors[stepId%grad_color_count],colors[(stepId+1)%grad_color_count], pow(color_pos/stepSize-stepId, pow(grad_curve,6)));
	#else 
        color = colors[stepId%grad_color_count];
    #endif

    color = mix(frontColor, color, grad_level);

    float strobe_value;

    strobe_value = mix(1.0, 1.0 * strob_adjusted_bpm_pos, strobe_level);

    color.rgb *= strobe_value;

    


	return mix(backgroundColor, color * brightness, value);
}

void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
