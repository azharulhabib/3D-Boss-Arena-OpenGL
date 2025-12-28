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


boss_state = "IDLE"     # IDLE, WINDUP, SMASH, COOLDOWN
boss_arm_angle = 0.0    # degrees
boss_timer = 0.0        # simple timer
boss_arm_angle = 0
boss_arm_dir = 1
boss_arm_speed = 0.8


fighters = []     # all fighters
ALLY = 1
IDLE = 0

walk_phase = 0.0
is_moving = False





def init_fighters():
    global fighters
    fighters = []

    # Yellow leader group
    for i in range(6):
        fighters.append({
            "x": -200 + i * 15,
            "y": 150,
            "state": ALLY,
            "alive": True
        })

    # White idle humans around arena
    for i in range(14):
        angle = i * (360 / 14)
        r = 320
        fighters.append({
            "x": r * math.cos(math.radians(angle)),
            "y": r * math.sin(math.radians(angle)),
            "state": IDLE,
            "alive": True
        })




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
# Boss model (animated arms)
# -------------------------------
def draw_boss():
    body_radius = 60
    body_height = 180
    head_radius = 48
    arm_length = 110
    arm_thickness = 18

    glPushMatrix()
    glTranslatef(boss_x, boss_y, boss_z)

    # BODY
    glColor3f(0.7, 0.2, 0.2)
    gluCylinder(quadric, body_radius, body_radius, body_height, 20, 6)

    # HEAD
    glPushMatrix()
    glTranslatef(0, 0, body_height + head_radius * 0.2)
    glColor3f(0.9, 0.3, 0.3)
    gluSphere(quadric, head_radius, 20, 20)
    glPopMatrix()

    # ===============================
    # ARMS (REAL UP-DOWN SMASH)
    # ===============================

    shoulder_z = body_height * 0.7
    shoulder_y = body_radius * 0.9  # move arms forward

    glPushMatrix()
    glTranslatef(0, shoulder_y, shoulder_z)

    # Rotate UP and DOWN (hinge motion)
    glRotatef(boss_arm_angle, 1, 0, 0)

    # LEFT ARM (extends forward in Y)
    glPushMatrix()
    glTranslatef(-body_radius * 0.9, arm_length * 0.5, 0)
    glScalef(arm_thickness, arm_length, arm_thickness)
    glColor3f(0.6, 0.2, 0.2)
    glutSolidCube(1)
    glPopMatrix()

    # RIGHT ARM
    glPushMatrix()
    glTranslatef(body_radius * 0.9, arm_length * 0.5, 0)
    glScalef(arm_thickness, arm_length, arm_thickness)
    glColor3f(0.6, 0.2, 0.2)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()  # arms
    glPopMatrix()  # boss



def update_boss_attack():
    global boss_state, boss_arm_angle, boss_timer

    if boss_state == "IDLE":
        boss_timer += 0.02
        if boss_timer > 2.5:
            boss_state = "WINDUP"
            boss_timer = 0.0

    elif boss_state == "WINDUP":
        boss_arm_angle -= 1.2     # slow lift
        if boss_arm_angle <= -75:
            boss_state = "SMASH"

    elif boss_state == "SMASH":
        boss_arm_angle += 4.5     # strong slam
        if boss_arm_angle >= 10:
            boss_state = "COOLDOWN"
            boss_timer = 0.0

    elif boss_state == "COOLDOWN":
        boss_timer += 0.02
        if boss_timer > 1.3:
            boss_arm_angle = 0.0
            boss_state = "IDLE"
            boss_timer = 0.0



# -------------------------------
# Player
# -------------------------------


