---VERTEX SHADER-------------------------------------------------------

#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord0;
varying vec2 tex_coord1;

/* vertex attributes */
attribute vec3     vPosition;
attribute vec2     vTexCoords0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;
uniform float      opacity;
uniform vec2       cylinder_position;
uniform vec2       cylinder_direction;
uniform float      cylinder_radius;

#define M_PI 3.14159265358979323846264338327950288

void main (void) {
	frag_color = color * vec4(1.0, 1.0, 1.0, opacity);
	tex_coord0 = vTexCoords0;
	//gl_Position = projection_mat * modelview_mat * vec4(vPosition.xyz, 1.0);

	vec2 n = vec2(cylinder_direction.y, -cylinder_direction.x);
    vec2 w = vPosition.xy - cylinder_position;
    float d = dot(w, n);

    vec2 dv = n * (2.0*d - M_PI*cylinder_radius);
    float dr = d/cylinder_radius;//projection angle
    float s = sin(dr);
    float c = cos(dr);
    vec2 proj = vPosition.xy - n*d;//projection of vertex on the cylinder axis projected on the xy plane

    float br1 = clamp(sign(d), 0.0, 1.0); // d > 0.0
    float br2 = clamp(sign(d - M_PI*cylinder_radius), 0.0, 1.0); // d > M_PI*cylinder_radius

    vec3 vProj = vec3(s*n.x, s*n.y, 1.0 - c)*cylinder_radius;
    vProj.xy += proj;
    vec3 v = mix(vPosition, vProj, br1);
    v = mix(v, vec3(vPosition.x - dv.x, vPosition.y - dv.y, 2.0 * cylinder_radius), br2);

    vec2 vw = v.xy - cylinder_position;
    float vd = dot(vw, -n);
    tex_coord1 = vec2(1. + vd / cylinder_radius, 0.5);

    gl_Position = projection_mat * modelview_mat * vec4(v.xy, -v.z, 1.0);
}


---FRAGMENT SHADER-----------------------------------------------------
$HEADER$

uniform sampler2D texture1;
varying vec2 tex_coord1;

void main (void){
    //gl_FragColor = frag_color * texture2D(texture0, tex_coord0);
    vec4 color = texture2D(texture0, tex_coord0);
    vec4 gradient = texture2D(texture1, tex_coord1);
    gl_FragColor = color * gradient;
}
