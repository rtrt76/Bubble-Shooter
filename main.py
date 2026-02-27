# =====================================================================
# BUBBLE SHOOTER PRO - VERSION 1.2.1.0 (ULTIMATE EDITION)
# Developed for: Omar
# UX/UI Focus: High-end Indie Game Standards
# Features: Store, Settings, Save System, Particles, Arabic Support
# =====================================================================

import pygame
import math
import random
import os
import json
from collections import deque

# --- محاولة استدعاء مكتبات اللغة العربية بأمان تام ---
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    print("⚠️ مكتبات اللغة العربية غير موجودة. سيتم استخدام اللغة الإنجليزية.")
    print("لتفعيل العربية: pip install arabic-reshaper python-bidi")

# ==========================================
# 1. الإعدادات والثوابت (Game Configurations)
# ==========================================
pygame.init()
pygame.mixer.init()

# إعدادات الشاشة (متوافقة مع أبعاد الهواتف 9:16)
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 960
FPS = 60

# الألوان (Modern UI Palette)
COLORS = {
    "red": (255, 60, 60),
    "blue": (60, 150, 255),
    "green": (60, 255, 60),
    "yellow": (255, 220, 60),
    "purple": (200, 60, 255),
    "cyan": (60, 255, 255),
    "orange": (255, 150, 50)
}
BG_COLOR = (15, 20, 40)       # خلفية ليلية
PANEL_COLOR = (30, 40, 70)    # لون القوائم
TEXT_COLOR = (255, 255, 255)
GOLD = (255, 215, 0)

# إعدادات الشبكة
ROWS = 15
COLS = 11
RADIUS = 22
DIAMETER = RADIUS * 2
ROW_HEIGHT = int(DIAMETER * math.sin(math.radians(60)))

# تهيئة الشاشة والخطوط
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bubble Shooter Pro v1.2.1.0")
clock = pygame.time.Clock()

# محاولة استخدام خط يدعم العربي (Arial أو Tahoma)
sys_font = 'arial' if pygame.font.match_font('arial') else None
font_large = pygame.font.SysFont(sys_font, 64, bold=True)
font_med = pygame.font.SysFont(sys_font, 36, bold=True)
font_small = pygame.font.SysFont(sys_font, 24, bold=True)

# ==========================================
# 2. الأنظمة المساعدة (Core Systems & UX Tools)
# ==========================================

class SaveSystem:
    """نظام لحفظ واسترجاع بيانات اللاعب (الفلوس والمستويات)"""
    FILE_NAME = "savegame.json"
    
    @staticmethod
    def load():
        if os.path.exists(SaveSystem.FILE_NAME):
            with open(SaveSystem.FILE_NAME, 'r') as f:
                return json.load(f)
        return {"level": 1, "coins": 0, "bombs": 1, "fireballs": 1, "rainbows": 1, "sound": True}

    @staticmethod
    def save(data):
        with open(SaveSystem.FILE_NAME, 'w') as f:
            json.dump(data, f)

# تحميل البيانات
game_data = SaveSystem.load()

def render_text(text_ar, text_en, font, color):
    """دالة ذكية لطباعة النص سواء عربي أو إنجليزي حسب المتوفر لمنع الأخطاء"""
    if ARABIC_SUPPORT and text_ar:
        reshaped = arabic_reshaper.reshape(text_ar)
        bidi_text = get_display(reshaped)
        return font.render(bidi_text, True, color)
    else:
        return font.render(text_en, True, color)

class SoundManager:
    """نظام إدارة الأصوات بدون أخطاء إذا كانت الملفات غير موجودة"""
    def __init__(self):
        self.enabled = game_data["sound"]
        self.sounds = {}
        # لو مفيش ملفات صوت، مش هيحصل خطأ
        
    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled
        game_data["sound"] = self.enabled
        SaveSystem.save(game_data)

sound_mgr = SoundManager()

