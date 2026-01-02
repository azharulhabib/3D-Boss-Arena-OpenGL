from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math

# -------------------------------
# Globals
# -------------------------------
WINDOW_W = 1000
WINDOW_H = 800

# Camera Variables
camera_angle = 0
camera_radius = 700
camera_height = 500
first_person = False 

# Boss Position
boss_x = 0.0
boss_y = 0.0
boss_z = 0.0
boss_hp = 1000

# Boss Hitbox (Relative to Center)
BOSS_BOX_MIN = [-90, -70, 0]
BOSS_BOX_MAX = [90, 70, 260]

quadric = None

# Boss State Variables
boss_state = "IDLE"     # Possible values: IDLE, WINDUP, SMASH, COOLDOWN
boss_timer = 0.0
boss_arm_angle = 0.0

# Arm length calculated to hit floor at radius 300
arm_length = 332

boss_arm_dir = 1
boss_did_damage = False
boss_facing_angle = 0.0 
game_over = False

# Game Entities
fighters = []
spawn_points = [] 

# Entity States
ALLY = 1
IDLE = 0

walk_phase = 0.0
SMASH_RADIUS = 220 

# Spear / Combat Variables
spear_state = "READY"   # Possible values: READY, THROWING, COOLDOWN
spear_anim_t = 0.0      # Animation progress (0.0 to 1.0)
spear_cooldown = 0.0
SPEAR_DAMAGE = 20


def init_fighters():
    global fighters, spawn_points
    fighters = []
    spawn_points = []

    # Create 6 Allies (Yellow Group)
    for i in range(6):
        fighter = {
            "x": -200 + i * 15,
            "y": 150,
            "state": ALLY,
            "alive": True,
            "moving": False
        }
        fighters.append(fighter)

    # Create 14 Idle Humans (White Group) around the arena
    for i in range(14):
        angle_deg = i * (360 / 14)
        r = 320
        
        # Calculate position using trigonometry
        fx = r * math.cos(math.radians(angle_deg))
        fy = r * math.sin(math.radians(angle_deg))
        
        # Save spawn point for respawning later
        spawn_data = {
            "x": fx, 
            "y": fy, 
            "timer": 0.0
        }
        spawn_points.append(spawn_data)
        
        fighter = {
            "x": fx,
            "y": fy,
            "state": IDLE,
            "alive": True,
            "moving": False,
            "spawn_id": i 
        }
        fighters.append(fighter)


def reset_game():
    global boss_state, boss_timer, boss_arm_angle, boss_did_damage
    global boss_facing_angle, game_over, boss_hp
    global spear_state, spear_anim_t, spear_cooldown
    
    # Reset Boss Logic
    boss_state = "IDLE"
    boss_timer = 0.0
    boss_arm_angle = 0.0
    boss_did_damage = False
    boss_facing_angle = 0.0
    boss_hp = 1000
    
    # Reset Game State
    game_over = False
    
    # Reset Spear Logic
    spear_state = "READY"
    spear_anim_t = 0.0
    spear_cooldown = 0.0
    
    # Re-initialize all characters
    init_fighters()


