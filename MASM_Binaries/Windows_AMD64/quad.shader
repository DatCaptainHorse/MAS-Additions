#SHADER VERTEX
#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 tc;

out vec2 texCoord;

layout(std140) uniform UniformBufferObject {
	uniform mat4 model;
	uniform mat4 view;
	uniform mat4 projection;
} UBO;

void main()
{
	gl_Position = UBO.projection * UBO.view * UBO.model * vec4(position, 1.0);
	texCoord = vec2(tc.x, tc.y);
}

#SHADER FRAGMENT
#version 330 core

uniform vec4 color;

uniform sampler2D tex;

in vec2 texCoord;

layout(location = 0) out vec4 outColor;

void main()
{
	outColor = texture(tex, texCoord) * color;
}
#SHADER END