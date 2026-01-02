from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random

# -------------------------------
# Globals
# -------------------------------
WINDOW_W = 1000
WINDOW_H = 800

# Camera Variables
camera_angle = -90  # Set to -90 to align WASD controls with camera view
camera_radius = 700
camera_height = 500
first_person = False 

# Boss Position
boss_x = 0.0
boss_y = 0.0
boss_z = 0.0
boss_hp = 1000

# Boss Hitbox (Relative to Center)
# Expanded to include Head (Z: 260 -> 420, Y: 70 -> 90)
BOSS_BOX_MIN = [-90, -90, 0]
BOSS_BOX_MAX = [90, 90, 420]

quadric = None

# Boss State Variables
boss_state = "IDLE"     # Possible values: IDLE, WINDUP, SMASH, COOLDOWN
boss_timer = 0.0
boss_arm_angle = 0.0

# Arm length calculated to hit floor at radius 300
# Updated to 345 to reach exactly the middle of the arena ring
arm_length = 345

boss_arm_dir = 1
boss_did_damage = False
boss_facing_angle = 0.0 
game_over = False
cheat_mode = False

# Game Entities
fighters = []
spawn_points = [] 
damage_texts = [] # Store active floating damage numbers

# Entity States
ALLY = 1
IDLE = 0

walk_phase = 0.0
SMASH_RADIUS = 220 

# Weapon / Combat Variables
weapon_state = "READY"   # Possible values: READY, ATTACKING, COOLDOWN
weapon_anim_t = 0.0      # Animation progress (0.0 to 1.0)
weapon_cooldown = 0.0
attack_count = 0         # Count attacks to spawn next drop

SPEAR_DAMAGE = 20

# Shield Variables
shield_active = False       # Is a shield currently on the ground?
shield_pos = [0, 0]         # Location of the shield on ground
allies_have_shield = False  # Do allies currently hold the shield?
shield_durability = 0       # Smashes remaining before shield breaks

# Gun Variables
gun_active = False
gun_pos = [0, 0]
allies_have_gun = False
gun_ammo = 0
BULLET_DAMAGE = 4
next_drop_is_gun = True 

# Input State for Burst Fire
mouse_left_down = False
last_mouse_x = 0
last_mouse_y = 0


def init_fighters():
    global fighters, spawn_points, damage_texts
    fighters = []
    spawn_points = []
    damage_texts = []

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
    global weapon_state, weapon_anim_t, weapon_cooldown, attack_count
    global cheat_mode, next_drop_is_gun
    global shield_active, allies_have_shield, shield_durability
    global gun_active, allies_have_gun, gun_ammo
    global mouse_left_down
    
    # Reset Boss Logic
    boss_state = "IDLE"
    boss_timer = 0.0
    boss_arm_angle = 0.0
    boss_did_damage = False
    boss_facing_angle = 0.0
    boss_hp = 1000
    
    # Reset Game State
    game_over = False
    cheat_mode = False
    mouse_left_down = False
    
    # Reset Weapons
    weapon_state = "READY"
    weapon_anim_t = 0.0
    weapon_cooldown = 0.0
    attack_count = 0
    next_drop_is_gun = True
    
    # Reset Shield Logic
    shield_active = False
    allies_have_shield = False
    shield_durability = 0
    
    # Reset Gun
    gun_active = False
    allies_have_gun = False
    gun_ammo = 0
    
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


def draw_health_bar():
    # Save current matrix state
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth test to ensure UI draws on top
    glDisable(GL_DEPTH_TEST)

    # Bar Dimensions
    bar_width = 400
    bar_height = 20
    x = (WINDOW_W - bar_width) / 2
    y = WINDOW_H - 40 # Top padding

    # Draw Background (Dark Red)
    glColor3f(0.5, 0.0, 0.0) 
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + bar_width, y)
    glVertex2f(x + bar_width, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()

    # Draw Health (Green)
    # Ensure HP doesn't go below 0 for drawing ratio
    current_hp = boss_hp
    if current_hp < 0:
        current_hp = 0
        
    health_ratio = current_hp / 1000.0
    current_width = bar_width * health_ratio
    
    if current_width > 0:
        glColor3f(0.0, 1.0, 0.0) 
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + current_width, y)
        glVertex2f(x + current_width, y + bar_height)
        glVertex2f(x, y + bar_height)
        glEnd()

    # Re-enable depth test
    glEnable(GL_DEPTH_TEST)

    # Restore matrix state
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_floating_damage():
    # Temporarily disable depth test to make numbers visible through boss
    glDisable(GL_DEPTH_TEST)
    
    for dt in damage_texts:
        # Bright Red Color
        glColor3f(1.0, 0.0, 0.0) 
        glRasterPos3f(dt["x"], dt["y"], dt["z"])
        
        for ch in dt["text"]:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            
    glEnable(GL_DEPTH_TEST)


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

    # Upper Arm (Shaft)
    glPushMatrix()
    glScalef(arm_thickness, arm_length * 0.9, arm_thickness)
    glColor3f(0.4, 0.1, 0.1)
    glutSolidCube(1)
    glPopMatrix()

    # Hammer Head
    glPushMatrix()
    glTranslatef(0, -arm_length * 0.5, 0) 
    
    glPushMatrix()
    glScalef(100, 60, 60) # Big blocky hammer
    glColor3f(0.2, 0.2, 0.2) # Dark Iron
    glutSolidCube(1)
    glPopMatrix()
    
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


