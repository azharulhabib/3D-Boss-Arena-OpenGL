3D Boss Arena – OpenGL (CSE423 Project)
Course: CSE423 — Computer Graphics
Project Type: 3D Lab Project (Based on Assignment-3 Template)

Project Summary

This project implements a 3D circular boss-battle environment using only the OpenGL functions permitted in Assignment-3 template.
The scene is fully 3D and includes:
A circular arena floor
A large central boss model (built with sphere, cube, cylinder)
Multiple fighter units approaching the boss
Simple boss attack animation using rotation
Damage / HP reduction logic
End condition when boss health reaches zero
Camera control with gluLookAt and keyboard rotation

Key Functionalities

Meets the requirement of providing 3× more features than Assignment-3.
Circular 3D Arena Rendering
Hierarchical Monster Model + Rotation Animation
Multiple NPC Fighters + Movement Toward Boss
Boss Punch Collision + Fighter Removal
Boss Health Calculation & On-Screen Display
Restart Option After Boss Defeat
Camera Orbit and Height Control (Arrow Keys)
Allowed Functions Used

All rendering follows Assignment-3 constraints:
glTranslatef, glRotatef, glScalef
gluPerspective, gluLookAt
glBegin(GL_QUADS/GL_LINES/GL_TRIANGLES)
glutSolidSphere, glutSolidCube, gluCylinder
glRasterPos2f text output
glPushMatrix, glPopMatrix
glutIdleFunc, glutDisplayFunc, glutKeyboardFunc
(No external models, shaders, or textures used.)

Controls

Arrow Keys → Camera Rotate / Height Adjust
Automatic NPC Movement Toward Boss
Restart Trigger (Key defined in code)
Idle updates handle animation and HP logic

End Condition

Boss HP = 0 → Display result and allow restart.
