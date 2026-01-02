from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math

# -------------------------------
# Globals
# -------------------------------
WINDOW_W, WINDOW_H = 1000, 800

# Camera
camera_angle = 0
camera_radius = 700
camera_height = 500

# Boss position
boss_x, boss_y, boss_z = 0.0, 0.0, 0.0
boss_hp = 1000

# Player
player_x, player_y, player_z = -200.0, 200.0, 0.0

quadric = None

# Boss State
boss_state = "IDLE"     # IDLE, WINDUP, SMASH, COOLDOWN
boss_timer = 0.0
boss_arm_angle = 0.0

# Calculated to hit exactly at Radius 300 (Middle of 180 and 420)
# Diagonal length needed to hit floor at distance 285 from shoulder height 195
# Adjusted to 332 to stop exactly at floor with angle ~35 degrees
arm_length = 332

boss_arm_dir = 1
boss_arm_speed = 0.8
boss_did_damage = False
boss_facing_angle = 0.0 
game_over = False  # Track game state

fighters = []
ALLY = 1
IDLE = 0

walk_phase = 0.0

# Radius for the hammer impact
SMASH_RADIUS = 220 


def init_fighters():
    global fighters
    fighters = []

    # Yellow leader group
    for i in range(6):
        fighters.append({
            "x": -200 + i * 15,
            "y": 150,
            "state": ALLY,
            "alive": True,
            "moving": False
        })

    # White idle humans around arena
    for i in range(14):
        angle = i * (360 / 14)
        r = 320
        fighters.append({
            "x": r * math.cos(math.radians(angle)),
            "y": r * math.sin(math.radians(angle)),
            "state": IDLE,
            "alive": True,
            "moving": False
        })


def reset_game():
    global boss_state, boss_timer, boss_arm_angle, boss_did_damage, boss_facing_angle, game_over
    boss_state = "IDLE"
    boss_timer = 0.0
    boss_arm_angle = 0.0
    boss_did_damage = False
    boss_facing_angle = 0.0
    game_over = False
    init_fighters()


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
# Donut arena
# -------------------------------
def draw_arena():
    inner_radius = 180
    outer_radius = 420
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

        # Floor
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
    global arm_length
    body_radius = 120
    body_height = 260
    head_radius = 90
    arm_thickness = 35
    torso_half_x = 90
    
    glPushMatrix()
    glTranslatef(boss_x, boss_y, boss_z)
    glRotatef(boss_facing_angle, 0, 0, 1)

    # BODY
    glColor3f(0.35, 0.35, 0.35)
    glPushMatrix()
    glTranslatef(0, 0, body_height * 0.5)
    glScalef(180, 140, body_height)
    glutSolidCube(1)
    glPopMatrix()

    # HEAD
    glPushMatrix()
    glTranslatef(0, 0, body_height + head_radius * 0.6)
    glColor3f(0.6, 0.1, 0.1)
    gluSphere(quadric, head_radius, 24, 24)
    glPopMatrix()

    # ===============================
    # ARMS
    # ===============================
    shoulder_z = body_height * 0.75

    # --- RIGHT ARM (ATTACK) ---
    glPushMatrix()
    # 1. Move to Shoulder (Local X offset)
    glTranslatef(torso_half_x + 5, 0, shoulder_z)

    # 2. Rotate
    glRotatef(boss_arm_angle, 1, 0, 0)

    # 3. Move down arm length (Visual centering)
    glTranslatef(0, -arm_length * 0.5, 0)

    # Upper Arm
    glPushMatrix()
    glScalef(arm_thickness, arm_length*0.8, arm_thickness)
    glColor3f(0.4, 0.1, 0.1)
    glutSolidCube(1)
    glPopMatrix()

    # Cleaver (The Hammer Head)
    glPushMatrix()
    glTranslatef(0, -arm_length * 0.45, 0) 
    glScalef(160, 60, 120) 
    glColor3f(0.8, 0.8, 0.8)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

    # --- LEFT ARM (IDLE) ---
    glPushMatrix()
    glTranslatef(-torso_half_x - 5, 0, shoulder_z)
    glTranslatef(0, -arm_length * 0.5, 0)
    glScalef(arm_thickness, arm_length * 0.8, arm_thickness)
    glColor3f(0.3, 0.1, 0.1)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix() # Boss Root