def draw_shield_model():
    # Simple Rectangular/Box Shield (Since we must stick to template)
    glPushMatrix()
    glScalef(10, 30, 40)
    glColor3f(0.2, 0.8, 1.0) # Cyan Shield
    glutSolidCube(1)
    glPopMatrix()
    
    # Decoration on shield
    glPushMatrix()
    glTranslatef(2, 0, 0)
    glScalef(8, 20, 30)
    glColor3f(1.0, 1.0, 1.0) # White Core
    glutSolidCube(1)
    glPopMatrix()


def draw_gun_model():
    glPushMatrix()
    # Gun Body
    glColor3f(0.2, 0.2, 0.2) # Dark Gray
    glScalef(6, 30, 6) # Long barrel
    glutSolidCube(1)
    glPopMatrix()
    
    # Handle/Grip
    glPushMatrix()
    glTranslatef(0, -10, -5)
    glRotatef(45, 1, 0, 0)
    glScalef(5, 10, 5)
    glutSolidCube(1)
    glPopMatrix()


def draw_bullet():
    glPushMatrix()
    glColor3f(1.0, 1.0, 0.0) # Yellow bullet
    glScalef(3, 8, 3)
    glutSolidCube(1)
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
            glColor3f(1.0, 0.85, 0.0) # Yellow (Moving)
        else:
            glColor3f(1.0, 1.0, 0.6) # Pale Yellow (Idle)

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

        # --- Draw Arms & Weapons ---
        if f["state"] == ALLY:
            
            # --- GUN MODE (Two Hands) ---
            if allies_have_gun:
                # Calculate recoil/shooting anim
                gun_offset = 0
                if weapon_state == "ATTACKING":
                    gun_offset = weapon_anim_t * 5 # Slight kickback visual
                
                # Right Arm (Holding Gun Back)
                glPushMatrix()
                glTranslatef(10, 0, 24)
                glRotatef(-45, 1, 0, 0) # Point forward
                glRotatef(-20, 0, 1, 0) # Angle inward
                glPushMatrix()
                glScalef(4, 4, 16)
                glutSolidCube(1)
                glPopMatrix()
                glPopMatrix()

                # Left Arm (Holding Gun Front)
                glPushMatrix()
                glTranslatef(-10, 0, 24)
                glRotatef(-45, 1, 0, 0) # Point forward
                glRotatef(20, 0, 1, 0)  # Angle inward
                glPushMatrix()
                glScalef(4, 4, 16)
                glutSolidCube(1)
                glPopMatrix()
                glPopMatrix()
                
                # Draw Gun in Center
                glPushMatrix()
                glTranslatef(0, 15 - gun_offset, 24)
                # Removed rotation so Gun points forward (Y axis) instead of Up
                draw_gun_model()
                
                # Draw Bullet if Shooting
                if weapon_state == "ATTACKING":
                    dist_to_boss = math.sqrt(x*x + y*y)
                    travel_dist = (dist_to_boss - 20) * weapon_anim_t
                    
                    glPushMatrix()
                    # Bullet travels forward along Y
                    glTranslatef(0, 20 + travel_dist, 0) 
                    draw_bullet()
                    glPopMatrix()
                    
                glPopMatrix()

            # --- SPEAR MODE (One Hand) ---
            else:
                arm_rot = 0
                if weapon_state == "ATTACKING":
                    arm_rot = -45 - (weapon_anim_t * 90)
                
                # Right Arm (Weapon)
                glPushMatrix()
                glTranslatef(10, 0, 24) 
                glRotatef(arm_rot, 1, 0, 0) 
                
                glPushMatrix()
                glScalef(4, 4, 16)
                glutSolidCube(1)
                glPopMatrix()

                if weapon_state == "READY":
                    glPushMatrix()
                    glTranslatef(0, 10, -5)
                    glRotatef(-90, 1, 0, 0)
                    draw_spear()
                    glPopMatrix()
                
                glPopMatrix() 

                # Flying Spear
                if weapon_state == "ATTACKING":
                    dist_to_boss = math.sqrt(x*x + y*y)
                    travel_dist = (dist_to_boss - 20) * weapon_anim_t
                    height_offset = 120 * weapon_anim_t

                    glPushMatrix()
                    glTranslatef(0, travel_dist, height_offset)
                    glRotatef(-90, 1, 0, 0)
                    glRotatef(-15, 1, 0, 0)
                    draw_spear()
                    glPopMatrix()

                # Left Arm (Shield or Idle)
                glColor3f(1.0, 0.85, 0.0) # Reset color
                glPushMatrix()
                glTranslatef(-10, 0, 24)
                glScalef(4, 4, 16)
                glutSolidCube(1)
                glPopMatrix()
                
                # Shield
                if allies_have_shield:
                    glPushMatrix()
                    glTranslatef(-15, 5, 20) 
                    glRotatef(15, 0, 1, 0)
                    draw_shield_model()
                    glPopMatrix()

        else:
            # Idle Fighter Arms (Static)
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

    if boss_arm_angle < -90:
        boss_arm_angle = -90
    if boss_arm_angle > 35:
        boss_arm_angle = 35


