from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random


WINDOW_W = 1000
WINDOW_H = 800

camera_angle = -90
camera_radius = 700
camera_height = 500
first_person = False

boss_x = 0.0
boss_y = 0.0
boss_z = 0.0
boss_hp = 1000

BOSS_BOX_MIN = [-90, -90, 0]
BOSS_BOX_MAX = [90, 90, 420]

quadric = None

boss_state = "IDLE"
boss_timer = 0.0
boss_arm_angle = 0.0

arm_length = 345

boss_arm_dir = 1
boss_did_damage = False
boss_facing_angle = 0.0
game_over = False
cheat_mode = False

fighters = []
spawn_points = []
damage_texts = []

ALLY = 1
IDLE = 0

walk_phase = 0.0
SMASH_RADIUS = 220

weapon_state = "READY"
weapon_anim_t = 0.0
weapon_cooldown = 0.0
attack_count = 0

SPEAR_DAMAGE = 20

shield_active = False
shield_pos = [0, 0]
allies_have_shield = False
shield_durability = 0

gun_active = False
gun_pos = [0, 0]
allies_have_gun = False
gun_ammo = 0
BULLET_DAMAGE = 4
next_drop_is_gun = True

mouse_left_down = False
last_mouse_x = 0
last_mouse_y = 0


def init_fighters():
    global fighters, spawn_points, damage_texts
    fighters = []
    spawn_points = []
    damage_texts = []

    for i in range(6):
        fighter = {
            "x": -200 + i * 15,
            "y": 150,
            "state": ALLY,
            "alive": True,
            "moving": False
        }
        fighters.append(fighter)

    for i in range(14):
        angle_deg = i * (360 / 14)
        r = 320

        fx = r * math.cos(math.radians(angle_deg))
        fy = r * math.sin(math.radians(angle_deg))

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

    boss_state = "IDLE"
    boss_timer = 0.0
    boss_arm_angle = 0.0
    boss_did_damage = False
    boss_facing_angle = 0.0
    boss_hp = 1000

    game_over = False
    cheat_mode = False
    mouse_left_down = False

    weapon_state = "READY"
    weapon_anim_t = 0.0
    weapon_cooldown = 0.0
    attack_count = 0
    next_drop_is_gun = True

    shield_active = False
    allies_have_shield = False
    shield_durability = 0

    gun_active = False
    allies_have_gun = False
    gun_ammo = 0

    init_fighters()


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
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)

    bar_width = 400
    bar_height = 20
    x = (WINDOW_W - bar_width) / 2
    y = WINDOW_H - 40

    glColor3f(0.5, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + bar_width, y)
    glVertex2f(x + bar_width, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()

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

    glEnable(GL_DEPTH_TEST)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_floating_damage():
    glDisable(GL_DEPTH_TEST)

    for dt in damage_texts:
        glColor3f(1.0, 0.0, 0.0)
        glRasterPos3f(dt["x"], dt["y"], dt["z"])

        for ch in dt["text"]:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glEnable(GL_DEPTH_TEST)


def setupCamera():
    global first_person

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(80, WINDOW_W / float(WINDOW_H), 0.1, 2500.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        target_f = None

        for f in fighters:
            if f["state"] == ALLY:
                if f["alive"]:
                    target_f = f
                    break

        if target_f is not None:
            eye_x = target_f["x"]
            eye_y = target_f["y"]
            eye_z = 60

            center_x = 0
            center_y = 0
            center_z = 120

            gluLookAt(eye_x, eye_y, eye_z,
                      center_x, center_y, center_z,
                      0, 0, 1)
            return

    cx = math.cos(math.radians(camera_angle)) * camera_radius
    cy = math.sin(math.radians(camera_angle)) * camera_radius
    cz = camera_height

    gluLookAt(cx, cy, cz,
              0.0, 0.0, 0.0,
              0.0, 0.0, 1.0)


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

        glVertex3f(x1i, y1i, 0)
        glVertex3f(x1o, y1o, 0)
        glVertex3f(x2o, y2o, 0)

        glVertex3f(x1i, y1i, 0)
        glVertex3f(x2o, y2o, 0)
        glVertex3f(x2i, y2i, 0)
    glEnd()


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

    glColor3f(0.35, 0.35, 0.35)
    glPushMatrix()
    glTranslatef(0, 0, body_height * 0.5)
    glScalef(180, 140, body_height)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, body_height + head_radius * 0.6)
    glColor3f(0.6, 0.1, 0.1)
    gluSphere(quadric, head_radius, 24, 24)
    glPopMatrix()

    shoulder_z = body_height * 0.75

    glPushMatrix()
    glTranslatef(torso_half_x + 5, 0, shoulder_z)
    glRotatef(boss_arm_angle, 1, 0, 0)
    glTranslatef(0, -arm_length * 0.5, 0)

    glPushMatrix()
    glScalef(arm_thickness, arm_length * 0.9, arm_thickness)
    glColor3f(0.4, 0.1, 0.1)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, -arm_length * 0.5, 0)

    glPushMatrix()
    glScalef(100, 60, 60)
    glColor3f(0.2, 0.2, 0.2)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

    glPopMatrix()

    glPushMatrix()
    glTranslatef(-torso_half_x - 5, 0, shoulder_z)
    glTranslatef(0, -arm_length * 0.5, 0)

    glScalef(arm_thickness, arm_length * 0.8, arm_thickness)
    glColor3f(0.3, 0.1, 0.1)
    glutSolidCube(1)

    glPopMatrix()

    glPopMatrix()