# -------------------------------
# Helper: Draw Text
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
# Camera Setup
# -------------------------------
def setupCamera():
    global first_person
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(80, WINDOW_W / float(WINDOW_H), 0.1, 2500.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        # First Person Mode Logic
        target_f = None
        
        # Find first alive ally
        for f in fighters:
            if f["state"] == ALLY:
                if f["alive"]:
                    target_f = f
                    break
        
        if target_f is not None:
            eye_x = target_f["x"]
            eye_y = target_f["y"]
            eye_z = 60 # Eye height
            
            # Look at Boss Center (Height 120)
            center_x = 0
            center_y = 0
            center_z = 120
            
            gluLookAt(eye_x, eye_y, eye_z,
                      center_x, center_y, center_z,
                      0, 0, 1)
            return

    # Default Orbit Camera Mode
    cx = math.cos(math.radians(camera_angle)) * camera_radius
    cy = math.sin(math.radians(camera_angle)) * camera_radius
    cz = camera_height

    gluLookAt(cx, cy, cz,
              0.0, 0.0, 0.0,
              0.0, 0.0, 1.0)


# -------------------------------
# Drawing Functions
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

        # Alternate colors for stripes
        if i % 2 == 0:
            glColor3f(0.9, 0.9, 0.9)
        else:
            glColor3f(0.55, 0.55, 0.55)

        # Calculate coordinates
        x1i = inner_radius * math.cos(a1)
        y1i = inner_radius * math.sin(a1)
        x2i = inner_radius * math.cos(a2)
        y2i = inner_radius * math.sin(a2)

        x1o = outer_radius * math.cos(a1)
        y1o = outer_radius * math.sin(a1)
        x2o = outer_radius * math.cos(a2)
        y2o = outer_radius * math.sin(a2)

        # Draw two triangles per slice
        glVertex3f(x1i, y1i, 0)
        glVertex3f(x1o, y1o, 0)
        glVertex3f(x2o, y2o, 0)

        glVertex3f(x1i, y1i, 0)
        glVertex3f(x2o, y2o, 0)
        glVertex3f(x2i, y2i, 0)
    glEnd()


def draw_boss():
    global arm_length
    
    # Boss Dimensions
    body_radius = 120
    body_height = 260
    head_radius = 90
    arm_thickness = 35
    torso_half_x = 90
    
    glPushMatrix()
    glTranslatef(boss_x, boss_y, boss_z)
    glRotatef(boss_facing_angle, 0, 0, 1)

    # 1. Body
    glColor3f(0.35, 0.35, 0.35)
    glPushMatrix()
    glTranslatef(0, 0, body_height * 0.5)
    glScalef(180, 140, body_height)
    glutSolidCube(1)
    glPopMatrix()

    # 2. Head
    glPushMatrix()
    glTranslatef(0, 0, body_height + head_radius * 0.6)
    glColor3f(0.6, 0.1, 0.1)
    gluSphere(quadric, head_radius, 24, 24)
    glPopMatrix()

    shoulder_z = body_height * 0.75

    # 3. Right Arm (Attack Arm)
    glPushMatrix()
    glTranslatef(torso_half_x + 5, 0, shoulder_z)
    glRotatef(boss_arm_angle, 1, 0, 0)
    glTranslatef(0, -arm_length * 0.5, 0)

    # Upper Arm
    glPushMatrix()
    glScalef(arm_thickness, arm_length*0.8, arm_thickness)
    glColor3f(0.4, 0.1, 0.1)
    glutSolidCube(1)
    glPopMatrix()

    # Hammer Head
    glPushMatrix()
    glTranslatef(0, -arm_length * 0.45, 0) 
    glScalef(160, 60, 120) 
    glColor3f(0.8, 0.8, 0.8)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix() # End Right Arm

    # 4. Left Arm (Idle Arm)
    glPushMatrix()
    glTranslatef(-torso_half_x - 5, 0, shoulder_z)
    glTranslatef(0, -arm_length * 0.5, 0)
    
    glScalef(arm_thickness, arm_length * 0.8, arm_thickness)
    glColor3f(0.3, 0.1, 0.1)
    glutSolidCube(1)
    
    glPopMatrix() # End Left Arm

    glPopMatrix() # End Boss Root


def draw_spear():
    glPushMatrix()
    
    # Shaft
    glPushMatrix()
    glScalef(3, 3, 50)
    glColor3f(0.55, 0.27, 0.07) # Brown
    glutSolidCube(1)
    glPopMatrix()
    
    # Tip
    glPushMatrix()
    glTranslatef(0, 0, 25)
    glColor3f(0.9, 0.9, 0.9) # Silver
    glutSolidCone(3, 15, 10, 10)
    glPopMatrix()
    
    glPopMatrix()


def draw_fighters():
    for f in fighters:
        if f["alive"] == False:
            continue

        x = f["x"]
        y = f["y"]
        
        # Calculate angle to face center (0,0)
        # -90 adjustment needed because model faces +Y by default
        rad_angle = math.atan2(-y, -x)
        angle_deg = math.degrees(rad_angle) - 90

        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(angle_deg, 0, 0, 1)

        # Set Color based on State
        if f["state"] == ALLY:
            glColor3f(1.0, 0.85, 0.0) # Yellow
        else:
            glColor3f(0.95, 0.95, 0.95) # White

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

        # --- Draw Arms ---
        if f["state"] == ALLY:
            # Determine Arm Rotation for Throwing
            arm_rot = 0
            if spear_state == "THROWING":
                arm_rot = -45 - (spear_anim_t * 90)
            
            # Right Arm (Weapon Arm)
            glPushMatrix()
            glTranslatef(10, 0, 24) # Shoulder
            
            # Rotate Arm
            glPushMatrix()
            glRotatef(arm_rot, 1, 0, 0) 
            
            # Arm Shape
            glPushMatrix()
            glScalef(4, 4, 16)
            glutSolidCube(1)
            glPopMatrix()

            # Draw Spear in hand if Ready
            if spear_state == "READY":
                glPushMatrix()
                glTranslatef(0, 10, -5)
                glRotatef(-90, 1, 0, 0)
                draw_spear()
                glPopMatrix()
            
            glPopMatrix() # End Arm Rotation

            # Draw Projectile Spear if Throwing
            if spear_state == "THROWING":
                dist_to_boss = math.sqrt(x*x + y*y)
                travel_dist = (dist_to_boss - 20) * spear_anim_t
                height_offset = 120 * spear_anim_t

                glPushMatrix()
                glTranslatef(0, travel_dist, height_offset)
                glRotatef(-90, 1, 0, 0)
                glRotatef(-15, 1, 0, 0)
                draw_spear()
                glPopMatrix()

            glPopMatrix() # End Shoulder

            # Reset color (Spear drawing changes color)
            glColor3f(1.0, 0.85, 0.0)

            # Left Arm (Static)
            glPushMatrix()
            glTranslatef(-10, 0, 24)
            glScalef(4, 4, 16)
            glutSolidCube(1)
            glPopMatrix()

        else:
            # Idle Fighter Arms (Both Static)
            # Left
            glPushMatrix()
            glTranslatef(-10, 0, 24)
            glScalef(4, 4, 16)
            glutSolidCube(1)
            glPopMatrix()
            # Right
            glPushMatrix()
            glTranslatef(10, 0, 24)
            glScalef(4, 4, 16)
            glutSolidCube(1)
            glPopMatrix()

        # Legs Animation
        leg_angle = 0
        if f["moving"]:
            leg_angle = math.sin(math.radians(walk_phase)) * 25
            
        # Left Leg
        glPushMatrix()
        glTranslatef(-4, 0, 14)
        glRotatef(leg_angle, 1, 0, 0)
        glTranslatef(0, 0, -8)
        glScalef(4, 4, 14)
        glutSolidCube(1)
        glPopMatrix()
        
        # Right Leg
        glPushMatrix()
        glTranslatef(4, 0, 14)
        glRotatef(-leg_angle, 1, 0, 0)
        glTranslatef(0, 0, -8)
        glScalef(4, 4, 14)
        glutSolidCube(1)
        glPopMatrix()
        
        glPopMatrix() # End Fighter


# -------------------------------
# Logic: Boss Behavior
# -------------------------------
def update_boss_attack():
    global boss_state, boss_arm_angle, boss_timer, boss_did_damage

    if boss_state == "IDLE":
        boss_timer += 0.02
        if boss_timer > 3.0: 
            boss_state = "WINDUP"
            boss_timer = 0.0

    elif boss_state == "WINDUP":
        boss_arm_angle -= 0.6
        if boss_arm_angle <= -85:
            boss_state = "SMASH"

    elif boss_state == "SMASH":
        boss_arm_angle += 5.5
        
        # Check damage when arm swings past 20 degrees
        if boss_arm_angle >= 20:
            if not boss_did_damage:
                 boss_smash_damage()

        if boss_arm_angle >= 35: 
            boss_state = "COOLDOWN"
            boss_timer = 0.0

    elif boss_state == "COOLDOWN":
        boss_timer += 0.02
        if boss_timer > 2.0:
            boss_arm_angle = 0.0
            boss_state = "IDLE"
            boss_timer = 0.0
            boss_did_damage = False

    # Keep angle within limits
    if boss_arm_angle < -90:
        boss_arm_angle = -90
    if boss_arm_angle > 35:
        boss_arm_angle = 35


def update_boss_rotation():
    global boss_facing_angle
    
    # Do not rotate while attacking
    if boss_state == "SMASH":
        return
    if boss_state == "COOLDOWN":
        return

    # Find closest Ally
    closest_fighter = None
    min_dist = 999999
    
    for f in fighters:
        if f["state"] == ALLY:
            if f["alive"]:
                dx = f["x"]
                dy = f["y"]
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < min_dist:
                    min_dist = dist
                    closest_fighter = f

    if closest_fighter is not None:
        # Calculate target angle
        y = closest_fighter["y"]
        x = closest_fighter["x"]
        
        target_angle = math.degrees(math.atan2(y, x)) + 90
        diff = target_angle - boss_facing_angle
        
        # Normalize difference to find shortest rotation path
        while diff > 180: 
            diff -= 360
        while diff < -180: 
            diff += 360
            
        boss_facing_angle += diff * 0.1


def boss_smash_damage():
    global boss_did_damage
    
    if boss_did_damage: 
        return

    # Calculate Hit Position relative to Boss
    local_x = 95
    local_y = -285 
    
    theta = math.radians(boss_facing_angle)
    
    # Rotate offset by boss facing angle
    rot_x = local_x * math.cos(theta) - local_y * math.sin(theta)
    rot_y = local_x * math.sin(theta) + local_y * math.cos(theta)
    
    hit_x = boss_x + rot_x
    hit_y = boss_y + rot_y
    
    CLEAVER_RADIUS = 130 
    MAX_KILLS = 1

    victims = []
    
    # Find all allies in range
    for f in fighters:
        if f["alive"] == False: 
            continue
        if f["state"] != ALLY: 
            continue
            
        dx = f["x"] - hit_x
        dy = f["y"] - hit_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist <= CLEAVER_RADIUS: 
            victims.append((dist, f))
    
    # Sort closest first
    victims.sort(key=lambda v: v[0])
    
    killed_count = 0
    for item in victims:
        dist = item[0]
        fighter = item[1]
        
        if killed_count < MAX_KILLS:
            fighter["alive"] = False
            killed_count += 1
        else: 
            break
            
    boss_did_damage = True


# -------------------------------
# Logic: Spears & Combat
# -------------------------------
def update_spears():
    global spear_state, spear_anim_t, spear_cooldown, boss_hp, game_over

    if spear_state == "THROWING":
        spear_anim_t += 0.01 # Slower speed (reduced from 0.02)
        
        if spear_anim_t >= 1.0:
            # Animation complete, impact boss
            ally_count = 0
            for f in fighters:
                if f["state"] == ALLY:
                    if f["alive"]:
                        ally_count += 1
            
            damage = ally_count * SPEAR_DAMAGE
            boss_hp -= damage
            
            if boss_hp <= 0: 
                boss_hp = 0
                game_over = True
            
            print("Boss Hit!")
            print(f"Damage Dealt: {damage}")
            print(f"HP Remaining: {boss_hp}")
            
            spear_state = "COOLDOWN"
            spear_cooldown = 1.0 
            spear_anim_t = 0.0

    elif spear_state == "COOLDOWN":
        spear_cooldown -= 0.02 
        if spear_cooldown <= 0:
            spear_state = "READY"


def check_hit_boss(mx, my):
    # Retrieve OpenGL Matrices
    model_view = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)

    winX = float(mx)
    winY = float(viewport[3] - my)

    try:
        near = gluUnProject(winX, winY, 0.0, model_view, projection, viewport)
        far = gluUnProject(winX, winY, 1.0, model_view, projection, viewport)
    except:
        return False

    # Ray Origin
    rx = near[0]
    ry = near[1]
    rz = near[2]
    
    # Ray Direction Vector
    dx = far[0] - near[0]
    dy = far[1] - near[1]
    dz = far[2] - near[2]
    
    # Normalize Direction
    mag = math.sqrt(dx*dx + dy*dy + dz*dz)
    dx /= mag
    dy /= mag
    dz /= mag

    # Check intersection with Boss Bounding Box
    t_min = 0.0
    t_max = 100000.0

    bb_min = [
        boss_x + BOSS_BOX_MIN[0], 
        boss_y + BOSS_BOX_MIN[1], 
        boss_z + BOSS_BOX_MIN[2]
    ]
    bb_max = [
        boss_x + BOSS_BOX_MAX[0], 
        boss_y + BOSS_BOX_MAX[1], 
        boss_z + BOSS_BOX_MAX[2]
    ]
    
    origin = [rx, ry, rz]
    direction = [dx, dy, dz]

    # Check X, Y, Z slabs
    for i in range(3):
        if abs(direction[i]) < 0.000001:
            # Ray is parallel to slab
            if origin[i] < bb_min[i] or origin[i] > bb_max[i]:
                return False
        else:
            inverse_direction = 1.0 / direction[i]
            t1 = (bb_min[i] - origin[i]) * inverse_direction
            t2 = (bb_max[i] - origin[i]) * inverse_direction
            
            if t1 > t2: 
                temp = t1
                t1 = t2
                t2 = temp
            
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
            
            if t_min > t_max:
                return False

    return True