def update_boss_rotation():
    global boss_facing_angle
    
    if boss_state == "SMASH":
        return
    if boss_state == "COOLDOWN":
        return

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
        y = closest_fighter["y"]
        x = closest_fighter["x"]
        target_angle = math.degrees(math.atan2(y, x)) + 90
        diff = target_angle - boss_facing_angle
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        boss_facing_angle += diff * 0.15


def boss_smash_damage():
    global boss_did_damage, shield_durability, allies_have_shield
    
    if boss_did_damage:
        return

    # Shield Check
    if allies_have_shield:
        print("BLOCKED BY SHIELD!")
        shield_durability -= 1
        if shield_durability <= 0:
            allies_have_shield = False
            print("SHIELD BROKEN!")
        boss_did_damage = True
        return 

    # Damage Logic
    local_x = 95
    local_y = -285 
    theta = math.radians(boss_facing_angle)
    rot_x = local_x * math.cos(theta) - local_y * math.sin(theta)
    rot_y = local_x * math.sin(theta) + local_y * math.cos(theta)
    hit_x = boss_x + rot_x
    hit_y = boss_y + rot_y
    CLEAVER_RADIUS = 150 
    
    total_alive = 0
    for f in fighters:
        if f["state"] == ALLY:
            if f["alive"]:
                total_alive += 1
    
    MAX_KILLS = int(math.ceil(total_alive * 0.2))

    victims = []
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
    
    victims.sort(key=lambda v: v[0])
    killed_count = 0
    for item in victims:
        if killed_count < MAX_KILLS:
            item[1]["alive"] = False
            killed_count += 1
        else:
            break
            
    boss_did_damage = True