def draw_spear():
    glPushMatrix()
    glPushMatrix()
    glScalef(3, 3, 50)
    glColor3f(0.55, 0.27, 0.07)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 25)
    glColor3f(0.9, 0.9, 0.9)
    glutSolidCone(3, 15, 10, 10)
    glPopMatrix()
    glPopMatrix()


def draw_shield_model():
    glPushMatrix()
    glScalef(10, 30, 40)
    glColor3f(0.2, 0.8, 1.0)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(2, 0, 0)
    glScalef(8, 20, 30)
    glColor3f(1.0, 1.0, 1.0)
    glutSolidCube(1)
    glPopMatrix()

def draw_gun_model():
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.2)
    glScalef(6, 30, 6)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, -10, -5)
    glRotatef(45, 1, 0, 0)
    glScalef(5, 10, 5)
    glutSolidCube(1)
    glPopMatrix()

def draw_bullet():
    glPushMatrix()
    glColor3f(1.0, 1.0, 0.0)
    glScalef(3, 8, 3)
    glutSolidCube(1)
    glPopMatrix()


def draw_fighters():
    for f in fighters:
        if f["alive"] == False:
            continue

        x = f["x"]
        y = f["y"]

        rad_angle = math.atan2(-y, -x)
        angle_deg = math.degrees(rad_angle) - 90

        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(angle_deg, 0, 0, 1)

        if f["state"] == ALLY:
            glColor3f(1.0, 0.85, 0.0)
        else:
            glColor3f(1.0, 1.0, 0.6)

        glPushMatrix()
        glTranslatef(0, 0, 22)
        glScalef(12, 8, 22)
        glutSolidCube(1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 38)
        gluSphere(quadric, 6, 12, 12)
        glPopMatrix()

        if f["state"] == ALLY:

            if allies_have_gun:
                gun_offset = 0
                if weapon_state == "ATTACKING":
                    gun_offset = weapon_anim_t * 5

                glPushMatrix()
                glTranslatef(10, 0, 24)
                glRotatef(-45, 1, 0, 0)
                glRotatef(-20, 0, 1, 0)
                glPushMatrix()
                glScalef(4, 4, 16)
                glutSolidCube(1)
                glPopMatrix()
                glPopMatrix()

                glPushMatrix()
                glTranslatef(-10, 0, 24)
                glRotatef(-45, 1, 0, 0)
                glRotatef(20, 0, 1, 0)
                glPushMatrix()
                glScalef(4, 4, 16)
                glutSolidCube(1)
                glPopMatrix()
                glPopMatrix()

                glPushMatrix()
                glTranslatef(0, 15 - gun_offset, 24)
                draw_gun_model()

                if weapon_state == "ATTACKING":
                    dist_to_boss = math.sqrt(x*x + y*y)
                    travel_dist = (dist_to_boss - 20) * weapon_anim_t

                    glPushMatrix()
                    glTranslatef(0, 20 + travel_dist, 0)
                    draw_bullet()
                    glPopMatrix()

                glPopMatrix()

            else:
                arm_rot = 0
                if weapon_state == "ATTACKING":
                    arm_rot = -45 - (weapon_anim_t * 90)

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

                glColor3f(1.0, 0.85, 0.0)
                glPushMatrix()
                glTranslatef(-10, 0, 24)
                glScalef(4, 4, 16)
                glutSolidCube(1)
                glPopMatrix()

                if allies_have_shield:
                    glPushMatrix()
                    glTranslatef(-15, 5, 20)
                    glRotatef(15, 0, 1, 0)
                    draw_shield_model()
                    glPopMatrix()

        else:
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

        leg_angle = 0
        if f["moving"]:
            leg_angle = math.sin(math.radians(walk_phase)) * 25

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

    if allies_have_shield:
        print("BLOCKED BY SHIELD!")
        shield_durability -= 1
        if shield_durability <= 0:
            allies_have_shield = False
            print("SHIELD BROKEN!")
        boss_did_damage = True
        return

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