# -------------------------------
# Logic: Movement & Spawning
# -------------------------------
def can_move_to(x, y):
    r = math.sqrt(x*x + y*y)
    
    # Check boundaries (Donut shape)
    if r > (180 + 15):
        if r < (420 - 15):
            return True
    
    return False


def move_allies(dx, dy):
    global walk_phase
    any_moved = False
    
    # Reset moving flag
    for f in fighters:
        if f["state"] == ALLY: 
            f["moving"] = False

    # Attempt move
    for f in fighters:
        if f["state"] == ALLY:
            if f["alive"]:
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
        # Only check alive allies against idle fighters
        if f["state"] != ALLY: 
            continue
        if not f["alive"]: 
            continue
            
        for other in fighters:
            if other["state"] == IDLE:
                if other["alive"]:
                    dx = f["x"] - other["x"]
                    dy = f["y"] - other["y"]
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist < 22:
                        other["state"] = ALLY
                        other["moving"] = False
                        
                        # Handle Respawn Logic
                        if "spawn_id" in other:
                            s_id = other["spawn_id"]
                            spawn_points[s_id]["timer"] = 30.0
                            del other["spawn_id"]


def update_spawns():
    for i in range(len(spawn_points)):
        sp = spawn_points[i]
        
        if sp["timer"] > 0:
            sp["timer"] -= 0.02
            
            if sp["timer"] <= 0:
                # Spawn new idle fighter
                fighter = {
                    "x": sp["x"], 
                    "y": sp["y"],
                    "state": IDLE, 
                    "alive": True, 
                    "moving": False,
                    "spawn_id": i
                }
                fighters.append(fighter)
                sp["timer"] = 0