def update_boss_attack():
    global boss_state, boss_arm_angle, boss_timer, boss_did_damage

    if boss_state == "IDLE":
        boss_timer += 0.02
        if boss_timer > 2.0: 
            boss_state = "WINDUP"
            boss_timer = 0.0

    elif boss_state == "WINDUP":
        boss_arm_angle -= 1.5
        if boss_arm_angle <= -85:
            boss_state = "SMASH"

    elif boss_state == "SMASH":
        boss_arm_angle += 5.5 

        # Damage triggering (when close to hitting ground)
        if boss_arm_angle >= 20 and not boss_did_damage:
             boss_smash_damage()

        # Stop at floor (approx 35 deg needed to hit floor with length 332)
        if boss_arm_angle >= 35: 
            boss_state = "COOLDOWN"
            boss_timer = 0.0

    elif boss_state == "COOLDOWN":
        boss_timer += 0.02
        if boss_timer > 1.0:
            boss_arm_angle = 0.0
            boss_state = "IDLE"
            boss_timer = 0.0
            boss_did_damage = False

    # Clamp to floor level (35 degrees)
    boss_arm_angle = max(-90, min(boss_arm_angle, 35))


def update_boss_rotation():
    global boss_facing_angle

    if boss_state == "SMASH" or boss_state == "COOLDOWN":
        return

    # Find closest ALLY fighter
    closest = None
    min_dist = 999999

    for f in fighters:
        if f["state"] == ALLY and f["alive"]:
            d = math.sqrt(f["x"]*f["x"] + f["y"]*f["y"])
            if d < min_dist:
                min_dist = d
                closest = f

    if closest:
        target_angle = math.degrees(math.atan2(closest["y"], closest["x"])) + 90
        diff = target_angle - boss_facing_angle
        while diff > 180: diff -= 360
        while diff < -180: diff += 360
        boss_facing_angle += diff * 0.1


# -------------------------------
# Logic: Hit Detection
# -------------------------------

def boss_smash_damage():
    global boss_did_damage
    if boss_did_damage:
        return

    # HIT POSITION CALCULATION
    # Goal: Hit exactly at Radius 300 (middle of arena)
    # Shoulder X (local) = 95
    # Required Y Reach (local) = sqrt(300^2 - 95^2) approx 285
    
    local_x = 95
    local_y = -285 
    
    theta = math.radians(boss_facing_angle)

    rot_x = local_x * math.cos(theta) - local_y * math.sin(theta)
    rot_y = local_x * math.sin(theta) + local_y * math.cos(theta)

    hit_x = boss_x + rot_x
    hit_y = boss_y + rot_y
    
    # Radius of the explosion/hit
    CLEAVER_RADIUS = 130 
    MAX_KILLS = 1

    victims = []
    for f in fighters:
        if not f["alive"]:
            continue
        if f["state"] != ALLY:
            continue

        dx = f["x"] - hit_x
        dy = f["y"] - hit_y
        dist = math.sqrt(dx*dx + dy*dy)

        if dist <= CLEAVER_RADIUS:
            victims.append((dist, f))
    
    victims.sort(key=lambda v: v[0])

    killed_count = 0
    for dist, f in victims:
        if killed_count < MAX_KILLS:
            f["alive"] = False
            killed_count += 1
            print(f"SMASHED! Fighter at {f['x']:.0f},{f['y']:.0f} (Dist: {dist:.1f})")
        else:
            break

    if killed_count > 0:
        print(f"Total Kills this smash: {killed_count}")

    boss_did_damage = True