# -------------------------------
# Logic: Weapons & Combat
# -------------------------------
def update_weapons():
    global weapon_state, weapon_anim_t, weapon_cooldown, boss_hp, game_over
    global attack_count, shield_active, shield_pos
    global gun_active, gun_pos, gun_ammo, allies_have_gun, next_drop_is_gun
    global mouse_left_down, last_mouse_x, last_mouse_y
    global damage_texts

    # Burst Fire Check
    if allies_have_gun:
        if mouse_left_down:
            if weapon_state == "READY":
                if check_hit_boss(last_mouse_x, last_mouse_y):
                    weapon_state = "ATTACKING"

    if weapon_state == "ATTACKING":
        # Bullet moves faster (0.1) than Spear (0.01)
        speed = 0.01
        if allies_have_gun:
            speed = 0.1
            
        weapon_anim_t += speed 
        
        if weapon_anim_t >= 1.0:
            # Hit Boss
            ally_count = 0
            for f in fighters:
                if f["state"] == ALLY:
                    if f["alive"]:
                        ally_count += 1
            
            damage_per_unit = SPEAR_DAMAGE
            if allies_have_gun:
                damage_per_unit = BULLET_DAMAGE
                
            damage = ally_count * damage_per_unit
            
            if damage > 300:
                damage = 300
            
            boss_hp -= damage
            if boss_hp <= 0: 
                boss_hp = 0
                game_over = True
            
            # Spawn Floating Damage Text for each ally
            for _ in range(ally_count):
                # Spread spawn location randomly around boss
                rx = random.uniform(-40, 40)
                ry = random.uniform(-40, 40)
                rz = random.uniform(260, 320) # Above head
                
                dt = {
                    "text": f"-{damage_per_unit}",
                    "x": boss_x + rx,
                    "y": boss_y + ry,
                    "z": boss_z + rz,
                    "life": 1.0 # 1 second lifetime
                }
                damage_texts.append(dt)
            
            print(f"Boss Hit! Damage: {damage}")
            
            # Ammo / Cooldown Logic
            if allies_have_gun:
                gun_ammo -= 1
                if gun_ammo <= 0:
                    allies_have_gun = False
                    print("Out of Ammo! Switching to Spear.")
                weapon_cooldown = 0.2 # Fast gun cooldown
            else:
                weapon_cooldown = 1.0 # Spear cooldown
                
            weapon_state = "COOLDOWN"
            weapon_anim_t = 0.0
            
            # --- Spawn Logic ---
            # Only count spear throws for spawning
            if not allies_have_gun:
                attack_count += 1
                if attack_count >= 4:
                    # Alternating Spawn
                    if next_drop_is_gun:
                        if not gun_active:
                            if not allies_have_gun:
                                gun_active = True
                                angle = random.randint(0, 360)
                                r = 250
                                gun_pos[0] = r * math.cos(math.radians(angle))
                                gun_pos[1] = r * math.sin(math.radians(angle))
                                print("Gun Spawned!")
                                next_drop_is_gun = False # Next time spawn Shield
                    else:
                        if not shield_active:
                            if not allies_have_shield:
                                shield_active = True
                                angle = random.randint(0, 360)
                                r = 250
                                shield_pos[0] = r * math.cos(math.radians(angle))
                                shield_pos[1] = r * math.sin(math.radians(angle))
                                print("Shield Spawned!")
                                next_drop_is_gun = True # Next time spawn Gun
                    
                    attack_count = 0

    elif weapon_state == "COOLDOWN":
        weapon_cooldown -= 0.02 
        if weapon_cooldown <= 0:
            weapon_state = "READY"


def update_damage_texts():
    global damage_texts
    to_keep = []
    
    for dt in damage_texts:
        dt["z"] += 2.0  # Float up
        dt["life"] -= 0.02
        
        if dt["life"] > 0:
            to_keep.append(dt)
            
    damage_texts = to_keep


def check_hit_boss(mx, my):
    center_x = WINDOW_W / 2
    center_y = WINDOW_H / 2
    box_width = 300  
    box_height = 550 
    if abs(mx - center_x) < (box_width / 2):
        if abs(my - center_y) < (box_height / 2):
            return True
    return False


# -------------------------------
# Logic: Movement & Spawning
# -------------------------------
def can_move_to(x, y):
    r = math.sqrt(x*x + y*y)
    if r > (180 + 15):
        if r < (420 - 15):
            return True
    return False


def move_allies(dx, dy, phase_speed=8):
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
        walk_phase += phase_speed


def check_ally_conversion():
    global shield_active, allies_have_shield, shield_durability
    global gun_active, allies_have_gun, gun_ammo
    
    for f in fighters:
        if f["state"] != ALLY or not f["alive"]:
            continue
            
        # 1. Idle Fighter Pickup
        for other in fighters:
            if other["state"] == IDLE:
                if other["alive"]:
                    dx = f["x"] - other["x"]
                    dy = f["y"] - other["y"]
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < 22:
                        other["state"] = ALLY
                        other["moving"] = False
                        if "spawn_id" in other:
                            s_id = other["spawn_id"]
                            spawn_points[s_id]["timer"] = 30.0
                            del other["spawn_id"]
                            
        # 2. Shield Pickup
        if shield_active:
            dx = f["x"] - shield_pos[0]
            dy = f["y"] - shield_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 30: 
                print("Shield Picked Up!")
                shield_active = False
                allies_have_shield = True
                allies_have_gun = False # Drop gun if picked up shield
                shield_durability = 3

        # 3. Gun Pickup
        if gun_active:
            dx = f["x"] - gun_pos[0]
            dy = f["y"] - gun_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 30:
                print("Gun Picked Up!")
                gun_active = False
                allies_have_gun = True
                allies_have_shield = False # Drop shield if picked up gun
                gun_ammo = 20


def update_spawns():
    for i in range(len(spawn_points)):
        sp = spawn_points[i]
        if sp["timer"] > 0:
            sp["timer"] -= 0.02
            if sp["timer"] <= 0:
                fighters.append({
                    "x": sp["x"], "y": sp["y"],
                    "state": IDLE, "alive": True, "moving": False, "spawn_id": i
                })
                sp["timer"] = 0


