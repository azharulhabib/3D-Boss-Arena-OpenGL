from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# -------------------------------
# Globals (simple, top-of-file)
# -------------------------------
WINDOW_W, WINDOW_H = 1000, 800

# Camera (orbiting around origin)
camera_angle = 0
camera_radius = 700
camera_height = 500

# Boss position
boss_x, boss_y, boss_z = 0.0, 0.0, 0.0
boss_hp = 1000

# Player position
player_x, player_y, player_z = -200.0, 200.0, 0.0

quadric = None


# -------------------------------
# Helper: draw text
# -------------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# -------------------------------
# Camera
# -------------------------------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(80, WINDOW_W / float(WINDOW_H), 0.1, 2500.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    cx = math.cos(math.radians(camera_angle)) * camera_radius
    cy = math.sin(math.radians(camera_angle)) * camera_radius
    cz = camera_height

    gluLookAt(cx, cy, cz,
              0.0, 0.0, 0.0,
              0.0, 0.0, 1.0)


# -------------------------------
# Donut arena (vertical stripes)
# -------------------------------
def draw_arena():
    inner_radius = 180     # same as before
    outer_radius = 420     # smaller arena thickness
    slices = 48

    angle_step = (2 * math.pi) / slices

    glBegin(GL_TRIANGLES)

    for i in range(slices):
        a1 = i * angle_step
        a2 = (i + 1) * angle_step

        if i % 2 == 0:
            glColor3f(0.9, 0.9, 0.9)
        else:
            glColor3f(0.55, 0.55, 0.55)

        x1i = inner_radius * math.cos(a1)
        y1i = inner_radius * math.sin(a1)
        x2i = inner_radius * math.cos(a2)
        y2i = inner_radius * math.sin(a2)

        x1o = outer_radius * math.cos(a1)
        y1o = outer_radius * math.sin(a1)
        x2o = outer_radius * math.cos(a2)
        y2o = outer_radius * math.sin(a2)

        glVertex3f(x1i, y1i, 0)
        glVertex3f(x1o, y1o, 0)
        glVertex3f(x2o, y2o, 0)

        glVertex3f(x1i, y1i, 0)
        glVertex3f(x2o, y2o, 0)
        glVertex3f(x2i, y2i, 0)

    glEnd()


# -------------------------------
# Boss model
# -------------------------------
def draw_boss():
    body_radius = 60
    body_height = 180
    head_radius = 48
    arm_length = 110
    arm_thickness = 18

    glPushMatrix()
    glTranslatef(boss_x, boss_y, boss_z)

    glColor3f(0.75, 0.15, 0.15)
    gluCylinder(quadric, body_radius, body_radius, body_height, 20, 6)

    glPushMatrix()
    glTranslatef(0, 0, body_height + head_radius * 0.2)
    glColor3f(0.9, 0.25, 0.25)
    gluSphere(quadric, head_radius, 20, 20)
    glPopMatrix()

    attach_z = body_height * 0.65

    glPushMatrix()
    glTranslatef(-(body_radius + arm_length * 0.5), 0, attach_z)
    glScalef(arm_length, arm_thickness, arm_thickness)
    glColor3f(0.6, 0.2, 0.2)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef((body_radius + arm_length * 0.5), 0, attach_z)
    glScalef(arm_length, arm_thickness, arm_thickness)
    glColor3f(0.6, 0.2, 0.2)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()


# -------------------------------
# Player
# -------------------------------
def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z + 25)
    glColor3f(1, 1, 0)
    glScalef(50, 50, 50)
    glutSolidCube(1)
    glPopMatrix()


# -------------------------------
# Input
# -------------------------------
def specialKeyListener(key, x, y):
    global camera_angle, camera_height

    if key == GLUT_KEY_LEFT:
        camera_angle -= 3
    if key == GLUT_KEY_RIGHT:
        camera_angle += 3
    if key == GLUT_KEY_UP:
        camera_height += 25
    if key == GLUT_KEY_DOWN:
        camera_height -= 25

    camera_height = max(120, min(camera_height, 2000))


# -------------------------------
# Display
# -------------------------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_W, WINDOW_H)

    setupCamera()

    draw_arena()
    draw_boss()
    draw_player()

    draw_text(10, WINDOW_H - 30, "Phase-2: Donut Arena + Upright Boss")
    draw_text(10, WINDOW_H - 60, f"Boss HP: {boss_hp}")

    glutSwapBuffers()


def idle():
    glutPostRedisplay()


# -------------------------------
# Main
# -------------------------------
def main():
    global quadric
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Phase 2 - Arena + Boss")

    glEnable(GL_DEPTH_TEST)

    # Background color RGBA(68,195,254)
    glClearColor(0.266, 0.765, 0.996, 1.0)

    quadric = gluNewQuadric()

    glutDisplayFunc(showScreen)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()