# -------------------------------
# Input Callbacks
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
    if key == b'w': 
        move_allies(0, step)
    elif key == b's': 
        move_allies(0, -step)
    elif key == b'a': 
        move_allies(-step, 0)
    elif key == b'd': 
        move_allies(step, 0)


def mouseListener(button, state, x, y):
    global spear_state, first_person
    
    if game_over: 
        return
    
    # Left Click - THROW SPEAR
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            if spear_state == "READY":
                if check_hit_boss(x, y):
                    print("Aim Correct! Throwing Spears...")
                    spear_state = "THROWING"
                else:
                    print("Missed Aim!")

    # Right Click - TOGGLE CAMERA
    if button == GLUT_RIGHT_BUTTON:
        if state == GLUT_DOWN:
            first_person = not first_person
            
            mode_str = "Orbit"
            if first_person:
                mode_str = "First Person"
            print(f"Camera Mode: {mode_str}")


# -------------------------------
# Main Loop & Display
# -------------------------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    
    setupCamera()

    draw_arena()
    draw_boss()
    draw_fighters()

    # UI Text
    cam_mode_text = "Orbit"
    if first_person:
        cam_mode_text = "First Person"
        
    draw_text(10, WINDOW_H - 30, f"Phase-3: Spear Throwing | Cam: {cam_mode_text}")
    draw_text(10, WINDOW_H - 60, f"Boss HP: {boss_hp}")
    draw_text(10, WINDOW_H - 90, f"Boss State: {boss_state}")
    
    alive_count = 0
    for f in fighters:
        if f['alive']:
            alive_count += 1
            
    draw_text(10, WINDOW_H - 120, f"Alive Fighters: {alive_count}")
    
    msg = "Spears: " + spear_state
    if spear_state == "COOLDOWN": 
        msg += f" ({spear_cooldown:.1f}s)"
    draw_text(10, WINDOW_H - 150, msg)

    if game_over:
        if boss_hp <= 0:
            draw_text(WINDOW_W // 2 - 80, WINDOW_H // 2, "VICTORY! BOSS SLAIN")
        else:
            draw_text(WINDOW_W // 2 - 50, WINDOW_H // 2, "GAME OVER")
        draw_text(WINDOW_W // 2 - 70, WINDOW_H // 2 - 30, "Press R to Restart")

    glutSwapBuffers()


def idle():
    global game_over
    
    # Check Game Over Conditions
    ally_count = 0
    for f in fighters:
        if f["state"] == ALLY:
            if f["alive"]:
                ally_count += 1
            
    if ally_count == 0: 
        game_over = True

    if game_over:
        glutPostRedisplay()
        return

    # Update Game Logic
    update_boss_attack()
    update_boss_rotation()
    check_ally_conversion()
    update_spawns()
    update_spears() 
    
    glutPostRedisplay()


def main():
    global quadric
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Phase 3 - Spear Attack")

    init_fighters()
    
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.266, 0.765, 0.996, 1.0)
    
    quadric = gluNewQuadric()

    glutDisplayFunc(showScreen)
    glutSpecialFunc(specialKeyListener)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()