# -------------------------------
# Logic: Cheat Mode
# -------------------------------
def update_cheat_movement():
    global cheat_mode
    if not cheat_mode:
        return
    if game_over:
        return

    ref_ally = None
    for f in fighters:
        if f["state"] == ALLY and f["alive"]:
            ref_ally = f
            break
    if ref_ally is None:
        return

    closest_idle = None
    min_dist = 999999.0
    for f in fighters:
        if f["state"] == IDLE:
            if f["alive"]:
                dx = f["x"] - ref_ally["x"]
                dy = f["y"] - ref_ally["y"]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < min_dist:
                    min_dist = dist
                    closest_idle = f
    
    if closest_idle is not None:
        target_x = closest_idle["x"]
        target_y = closest_idle["y"]
        dir_x = target_x - ref_ally["x"]
        dir_y = target_y - ref_ally["y"]
        length = math.sqrt(dir_x*dir_x + dir_y*dir_y)
        if length > 0:
            speed = 0.8 
            move_x = (dir_x / length) * speed
            move_y = (dir_y / length) * speed
            move_allies(move_x, move_y, 3)


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
    global cheat_mode
    if key == b'r':
        reset_game()
        glutPostRedisplay()
        return
    if game_over:
        return
    if key == b'c':
        cheat_mode = not cheat_mode
        print(f"Cheat Mode: {'ON' if cheat_mode else 'OFF'}")
    
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
    global weapon_state, first_person, mouse_left_down
    global last_mouse_x, last_mouse_y
    if game_over:
        return
    
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            mouse_left_down = True
            last_mouse_x = x
            last_mouse_y = y
            if weapon_state == "READY":
                if check_hit_boss(x, y):
                    print("Aim Correct! Attacking...")
                    weapon_state = "ATTACKING"
                else:
                    print("Missed Aim!")
        elif state == GLUT_UP:
            mouse_left_down = False

    if button == GLUT_RIGHT_BUTTON:
        if state == GLUT_DOWN:
            first_person = not first_person
            print(f"Camera Mode: {'First Person' if first_person else 'Orbit'}")


# -------------------------------
# Main Loop & Display
# -------------------------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    setupCamera()

    draw_arena()
    
    if shield_active:
        glPushMatrix()
        glTranslatef(shield_pos[0], shield_pos[1], 30)
        glRotatef(90, 1, 0, 0)
        draw_shield_model()
        glPopMatrix()

    if gun_active:
        glPushMatrix()
        glTranslatef(gun_pos[0], gun_pos[1], 10)
        glRotatef(90, 1, 0, 0)
        draw_gun_model()
        glPopMatrix()
        
    draw_boss()
    draw_fighters()
    
    draw_floating_damage()
    
    # Draw 2D UI elements
    draw_health_bar()

    if first_person:
        cam_mode_text = "First Person"
        
    draw_text(10, WINDOW_H - 30, f"Boss Arena: Circle of Fury ")
    draw_text(10, WINDOW_H - 60, f"Boss HP: {boss_hp}")
    
    alive_count = 0
    for f in fighters:
        if f['alive']:
            alive_count += 1
    draw_text(10, WINDOW_H - 90, f"Alive Fighters: {alive_count}")
    
    msg = "Weapon: Spear"
    if allies_have_gun:
        msg = f"Weapon: Gun (Ammo: {gun_ammo})"
    
    if weapon_state == "COOLDOWN":
        msg += " (Cooldown)"
    draw_text(10, WINDOW_H - 120, msg)

    cheat_text = "OFF"
    if cheat_mode:
        cheat_text = "ON"
    draw_text(10, WINDOW_H - 150, f"Cheat Mode (C): {cheat_text}") 
    
    if allies_have_shield:
        draw_text(10, WINDOW_H - 180, f"SHIELD ACTIVE! Blocks Left: {shield_durability}")

    if game_over:
        if boss_hp <= 0:
            draw_text(WINDOW_W // 2 - 80, WINDOW_H // 2, "VICTORY! BOSS SLAIN")
        else:
            draw_text(WINDOW_W // 2 - 50, WINDOW_H // 2, "GAME OVER")
        draw_text(WINDOW_W // 2 - 70, WINDOW_H // 2 - 30, "Press R to Restart")

    glutSwapBuffers()


def idle():
    global game_over
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

    update_boss_attack()
    update_boss_rotation()
    check_ally_conversion()
    update_spawns()
    update_weapons()
    update_damage_texts()
    update_cheat_movement()
    glutPostRedisplay()


def main():
    global quadric
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Boss Arena: Circle of Fury")

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