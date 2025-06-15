import pygame
import sys
import random
import math
import time

pygame.init()

# Font ayarları
pygame.font.init()
font = pygame.font.Font(None, 36)  

# — SABİTLER VE EKRAN AYARI —
WIDTH, HEIGHT   = 1000, 600
RADIUS          = 10
NUM_SOLDIERS    = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Turan Taktiği Simülasyonu")

# — ARKA PLAN —
background = pygame.image.load("IMG_2028.JPG").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# — DAĞ GÖRSELLERİ —
mountain_img = pygame.image.load("mountainS.png").convert_alpha()
mountain_img = pygame.transform.scale(mountain_img, (200, 200))
mountain_positions = [
    (WIDTH//2 - 200, HEIGHT//2),
    (WIDTH//2 + 200, HEIGHT//2),
]

# — ASKER SPRİTLERİ —
green_img = pygame.image.load("soldier_greenn.png").convert_alpha()
green_img = pygame.transform.scale(green_img, (RADIUS*6, RADIUS*6))
red_img = pygame.image.load("soldier_red.png").convert_alpha()
red_img = pygame.transform.scale(red_img, (RADIUS*6, RADIUS*6))

# — YEŞİL BİRLİKLERİ OLUŞTURMA —
green_soldiers = []
line_y = HEIGHT - 100
initial_line_y = line_y

# Dağların konumlarını kullanarak birlikleri yerleştir
left_mountain_x = WIDTH//2 - 200  # Sol dağın x konumu
right_mountain_x = WIDTH//2 + 200  # Sağ dağın x konumu
mountain_y = HEIGHT//2  # Dağların y konumu
battle_y = mountain_y  # Savaş yapılacak y pozisyonu

# Merkez birlik sayısını takip etmek için değişkenler
initial_center_count = int(NUM_SOLDIERS * 0.5)  # Başlangıçtaki merkez birlik sayısı (50 birim)
retreat_threshold = 0.85  # %15 kayıp olunca geri çekilme başlasın
flank_attack_threshold = 0.90  # %10 kayıp olunca kenar birlikler harekete geçsin
is_retreating = False  # Geri çekilme durumu

for i in range(NUM_SOLDIERS):
    if i < NUM_SOLDIERS * 0.25:  # Sol kanat (25 birim)
        role = "left"
        x = random.randint(50, left_mountain_x - 150)
        y = random.randint(mountain_y - 200, mountain_y + 200)  # Dikey alanı artırdık
    elif i > NUM_SOLDIERS * 0.75:  # Sağ kanat (25 birim)
        role = "right"
        x = random.randint(right_mountain_x + 150, WIDTH - 50)
        y = random.randint(mountain_y - 200, mountain_y + 200)  # Dikey alanı artırdık
    else:  # Merkez birlikler (50 birim)
        role = "center"
        center_index = i - int(NUM_SOLDIERS * 0.25)
        num_center_units = int(NUM_SOLDIERS * 0.5)
        units_per_row = num_center_units // 2
        
        row = center_index // units_per_row
        position_in_row = center_index % units_per_row
        
        spacing = (right_mountain_x - left_mountain_x - 100) / (units_per_row - 1)
        x = left_mountain_x + 50 + position_in_row * spacing
        
        if row == 0:
            y = line_y - 20  # Sıralar arası mesafeyi artırdık
        else:
            y = line_y + 20  # Sıralar arası mesafeyi artırdık
    
    green_soldiers.append({
        "x": x,
        "y": y,
        "initial_x": x,     # Başlangıç x pozisyonu
        "initial_y": y,     # Başlangıç y pozisyonu
        "role": role,
        "target_y": battle_y,
        "is_dying": False,
        "death_time": 0,
        "speed": 0.5,
        "is_retreating": False,  # Her asker için ayrı geri çekilme durumu
        "mountain_phase": 0,  # Yeni eklenen mountain_phase
        "random_offset": None,
        "attack_start_time": None
    })

# — KIRMIZI BİRLİKLERİ OLUŞTURMA —
red_soldiers = []
num_red_units = 50  # NUM_SOLDIERS yerine sabit 50 birim
units_per_row = num_red_units // 2

start_x = left_mountain_x + 50
end_x = right_mountain_x - 50
spacing = (end_x - start_x) / (units_per_row - 1)

# Başlangıç ve hedef pozisyonları arasındaki mesafeyi hesapla
battle_y = mountain_y  # Savaş yapılacak y pozisyonu
green_start_y = line_y  # Yeşil birliklerin başlangıç y pozisyonu
red_start_y = -100     # Kırmızı birliklerin başlangıç y pozisyonu

# Her iki ordunun da aynı sürede hedefe ulaşması için hızları hesapla
green_distance = abs(battle_y - green_start_y)
red_distance = abs(battle_y - red_start_y)
total_distance = green_distance + red_distance

# Hızları mesafeye göre orantılı ayarla
green_speed = 1 * (green_distance / total_distance)
red_speed = 1 * (red_distance / total_distance)

for i in range(num_red_units):
    row = i // units_per_row
    position_in_row = i % units_per_row
    
    x = start_x + position_in_row * spacing
    
    if row == 0:
        y = red_start_y
    else:
        y = red_start_y + 30  # İkinci sıra 30 piksel aşağıda
    
    red_soldiers.append({
        "x": x,
        "y": y,
        "target_y": battle_y,
        "is_dying": False,
        "death_time": 0,
        "speed": red_speed
    })

# Yeşil birliklerin hızlarını güncelle
for g in green_soldiers:
    if g["role"] == "center":
        g["speed"] = green_speed

def find_nearest_retreating_center(red_soldier, green_soldiers):
    nearest_distance = float('inf')
    nearest_target = None
    
    for g in green_soldiers:
        if g["role"] == "center" and g["is_retreating"] and not g["is_dying"]:
            dist = math.hypot(red_soldier["x"] - g["x"], red_soldier["y"] - g["y"])
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_target = g
    
    return nearest_target

def find_nearest_flank(red_soldier, green_soldiers):
    """En yakın kanat birliğini bul"""
    nearest_distance = float('inf')
    nearest_target = None
    
    for g in green_soldiers:
        if g["role"] in ["left", "right"] and not g["is_dying"]:
            dist = math.hypot(red_soldier["x"] - g["x"], red_soldier["y"] - g["y"])
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_target = g
    
    return nearest_target

def find_nearest_red_soldier(green_soldier, red_soldiers):
    """En yakın kırmızı askeri bul"""
    nearest_distance = float('inf')
    nearest_target = None
    
    for r in red_soldiers:
        if not r["is_dying"]:
            dist = math.hypot(green_soldier["x"] - r["x"], green_soldier["y"] - r["y"])
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_target = r
    
    return nearest_target

def calculate_mountain_path(soldier, target):
    """Dağın etrafından dolaşarak geçen yolu hesapla"""
    mountain_width = 200
    mountain_height = 200
    
    # Her asker için rastgele sapma değerleri
    if not soldier.get("random_offset"):
        soldier["random_offset"] = {
            "x": random.uniform(-50, 50),
            "y": random.uniform(-40, 40),
            "delay": random.uniform(0, 3.0),
            "zigzag": random.uniform(0.05, 0.15)  # Zigzag hareketi yavaşlatıldı (0.1-0.3'ten 0.05-0.15'e)
        }
        soldier["zigzag_phase"] = 0
        soldier["last_direction_change"] = current_time
    
    # Gecikme süresini kontrol et
    if not soldier.get("attack_start_time"):
        soldier["attack_start_time"] = current_time + soldier["random_offset"]["delay"]
    if current_time < soldier["attack_start_time"]:
        return soldier["x"], soldier["y"]
    
    # Zigzag hareketi için yön değişimi (daha yavaş)
    if current_time - soldier.get("last_direction_change", 0) > 0.8:  # 0.5'ten 0.8'e çıkarıldı
        soldier["zigzag_phase"] = (soldier["zigzag_phase"] + 1) % 4
        soldier["last_direction_change"] = current_time
    
    # Zigzag hareketi için sapma hesapla
    zigzag_offset = 0
    if soldier["mountain_phase"] >= 2:  # Dağın üstüne çıktıktan sonra zigzag başla
        if soldier["zigzag_phase"] == 0:
            zigzag_offset = soldier["random_offset"]["zigzag"] * 30
        elif soldier["zigzag_phase"] == 1:
            zigzag_offset = -soldier["random_offset"]["zigzag"] * 30
        elif soldier["zigzag_phase"] == 2:
            zigzag_offset = soldier["random_offset"]["zigzag"] * 20
        else:
            zigzag_offset = -soldier["random_offset"]["zigzag"] * 20
    
    if soldier["role"] == "left":
        mountain_x = left_mountain_x - mountain_width//2 - 30 + soldier["random_offset"]["x"] + zigzag_offset
        mountain_bottom_y = mountain_y + mountain_height//2 + soldier["random_offset"]["y"]
        mountain_top_y = mountain_y - mountain_height//2 - 30 + soldier["random_offset"]["y"]
    else:
        mountain_x = right_mountain_x + mountain_width//2 + 30 + soldier["random_offset"]["x"] + zigzag_offset
        mountain_bottom_y = mountain_y + mountain_height//2 + soldier["random_offset"]["y"]
        mountain_top_y = mountain_y - mountain_height//2 - 30 + soldier["random_offset"]["y"]
    
    # Askerin hareket aşaması
    if soldier.get("mountain_phase", 0) == 0:
        # İlk aşama: Dağın yanına git (rastgele yükseklikten)
        if abs(soldier["x"] - mountain_x) > 2:
            return mountain_x, soldier["y"] + random.uniform(-10, 10)
        else:
            soldier["mountain_phase"] = 1
            return mountain_x, soldier["y"]
            
    elif soldier.get("mountain_phase") == 1:
        # İkinci aşama: Dağın üst kısmına çık (zigzag hareketiyle)
        if abs(soldier["y"] - mountain_top_y) > 2:
            return mountain_x + zigzag_offset, mountain_top_y
        else:
            soldier["mountain_phase"] = 2
            return mountain_x, mountain_top_y
            
    elif soldier.get("mountain_phase") == 2:
        # Üçüncü aşama: Dağın diğer tarafına geç (daha dağınık)
        target_side_x = (left_mountain_x + right_mountain_x) // 2
        if soldier["role"] == "left":
            target_side_x += 50 + random.uniform(-40, 40) + zigzag_offset
        else:
            target_side_x -= 50 + random.uniform(-40, 40) + zigzag_offset
            
        if abs(soldier["x"] - target_side_x) > 2:
            return target_side_x, mountain_top_y + random.uniform(-20, 20)
        else:
            soldier["mountain_phase"] = 3
            return target_side_x, mountain_top_y
    
    # Son aşama: Hedefe doğru in (zigzag hareketiyle)
    target_x = target["x"] + random.uniform(-20, 20) + zigzag_offset
    target_y = target["y"] + random.uniform(-20, 20)
    return target_x, target_y

# — ANA DÖNGÜ —
clock = pygame.time.Clock()
frame = 0
current_time = time.time()
flank_attack_started = False

def get_battle_status():
    """Savaşın durumunu belirle"""
    if not flank_attack_started:
        return "Savaş Başlangıcı"
    elif is_retreating and flank_attack_started:
        return "Merkez Geri Çekiliyor - Kanat Saldırısı"
    elif flank_attack_started:
        return "Kanat Saldırısı"
    return "Savaş Devam Ediyor"

while True:
    current_time = time.time()
    
    # Arka plan ve dağları çiz
    screen.blit(background, (0, 0))
    for mx, my in mountain_positions:
        w, h = mountain_img.get_size()
        screen.blit(mountain_img, (mx - w//2, my - h//2))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Merkez birlik sayısını kontrol et
    current_center_count = len([g for g in green_soldiers if g["role"] == "center" and not g["is_dying"]])
    center_ratio = current_center_count / initial_center_count

    # Merkez birliklerin geri çekilmesi (%15 kayıp verince)
    if center_ratio <= retreat_threshold and not is_retreating:
        is_retreating = True
        print(f"Merkez birlikler geri çekiliyor! Kalan merkez asker sayısı: {current_center_count}")
        # Merkez birliklerin geri çekilme durumunu güncelle
        for g in green_soldiers:
            if g["role"] == "center":
                g["is_retreating"] = True
                g["speed"] = 1.2  # Geri çekilme hızı azaltıldı (1.8'den 1.2'ye)
        # Kırmızı askerlerin hızını artır
        for r in red_soldiers:
            r["speed"] = 0.6  # Kırmızıların takip hızı artırıldı (0.4'ten 0.6'ya)
            
        # Merkez birlikler geri çekilmeye başladığında kenar birlikleri harekete geçir
        if not flank_attack_started:
            flank_attack_started = True
            print("Kenar birlikler saldırıya geçiyor!")
            # Kenar birliklerin hızını artır
            for g in green_soldiers:
                if g["role"] in ["left", "right"]:
                    g["speed"] = 2.0  # Kenar birlikler çok daha hızlı saldırsın (1.5'ten 2.0'a çıkarıldı)
                    g["mountain_phase"] = 0
                elif g["role"] == "center":
                    g["speed"] = 0.5  # Geri çekilme hızı yavaşlatıldı (1.0'dan 0.5'e düşürüldü)

    # Birliklerin hareketi
    for g in green_soldiers:
        if g["role"] == "center" and not g["is_dying"]:
            if g["is_retreating"]:
                # Başlangıç pozisyonuna geri dön
                dx = g["initial_x"] - g["x"]
                dy = g["initial_y"] - g["y"]
                dist = math.hypot(dx, dy)
                if dist > 2:
                    g["x"] += dx/dist * g["speed"]
                    g["y"] += dy/dist * g["speed"]
            else:
                # Normal ilerleme
                if g["y"] > g["target_y"]:
                    g["y"] -= g["speed"]
        elif (g["role"] in ["left", "right"]) and not g["is_dying"]:
            if flank_attack_started:
                target = find_nearest_red_soldier(g, red_soldiers)
                if target:
                    target_x, target_y = calculate_mountain_path(g, target)
                    dx = target_x - g["x"]
                    dy = target_y - g["y"]
                    dist = math.hypot(dx, dy)
                    if dist > 2:
                        # Aşamaya göre hız ayarla ve rastgele hız değişimi ekle
                        if g["mountain_phase"] < 3:
                            speed_multiplier = 0.8 + random.uniform(-0.2, 0.2)  # 1.5'ten 0.8'e düşürüldü
                        else:
                            speed_multiplier = 1.2 + random.uniform(-0.2, 0.2)  # 2.0'dan 1.2'ye düşürüldü
                        g["x"] += dx/dist * g["speed"] * speed_multiplier
                        g["y"] += dy/dist * g["speed"] * speed_multiplier

    # Kırmızı birliklerin hareketi
    for r in red_soldiers:
        if not r["is_dying"]:
            if is_retreating:
                # En yakın kanat birliğini kontrol et
                nearest_flank = find_nearest_flank(r, green_soldiers)
                if nearest_flank and math.hypot(r["x"] - nearest_flank["x"], r["y"] - nearest_flank["y"]) < 100:
                    # Kanat birliğine yakınsa onunla savaş
                    dx = nearest_flank["x"] - r["x"]
                    dy = nearest_flank["y"] - r["y"]
                    dist = math.hypot(dx, dy)
                    if dist > 2:
                        r["x"] += dx/dist * r["speed"]
                        r["y"] += dy/dist * r["speed"]
                else:
                    # En yakın geri çekilen merkez birliği bul ve takip et
                    target = find_nearest_retreating_center(r, green_soldiers)
                    if target:
                        dx = target["x"] - r["x"]
                        dy = target["y"] - r["y"]
                        dist = math.hypot(dx, dy)
                        if dist > 2:
                            r["x"] += dx/dist * r["speed"]
                            r["y"] += dy/dist * r["speed"]
            else:
                # Normal hareket
                if r["y"] < r["target_y"]:
                    r["y"] += r["speed"]

    # Çarpışma kontrolü
    for g in green_soldiers:
        if g["is_dying"]:
            continue
        for r in red_soldiers:
            if r["is_dying"]:
                continue
            
            distance = math.hypot(g["x"] - r["x"], g["y"] - r["y"])
            if distance < 20:  # Çarpışma mesafesi
                if g["role"] == "center":
                    # Merkez birliklerle çarpışma
                    if random.random() < 0.55:  # Kırmızıların kazanma şansı %55'e düşürüldü (önceki %75)
                        g["is_dying"] = True
                        g["death_time"] = current_time
                    else:  # Merkez ordunun kazanma şansı %45'e yükseltildi (önceki %25)
                        r["is_dying"] = True
                        r["death_time"] = current_time
                elif g["role"] in ["left", "right"] and flank_attack_started:
                    # Kanat birliklerle çarpışma
                    if random.random() < 0.45:  # Kırmızıların kazanma şansı %45'e düşürüldü (önceki %60)
                        g["is_dying"] = True
                        g["death_time"] = current_time
                    if random.random() < 0.55:  # Kanat birliklerin kazanma şansı %55'e yükseltildi (önceki %40)
                        r["is_dying"] = True
                        r["death_time"] = current_time

    # 3 saniye geçmiş ölü birimleri kaldır
    green_soldiers = [g for g in green_soldiers if not g["is_dying"] or current_time - g["death_time"] < 3]
    red_soldiers = [r for r in red_soldiers if not r["is_dying"] or current_time - r["death_time"] < 3]

    # Askerleri çiz
    for g in green_soldiers:
        if not g["is_dying"]:
            screen.blit(green_img, (int(g["x"])-RADIUS*3, int(g["y"])-RADIUS*3))
    for r in red_soldiers:
        if not r["is_dying"]:
            screen.blit(red_img, (int(r["x"])-RADIUS*3, int(r["y"])-RADIUS*3))

    # Asker sayılarını hesapla
    active_green = len([g for g in green_soldiers if not g["is_dying"]])
    active_red = len([r for r in red_soldiers if not r["is_dying"]])
    
    # Savaş durumunu al
    battle_status = get_battle_status()
    
    # Metinleri oluştur
    status_text = font.render(f"Durum: {battle_status}", True, (255, 255, 255))
    green_text = font.render(f"Yeşil Ordu: {active_green}", True, (0, 255, 0))
    red_text = font.render(f"Kırmızı Ordu: {active_red}", True, (255, 0, 0))
    
    # Metinleri ekrana çiz
    screen.blit(status_text, (10, 10))
    screen.blit(green_text, (10, 50))
    screen.blit(red_text, (10, 90))

    pygame.display.flip()
    clock.tick(60)
    frame += 1