def update_weapons():
    global weapon_state, weapon_anim_t, weapon_cooldown, boss_hp, game_over
    global attack_count, shield_active, shield_pos
    global gun_active, gun_pos, gun_ammo, allies_have_gun, next_drop_is_gun
    global mouse_left_down, last_mouse_x, last_mouse_y
    global damage_texts

    if allies_have_gun:
        if mouse_left_down:
            if weapon_state == "READY":
                if check_hit_boss(last_mouse_x, last_mouse_y):
                    weapon_state = "ATTACKING"

    if weapon_state == "ATTACKING":
        speed = 0.01
        if allies_have_gun:
            speed = 0.1

        weapon_anim_t += speed

        if weapon_anim_t >= 1.0:
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

            for _ in range(ally_count):
                rx = random.uniform(-40, 40)
                ry = random.uniform(-40, 40)
                rz = random.uniform(260, 320)

                dt = {
                    "text": f"-{damage_per_unit}",
                    "x": boss_x + rx,
                    "y": boss_y + ry,
                    "z": boss_z + rz,
                    "life": 1.0
                }
                damage_texts.append(dt)

            print(f"Boss Hit! Damage: {damage}")

            if allies_have_gun:
                gun_ammo -= 1
                if gun_ammo <= 0:
                    allies_have_gun = False
                    print("Out of Ammo! Switching to Spear.")
                weapon_cooldown = 0.2
            else:
                weapon_cooldown = 1.0

            weapon_state = "COOLDOWN"
            weapon_anim_t = 0.0

            if not allies_have_gun:
                attack_count += 1
                if attack_count >= 4:
                    if next_drop_is_gun:
                        if not gun_active:
                            if not allies_have_gun:
                                gun_active = True
                                angle = random.randint(0, 360)
                                r = 250
                                gun_pos[0] = r * math.cos(math.radians(angle))
                                gun_pos[1] = r * math.sin(math.radians(angle))
                                print("Gun Spawned!")
                                next_drop_is_gun = False
                    else:
                        if not shield_active:
                            if not allies_have_shield:
                                shield_active = True
                                angle = random.randint(0, 360)
                                r = 250
                                shield_pos[0] = r * math.cos(math.radians(angle))
                                shield_pos[1] = r * math.sin(math.radians(angle))
                                print("Shield Spawned!")
                                next_drop_is_gun = True

                    attack_count = 0

    elif weapon_state == "COOLDOWN":
        weapon_cooldown -= 0.02
        if weapon_cooldown <= 0:
            weapon_state = "READY"


def update_damage_texts():
    global damage_texts
    to_keep = []

    for dt in damage_texts:
        dt["z"] += 2.0
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

        if shield_active:
            dx = f["x"] - shield_pos[0]
            dy = f["y"] - shield_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 30:
                print("Shield Picked Up!")
                shield_active = False
                allies_have_shield = True
                allies_have_gun = False
                shield_durability = 3

        if gun_active:
            dx = f["x"] - gun_pos[0]
            dy = f["y"] - gun_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 30:
                print("Gun Picked Up!")
                gun_active = False
                allies_have_gun = True
                allies_have_shield = False
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

    draw_health_bar()

    cam_mode_text = "Orbit"
    if first_person:
        cam_mode_text = "First Person"

    draw_text(10, WINDOW_H - 30, f"Boss Arena: Circle of Fury")
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