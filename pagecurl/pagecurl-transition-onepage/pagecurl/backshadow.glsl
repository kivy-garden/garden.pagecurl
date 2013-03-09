---VERTEX SHADER-------------------------------------------------------

#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 v_position;

/* vertex attributes */
attribute vec3     vPosition;
attribute vec2     vTexCoords0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;
uniform float      opacity;

void main (void) {
	frag_color = color * vec4(1.0, 1.0, 1.0, opacity);
	v_position = vPosition.xy;
	gl_Position = modelview_mat * projection_mat * vec4(vPosition.xyz, 1.0);
}


---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 frag_color;

uniform vec2 cylinder_position;
uniform vec2 cylinder_direction;
uniform float cylinder_radius;
varying vec2 v_position;

void main (void){
    vec2 dir = vec2(cylinder_direction.y, -cylinder_direction.x);
    vec2 v = v_position - cylinder_position;
    float d = dot(v, dir);
    float l = smoothstep(0.5, 0.8, d / (2.0 * cylinder_radius));
	gl_FragColor = frag_color * vec4(0., 0., 0., 0.5 - l * 0.5);
}