def draw_fighters():
    for f in fighters:
        if not f["alive"]:
            continue

        x, y = f["x"], f["y"]

        # Angle to face boss (boss is at 0,0)
        angle = math.degrees(math.atan2(-x, y))

        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(angle, 0, 0, 1)

        # Color by state
        if f["state"] == ALLY:
            glColor3f(1.0, 0.85, 0.0)   # yellow
        else:
            glColor3f(0.95, 0.95, 0.95) # white

        # -----------------
        # BODY
        # -----------------
        glPushMatrix()
        glTranslatef(0, 0, 22)
        glScalef(12, 8, 22)
        glutSolidCube(1)
        glPopMatrix()

        # -----------------
        # HEAD
        # -----------------
        glPushMatrix()
        glTranslatef(0, 0, 38)
        gluSphere(quadric, 6, 12, 12)
        glPopMatrix()

        # -----------------
        # LEFT ARM
        # -----------------
        glPushMatrix()
        glTranslatef(-10, 0, 24)
        glScalef(4, 4, 16)
        glutSolidCube(1)
        glPopMatrix()

        # -----------------
        # RIGHT ARM
        # -----------------
        glPushMatrix()
        glTranslatef(10, 0, 24)
        glScalef(4, 4, 16)
        glutSolidCube(1)
        glPopMatrix()

        # Leg swing angle
        leg_angle = math.sin(math.radians(walk_phase)) * 25 if is_moving else 0

        # -----------------
        # LEFT LEG
        # -----------------
        glPushMatrix()
        glTranslatef(-4, 0, 14)
        glRotatef(leg_angle, 1, 0, 0)
        glTranslatef(0, 0, -8)
        glScalef(4, 4, 14)
        glutSolidCube(1)
        glPopMatrix()

        # -----------------
        # RIGHT LEG
        # -----------------
        glPushMatrix()
        glTranslatef(4, 0, 14)
        glRotatef(-leg_angle, 1, 0, 0)
        glTranslatef(0, 0, -8)
        glScalef(4, 4, 14)
        glutSolidCube(1)
        glPopMatrix()
        glPopMatrix()




INNER_R = 180
OUTER_R = 420

def can_move_to(x, y):
    r = math.hypot(x, y)
    return INNER_R + 15 < r < OUTER_R - 15


def move_allies(dx, dy):
    global walk_phase, is_moving

    moved = False

    for f in fighters:
        if f["state"] == ALLY and f["alive"]:
            nx = f["x"] + dx
            ny = f["y"] + dy

            if can_move_to(nx, ny):
                f["x"] = nx
                f["y"] = ny
                moved = True

    if moved:
        walk_phase += 8      # speed of leg swing
        is_moving = True
    else:
        is_moving = False



def check_ally_conversion():
    for f in fighters:
        if f["state"] != ALLY or not f["alive"]:
            continue

        for other in fighters:
            if other["state"] == IDLE and other["alive"]:
                dx = f["x"] - other["x"]
                dy = f["y"] - other["y"]
                if math.hypot(dx, dy) < 22:
                    other["state"] = ALLY


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


def keyboardListener(key, x, y):
    step = 12

    if key == b'w':
        move_allies(0, step)
    elif key == b's':
        move_allies(0, -step)
    elif key == b'a':
        move_allies(-step, 0)
    elif key == b'd':
        move_allies(step, 0)


# -------------------------------
# Display
# -------------------------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_W, WINDOW_H)

    setupCamera()

    draw_arena()
    draw_boss()
    draw_fighters()

    draw_text(10, WINDOW_H - 30, "Phase-2: Donut Arena + Upright Boss")
    draw_text(10, WINDOW_H - 60, f"Boss HP: {boss_hp}")
    draw_text(10, WINDOW_H - 90, f"Boss State: {boss_state}")


    glutSwapBuffers()


def idle():
    update_boss_attack()
    check_ally_conversion()
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

    init_fighters()

    glEnable(GL_DEPTH_TEST)

    # Background color RGBA(68,195,254)
    glClearColor(0.266, 0.765, 0.996, 1.0)

    quadric = gluNewQuadric()

    glutDisplayFunc(showScreen)
    glutSpecialFunc(specialKeyListener)
    glutKeyboardFunc(keyboardListener)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()