class Particle:
    """جزيئات الانفجار لزيادة متعة اللعب (VFX)"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(4, 10)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 8)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.life = 255 # الشفافية والعمر

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.3 # الجاذبية
        self.life -= 10
        self.size *= 0.95

    def draw(self, surface):
        if self.life > 0:
            surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, max(0, self.life)), (self.size, self.size), self.size)
            surface.blit(surf, (self.x - self.size, self.y - self.size))

class FloatingText:
    """نصوص تطير لأعلى (مثال: +100 نقطة)"""
    def __init__(self, x, y, text_ar, text_en, color):
        self.x = x
        self.y = y
        self.text_surf = render_text(text_ar, text_en, font_small, color)
        self.life = 60
        self.dy = -2

    def update(self):
        self.y += self.dy
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            self.text_surf.set_alpha(int((self.life / 60) * 255))
            surface.blit(self.text_surf, (self.x - self.text_surf.get_width()//2, self.y))

class Button:
    """أزرار واجهة المستخدم التفاعلية (UX Interactive Buttons)"""
    def __init__(self, x, y, width, height, text_ar, text_en, color):
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)
        self.color = color
        self.text_ar = text_ar
        self.text_en = text_en
        self.hovered = False
        self.scale = 1.0

    def draw(self, surface):
        # تأثير التكبير عند الوقوف بالماوس
        target_scale = 1.1 if self.hovered else 1.0
        self.scale += (target_scale - self.scale) * 0.2
        
        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        r = pygame.Rect(self.rect.centerx - w//2, self.rect.centery - h//2, w, h)
        
        # رسم الزر مع حواف ناعمة الظل
        pygame.draw.rect(surface, (20, 20, 20), (r.x+5, r.y+5, w, h), border_radius=15)
        pygame.draw.rect(surface, self.color, r, border_radius=15)
        pygame.draw.rect(surface, (255, 255, 255), r, width=2, border_radius=15) # إطار
        
        txt_surf = render_text(self.text_ar, self.text_en, font_med, TEXT_COLOR)
        surface.blit(txt_surf, (r.centerx - txt_surf.get_width()//2, r.centery - txt_surf.get_height()//2))

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered

# ==========================================
# 3. كائنات اللعبة الأساسية (Game Entities)
# ==========================================

class Bubble:
    def __init__(self, x, y, color_name, is_powerup=None):
        self.x = x
        self.y = y
        self.color_name = color_name
        self.color = COLORS.get(color_name, (200, 200, 200))
        self.radius = RADIUS
        self.dx = 0
        self.dy = 0
        self.speed = 25
        self.is_moving = False
        self.is_powerup = is_powerup # "bomb", "fireball", "rainbow"

    def draw(self, surface):
        if self.is_powerup == "bomb":
            pygame.draw.circle(surface, (50, 50, 50), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 50, 50), (int(self.x), int(self.y)), self.radius//2)
        elif self.is_powerup == "fireball":
            pygame.draw.circle(surface, (255, 100, 0), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), self.radius//2)
        elif self.is_powerup == "rainbow":
            pygame.draw.circle(surface, random.choice(list(COLORS.values())), (int(self.x), int(self.y)), self.radius)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x) - 6, int(self.y) - 6), self.radius // 3)
            pygame.draw.circle(surface, (0, 0, 0), (int(self.x), int(self.y)), self.radius, 1)

    def move(self):
        if self.is_moving:
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed
            
            if self.x - self.radius <= 0:
                self.x = self.radius
                self.dx *= -1
                sound_mgr.play("bounce")
            elif self.x + self.radius >= SCREEN_WIDTH:
                self.x = SCREEN_WIDTH - self.radius
                self.dx *= -1
                sound_mgr.play("bounce")

class GridManager:
    def __init__(self, level):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.top_margin = 80
        self.level = level
        self.populate_initial_grid()

    def populate_initial_grid(self):
        # كل مستوى بيزود الألوان والصفوف
        num_colors = min(3 + self.level // 2, len(COLORS))
        available_colors = list(COLORS.keys())[:num_colors]
        num_rows = min(4 + self.level, 10) # أقصى حاجة 10 صفوف بداية
        
        for row in range(num_rows):
            for col in range(COLS):
                if row % 2 != 0 and col == COLS - 1: continue
                color = random.choice(available_colors)
                x, y = self.get_xy(row, col)
                self.grid[row][col] = Bubble(x, y, color)

    def get_xy(self, row, col):
        x = col * DIAMETER + RADIUS
        if row % 2 != 0: x += RADIUS
        y = row * ROW_HEIGHT + RADIUS + self.top_margin
        return x, y

    def get_row_col(self, x, y):
        row = int(round((y - self.top_margin - RADIUS) / ROW_HEIGHT))
        row = max(0, min(row, ROWS - 1))
        offset = RADIUS if row % 2 != 0 else 0
        col = int(round((x - RADIUS - offset) / DIAMETER))
        col = max(0, min(col, COLS - 1))
        if row % 2 != 0 and col == COLS - 1: col -= 1
        return row, col

    def get_active_colors(self):
        active = set()
        for row in range(ROWS):
            for col in range(COLS):
                if self.grid[row][col]:
                    active.add(self.grid[row][col].color_name)
        return list(active) if active else ["red"]

    def draw(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                b = self.grid[row][col]
                if b: b.draw(surface)
                
        # رسم خط الخطر (Danger Line)
        danger_y = (ROWS - 2) * ROW_HEIGHT + self.top_margin
        pygame.draw.line(surface, (255, 0, 0), (0, danger_y), (SCREEN_WIDTH, danger_y), 2)

class Shooter:
    def __init__(self, grid_manager):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 80
        self.gm = grid_manager
        self.flying = None
        self.current = None
        self.next = None
        self.shots_fired = 0
        self.reload()

    def reload(self, powerup=None):
        active = self.gm.get_active_colors()
        if not self.current:
            self.current = Bubble(self.x, self.y, random.choice(active))
            self.next = Bubble(self.x - 100, self.y + 20, random.choice(active))
        else:
            self.current = self.next
            self.current.x, self.current.y = self.x, self.y
            self.next = Bubble(self.x - 100, self.y + 20, random.choice(active))

        if powerup:
            self.current.is_powerup = powerup

    def swap(self):
        # ميزة التبديل (Swap UX Feature)
        if not self.current.is_powerup and not self.next.is_powerup:
            self.current, self.next = self.next, self.current
            self.current.x, self.current.y = self.x, self.y
            self.next.x, self.next.y = self.x - 100, self.y + 20

    def shoot(self, target_x, target_y):
        if self.flying is not None: return
        dx = target_x - self.x
        dy = target_y - self.y
        if dy >= -10: return # لا تضرب لأسفل
        
        angle = math.atan2(dy, dx)
        self.flying = self.current
        self.flying.dx = math.cos(angle)
        self.flying.dy = math.sin(angle)
        self.flying.is_moving = True
        self.shots_fired += 1
        self.reload()
        sound_mgr.play("shoot")

    def draw(self, surface, mouse_pos):
        # قاعدة المدفع
        pygame.draw.circle(surface, (80, 80, 100), (self.x, self.y), 45)
        pygame.draw.circle(surface, (40, 40, 60), (self.x, self.y), 35)
        
        # مكان الفقاعة القادمة
        pygame.draw.circle(surface, (50, 50, 70), (self.x - 100, self.y + 20), RADIUS + 5)
        
        if self.flying is None and mouse_pos[1] < self.y:
            dx = mouse_pos[0] - self.x
            dy = mouse_pos[1] - self.y
            angle = math.atan2(dy, dx)
            # خط تصويب طويل ومريح
            for i in range(1, 15):
                dot_x = self.x + math.cos(angle) * (i * 35)
                dot_y = self.y + math.sin(angle) * (i * 35)
                # ارتداد خط التصويب (UX Pro Feature)
                if dot_x <= 0 or dot_x >= SCREEN_WIDTH:
                    angle = math.pi - angle
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                pygame.draw.circle(surface, (255, 255, 255), (int(dot_x), int(dot_y)), 4)

        if self.current and not self.flying: self.current.draw(surface)
        if self.next: self.next.draw(surface)
        if self.flying: self.flying.draw(surface)

# ==========================================
# 4. محرك اللعبة وإدارة الحالات (Game Engine & States)
# ==========================================

class Engine:
    def __init__(self):
        self.state = "MENU"
        self.running = True
        self.particles = []
        self.texts = []
        self.screen_shake = 0
        
        # UI القائمة الرئيسية
        self.btn_play = Button(SCREEN_WIDTH//2, 400, 250, 60, "العب الآن", "PLAY NOW", COLORS["green"])
        self.btn_store = Button(SCREEN_WIDTH//2, 500, 250, 60, "المتجر", "STORE", COLORS["blue"])
        self.btn_settings = Button(SCREEN_WIDTH//2, 600, 250, 60, "الإعدادات", "SETTINGS", COLORS["purple"])
        self.btn_quit = Button(SCREEN_WIDTH//2, 700, 250, 60, "خروج", "QUIT", COLORS["red"])
        
        # UI المتجر
        self.btn_buy_bomb = Button(SCREEN_WIDTH//2, 300, 300, 60, "قنبلة (100 عملة)", "BOMB (100)", (100, 100, 100))
        self.btn_buy_fire = Button(SCREEN_WIDTH//2, 400, 300, 60, "كرة نار (150 عملة)", "FIRE (150)", COLORS["orange"])
        self.btn_buy_rain = Button(SCREEN_WIDTH//2, 500, 300, 60, "ألوان (200 عملة)", "RAINBOW (200)", COLORS["cyan"])
        self.btn_back = Button(SCREEN_WIDTH//2, 700, 200, 60, "رجوع", "BACK", COLORS["red"])

        # UI الإعدادات
        self.btn_sound = Button(SCREEN_WIDTH//2, 400, 300, 60, "الصوت: تشغيل/إيقاف", "SOUND: ON/OFF", COLORS["blue"])

        # UI اللعب (Powerups)
        self.btn_use_bomb = Button(100, SCREEN_HEIGHT - 30, 80, 40, "قنبلة", "BOMB", (100, 100, 100))
        self.btn_use_fire = Button(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30, 80, 40, "نار", "FIRE", COLORS["orange"])
        self.btn_use_rain = Button(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30, 80, 40, "قوس", "RAIN", COLORS["cyan"])

        self.reset_game()

    def reset_game(self):
        self.gm = GridManager(game_data["level"])
        self.shooter = Shooter(self.gm)
        self.score = 0
        self.combo = 1
        self.particles.clear()
        self.texts.clear()

    def spawn_particles(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def add_floating_text(self, x, y, text_ar, text_en, color):
        self.texts.append(FloatingText(x, y, text_ar, text_en, color))

    def get_neighbors(self, r, c):
        directions = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)] if r % 2 == 0 else [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        return [(r+dr, c+dc) for dr, dc in directions if 0 <= r+dr < ROWS and 0 <= c+dc < COLS]

    def process_match(self, r, c):
        b = self.gm.grid[r][c]
        if not b: return
        
        # معالجة القوى الخارقة (Powerups Logic)
        if b.is_powerup == "bomb":
            self.screen_shake = 20
            self.add_floating_text(b.x, b.y, "انفجار!", "BOOM!", COLORS["red"])
            for nr, nc in self.get_neighbors(r, c) + [(r,c)]:
                if self.gm.grid[nr][nc]:
                    self.spawn_particles(self.gm.grid[nr][nc].x, self.gm.grid[nr][nc].y, self.gm.grid[nr][nc].color)
                    self.gm.grid[nr][nc] = None
            sound_mgr.play("pop")
            return True

        if b.is_powerup == "fireball":
            self.screen_shake = 15
            self.add_floating_text(b.x, b.y, "حريق!", "FIRE!", COLORS["orange"])
            for col in range(COLS):
                if self.gm.grid[r][col]:
                    self.spawn_particles(self.gm.grid[r][col].x, self.gm.grid[r][col].y, self.gm.grid[r][col].color)
                    self.gm.grid[r][col] = None
            sound_mgr.play("pop")
            return True

        # الخوارزمية العادية (Flood Fill) للبحث عن الألوان المتطابقة أو الـ Rainbow
        target_color = b.color_name
        visited = set()
        group = []

        def flood(row, col):
            if (row, col) in visited: return
            cb = self.gm.grid[row][col]
            if not cb: return
            if cb.color_name != target_color and cb.is_powerup != "rainbow" and b.is_powerup != "rainbow": return
            
            visited.add((row, col))
            group.append((row, col))
            for nr, nc in self.get_neighbors(row, col): flood(nr, nc)

        flood(r, c)

        if len(group) >= 3:
            pts = len(group) * 10 * self.combo
            self.score += pts
            game_data["coins"] += len(group) # كل فقاعة بعملة
            self.add_floating_text(b.x, b.y, f"+{pts}", f"+{pts}", GOLD)
            
            if self.combo > 1:
                self.add_floating_text(b.x, b.y-30, f"كومبو x{self.combo}!", f"COMBO x{self.combo}!", COLORS["purple"])

            for gr, gc in group:
                self.spawn_particles(self.gm.grid[gr][gc].x, self.gm.grid[gr][gc].y, self.gm.grid[gr][gc].color)
                self.gm.grid[gr][gc] = None
            
            self.combo += 1
            sound_mgr.play("pop")
            return True
            
        self.combo = 1 # فقدان الكومبو لو مفيش تطابق
        return False

    def remove_floating(self):
        """إسقاط الفقاعات غير المتصلة بالسقف (BFS Algorithm)"""
        visited = set()
        queue = deque()
        for col in range(COLS):
            if self.gm.grid[0][col]:
                queue.append((0, col))
                visited.add((0, col))

        while queue:
            r, c = queue.popleft()
            for nr, nc in self.get_neighbors(r, c):
                if (nr, nc) not in visited and self.gm.grid[nr][nc]:
                    visited.add((nr, nc))
                    queue.append((nr, nc))

        dropped = 0
        for r in range(ROWS):
            for c in range(COLS):
                if self.gm.grid[r][c] and (r, c) not in visited:
                    self.spawn_particles(self.gm.grid[r][c].x, self.gm.grid[r][c].y, self.gm.grid[r][c].color, 5)
                    self.gm.grid[r][c] = None
                    dropped += 1
        
        if dropped > 0:
            pts = dropped * 20
            self.score += pts
            game_data["coins"] += dropped * 2
            self.add_floating_text(SCREEN_WIDTH//2, 300, "تساقط رائع!", "GREAT DROP!", COLORS["cyan"])

    def run(self):
        while self.running:
            screen.fill(BG_COLOR)
            mouse_pos = pygame.mouse.get_pos()
            
            # 1. الاهتزاز (Screen Shake)
            offset_x, offset_y = 0, 0
            if self.screen_shake > 0:
                offset_x = random.randint(-self.screen_shake, self.screen_shake)
                offset_y = random.randint(-self.screen_shake, self.screen_shake)
                self.screen_shake -= 1

            # 2. رسم الخلفية المليئة بالنجوم (UX)
            for _ in range(5):
                pygame.draw.circle(screen, (255,255,255), (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)), 1)

            # --- التحكم في الحالات (State Machine) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    SaveSystem.save(game_data)
                    self.running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    
                    if self.state == "MENU":
                        if self.btn_play.check_hover(mouse_pos): self.state = "PLAYING"; self.reset_game()
                        if self.btn_store.check_hover(mouse_pos): self.state = "STORE"
                        if self.btn_settings.check_hover(mouse_pos): self.state = "SETTINGS"
                        if self.btn_quit.check_hover(mouse_pos): self.running = False

                    elif self.state == "STORE":
                        if self.btn_back.check_hover(mouse_pos): self.state = "MENU"; SaveSystem.save(game_data)
                        if self.btn_buy_bomb.check_hover(mouse_pos) and game_data["coins"] >= 100:
                            game_data["coins"] -= 100; game_data["bombs"] += 1
                        if self.btn_buy_fire.check_hover(mouse_pos) and game_data["coins"] >= 150:
                            game_data["coins"] -= 150; game_data["fireballs"] += 1
                        if self.btn_buy_rain.check_hover(mouse_pos) and game_data["coins"] >= 200:
                            game_data["coins"] -= 200; game_data["rainbows"] += 1

                    elif self.state == "SETTINGS":
                        if self.btn_back.check_hover(mouse_pos): self.state = "MENU"
                        if self.btn_sound.check_hover(mouse_pos): sound_mgr.toggle()

                    elif self.state == "PLAYING":
                        # فحص زراير الأدوات
                        if self.btn_use_bomb.check_hover(mouse_pos) and game_data["bombs"] > 0:
                            game_data["bombs"] -= 1; self.shooter.reload("bomb")
                        elif self.btn_use_fire.check_hover(mouse_pos) and game_data["fireballs"] > 0:
                            game_data["fireballs"] -= 1; self.shooter.reload("fireball")
                        elif self.btn_use_rain.check_hover(mouse_pos) and game_data["rainbows"] > 0:
                            game_data["rainbows"] -= 1; self.shooter.reload("rainbow")
                        elif mouse_pos[1] > self.shooter.y - 40 and mouse_pos[1] < self.shooter.y + 40 and mouse_pos[0] > self.shooter.x - 120 and mouse_pos[0] < self.shooter.x + 40:
                            self.shooter.swap() # تبديل الفقاعة إذا ضغط على منطقة المدفع
                        else:
                            self.shooter.shoot(mouse_pos[0], mouse_pos[1])

                    elif self.state in ["GAME_OVER", "LEVEL_UP"]:
                        self.state = "MENU"
                        SaveSystem.save(game_data)

            # --- منطق ورسم كل حالة ---
            surface_game = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

            if self.state == "MENU":
                title = render_text("لعبة عمر فقاعات برو", "BUBBLE SHOOTER PRO", font_large, GOLD)
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
                self.btn_play.draw(screen)
                self.btn_store.draw(screen)
                self.btn_settings.draw(screen)
                self.btn_quit.draw(screen)

            elif self.state == "STORE":
                title = render_text("المتجر - طور أسلحتك", "STORE", font_large, GOLD)
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
                coins_txt = render_text(f"عملاتك: {game_data['coins']}", f"COINS: {game_data['coins']}", font_med, COLORS["yellow"])
                screen.blit(coins_txt, (SCREEN_WIDTH//2 - coins_txt.get_width()//2, 180))
                
                self.btn_buy_bomb.draw(screen)
                inv_bomb = render_text(f"معاك: {game_data['bombs']}", f"Owned: {game_data['bombs']}", font_small, TEXT_COLOR)
                screen.blit(inv_bomb, (SCREEN_WIDTH//2 - inv_bomb.get_width()//2, 340))
                
                self.btn_buy_fire.draw(screen)
                inv_fire = render_text(f"معاك: {game_data['fireballs']}", f"Owned: {game_data['fireballs']}", font_small, TEXT_COLOR)
                screen.blit(inv_fire, (SCREEN_WIDTH//2 - inv_fire.get_width()//2, 440))
                
                self.btn_buy_rain.draw(screen)
                inv_rain = render_text(f"معاك: {game_data['rainbows']}", f"Owned: {game_data['rainbows']}", font_small, TEXT_COLOR)
                screen.blit(inv_rain, (SCREEN_WIDTH//2 - inv_rain.get_width()//2, 540))
                
                self.btn_back.draw(screen)

            elif self.state == "SETTINGS":
                title = render_text("الإعدادات", "SETTINGS", font_large, GOLD)
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
                status = "شغال (ON)" if game_data["sound"] else "مقفول (OFF)"
                self.btn_sound.text_ar = f"الصوت: {status}"
                self.btn_sound.text_en = f"SOUND: {status}"
                self.btn_sound.draw(screen)
                self.btn_back.draw(screen)

            elif self.state == "PLAYING":
                # حركة الفقاعة (Collision Logic)
                f = self.shooter.flying
                if f:
                    f.move()
                    collided = False
                    if f.y - f.radius <= self.gm.top_margin: collided = True
                    else:
                        for r in range(ROWS):
                            for c in range(COLS):
                                t = self.gm.grid[r][c]
                                if t and math.hypot(f.x - t.x, f.y - t.y) <= RADIUS * 2 - 4:
                                    collided = True; break
                            if collided: break
                    
                    if collided:
                        # التثبيت (Snapping)
                        r, c = self.gm.get_row_col(f.x, f.y)
                        if self.gm.grid[r][c]: # لو المكان مليان
                            for nr, nc in self.get_neighbors(r, c):
                                if not self.gm.grid[nr][nc]:
                                    r, c = nr, nc; break
                        
                        if r < ROWS:
                            f.x, f.y = self.gm.get_xy(r, c)
                            f.is_moving = False
                            self.gm.grid[r][c] = f
                            
                            if self.process_match(r, c):
                                self.remove_floating()

                            # آلية سقوط السقف لزيادة الصعوبة
                            if self.shooter.shots_fired % 10 == 0:
                                self.gm.top_margin += ROW_HEIGHT
                                self.screen_shake = 5
                                self.add_floating_text(SCREEN_WIDTH//2, 150, "السقف يقترب!", "CEILING DROP!", COLORS["red"])

                        self.shooter.flying = None

                        # فحص الخسارة (Game Over Check)
                        for col in range(COLS):
                            if self.gm.grid[ROWS-2][col]:
                                self.state = "GAME_OVER"
                                sound_mgr.play("lose")
                                break
                                
                        # فحص الفوز (Level Up Check)
                        is_empty = all(self.gm.grid[r][c] is None for r in range(ROWS) for c in range(COLS))
                        if is_empty:
                            game_data["level"] += 1
                            self.state = "LEVEL_UP"
                            sound_mgr.play("win")

                # رسم اللعبة
                self.gm.draw(surface_game)
                self.shooter.draw(surface_game, mouse_pos)
                
                # رسم الأدوات السفلية
                self.btn_use_bomb.text_ar = f"قنبلة({game_data['bombs']})"
                self.btn_use_bomb.text_en = f"B({game_data['bombs']})"
                self.btn_use_bomb.draw(surface_game)
                
                self.btn_use_fire.text_ar = f"نار({game_data['fireballs']})"
                self.btn_use_fire.text_en = f"F({game_data['fireballs']})"
                self.btn_use_fire.draw(surface_game)
                
                self.btn_use_rain.text_ar = f"قوس({game_data['rainbows']})"
                self.btn_use_rain.text_en = f"R({game_data['rainbows']})"
                self.btn_use_rain.draw(surface_game)

                # UI اللعب العلوي (HUD)
                pygame.draw.rect(surface_game, PANEL_COLOR, (0, 0, SCREEN_WIDTH, 60))
                ui_score = render_text(f"سكور: {self.score}", f"SCORE: {self.score}", font_med, TEXT_COLOR)
                ui_lvl = render_text(f"مستوى: {game_data['level']}", f"LVL: {game_data['level']}", font_med, COLORS["yellow"])
                ui_coins = render_text(f"💰 {game_data['coins']}", f"💰 {game_data['coins']}", font_med, GOLD)
                
                surface_game.blit(ui_score, (20, 10))
                surface_game.blit(ui_coins, (SCREEN_WIDTH//2 - ui_coins.get_width()//2, 10))
                surface_game.blit(ui_lvl, (SCREEN_WIDTH - ui_lvl.get_width() - 20, 10))

            elif self.state == "GAME_OVER":
                title = render_text("خسرت يا بطل!", "GAME OVER!", font_large, COLORS["red"])
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 300))
                msg = render_text("اضغط في أي مكان للعودة", "CLICK TO RETURN", font_small, TEXT_COLOR)
                screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, 450))

            elif self.state == "LEVEL_UP":
                title = render_text("مستوى جديد!", "LEVEL UP!", font_large, COLORS["green"])
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 300))
                msg = render_text("عاش! اضغط للاستمرار", "NICE! CLICK TO CONTINUE", font_small, TEXT_COLOR)
                screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, 450))

            # تحديث الجزيئات والنصوص (VFX Update)
            for p in self.particles[:]:
                p.update()
                p.draw(surface_game)
                if p.life <= 0: self.particles.remove(p)
                
            for t in self.texts[:]:
                t.update()
                t.draw(surface_game)
                if t.life <= 0: self.texts.remove(t)

            # دمج الشاشة مع تأثير الاهتزاز
            screen.blit(surface_game, (offset_x, offset_y))

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Engine()
    game.run()