# -------------------------------
# Allies / Player Logic
# -------------------------------

def draw_fighters():
    for f in fighters:
        if not f["alive"]:
            continue

        x, y = f["x"], f["y"]
        angle = math.degrees(math.atan2(-x, -y))

        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(angle, 0, 0, 1)

        if f["state"] == ALLY:
            glColor3f(1.0, 0.85, 0.0)
        else:
            glColor3f(0.95, 0.95, 0.95)

        # Body
        glPushMatrix()
        glTranslatef(0, 0, 22)
        glScalef(12, 8, 22)
        glutSolidCube(1)
        glPopMatrix()

        # Head
        glPushMatrix()
        glTranslatef(0, 0, 38)
        gluSphere(quadric, 6, 12, 12)
        glPopMatrix()

        # Arms
        glPushMatrix()
        glTranslatef(-10, 0, 24)
        glScalef(4, 4, 16)
        glutSolidCube(1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(10, 0, 24)
        glScalef(4, 4, 16)
        glutSolidCube(1)
        glPopMatrix()

        # Walking Legs
        leg_angle = math.sin(math.radians(walk_phase)) * 25 if f["moving"] else 0

        glPushMatrix()
        glTranslatef(-4, 0, 14)
        glRotatef(leg_angle, 1, 0, 0)
        glTranslatef(0, 0, -8)
        glScalef(4, 4, 14)
        glutSolidCube(1)
        glPopMatrix()

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
    r = math.sqrt(x*x + y*y)
    return INNER_R + 15 < r < OUTER_R - 15

def move_allies(dx, dy):
    global walk_phase
    any_moved = False

    for f in fighters:
        if f["state"] == ALLY:
            f["moving"] = False

    for f in fighters:
        if f["state"] == ALLY and f["alive"]:
            nx = f["x"] + dx
            ny = f["y"] + dy
            if can_move_to(nx, ny):
                f["x"] = nx
                f["y"] = ny
                f["moving"] = True
                any_moved = True

    if any_moved:
        walk_phase += 8

def check_ally_conversion():
    for f in fighters:
        if f["state"] != ALLY or not f["alive"]:
            continue
        for other in fighters:
            if other["state"] == IDLE and other["alive"]:
                dx = f["x"] - other["x"]
                dy = f["y"] - other["y"]
                if math.sqrt(dx*dx + dy*dy) < 22:
                    other["state"] = ALLY
                    other["moving"] = False


# -------------------------------
# Input / Main
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
    if key == b'r':
        reset_game()
        glutPostRedisplay()
        return

    if game_over:
        return

    step = 12
    if key == b'w': move_allies(0, step)
    elif key == b's': move_allies(0, -step)
    elif key == b'a': move_allies(-step, 0)
    elif key == b'd': move_allies(step, 0)

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
    
    alive_count = 0
    for f in fighters:
        if f['alive']:
            alive_count += 1
    draw_text(10, WINDOW_H - 120, f"Alive Fighters: {alive_count}")

    if game_over:
        draw_text(WINDOW_W // 2 - 50, WINDOW_H // 2, "GAME OVER")
        draw_text(WINDOW_W // 2 - 70, WINDOW_H // 2 - 30, "Press R to Restart")

    glutSwapBuffers()

def idle():
    global game_over

    ally_count = 0
    for f in fighters:
        if f["state"] == ALLY and f["alive"]:
            ally_count += 1
    
    if ally_count == 0:
        game_over = True

    if game_over:
        glutPostRedisplay()
        return

    update_boss_attack()
    update_boss_rotation()
    check_ally_conversion()
    glutPostRedisplay()

def main():
    global quadric
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Phase 2 - Arena + Boss FIXED")

    init_fighters()
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.266, 0.765, 0.996, 1.0)
    quadric = gluNewQuadric()

    glutDisplayFunc(showScreen)
    glutSpecialFunc(specialKeyListener)
    glutKeyboardFunc(keyboardListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()