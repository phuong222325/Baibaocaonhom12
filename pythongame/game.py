import pygame
import random
import sys
import math
import os

# Khởi tạo pygame
pygame.init()

# Lấy đường dẫn thư mục chứa script này
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Các hằng số
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 700
FPS = 70

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Hỗ trợ: vẽ chữ có viền để dễ nhìn, nổi bật hơn
def draw_text_with_outline(screen, font, text, pos, color, outline_color=(0, 0, 0), outline_width=2, center=False):
    """Vẽ chữ kèm viền (outline) bằng cách vẽ nhiều lớp chồng nhau.
    pos: tọa độ (x, y). Nếu center=True thì pos là tâm; ngược lại là góc trên trái.
    """
    try:
        # Render main surface
        text_surf = font.render(str(text), True, color)
        # Create outline by rendering text in outline_color at offsets
        ox, oy = pos
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue
                outline_surf = font.render(str(text), True, outline_color)
                rect = outline_surf.get_rect()
                if center:
                    rect.center = (ox + dx, oy + dy)
                else:
                    rect.topleft = (ox + dx, oy + dy)
                screen.blit(outline_surf, rect)
        # Blit main text
        rect = text_surf.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        screen.blit(text_surf, rect)
    except Exception:
        # Trường hợp lỗi: vẽ chữ bình thường, không có viền
        try:
            surf = font.render(str(text), True, color)
            rect = surf.get_rect()
            if center:
                rect.center = pos
            else:
                rect.topleft = pos
            screen.blit(surf, rect)
        except Exception:
            pass
GREEN = (34, 139, 34)
RED = (255, 0, 0)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
SKY_COLOR = (135, 206, 235)
BUTTON_COLOR = (255, 140, 0)
BUTTON_HOVER = (255, 165, 0)
BUTTON_TEXT = (255, 255, 255)
BUTTON_BORDER = (139, 69, 19)


def remove_image_background(surface, tol=60):
    """Xóa background bằng flood-fill từ các góc"""
    try:
        surf = surface.convert_alpha()
    except Exception:
        surf = surface.copy()
    w, h = surf.get_size()
    if w == 0 or h == 0:
        return surf

    def get_rgb(px, py):
        c = surf.get_at((px, py))
        return (c.r, c.g, c.b)

    # Lấy màu trung bình của 4 góc (và kiểm tra alpha)
    # Nếu các góc đã trong suốt thì bỏ qua việc xóa nền
    def get_rgba(px, py):
        c = surf.get_at((px, py))
        return (c.r, c.g, c.b, c.a)

    corners = [
        get_rgba(0, 0),
        get_rgba(max(0, w-1), 0),
        get_rgba(0, max(0, h-1)),
        get_rgba(max(0, w-1), max(0, h-1))
    ]

    # Nếu các góc đã trong suốt, không cần xóa nền
    avg_corner_alpha = sum(c[3] for c in corners) / 4.0
    if avg_corner_alpha < 250:
        return surf

    bg = (
        sum(c[0] for c in corners) // len(corners),
        sum(c[1] for c in corners) // len(corners),
        sum(c[2] for c in corners) // len(corners)
    )

    tol_sq = tol * tol
    # Chỉ coi pixel là nền nếu màu RGB giống và pixel gần như hoàn toàn đục
    # Điều này bảo vệ các pixel viền mịn và các chi tiết trong suốt
    def similar_color(col, alpha):
        if alpha < 250:
            return False
        dr = col[0] - bg[0]
        dg = col[1] - bg[1]
        db = col[2] - bg[2]
        return (dr*dr + dg*dg + db*db) <= tol_sq

    from collections import deque
    visited = [[False]*h for _ in range(w)]
    q = deque()

    starts = [(0,0), (w-1,0), (0,h-1), (w-1,h-1)]
    for sx, sy in starts:
        if 0 <= sx < w and 0 <= sy < h:
            c = surf.get_at((sx, sy))
            if similar_color((c.r, c.g, c.b), c.a):
                visited[sx][sy] = True
                q.append((sx, sy))

    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                c = surf.get_at((nx, ny))
                if similar_color((c.r, c.g, c.b), c.a):
                    visited[nx][ny] = True
                    q.append((nx, ny))

    # Làm trong suốt các pixel đã đánh dấu
    # Không chạm vào các pixel đã trong suốt một phần để giữ nguyên viền mịn
    for x in range(w):
        for y in range(h):
            if visited[x][y]:
                col = surf.get_at((x, y))
                surf.set_at((x, y), (col.r, col.g, col.b, 0))

    return surf


class Button:
    """Lớp Button để tạo các nút bấm tương tác trong game (hover/click)."""
    def __init__(self, x, y, width, height, text, font_size=24, icon=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.icon = icon  # Icon hiển thị trên button (nếu có)
        # Tìm và load font hệ thống hỗ trợ tiếng Việt
        font_candidates = ["Segoe UI", "Arial", "Tahoma", "Calibri", "DejaVu Sans"]
        font_path = None
        for fname in font_candidates:
            try:
                path = pygame.font.match_font(fname)
                if path:
                    font_path = path
                    break
            except:
                pass
        try:
            if font_path:
                self.font = pygame.font.Font(font_path, font_size)
            else:
                self.font = pygame.font.Font(None, font_size)
        except:
            self.font = pygame.font.Font(pygame.font.get_default_font(), font_size)
        self.rect = pygame.Rect(x, y, width, height)
        self.hovered = False  # Trạng thái chuột đang ở trên nút
        self.clicked = False  # Trạng thái nút đang được nhấn
        self.color = None  # Màu tùy chỉnh (nếu có)
        # Khởi tạo cache (lưu trữ) các hình ảnh đã xử lý sẵn
        if self.icon:
            self.init_cached_surfaces()

    def init_cached_surfaces(self):
        """Chuẩn bị sẵn các surface (bóng, hiệu ứng click, icon) để vẽ nhanh."""
        if not hasattr(self, '_cached_surfaces'):
            self._cached_surfaces = {}
        
        # Luôn cập nhật icon cache khi icon thay đổi
        if self.icon and not self.text:
            icon_h = min(self.height - 8, self.icon.get_height())
            icon_w = int(self.icon.get_width() * (icon_h / self.icon.get_height()))
            self._cached_surfaces['icon'] = pygame.transform.smoothscale(self.icon, (icon_w, icon_h))
        
        # Cache các surface phụ (chỉ tạo 1 lần)
        if 'shadow' not in self._cached_surfaces:
            shadow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 30))
            self._cached_surfaces['shadow'] = shadow
        
        if 'click' not in self._cached_surfaces:
            click_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            click_overlay.fill((0, 0, 0, 80))
            self._cached_surfaces['click'] = click_overlay
            
    def draw(self, screen):
        # Đảm bảo surfaces được cache
        if not hasattr(self, '_cached_surfaces'):
            self.init_cached_surfaces()
            
        # Nếu có icon và không có text, vẽ icon đơn giản (không có background button)
        if self.icon and not self.text:
            # Kiểm tra xem icon có trong cache không
            if 'icon' in self._cached_surfaces:
                icon_s = self._cached_surfaces['icon']
            else:
                # Tạo icon mới nếu chưa có trong cache
                icon_h = min(self.height - 8, self.icon.get_height())
                icon_w = int(self.icon.get_width() * (icon_h / self.icon.get_height()))
                icon_s = pygame.transform.smoothscale(self.icon, (icon_w, icon_h))
            
            icon_rect = icon_s.get_rect(center=self.rect.center)
            if self.clicked:
                icon_rect.move_ip(0, 2)
            screen.blit(icon_s, icon_rect)
        else:
            # Vẽ button với background
            # Sử dụng self.color nếu có, ngược lại dùng màu mặc định
            if hasattr(self, 'color') and self.color:
                base_color = self.color
            else:
                base_color = BUTTON_COLOR
            
            color = base_color if not self.hovered else tuple(min(255, c + 20) for c in base_color)
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, BUTTON_BORDER, self.rect, 3)
            
            # Vẽ shadow nếu hover
            if self.hovered and 'shadow' in self._cached_surfaces:
                screen.blit(self._cached_surfaces['shadow'], (self.x + 2, self.y + 2))
            
            # Vẽ overlay nếu clicked
            if self.clicked and 'click' in self._cached_surfaces:
                screen.blit(self._cached_surfaces['click'], (self.x, self.y))
            
            # Nếu có icon, vẽ icon ở giữa; ngược lại vẽ text
            if self.icon:
                icon_h = min(self.height - 8, self.icon.get_height())
                icon_w = int(self.icon.get_width() * (icon_h / self.icon.get_height()))
                icon_s = pygame.transform.smoothscale(self.icon, (icon_w, icon_h))
                icon_rect = icon_s.get_rect(center=self.rect.center)
                # Nếu đang clicked, dịch icon nhẹ xuống
                if self.clicked:
                    icon_rect.move_ip(0, 2)
                screen.blit(icon_s, icon_rect)
            else:
                # Vẽ text ở giữa button với anti-aliasing (vẽ sau overlay để luôn rõ)
                text_surface = self.font.render(self.text, True, BUTTON_TEXT)
                text_rect = text_surface.get_rect(center=self.rect.center)
                # Nếu đang clicked, đẩy text nhẹ xuống để tạo cảm giác nhấn
                if self.clicked:
                    text_rect.move_ip(0, 2)
                screen.blit(text_surface, text_rect)
            
            # Hiệu ứng click (giữ thuộc tính clicked để logic khác vẫn dùng được)
            if self.clicked:
                pygame.draw.rect(screen, (0, 0, 0, 20), self.rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.clicked = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.clicked = False
        return False
    

class Bird:
    """Lớp Bird - đại diện cho con chim; xử lý nhảy, rơi, xoay, skin."""
    # Lưu trữ chung các hình ảnh chim đã load để tái sử dụng
    _image_cache = {}
    _rotated_cache = {}
    
    def __init__(self, x, y, skin_source=1, size=20):
        self.x = x  # Vị trí ngang
        self.y = y  # Vị trí dọc
        self.velocity = 0  # Vận tốc rơi
        self.gravity = 0.55  # Trọng lực (tốc độ tăng vận tốc)
        self.jump_strength = -8.25  # Lực nhảy (âm = hướng lên)
        self.size = size  # Kích thước chim
        self.rotation = 0  # Góc xoay chim (độ)
        self.animation_timer = 0  # Bộ đếm cho animation
        # skin_source: số (1,2,3...) hoặc đường dẫn file ảnh
        self.skin_source = skin_source
        self.bird_image = None  # Ảnh chim hiện tại
        self.base_image = None  # Ảnh gốc (chưa xoay)
        self.load_skin(skin_source)
        # Lưu trữ các ảnh đã xoay của chim này
        self._instance_rotated_cache = {}
    
    def load_skin(self, skin_source):
        """Load ảnh chim: skin_source có thể là đường dẫn file hoặc số (index)."""
        self.skin_source = skin_source
        
        # Tạo khóa cache
        cache_key = (str(skin_source), self.size)
        
        # Kiểm tra xem đã có trong cache chưa
        if cache_key in Bird._image_cache:
            self.bird_image = Bird._image_cache[cache_key]
            self.base_image = self.bird_image.copy()
            return
        
        try:
            path = None
            # Nếu là chuỗi thì coi như đường dẫn trực tiếp
            if isinstance(skin_source, str):
                if os.path.exists(skin_source):
                    path = skin_source
                else:
                    # thử tìm trong thư mục skin nếu người dùng chỉ truyền tên file
                    candidate = os.path.join(SCRIPT_DIR, "skin", skin_source)
                    if os.path.exists(candidate):
                        path = candidate
            elif isinstance(skin_source, int):
                # Thử tìm file trong folder skin: 1.png, 2.png...
                skins_dir = os.path.join(SCRIPT_DIR, "skin")
                candidate = os.path.join(skins_dir, f"{skin_source}.png")
                if os.path.exists(candidate):
                    path = candidate
                else:
                    # fallback: tìm file ảnh bất kỳ trong script dir
                    for f in sorted(os.listdir(SCRIPT_DIR)):
                        if f.lower().endswith((".png", ".jpg", ".webp")):
                            path = os.path.join(SCRIPT_DIR, f)
                            break
            
            # Nếu không tìm được path, thử mặc định
            if path is None:
                # Nếu chưa tìm được, thử lấy file ảnh bất kỳ trong script dir
                for f in sorted(os.listdir(SCRIPT_DIR)):
                    if f.lower().endswith((".png", ".jpg", ".webp")):
                        path = os.path.join(SCRIPT_DIR, f)
                        break

            if path:
                # Load và optimize image
                img = pygame.image.load(path).convert_alpha()
                # Xóa nền 
                try:
                    img = self.remove_background(img)
                except Exception:
                    pass
                # Resize với smoothscale
                target = max(8, int(self.size * 2))
                scaled_image = pygame.transform.smoothscale(img, (target, target))
                # Convert để tối ưu blitting
                self.bird_image = scaled_image.convert_alpha()
                # Copy cho base image
                self.base_image = self.bird_image.copy()
                # Cache lại image đã xử lý
                Bird._image_cache[cache_key] = self.bird_image
            else:
                self.bird_image = None
                self.base_image = None
                
        except Exception:
            self.bird_image = None
            self.base_image = None
    
    def remove_background(self, image):
        # Xóa nền ảnh chim bằng hàm chung để đảm bảo đồng nhất
        try:
            return remove_image_background(image, tol=60)
        except Exception:
            try:
                return image.convert_alpha()
            except Exception:
                return image
        
    def jump(self, game_instance=None):
        self.velocity = self.jump_strength
        self.rotation = -20
        # Phát âm thanh vỗ cánh nếu có game instance
        if game_instance and hasattr(game_instance, 'play_flap_sound'):
            game_instance.play_flap_sound()
        
    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity
        if self.velocity > 0:
            self.rotation = min(90, self.rotation + 3)
        else:
            self.rotation = max(-20, self.rotation - 2)
        self.animation_timer += 1
        
    def draw(self, screen):
        # Dùng base_image (đã remove background) nếu có
        if self.base_image is not None:
            # Lấy ảnh đã xoay từ cache
            cache_key = self.rotation % 360  # Chuẩn hóa góc (0-359)
            if cache_key in self._instance_rotated_cache:
                rotated_image = self._instance_rotated_cache[cache_key]
            else:
                # Tạo mới nếu chưa có trong cache
                rotated_image = pygame.transform.rotate(self.base_image, self.rotation)
                # Cache lại cho lần sau
                self._instance_rotated_cache[cache_key] = rotated_image
                
                # Giới hạn số lượng cache để tránh tràn bộ nhớ
                if len(self._instance_rotated_cache) > 360:  # Tối đa 360 góc
                    # Xóa cache entries cũ nhất
                    oldest_keys = sorted(self._instance_rotated_cache.keys())[:-360]  
                    for k in oldest_keys:
                        del self._instance_rotated_cache[k]
            
            rect = rotated_image.get_rect(center=(self.x, self.y))
            screen.blit(rotated_image, rect)
            
        elif self.bird_image is not None:
            # Dự phòng: nếu không có ảnh gốc
            rotated_image = pygame.transform.rotate(self.bird_image, self.rotation)
            rect = rotated_image.get_rect(center=(self.x, self.y))
            screen.blit(rotated_image, rect)
        else:
            # Vẽ mặc định nếu không có ảnh
            pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), int(self.size))
            pygame.draw.circle(screen, BLACK, (int(self.x + 5), int(self.y - 3)), 3)
            pygame.draw.circle(screen, WHITE, (int(self.x + 6), int(self.y - 4)), 1)
            pygame.draw.polygon(screen, (255, 165, 0), [
                (self.x + self.size, self.y),
                (self.x + self.size + 8, self.y - 2),
                (self.x + self.size + 8, self.y + 2)
            ])
        
    def get_rect(self):
        collision_size = self.size * 0.8
        return pygame.Rect(self.x - collision_size, self.y - collision_size, 
                          collision_size * 2, collision_size * 2)

class MapSelector:
    """Lớp quản lý việc chọn và lưu map nền"""
    def __init__(self):
        # Tìm tất cả file ảnh map trong thư mục "map"
        self.maps = []  # Danh sách đường dẫn các map
        self.map_cache = {}  # Lưu trữ ảnh map đã load để tái sử dụng
        maps_dir = os.path.join(SCRIPT_DIR, "map")
        if os.path.isdir(maps_dir):
            for fname in sorted(os.listdir(maps_dir)):
                if fname.lower().endswith((".png", ".jpg", ".webp")):
                    self.maps.append(os.path.join(maps_dir, fname))
        
        # Nếu không có file nào, tạo map mặc định
        if not self.maps:
            self.maps = ["default"]
        
        self.total_maps = len(self.maps) if self.maps else 1
        # Tạo tên hiển thị từ filename
        self.map_names = []
        for p in self.maps:
            if p == "default":
                self.map_names.append("Mặc định")
            else:
                name = os.path.splitext(os.path.basename(p))[0].replace("_", " ").title()
                self.map_names.append(name)
        
        # Giá xu cho mỗi map (map đầu tiên miễn phí)
        self.map_prices = []
        for i in range(self.total_maps):
            if i == 0:
                self.map_prices.append(0)  # Map đầu tiên miễn phí
            else:
                self.map_prices.append(i * 50)  # Map 2: 50 xu, Map 3: 100 xu, ...
        
        # Load danh sách map đã mở khóa
        self.unlocked_maps = self.load_unlocked_maps()
        
        # current_map và selected_map là chỉ số 0-based
        self.current_map = 0
        self.selected_map = self.load_selected_map()
        if self.selected_map >= self.total_maps:
            self.selected_map = 0
    
    def load_selected_map(self):
        """Load map đã chọn"""
        try:
            filepath = os.path.join(SCRIPT_DIR, "selected_map.txt")
            with open(filepath, "r") as f:
                map_id = int(f.read())
                if 0 <= map_id < self.total_maps:
                    return map_id
        except:
            pass
        return 0
    
    def save_selected_map(self, map_id):
        """Lưu map đã chọn"""
        try:
            filepath = os.path.join(SCRIPT_DIR, "selected_map.txt")
            with open(filepath, "w") as f:
                f.write(str(map_id))
            self.selected_map = map_id
        except:
            pass
    
    def next_map(self):
        if self.total_maps > 0:
            self.current_map = (self.current_map + 1) % self.total_maps
    
    def prev_map(self):
        if self.total_maps > 0:
            self.current_map = (self.current_map - 1) % self.total_maps
    
    def select_current_map(self):
        if self.total_maps > 0:
            self.save_selected_map(self.current_map)
    
    def get_selected_map_path(self):
        if self.total_maps > 0 and self.selected_map < len(self.maps):
            return self.maps[self.selected_map]
        return None
    
    def get_current_map_path(self):
        if self.total_maps > 0 and self.current_map < len(self.maps):
            return self.maps[self.current_map]
        return None
    
    def preload_map_image(self, map_path):
        """Pre-load ảnh map để tối ưu hiệu suất"""
        if map_path and map_path != "default" and map_path not in self.map_cache:
            try:
                # Load và scale ảnh
                original_image = pygame.image.load(map_path)
                scaled_image = pygame.transform.smoothscale(original_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                # Convert để tối ưu render
                scaled_image = scaled_image.convert()
                # Lưu vào cache
                self.map_cache[map_path] = scaled_image
                print(f"Đã pre-load map: {os.path.basename(map_path)}")
            except Exception as e:
                print(f"Lỗi pre-load map {map_path}: {e}")
    
    def get_cached_map_image(self, map_path):
        """Lấy ảnh map từ cache"""
        if map_path in self.map_cache:
            return self.map_cache[map_path]
        return None
    
    def load_unlocked_maps(self):
        """Load danh sách map đã mở khóa từ file"""
        try:
            filepath = os.path.join(SCRIPT_DIR, "unlocked_maps.txt")
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content = f.read().strip()
                    if content:
                        unlocked = [int(x) for x in content.split(",")]
                        return unlocked
        except Exception as e:
            print(f"Lỗi load unlocked maps: {e}")
        # Mặc định: map đầu tiên luôn mở khóa
        return [0]
    
    def save_unlocked_maps(self):
        """Lưu danh sách map đã mở khóa vào file"""
        try:
            filepath = os.path.join(SCRIPT_DIR, "unlocked_maps.txt")
            with open(filepath, "w") as f:
                f.write(",".join(str(x) for x in self.unlocked_maps))
        except Exception as e:
            print(f"Lỗi save unlocked maps: {e}")
    
    def is_map_unlocked(self, map_index):
        """Kiểm tra map có được mở khóa chưa"""
        return map_index in self.unlocked_maps
    
    def unlock_map(self, map_index):
        """Mở khóa map"""
        if map_index not in self.unlocked_maps:
            self.unlocked_maps.append(map_index)
            self.save_unlocked_maps()
            return True
        return False
    
    def get_map_price(self, map_index):
        """Lấy giá của map"""
        if 0 <= map_index < len(self.map_prices):
            return self.map_prices[map_index]
        return 0

class SkinSelector:
    """Lớp quản lý việc chọn và lưu skin (hình dạng) chim"""
    def __init__(self):
        # Khởi tạo dữ liệu
        self.skins = []  # Danh sách đường dẫn các skin
        self.total_skins = 0  # Tổng số skin có sẵn
        self.skin_names = ["Mặc định"]  # Tên hiển thị của các skin
        # Chỉ số skin: 1 = skin đầu tiên, 2 = skin thứ 2, ...
        self.current_skin = 1  # Skin đang xem trong menu chọn
        self.selected_skin = 1  # Skin đã chọn để chơi
        # Lưu trữ ảnh xem trước của skin đã load
        self.preview_cache = {}
        # Quét thư mục skin để tìm các file ảnh
        self.rescan()
        
    def get_preview(self, skin_path, size):
        """Lấy preview skin từ cache"""
        cache_key = (skin_path, size)
        if cache_key not in self.preview_cache:
            try:
                if skin_path and os.path.exists(skin_path):
                    # Load và optimize image
                    image = pygame.image.load(skin_path).convert_alpha()
                    # Xóa nền để preview sạch sẽ (dùng flood-fill từ góc)
                    try:
                        image = remove_image_background(image)
                    except Exception:
                        pass
                    preview = pygame.transform.smoothscale(image, (size, size))
                else:
                    # Fallback: tạo hình tròn đỏ
                    preview = pygame.Surface((size, size), pygame.SRCALPHA)
                    pygame.draw.circle(preview, RED, (size//2, size//2), size//2)
                    preview = preview.convert_alpha()
                self.preview_cache[cache_key] = preview
            except Exception:
                # Fallback nếu load lỗi
                preview = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(preview, RED, (size//2, size//2), size//2)
                preview = preview.convert_alpha()
                self.preview_cache[cache_key] = preview
        return self.preview_cache[cache_key]

    def rescan(self):
        """Quét lại thư mục skin"""
        self.skins = []
        skins_dir = os.path.join(SCRIPT_DIR, "skin")
        if os.path.isdir(skins_dir):
            for fname in sorted(os.listdir(skins_dir)):
                if fname.lower().endswith((".png", ".jpg", ".webp")):
                    self.skins.append(os.path.join(skins_dir, fname))

        # Nếu không có file nào trong skin/, fallback: tìm file ảnh trong script dir
        if not self.skins:
            for f in sorted(os.listdir(SCRIPT_DIR)):
                if f.lower().endswith((".png", ".jpg", ".webp")):
                    self.skins.append(os.path.join(SCRIPT_DIR, f))

        # Tính toán lại các thuộc tính
        self.total_skins = len(self.skins)
        if self.skins:
            self.skin_names = [os.path.splitext(os.path.basename(p))[0].replace("_", " ").title() for p in self.skins]
        else:
            self.skin_names = ["Mặc định"]

        # Load selected từ file (nếu có)
        self.selected_skin = self.load_selected_skin()
        if self.selected_skin > max(1, self.total_skins):
            self.selected_skin = 1

        # Đặt current_skin về selected nếu có skin, else 1
        if self.total_skins > 0:
            if not (1 <= self.current_skin <= self.total_skins):
                self.current_skin = self.selected_skin if 1 <= self.selected_skin <= self.total_skins else 1
        else:
            self.current_skin = 1
    
    def load_selected_skin(self):
        """Load skin đã chọn"""
        try:
            filepath = os.path.join(SCRIPT_DIR, "selected_skin.txt")
            with open(filepath, "r") as f:
                skin_id = int(f.read())
                if 1 <= skin_id <= max(1, self.total_skins):
                    return skin_id
        except:
            pass
        return 1
    
    def save_selected_skin(self, skin_id):
        """Lưu skin đã chọn"""
        try:
            filepath = os.path.join(SCRIPT_DIR, "selected_skin.txt")
            with open(filepath, "w") as f:
                f.write(str(skin_id))
            self.selected_skin = skin_id
        except:
            pass
    
    def next_skin(self):
        if self.total_skins > 0:
            self.current_skin = (self.current_skin % self.total_skins) + 1
    
    def prev_skin(self):
        if self.total_skins > 0:
            self.current_skin = self.current_skin - 1 if self.current_skin > 1 else self.total_skins
    
    def select_current_skin(self):
        if self.total_skins > 0:
            self.save_selected_skin(self.current_skin)
    
    def get_selected_skin_path(self):
        if self.total_skins > 0:
            return self.skins[self.selected_skin - 1]
        return None
    
    def get_current_skin_path(self):
        if self.total_skins > 0:
            return self.skins[self.current_skin - 1]
        return None

class Pipe:
    """Lớp Pipe - đại diện cho các cột chướng ngại vật"""
    def __init__(self, x, speed=2.5, map_type="default"):
        self.x = x  # Vị trí ngang của cột
        self.gap = 170  # Khoảng trống giữa cột trên và dưới (chỗ chim bay qua)
        self.top_height = random.randint(100, SCREEN_HEIGHT - 250)  # Chiều cao cột trên
        self.bottom_y = self.top_height + self.gap  # Vị trí bắt đầu cột dưới
        self.width = 52  # Độ rộng cột
        self.speed = speed  # Tốc độ di chuyển sang trái
        self.passed = False  # Đã bay qua cột chưa (để tính điểm)
        self.map_type = map_type  # Loại map để vẽ cột phù hợp với map

    def update(self):
        self.x -= self.speed
        
    def draw(self, screen):
        # Vẽ ống trên giống cây cột
        self.draw_pillar(screen, self.x, 0, self.width, self.top_height, True)
        
        # Vẽ ống dưới giống cây cột - kéo dài xuống tận đáy màn hình
        self.draw_pillar(screen, self.x, self.bottom_y, self.width, 
                        SCREEN_HEIGHT - self.bottom_y, False)
    
    def draw_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột phù hợp với loại map"""
        map_str = str(self.map_type).lower()
        
        # Map 1 - Thành phố (cột kim loại hiện đại)
        if "(1)" in map_str:
            self.draw_metal_pillar(screen, x, y, width, height, is_top)
        # Map 2 - Cây leo xanh (cột cây với lá)
        elif "(2)" in map_str:
            self.draw_vine_pillar(screen, x, y, width, height, is_top)
        # Map 3 - Đền cổ (cột đá cổ điển)
        elif "(3)" in map_str:
            self.draw_stone_pillar(screen, x, y, width, height, is_top)
        # Map 4 - Vườn hoa (cột hoa anh đào)
        elif "(4)" in map_str:
            self.draw_sakura_pillar(screen, x, y, width, height, is_top)
        # Map 5 - Mùa đông (cột băng)
        elif "(5)" in map_str:
            self.draw_ice_pillar(screen, x, y, width, height, is_top)
        # Map 6 - Cột bình tưới (giống map 2)
        elif "(6)" in map_str:
            self.draw_watering_can_pillar(screen, x, y, width, height, is_top)
        # Map 7 - Rừng tre (cột tre)
        elif "(7)" in map_str:
            self.draw_bamboo_pillar(screen, x, y, width, height, is_top)
        # Map 8 - Cột gạch
        elif "(8)" in map_str:
            self.draw_brick_pillar(screen, x, y, width, height, is_top)
        else:
            # Vẽ cột mặc định - ống khói gạch
            self.draw_brick_pillar(screen, x, y, width, height, is_top)
    
    def draw_brick_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ ống khói bằng gạch màu cam (map mặc định)"""
        # Màu sắc cho ống khói gạch
        brick_color = (255, 140, 0)      # Orange brick background
        dark_brick = (185, 80, 0)        # Dark orange cho gạch (đậm hơn)
        mortar_color = (100, 50, 0)      # Dark brown mortar (đậm hơn)
        highlight = (255, 200, 100)      # Light orange highlight (sáng hơn)
        shadow_color = (100, 60, 0)      # Dark shadow (đậm hơn)
        
        # Vẽ thân ống khói chính
        pygame.draw.rect(screen, brick_color, (x, y, width, height))
        
        # Vẽ viền gạch
        pygame.draw.rect(screen, dark_brick, (x - 2, y, 2, height))  # Viền trái
        pygame.draw.rect(screen, dark_brick, (x + width, y, 2, height))  # Viền phải
        pygame.draw.rect(screen, dark_brick, (x - 2, y - 2, width + 4, 2))  # Viền trên
        pygame.draw.rect(screen, dark_brick, (x - 2, y + height, width + 4, 2))  # Viền dưới
        
        # Vẽ pattern gạch hoàn hảo - không thừa không thiếu
        brick_height = 10  # Chiều cao mỗi viên gạch
        brick_width = 14   # Chiều rộng mỗi viên gạch  
        mortar_width = 1   # Độ dày vữa
        
        # Vẽ từng hàng gạch
        current_y = y
        row_count = 0
        
        while current_y < y + height:
            # Tính offset cho hàng (staggered pattern)
            row_offset = 0 if row_count % 2 == 0 else brick_width // 2
            
            # Vẽ gạch trong hàng này
            current_x = x + row_offset
            
            while current_x < x + width:
                # Tính kích thước gạch thực tế
                brick_w = min(brick_width, x + width - current_x)
                brick_h = min(brick_height, y + height - current_y)
                
                # Chỉ vẽ nếu đủ lớn
                if brick_w >= 4 and brick_h >= 4:
                    # Vẽ viên gạch với màu đậm hơn
                    pygame.draw.rect(screen, dark_brick, 
                                   (current_x, current_y, brick_w, brick_h))
                    
                    # Vẽ viền gạch để nổi bật
                    pygame.draw.rect(screen, shadow_color, 
                                   (current_x, current_y, brick_w, brick_h), 1)
                    
                    # Vẽ highlight cho gạch
                    if brick_w > 3:
                        pygame.draw.line(screen, highlight, 
                                       (current_x + 1, current_y + 1), 
                                       (current_x + 1, current_y + brick_h - 2), 1)
                        pygame.draw.line(screen, highlight, 
                                       (current_x + 1, current_y + 1), 
                                       (current_x + brick_w - 2, current_y + 1), 1)
                
                current_x += brick_width
            
            # Vẽ đường mortar ngang
            if current_y + brick_height < y + height:
                pygame.draw.line(screen, mortar_color, 
                               (x, current_y + brick_height), 
                               (x + width, current_y + brick_height), mortar_width)
            
            current_y += brick_height
            row_count += 1
        
        # Vẽ đầu ống khói đối xứng - bo tròn hoàn hảo
        cap_height = 25
        cap_width = width + 6
        cap_x = x - 3
        
        if is_top:
            # Đầu ống khói trên - bo tròn dưới (giống dưới)
            cap_y = self.top_height - cap_height
            
            # Vẽ đầu ống khói
            pygame.draw.rect(screen, dark_brick, 
                           (cap_x, cap_y, cap_width, cap_height))
            
            # Vẽ góc bo tròn ở dưới (giống đầu dưới)
            pygame.draw.circle(screen, dark_brick, 
                             (cap_x + 4, cap_y + cap_height - 4), 4)
            pygame.draw.circle(screen, dark_brick, 
                             (cap_x + cap_width - 4, cap_y + cap_height - 4), 4)
            
            # Viền đầu ống khói
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x - 1, cap_y - 1, cap_width + 2, 1))  # Viền trên
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x - 1, cap_y, 1, cap_height))  # Viền trái
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x + cap_width, cap_y, 1, cap_height))  # Viền phải
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x - 1, cap_y + cap_height, cap_width + 2, 1))  # Viền dưới
            
            # Highlight cho đầu ống khói
            pygame.draw.line(screen, highlight, 
                           (cap_x + 1, cap_y + 1), 
                           (cap_x + cap_width - 1, cap_y + 1), 1)  # Highlight trên
            pygame.draw.line(screen, highlight, 
                           (cap_x + 1, cap_y + 1), 
                           (cap_x + 1, cap_y + cap_height - 1), 1)  # Highlight trái
        else:
            # Đầu ống khói dưới - bo tròn trên (giống trên)
            cap_y = self.bottom_y
            
            # Vẽ đầu ống khói
            pygame.draw.rect(screen, dark_brick, 
                           (cap_x, cap_y, cap_width, cap_height))
            
            # Vẽ góc bo tròn ở trên (giống đầu trên)
            pygame.draw.circle(screen, dark_brick, 
                             (cap_x + 4, cap_y + 4), 4)
            pygame.draw.circle(screen, dark_brick, 
                             (cap_x + cap_width - 4, cap_y + 4), 4)
            
            # Viền đầu ống khói
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x - 1, cap_y - 1, cap_width + 2, 1))  # Viền trên
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x - 1, cap_y, 1, cap_height))  # Viền trái
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x + cap_width, cap_y, 1, cap_height))  # Viền phải
            pygame.draw.rect(screen, shadow_color, 
                           (cap_x - 1, cap_y + cap_height, cap_width + 2, 1))  # Viền dưới
            
            # Highlight cho đầu ống khói
            pygame.draw.line(screen, highlight, 
                           (cap_x + 1, cap_y + cap_height - 1), 
                           (cap_x + cap_width - 1, cap_y + cap_height - 1), 1)  # Highlight dưới
            pygame.draw.line(screen, highlight, 
                           (cap_x + 1, cap_y + 1), 
                           (cap_x + 1, cap_y + cap_height - 1), 1)  # Highlight trái
        
        # Vẽ bóng đổ cho ống khói (chỉ khi có kích thước hợp lệ)
        if width > 0 and height > 0:
            shadow_surface = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 50))
            screen.blit(shadow_surface, (x - 1, y + 3))
    
    def draw_wooden_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột gỗ tự nhiên cho map tp.jpg"""
        # Màu sắc cho cột gỗ - tối hơn để nổi bật trên background tp.jpg
        wood_color = (101, 67, 33)       # Dark brown - màu gỗ chính tối hơn
        dark_wood = (69, 45, 23)         # Darker brown cho vân gỗ
        light_wood = (139, 90, 45)       # Medium brown - màu gỗ sáng
        bark_color = (60, 35, 15)        # Very dark brown cho vỏ cây
        highlight = (160, 100, 50)        # Light brown - highlight gỗ
        
        # Vẽ thân cột gỗ chính
        pygame.draw.rect(screen, wood_color, (x, y, width, height))
        
        # Vẽ viền vỏ cây
        pygame.draw.rect(screen, bark_color, (x - 2, y, 2, height))  # Viền trái
        pygame.draw.rect(screen, bark_color, (x + width, y, 2, height))  # Viền phải
        pygame.draw.rect(screen, bark_color, (x - 2, y - 2, width + 4, 2))  # Viền trên
        pygame.draw.rect(screen, bark_color, (x - 2, y + height, width + 4, 2))  # Viền dưới
        
        # Vẽ vân gỗ dọc - tạo texture gỗ tự nhiên
        for i in range(0, width, 4):
            if i < width - 2:
                # Vân gỗ dọc với độ dày khác nhau
                line_width = 1 if i % 8 == 0 else 1
                pygame.draw.line(screen, dark_wood, 
                               (x + i, y + 3), 
                               (x + i, y + height - 3), line_width)
        
        # Vẽ vân gỗ ngang (tạo texture gỗ)
        for i in range(8, height - 8, 12):
            if i < height - 15:
                # Vân gỗ ngang với độ dày khác nhau
                line_width = 1 if i % 24 == 0 else 1
                pygame.draw.line(screen, light_wood, 
                               (x + 3, y + i), 
                               (x + width - 3, y + i), line_width)
        
        # Vẽ các nút gỗ (knots) ở vị trí cố định
        if width > 15 and height > 30:
            pygame.draw.circle(screen, dark_wood, (x + 10, y + 30), 2)
            pygame.draw.circle(screen, dark_wood, (x + width - 15, y + height - 40), 2)
        
        # Vẽ highlight cho cột gỗ
        pygame.draw.line(screen, highlight, 
                       (x + 1, y + 1), 
                       (x + 1, y + height - 1), 1)  # Highlight trái
        pygame.draw.line(screen, highlight, 
                       (x + 1, y + 1), 
                       (x + width - 1, y + 1), 1)  # Highlight trên
        
        # Vẽ đầu cột gỗ - thiết kế phù hợp với background tp.jpg
        cap_height = 25
        cap_width = width + 6
        cap_x = x - 3
        
        if is_top:
            # Đầu cột trên - thiết kế như cột đền thờ
            cap_y = y - cap_height
            # Vẽ đầu cột chính
            pygame.draw.rect(screen, dark_wood, (cap_x, cap_y, cap_width, cap_height))
            # Vẽ viền đầu cột
            pygame.draw.rect(screen, bark_color, (cap_x - 1, cap_y - 1, cap_width + 2, cap_height + 2), 2)
            # Bo tròn góc dưới
            pygame.draw.circle(screen, dark_wood, 
                             (cap_x + 4, cap_y + cap_height - 4), 4)
            pygame.draw.circle(screen, dark_wood, 
                             (cap_x + cap_width - 4, cap_y + cap_height - 4), 4)
            # Vẽ pattern trang trí trên đầu cột
            for i in range(0, cap_width - 4, 8):
                pygame.draw.line(screen, light_wood, 
                               (cap_x + 2 + i, cap_y + 5), 
                               (cap_x + 2 + i, cap_y + 8), 1)
        else:
            # Đầu cột dưới - thiết kế như chân cột
            cap_y = y + height
            # Vẽ chân cột chính
            pygame.draw.rect(screen, dark_wood, (cap_x, cap_y, cap_width, cap_height))
            # Vẽ viền chân cột
            pygame.draw.rect(screen, bark_color, (cap_x - 1, cap_y - 1, cap_width + 2, cap_height + 2), 2)
            # Bo tròn góc trên
            pygame.draw.circle(screen, dark_wood, 
                             (cap_x + 4, cap_y + 4), 4)
            pygame.draw.circle(screen, dark_wood, 
                             (cap_x + cap_width - 4, cap_y + 4), 4)
            # Vẽ pattern trang trí trên chân cột
            for i in range(0, cap_width - 4, 8):
                pygame.draw.line(screen, light_wood, 
                               (cap_x + 2 + i, cap_y + cap_height - 8), 
                               (cap_x + 2 + i, cap_y + cap_height - 5), 1)
        
        # Vẽ bóng đổ cho cột gỗ
        if width > 0 and height > 0:
            shadow_surface = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 40))
            screen.blit(shadow_surface, (x - 1, y + 2))
    
    def draw_stone_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột đá cổ điển cho map 3.jpg"""
        # Màu sắc cho cột đá cổ điển
        stone_color = (169, 169, 169)     # Dark gray - màu đá chính
        dark_stone = (105, 105, 105)      # Dim gray cho vân đá
        light_stone = (211, 211, 211)     # Light gray - highlight đá
        moss_color = (34, 139, 34)        # Forest green cho rêu
        shadow_color = (64, 64, 64)       # Dark shadow
        
        # Vẽ thân cột đá chính
        pygame.draw.rect(screen, stone_color, (x, y, width, height))
        
        # Vẽ viền đá
        pygame.draw.rect(screen, dark_stone, (x - 2, y, 2, height))  # Viền trái
        pygame.draw.rect(screen, dark_stone, (x + width, y, 2, height))  # Viền phải
        pygame.draw.rect(screen, dark_stone, (x - 2, y - 2, width + 4, 2))  # Viền trên
        pygame.draw.rect(screen, dark_stone, (x - 2, y + height, width + 4, 2))  # Viền dưới
        
        # Vẽ vân đá dọc
        for i in range(0, width, 6):
            if i < width - 3:
                pygame.draw.line(screen, dark_stone, 
                               (x + i, y + 5), 
                               (x + i, y + height - 5), 1)
        
        # Vẽ vân đá ngang
        for i in range(10, height - 10, 15):
            if i < height - 20:
                pygame.draw.line(screen, light_stone, 
                               (x + 3, y + i), 
                               (x + width - 3, y + i), 1)
        
        # Vẽ highlight cho cột đá
        pygame.draw.line(screen, light_stone, 
                       (x + 1, y + 1), 
                       (x + 1, y + height - 1), 1)  # Highlight trái
        pygame.draw.line(screen, light_stone, 
                       (x + 1, y + 1), 
                       (x + width - 1, y + 1), 1)  # Highlight trên
        
        # Vẽ đầu cột đá - thiết kế cổ điển
        cap_height = 30
        cap_width = width + 8
        cap_x = x - 4
        
        if is_top:
            # Đầu cột trên - thiết kế cổ điển
            cap_y = y - cap_height
            # Vẽ đầu cột chính
            pygame.draw.rect(screen, dark_stone, (cap_x, cap_y, cap_width, cap_height))
            # Vẽ viền đầu cột
            pygame.draw.rect(screen, shadow_color, (cap_x - 1, cap_y - 1, cap_width + 2, cap_height + 2), 2)
            # Bo tròn góc dưới
            pygame.draw.circle(screen, dark_stone, 
                             (cap_x + 6, cap_y + cap_height - 6), 6)
            pygame.draw.circle(screen, dark_stone, 
                             (cap_x + cap_width - 6, cap_y + cap_height - 6), 6)
        else:
            # Đầu cột dưới - thiết kế chân cột
            cap_y = y + height
            # Vẽ chân cột chính
            pygame.draw.rect(screen, dark_stone, (cap_x, cap_y, cap_width, cap_height))
            # Vẽ viền chân cột
            pygame.draw.rect(screen, shadow_color, (cap_x - 1, cap_y - 1, cap_width + 2, cap_height + 2), 2)
            # Bo tròn góc trên
            pygame.draw.circle(screen, dark_stone, 
                             (cap_x + 6, cap_y + 6), 6)
            pygame.draw.circle(screen, dark_stone, 
                             (cap_x + cap_width - 6, cap_y + 6), 6)
        
        # Vẽ bóng đổ cho cột đá
        if width > 0 and height > 0:
            shadow_surface = pygame.Surface((width + 6, height + 6), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 60))
            screen.blit(shadow_surface, (x - 2, y + 3))
    
    def draw_metal_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột kim loại hiện đại cho map 2.jpg"""
        # Màu sắc cho cột kim loại hiện đại
        metal_color = (192, 192, 192)     # Silver - màu kim loại chính
        dark_metal = (128, 128, 128)      # Gray cho viền kim loại
        light_metal = (224, 224, 224)     # Light gray - highlight kim loại
        rust_color = (139, 69, 19)         # Saddle brown cho gỉ sét
        shadow_color = (64, 64, 64)       # Dark shadow
        
        # Vẽ thân cột kim loại chính
        pygame.draw.rect(screen, metal_color, (x, y, width, height))
        
        # Vẽ viền kim loại
        pygame.draw.rect(screen, dark_metal, (x - 2, y, 2, height))  # Viền trái
        pygame.draw.rect(screen, dark_metal, (x + width, y, 2, height))  # Viền phải
        pygame.draw.rect(screen, dark_metal, (x - 2, y - 2, width + 4, 2))  # Viền trên
        pygame.draw.rect(screen, dark_metal, (x - 2, y + height, width + 4, 2))  # Viền dưới
        
        # Vẽ vân kim loại dọc
        for i in range(0, width, 3):
            if i < width - 2:
                pygame.draw.line(screen, light_metal, 
                               (x + i, y + 2), 
                               (x + i, y + height - 2), 1)
        
        # Vẽ vân kim loại ngang
        for i in range(5, height - 5, 8):
            if i < height - 10:
                pygame.draw.line(screen, dark_metal, 
                               (x + 2, y + i), 
                               (x + width - 2, y + i), 1)
        
        # Vẽ highlight cho cột kim loại
        pygame.draw.line(screen, light_metal, 
                       (x + 1, y + 1), 
                       (x + 1, y + height - 1), 1)  # Highlight trái
        pygame.draw.line(screen, light_metal, 
                       (x + 1, y + 1), 
                       (x + width - 1, y + 1), 1)  # Highlight trên
        
        # Vẽ đầu cột kim loại - thiết kế hiện đại
        cap_height = 20
        cap_width = width + 4
        cap_x = x - 2
        
        if is_top:
            # Đầu cột trên - thiết kế hiện đại
            cap_y = y - cap_height
            # Vẽ đầu cột chính
            pygame.draw.rect(screen, dark_metal, (cap_x, cap_y, cap_width, cap_height))
            # Vẽ viền đầu cột
            pygame.draw.rect(screen, shadow_color, (cap_x - 1, cap_y - 1, cap_width + 2, cap_height + 2), 2)
            # Bo tròn góc dưới
            pygame.draw.circle(screen, dark_metal, 
                             (cap_x + 3, cap_y + cap_height - 3), 3)
            pygame.draw.circle(screen, dark_metal, 
                             (cap_x + cap_width - 3, cap_y + cap_height - 3), 3)
        else:
            # Đầu cột dưới - thiết kế chân cột
            cap_y = y + height
            # Vẽ chân cột chính
            pygame.draw.rect(screen, dark_metal, (cap_x, cap_y, cap_width, cap_height))
            # Vẽ viền chân cột
            pygame.draw.rect(screen, shadow_color, (cap_x - 1, cap_y - 1, cap_width + 2, cap_height + 2), 2)
            # Bo tròn góc trên
            pygame.draw.circle(screen, dark_metal, 
                             (cap_x + 3, cap_y + 3), 3)
            pygame.draw.circle(screen, dark_metal, 
                             (cap_x + cap_width - 3, cap_y + 3), 3)
        
        # Vẽ bóng đổ cho cột kim loại
        if width > 0 and height > 0:
            shadow_surface = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 50))
            screen.blit(shadow_surface, (x - 1, y + 2))
    
    def draw_vine_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột cây leo với lá xanh cho map 2"""
        # Màu sắc tone xanh lá
        vine_green = (60, 140, 60)        # Xanh lá đậm (thân cây)
        dark_green = (40, 100, 40)        # Xanh đậm (bóng)
        leaf_green = (80, 180, 80)        # Xanh lá sáng (lá)
        light_green = (120, 200, 120)     # Xanh nhạt (highlight lá)
        branch_brown = (90, 70, 50)       # Nâu cành
        
        # Vẽ thân cây leo chính
        pygame.draw.rect(screen, vine_green, (x, y, width, height))
        pygame.draw.rect(screen, dark_green, (x - 2, y, 2, height))
        pygame.draw.rect(screen, dark_green, (x + width, y, 2, height))
        
        # Vẽ vân gỗ dọc cho cột
        for i in range(0, width, 6):
            if i < width - 2:
                pygame.draw.line(screen, dark_green, (x + i, y + 3), (x + i, y + height - 3), 1)
        
        # Vẽ lá cây rải rác trên cột
        for i in range(10, height - 10, 30):
            if width > 10:
                # Lá bên trái
                leaf_x = x + 5
                leaf_y = y + i
                # Vẽ lá hình oval
                pygame.draw.ellipse(screen, leaf_green, (leaf_x - 4, leaf_y - 3, 8, 6))
                pygame.draw.ellipse(screen, light_green, (leaf_x - 3, leaf_y - 2, 6, 4))
                # Gân lá
                pygame.draw.line(screen, dark_green, (leaf_x - 3, leaf_y), (leaf_x + 3, leaf_y), 1)
                
                # Lá bên phải
                if width > 15:
                    leaf_x2 = x + width - 5
                    leaf_y2 = y + i + 15
                    pygame.draw.ellipse(screen, leaf_green, (leaf_x2 - 4, leaf_y2 - 3, 8, 6))
                    pygame.draw.ellipse(screen, light_green, (leaf_x2 - 3, leaf_y2 - 2, 6, 4))
                    pygame.draw.line(screen, dark_green, (leaf_x2 - 3, leaf_y2), (leaf_x2 + 3, leaf_y2), 1)
        
        # Đầu cột với nhiều lá
        cap_height = 28
        cap_x = x - 3
        if is_top:
            cap_y = y - cap_height
            pygame.draw.rect(screen, dark_green, (cap_x, cap_y, width + 6, cap_height))
            # Vẽ nhiều lá ở đầu cột
            for i in range(4, width + 2, 10):
                pygame.draw.ellipse(screen, leaf_green, (cap_x + i - 3, cap_y + 8, 8, 6))
                pygame.draw.ellipse(screen, light_green, (cap_x + i - 2, cap_y + 9, 6, 4))
        else:
            cap_y = y + height
            pygame.draw.rect(screen, dark_green, (cap_x, cap_y, width + 6, cap_height))
            # Vẽ lá ở đầu dưới
            for i in range(4, width + 2, 10):
                pygame.draw.ellipse(screen, leaf_green, (cap_x + i - 3, cap_y + 10, 8, 6))
    
    def draw_sakura_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột hoa anh đào đơn giản cho map (4)"""
        # Màu sắc cho cột hoa anh đào
        wood_brown = (139, 90, 60)        # Nâu gỗ
        dark_brown = (100, 60, 40)        # Nâu đậm
        pink = (255, 182, 193)            # Hồng nhạt
        dark_pink = (255, 105, 180)       # Hồng đậm
        yellow_center = (255, 220, 100)   # Vàng nhụy
        
        # Vẽ thân cây
        pygame.draw.rect(screen, wood_brown, (x, y, width, height))
        pygame.draw.rect(screen, dark_brown, (x - 2, y, 2, height))
        pygame.draw.rect(screen, dark_brown, (x + width, y, 2, height))
        
        # Vẽ vân gỗ
        for i in range(0, width, 5):
            if i < width - 2:
                pygame.draw.line(screen, dark_brown, (x + i, y + 3), (x + i, y + height - 3), 1)
        
        # Vẽ vài hoa nhỏ đơn giản rải rác
        for i in range(30, height - 30, 60):
            if width > 10:
                flower_x = x + width // 2
                flower_y = y + i
                # Vẽ 5 cánh hoa to hơn
                for petal in range(5):
                    angle = (petal * 72) * 3.14159 / 180
                    px = int(flower_x + 5 * math.cos(angle))
                    py = int(flower_y + 5 * math.sin(angle))
                    pygame.draw.circle(screen, pink, (px, py), 4)
                # Nhụy hoa to hơn
                pygame.draw.circle(screen, yellow_center, (flower_x, flower_y), 3)
                pygame.draw.circle(screen, dark_pink, (flower_x, flower_y), 2)
        
        # Đầu cột đơn giản
        cap_height = 25
        cap_x = x - 3
        if is_top:
            cap_y = y - cap_height
            pygame.draw.rect(screen, dark_brown, (cap_x, cap_y, width + 6, cap_height))
            # Vài hoa to hơn ở đầu cột
            for i in range(8, width - 2, 15):
                pygame.draw.circle(screen, pink, (cap_x + i, cap_y + 10), 3)
                pygame.draw.circle(screen, yellow_center, (cap_x + i, cap_y + 10), 1)
        else:
            cap_y = y + height
            pygame.draw.rect(screen, dark_brown, (cap_x, cap_y, width + 6, cap_height))
    
    def draw_watering_can_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột bình tưới hoa cho map vườn hoa (map 4)"""
        # Màu sắc
        can_color = (100, 180, 100)       # Xanh lá
        dark_can = (70, 140, 70)          # Xanh đậm
        light_can = (140, 210, 140)       # Xanh sáng
        metal_rim = (180, 180, 180)       # Viền kim loại
        water_blue = (100, 180, 220)      # Xanh nước
        flower_colors = [(255, 100, 150), (255, 200, 100), (150, 100, 255), (100, 255, 150)]
        
        # Vẽ thân bình tưới
        pygame.draw.rect(screen, can_color, (x, y, width, height))
        pygame.draw.rect(screen, metal_rim, (x - 2, y, 2, height))
        pygame.draw.rect(screen, metal_rim, (x + width, y, 2, height))
        
        # Vẽ vân kim loại
        for i in range(0, width, 6):
            if i < width - 2:
                pygame.draw.line(screen, light_can, (x + i, y + 3), (x + i, y + height - 3), 1)
        
        # Vẽ giọt nước
        for i in range(15, height - 15, 40):
            if width > 10:
                water_x = x + width // 2
                water_y = y + i
                pygame.draw.circle(screen, water_blue, (water_x, water_y), 2)
                pygame.draw.circle(screen, water_blue, (water_x, water_y + 3), 1)
        
        # Vẽ hoa nhỏ
        for i in range(20, height - 20, 50):
            if width > 15:
                flower_x = x + 8
                flower_y = y + i
                flower_color = flower_colors[i % len(flower_colors)]
                pygame.draw.line(screen, (50, 150, 50), (flower_x, flower_y + 4), (flower_x, flower_y - 2), 1)
                pygame.draw.circle(screen, flower_color, (flower_x, flower_y), 2)
                pygame.draw.circle(screen, (255, 255, 0), (flower_x, flower_y), 1)
        
        # Đầu cột (vòi tưới)
        cap_x = x - 2
        if is_top:
            cap_y = y - 22
            pygame.draw.rect(screen, dark_can, (cap_x, cap_y, width + 4, 22))
            for i in range(5, width, 8):
                pygame.draw.circle(screen, water_blue, (cap_x + i, cap_y + 19), 1)
                pygame.draw.line(screen, water_blue, (cap_x + i, cap_y + 21), (cap_x + i, cap_y + 23), 1)
        else:
            cap_y = y + height
            pygame.draw.rect(screen, dark_can, (cap_x, cap_y, width + 4, 22))
    
    def draw_ice_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột băng cho map mùa đông (map 5, 6)"""
        # Màu sắc
        ice_color = (200, 230, 255)       # Xanh băng
        dark_ice = (150, 200, 240)        # Xanh đậm
        light_ice = (230, 245, 255)       # Xanh sáng
        crystal_color = (180, 220, 255)   # Tinh thể
        
        # Vẽ thân băng
        pygame.draw.rect(screen, ice_color, (x, y, width, height))
        pygame.draw.rect(screen, dark_ice, (x - 2, y, 2, height))
        pygame.draw.rect(screen, dark_ice, (x + width, y, 2, height))
        
        # Vẽ vân băng
        for i in range(0, width, 4):
            if i < width - 2:
                pygame.draw.line(screen, light_ice, (x + i, y + 2), (x + i, y + height - 2), 1)
        
        # Vẽ tinh thể băng ở vị trí cố định
        for i in range(0, height - 10, 20):
            if width > 10:
                cx = x + width // 2
                cy = y + i
                pygame.draw.polygon(screen, crystal_color, [
                    (cx, cy - 3), (cx + 2, cy), (cx, cy + 3), (cx - 2, cy)
                ])
        
        # Highlight
        pygame.draw.line(screen, light_ice, (x + 2, y + 2), (x + 2, y + height - 2), 2)
        
        # Đầu cột (nhũ băng)
        cap_x = x - 3
        if is_top:
            cap_y = y - 25
            pygame.draw.rect(screen, dark_ice, (cap_x, cap_y, width + 6, 25))
            for i in range(0, width + 6, 8):
                pygame.draw.polygon(screen, light_ice, [
                    (cap_x + i, cap_y), (cap_x + i + 3, cap_y), (cap_x + i + 1, cap_y - 4)
                ])
        else:
            cap_y = y + height
            pygame.draw.rect(screen, dark_ice, (cap_x, cap_y, width + 6, 25))
            for i in range(0, width + 6, 8):
                pygame.draw.polygon(screen, light_ice, [
                    (cap_x + i, cap_y + 25), (cap_x + i + 3, cap_y + 25), (cap_x + i + 1, cap_y + 29)
                ])
    
    def draw_bamboo_pillar(self, screen, x, y, width, height, is_top):
        """Vẽ cột tre cho map rừng tre (map 7, 8)"""
        # Màu sắc
        bamboo_color = (144, 185, 99)     # Xanh tre
        dark_bamboo = (100, 140, 70)      # Xanh đậm
        light_bamboo = (180, 210, 130)    # Xanh sáng
        node_color = (80, 120, 60)        # Đốt tre
        
        # Vẽ thân tre
        pygame.draw.rect(screen, bamboo_color, (x, y, width, height))
        pygame.draw.rect(screen, dark_bamboo, (x - 2, y, 2, height))
        pygame.draw.rect(screen, dark_bamboo, (x + width, y, 2, height))
        
        # Vẽ các đốt tre
        segment_height = 40
        for i in range(0, height, segment_height):
            if i < height:
                pygame.draw.line(screen, node_color, (x, y + i), (x + width, y + i), 3)
                pygame.draw.line(screen, light_bamboo, (x, y + i + 2), (x + width, y + i + 2), 1)
        
        # Vẽ vân tre dọc
        for i in range(0, width, 8):
            if i < width - 2:
                pygame.draw.line(screen, light_bamboo, (x + i, y + 2), (x + i, y + height - 2), 1)
        
        # Highlight
        pygame.draw.line(screen, light_bamboo, (x + 2, y + 2), (x + 2, y + height - 2), 2)
        
        # Đầu tre
        cap_x = x - 2
        if is_top:
            cap_y = y - 20
            pygame.draw.rect(screen, dark_bamboo, (cap_x, cap_y, width + 4, 20))
            pygame.draw.rect(screen, node_color, (cap_x - 1, cap_y - 1, width + 6, 22), 2)
            # Lá tre
            for i in range(0, width + 4, 10):
                pygame.draw.line(screen, light_bamboo, (cap_x + i, cap_y), (cap_x + i - 3, cap_y - 5), 1)
        else:
            cap_y = y + height
            pygame.draw.rect(screen, dark_bamboo, (cap_x, cap_y, width + 4, 20))
            pygame.draw.rect(screen, node_color, (cap_x - 1, cap_y - 1, width + 6, 22), 2)
        
    def get_top_rect(self):
        return pygame.Rect(self.x, 0, self.width, self.top_height)
        
    def get_bottom_rect(self):
        return pygame.Rect(self.x, self.bottom_y, self.width, SCREEN_HEIGHT - self.bottom_y)


class Coin:
    """Lớp Coin - vật phẩm xu mà chim có thể thu thập"""
    def __init__(self, x, y, image=None, speed=2.5, size=28):
        self.x = x
        self.y = y
        self.image = image
        self.speed = speed
        self.size = size
        # Nếu có image, dùng kích thước image, ngược lại tạo surface tạm
        if self.image:
            try:
                self.image = pygame.transform.smoothscale(self.image, (self.size, self.size)).convert_alpha()
            except Exception:
                pass

    def update(self, speed=None):
        # Nếu speed truyền vào thì cập nhật tốc độ (theo tốc độ pipe hiện tại)
        if speed is not None:
            self.speed = speed
        self.x -= self.speed

    def draw(self, screen):
        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.image, rect)
        else:
            # Fallback: vẽ hình tròn vàng
            pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), max(4, self.size//2))

    def get_rect(self):
        hw = max(4, self.size // 2)
        return pygame.Rect(self.x - hw, self.y - hw, hw * 2, hw * 2)

class X2Item:
    """Lớp X2Item - vật phẩm nhân đôi xu trong một thời gian ngắn"""
    def __init__(self, x, y, image=None, speed=2.5, size=48):
        self.x = x
        self.y = y
        self.image = image
        self.speed = speed
        self.size = size
        if self.image:
            try:
                self.image = pygame.transform.smoothscale(self.image, (self.size, self.size)).convert_alpha()
            except Exception:
                pass

    def update(self, speed=None):
        if speed is not None:
            self.speed = speed
        self.x -= self.speed

    def draw(self, screen):
        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.image, rect)
        else:
            # Fallback: draw a magenta X2 circle
            pygame.draw.circle(screen, (200, 50, 200), (int(self.x), int(self.y)), max(6, self.size//2))

    def get_rect(self):
        hw = max(6, self.size // 2)
        return pygame.Rect(self.x - hw, self.y - hw, hw * 2, hw * 2)

class Cloud:
    """Lớp Cloud - đám mây di chuyển trên bầu trời"""
    def __init__(self, x, y):
        self.x = x  # Vị trí ngang
        self.y = y  # Vị trí dọc
        self.speed = random.uniform(0.1, 0.4)  # Tốc độ bay (chậm)
        self.size = random.uniform(0.8, 1.5)  # Kích thước ngẫu nhiên (0.8x - 1.5x)
        
    def update(self):
        """Cập nhật vị trí mây"""
        self.x += self.speed
        # Nếu mây ra khỏi màn hình, đặt lại vị trí bên trái
        if self.x > SCREEN_WIDTH + 100:
            self.x = -100
            self.y = random.randint(50, 200)
            self.speed = random.uniform(0.1, 0.4)  # Giảm tốc độ mây
            self.size = random.uniform(0.8, 1.5)
    
    def draw(self, screen):
        """Vẽ mây với nhiều hình tròn chồng nhau"""
        # Màu mây trắng với alpha
        cloud_color = (255, 255, 255, 180)
        
        # Vẽ đám mây từ nhiều hình tròn chồng nhau
        base_size = int(25 * self.size)
        pygame.draw.circle(screen, cloud_color, (int(self.x), int(self.y)), base_size)
        pygame.draw.circle(screen, cloud_color, (int(self.x + 30 * self.size), int(self.y)), int(30 * self.size))
        pygame.draw.circle(screen, cloud_color, (int(self.x + 60 * self.size), int(self.y)), base_size)
        pygame.draw.circle(screen, cloud_color, (int(self.x + 15 * self.size), int(self.y - 20 * self.size)), int(20 * self.size))
        pygame.draw.circle(screen, cloud_color, (int(self.x + 45 * self.size), int(self.y - 20 * self.size)), int(20 * self.size))

class GameLogo:
    def __init__(self, x, y, size=200):
        self.x = x
        self.y = y
        self.size = size
        self.animation_timer = 0
        self.bounce_height = 0
        self.logo_image = None
        self.load_logo()
        
    def load_logo(self):
        """Load ảnh logo từ thư mục icon"""
        try:
            logo_path = os.path.join(SCRIPT_DIR, "icon", "flappybird_title.png")
            if os.path.exists(logo_path):
                logo_img = pygame.image.load(logo_path).convert_alpha()
                # Scale logo theo kích thước mong muốn
                self.logo_image = pygame.transform.smoothscale(logo_img, (self.size, self.size//2))
            else:
                self.logo_image = None
        except Exception:
            self.logo_image = None
    
    def update(self):
        """Cập nhật animation cho logo"""
        self.animation_timer += 1
        # Hiệu ứng bounce nhẹ
        self.bounce_height = math.sin(self.animation_timer * 0.1) * 3
        
    def draw(self, screen):
        """Vẽ logo Flappy Bird"""
        if self.logo_image:
            # Vẽ logo với hiệu ứng bounce
            logo_rect = self.logo_image.get_rect(center=(self.x, self.y + self.bounce_height))
            screen.blit(self.logo_image, logo_rect)
        else:
            # Fallback: vẽ text nếu không load được ảnh
            font = pygame.font.Font(None, 48)
            text = font.render("FLAPPY BIRD", True, BLACK)
            text_rect = text.get_rect(center=(self.x, self.y + self.bounce_height))
            screen.blit(text, text_rect)

class BackgroundManager:
    def __init__(self, map_selector=None):
        self.backgrounds = []
        self.map_selector = map_selector
        self.custom_map_image = None
        self.load_backgrounds()
        
    def load_backgrounds(self):
        """Load background mặc định"""
        # Tạo background mặc định đơn giản
        self.create_default_backgrounds()
    
    def load_custom_map(self):
        """Load map tùy chỉnh từ map selector với cache tối ưu"""
        if self.map_selector:
            selected_map = self.map_selector.get_selected_map_path()
            if selected_map and selected_map != "default":
                # Kiểm tra cache - chỉ load lại nếu map thay đổi
                if not hasattr(self, 'cached_map_path') or self.cached_map_path != selected_map:
                    # Thử lấy từ cache trước
                    cached_image = self.map_selector.get_cached_map_image(selected_map)
                    if cached_image:
                        self.custom_map_image = cached_image
                        self.cached_map_path = selected_map
                    else:
                        # Nếu chưa có trong cache, load mới
                        try:
                            # Load ảnh gốc
                            original_image = pygame.image.load(selected_map)
                            
                            # Scale với smoothscale để chất lượng tốt hơn
                            self.custom_map_image = pygame.transform.smoothscale(original_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                            
                            # Convert để tối ưu hiệu suất render
                            self.custom_map_image = self.custom_map_image.convert()
                            
                            # Lưu vào cache của map_selector
                            self.map_selector.map_cache[selected_map] = self.custom_map_image
                            
                            # Lưu cache local
                            self.cached_map_path = selected_map
                            
                        except Exception as e:
                            print(f"Lỗi load map: {e}")
                            self.custom_map_image = None
                            self.cached_map_path = None
            else:
                self.custom_map_image = None
                self.cached_map_path = None
    
    def create_default_backgrounds(self):
        """Tạo background mặc định đơn giản"""
        # Tạo 1 background mặc định đơn giản
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(SKY_COLOR)  # Màu xanh trời
        self.backgrounds.append(bg)
    
    def update(self):
        """Cập nhật background manager"""
        pass
    
    def draw(self, screen):
        """Vẽ background hiện tại - tối ưu hóa"""
        # Load custom map nếu có (chỉ load khi cần)
        self.load_custom_map()
        
        # Nếu có custom map, vẽ custom map
        if self.custom_map_image:
            # Blit trực tiếp - đã được convert() nên nhanh hơn
            screen.blit(self.custom_map_image, (0, 0))
            return
            
        # Vẽ background mặc định
        if self.backgrounds:
            current_bg = self.backgrounds[0]  # Chỉ có 1 background mặc định
            screen.blit(current_bg, (0, 0))
    

class Game:
    """Lớp Game - quản lý toàn bộ trò chơi Flappy Bird"""
    def __init__(self):
        # Tạo cửa sổ game
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird")
        self.clock = pygame.time.Clock()  # Đồng hồ để giới hạn FPS
        # Khởi động nhạc nền
        self.init_music("Music/nhac.mp3")

        def load_sys_font(size):
            candidates = ["Segoe UI", "Arial", "Tahoma", "Calibri", "DejaVu Sans"]
            for n in candidates:
                try:
                    path = pygame.font.match_font(n)
                    if path:
                        return pygame.font.Font(path, size)
                except:
                    continue
            try:
                return pygame.font.Font(None, size)
            except:
                return pygame.font.Font(pygame.font.get_default_font(), size)

        self.font = load_sys_font(24)  # Font chữ thường
        self.big_font = load_sys_font(48)  # Font chữ lớn
        self.huge_font = load_sys_font(60)  # Font chữ cực lớn cho high score
        self.button_font = load_sys_font(20)  # Font cho button
        
        # Trạng thái game
        self.state = "MENU"  # MENU, PLAYING, COUNTDOWN, GAME_OVER, SKIN_SELECTION, MAP_SELECTION
        self.score = 0  # Điểm hiện tại
        self.high_score = self.load_high_score()  # Điểm cao nhất
        self.key_pressed = False  # Phím space đang được giữ
        
        # Phát hiện nhấn space 2 lần
        self.last_space_time = 0  # Thời điểm nhấn space lần cuối
        self.double_space_threshold = 500  # 500ms = 0.5 giây
        
        # Đếm ngược trước khi chơi
        self.countdown_timer = 0  # Bộ đếm
        self.countdown_duration = 180  # 180 frames = 3 giây (60 FPS)
        
        # Âm thanh hiệu ứng
        self.die_sound = None  # Âm thanh khi chết
        self.flap_sound = None  # Âm thanh vỗ cánh
        self.load_sound_effects()
        
        # Hình ảnh Game Over
        self.game_over_image = None
        self.load_game_over_image()
        
        # Animation cho skin selection
        self.skin_bounce_offset = 0  # Offset cho hiệu ứng nhúng nhúng
        self.skin_bounce_direction = 1  # Hướng bounce (1 = xuống, -1 = lên)
        self.skin_bounce_speed = 0.5  # Tốc độ bounce
        
        # Các đối tượng chính trong game
        self.skin_selector = SkinSelector()  # Quản lý chọn skin
        self.map_selector = MapSelector()  # Quản lý chọn map
        # Tạo con chim với skin đã chọn
        selected_path = self.skin_selector.get_selected_skin_path()
        if selected_path:
            self.bird = Bird(80, SCREEN_HEIGHT // 2, selected_path)
        else:
            self.bird = Bird(80, SCREEN_HEIGHT // 2, self.skin_selector.selected_skin)
        self.pipes = []  # Danh sách các cột chướng ngại vật
        self.pipe_timer = 0  # Bộ đếm để spawn cột mới
        self.pipe_spawn_rate = 120  # Spawn cột mới mỗi 120 frames
        
        # Mặt đất
        self.ground_y = SCREEN_HEIGHT - 100  # Vị trí mặt đất
        self.ground_scroll = 0  # Vị trí cuộn của mặt đất
        
        # Background (nền)
        self.background_y = 0  # Vị trí cuộn nền
        
        # Logo Flappy Bird
        self.logo = GameLogo(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120, size=300)
        
        # Hệ thống mây
        self.clouds = []  # Danh sách các đám mây
        self.init_clouds()
        
        self.base_pipe_speed = 2.5  # Tốc độ cơ bản của cột
        self.level = 1  # Level hiện tại
        
        # Khởi tạo background manager với map selector
        self.background_manager = BackgroundManager(self.map_selector)
        
        # Pre-load map được chọn để tối ưu hiệu suất
        selected_map = self.map_selector.get_selected_map_path()
        if selected_map:
            self.map_selector.preload_map_image(selected_map)
        # Tạo danh sách coin và load asset xu (coin.png)
        self.coins = []  # Danh sách các coin trên màn hình
        self.coins_collected = 0  # Tổng số xu đã thu thập trong lượt chơi
        try:
            # Try multiple candidate locations for coin.png (root, icon/, effect/)
            candidate_paths = [
                os.path.join(SCRIPT_DIR, "coin.png"),
                os.path.join(SCRIPT_DIR, "icon", "coin.png"),
                os.path.join(SCRIPT_DIR, "effect", "coin.png"),
            ]
            img = None
            for p in candidate_paths:
                if os.path.exists(p):
                    try:
                        img = pygame.image.load(p).convert_alpha()
                        break
                    except Exception:
                        img = None
                        continue
            if img is not None:
                try:
                    img = remove_image_background(img)
                except Exception:
                    pass
                # scale nhỏ lại để vừa hiển thị
                self.coin_image = pygame.transform.smoothscale(img, (28, 28)).convert_alpha()
            else:
                self.coin_image = None
        except Exception:
            self.coin_image = None

        # Load tổng số xu tích lũy (persistent)
        try:
            self.total_coins = self.load_total_coins()
        except Exception:
            self.total_coins = 0

        # Load effect image (ef.png) used when revived (invulnerable)
        try:
            ef_path = os.path.join(SCRIPT_DIR, "icon", "ef.png")
            if os.path.exists(ef_path):
                ef_img = pygame.image.load(ef_path).convert_alpha()
                # keep original, scale on draw if needed
                self.shield_effect_image = ef_img
            else:
                self.shield_effect_image = None
        except Exception:
            self.shield_effect_image = None

        # Load X2 image (power-up for doubling coins temporarily)
        self.x2_items = []
        self.x2_active = False
        self.x2_frames = 0
        self.x2_duration_seconds = 30
        self.spawn_x2_for_next_pipe = False
        try:
            # Try multiple candidate locations for X2.png (root, icon/, effect/)
            candidate_paths = [
                os.path.join(SCRIPT_DIR, "X2.png"),
                os.path.join(SCRIPT_DIR, "icon", "X2.png"),
                os.path.join(SCRIPT_DIR, "effect", "X2.png"),
            ]
            x2_img = None
            for p in candidate_paths:
                if os.path.exists(p):
                    try:
                        x2_img = pygame.image.load(p).convert_alpha()
                        break
                    except Exception:
                        x2_img = None
                        continue
            if x2_img is not None:
                try:
                    x2_img = remove_image_background(x2_img)
                except Exception:
                    pass
                self.x2_image = pygame.transform.smoothscale(x2_img, (48, 48)).convert_alpha()
            else:
                self.x2_image = None
        except Exception:
            self.x2_image = None

        # Invulnerability timer (frames). When >0 player is invulnerable
        self.invulnerable_frames = 0
        # Duration in seconds for revive invulnerability
        self.revive_invul_seconds = 3

        # Thiết lập cơ chế spawn coin theo điểm: spawn 1 coin sau mỗi
        # một khoảng điểm ngẫu nhiên trong [5,7]
        self.next_coin_score = self.score + random.randint(5, 7)
        self.spawn_coin_for_next_pipe = False

        # Tạo các button
        self.create_buttons()

        # Revive trạng thái: chỉ được hồi sinh 1 lần mỗi lượt
        self.revive_used = False
    
    def init_clouds(self):
        """Khởi tạo hệ thống mây"""
        # Tạo 5-8 đám mây với vị trí ngẫu nhiên
        for _ in range(random.randint(5, 8)):
            x = random.randint(-200, SCREEN_WIDTH + 100)
            y = random.randint(50, 250)
            self.clouds.append(Cloud(x, y))
    
    def create_buttons(self):
        """Tạo tất cả các button cho game"""
        button_width = 150
        button_height = 50
        
        # Menu buttons
        self.play_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT // 2 + 20, 
            button_width, button_height, 
            "CHƠI NGAY", 20
        )
        
        self.skin_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT // 2 + 80, 
            button_width, button_height, 
            "CHỌN SKIN", 20
        )
        
        self.map_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT // 2 + 140, 
            button_width, button_height, 
            "CHỌN MAP", 20
        )
        
        # Skin selection buttons - sử dụng icon PNG
        self.prev_skin_button = Button(
            50, SCREEN_HEIGHT // 2 - 25, 
            50, 50, 
            "", 24
        )
        
        self.next_skin_button = Button(
            SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2 - 25, 
            50, 50, 
            "", 24
        )
        
        self.select_skin_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT // 2 + 120, 
            button_width, button_height, 
            "CHỌN SKIN NÀY", 18
        )
        
        # Map selection buttons
        self.prev_map_button = Button(
            50, SCREEN_HEIGHT // 2 - 25, 
            50, 50, 
            "", 24
        )
        
        self.next_map_button = Button(
            SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2 - 25, 
            50, 50, 
            "", 24
        )
        
        self.select_map_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT // 2 + 155, 
            button_width, button_height, 
            "CHỌN MAP NÀY", 18
        )
        
        self.back_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT - 80, 
            button_width, button_height, 
            "QUAY LẠI", 20
        )
        
        # Game over buttons
        self.restart_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT // 2 + 80, 
            button_width, button_height, 
            "CHƠI LẠI", 20
        )
        
        self.menu_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, 
            SCREEN_HEIGHT // 2 + 140, 
            button_width, button_height, 
            "VỀ MENU", 20
        )
        # Revive button (hiển thị khi có đủ xu và chưa hồi sinh)
        self.revive_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            SCREEN_HEIGHT // 2 + 20,
            button_width, button_height,
            "HỒI SINH (10 xu)", 18
        )
        # Revive decline button (for the modal prompt)
        self.revive_decline_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            SCREEN_HEIGHT // 2 + 80,
            button_width, button_height,
            "KHÔNG", 18
        )
        # Nút tắt/bật nhạc (luôn hiển thị góc phải trên) - sử dụng icon
        self.mute_button = Button(SCREEN_WIDTH - 50, 10, 40, 40, "", 16)
        self.load_mute_icons()
        self.load_skin_navigation_icons()
        self.load_map_navigation_icons()
        # Set icon ban đầu cho nút âm thanh
        self.set_initial_mute_icon()
        # Revive prompt state
        self.revive_prompt_active = False
        self.revive_countdown_frames = 0

    def load_mute_icons(self):
        """Load các icon cho nút mute/unmute từ file PNG"""
        try:
            # Load icon loa (khi có nhạc)
            speaker_path = os.path.join(SCRIPT_DIR, "icon", "speaker-filled-audio-tool.png")
            if os.path.exists(speaker_path):
                speaker_img = pygame.image.load(speaker_path).convert_alpha()
                # Resize về kích thước phù hợp
                self.volume_icon = pygame.transform.smoothscale(speaker_img, (32, 32))
            else:
                self.volume_icon = None
                
            # Load icon tắt âm (khi mute)
            mute_path = os.path.join(SCRIPT_DIR, "icon", "no-sound.png")
            if os.path.exists(mute_path):
                mute_img = pygame.image.load(mute_path).convert_alpha()
                # Resize về kích thước phù hợp
                self.mute_icon = pygame.transform.smoothscale(mute_img, (32, 32))
            else:
                self.mute_icon = None
                
        except Exception:
            self.volume_icon = None
            self.mute_icon = None

    def load_skin_navigation_icons(self):
        """Load các icon cho nút điều hướng skin"""
        try:
            # Load icon paths from script directory
            left_path = os.path.join(SCRIPT_DIR, "icon", "left-chevron.png")
            right_path = os.path.join(SCRIPT_DIR, "icon", "right-arrow.png")

            # Load left icon if available
            if os.path.exists(left_path):
                left_img = pygame.image.load(left_path).convert_alpha()
                self.left_icon = pygame.transform.smoothscale(left_img, (32, 32)).convert_alpha()
                if hasattr(self, 'prev_skin_button'):
                    self.prev_skin_button.icon = self.left_icon
                    self.prev_skin_button.init_cached_surfaces()
            else:
                self.left_icon = None

            # Load right icon if available
            if os.path.exists(right_path):
                right_img = pygame.image.load(right_path).convert_alpha()
                self.right_icon = pygame.transform.smoothscale(right_img, (32, 32)).convert_alpha()
                if hasattr(self, 'next_skin_button'):
                    self.next_skin_button.icon = self.right_icon
                    self.next_skin_button.init_cached_surfaces()
            else:
                self.right_icon = None

        except Exception as e:
            print("Error loading skin navigation icons:", e)
            self.left_icon = None
            self.right_icon = None

    def load_map_navigation_icons(self):
        """Load các icon cho nút điều hướng map"""
        try:
            # Load icon mũi tên trái cho map
            left_path = os.path.join(SCRIPT_DIR, "icon", "left-chevron.png")
            if os.path.exists(left_path):
                left_img = pygame.image.load(left_path).convert_alpha()
                # Resize về kích thước phù hợp
                self.left_map_icon = pygame.transform.smoothscale(left_img, (32, 32))
                self.prev_map_button.icon = self.left_map_icon
            else:
                self.left_map_icon = None
                
            # Load icon mũi tên phải cho map
            right_path = os.path.join(SCRIPT_DIR, "icon", "right-arrow.png")
            if os.path.exists(right_path):
                right_img = pygame.image.load(right_path).convert_alpha()
                # Resize về kích thước phù hợp
                self.right_map_icon = pygame.transform.smoothscale(right_img, (32, 32))
                self.next_map_button.icon = self.right_map_icon
            else:
                self.right_map_icon = None
                
        except Exception:
            self.left_map_icon = None
            self.right_map_icon = None

    def load_sound_effects(self):
        """Load các âm thanh hiệu ứng"""
        try:
            # Load âm thanh khi chết
            die_path = os.path.join(SCRIPT_DIR, "Music", "die.mp3")
            if os.path.exists(die_path):
                self.die_sound = pygame.mixer.Sound(die_path)
            else:
                self.die_sound = None
                
            # Load âm thanh vỗ cánh
            flap_path = os.path.join(SCRIPT_DIR, "Music", "flapping wings.mp3")
            if os.path.exists(flap_path):
                self.flap_sound = pygame.mixer.Sound(flap_path)
            else:
                self.flap_sound = None
        except Exception:
            self.die_sound = None
            self.flap_sound = None

    def load_game_over_image(self):
        """Load hình ảnh game over và xóa nền"""
        try:
            game_over_path = os.path.join(SCRIPT_DIR, "icon", "gameover.jpg")
            if os.path.exists(game_over_path):
                game_over_img = pygame.image.load(game_over_path).convert_alpha()
                # Xóa background
                try:
                    game_over_img = remove_image_background(game_over_img, tol=80)
                except Exception:
                    pass
                # Scale hình ảnh
                self.game_over_image = pygame.transform.smoothscale(game_over_img, (300, 100))
            else:
                self.game_over_image = None
        except Exception:
            self.game_over_image = None

    def play_die_sound(self):
        """Phát âm thanh khi chim chết"""
        if self.die_sound and not getattr(self, "muted", False):
            try:
                self.die_sound.play()
            except:
                pass

    def play_flap_sound(self):
        """Phát âm thanh vỗ cánh"""
        if self.flap_sound and not getattr(self, "muted", False):
            try:
                self.flap_sound.play()
            except:
                pass

    def set_initial_mute_icon(self):
        """Set icon ban đầu cho nút âm thanh dựa trên trạng thái muted"""
        if hasattr(self, 'muted') and self.muted:
            # Nếu đã muted, hiển thị icon tắt âm
            if hasattr(self, 'mute_icon') and self.mute_icon:
                self.mute_button.icon = self.mute_icon
                self.mute_button.init_cached_surfaces()
        else:
            # Nếu chưa muted, hiển thị icon loa
            if hasattr(self, 'volume_icon') and self.volume_icon:
                self.mute_button.icon = self.volume_icon
                self.mute_button.init_cached_surfaces()

    def init_music(self, filename=None, volume=0.4):
        """Khởi tạo và phát nhạc nền. Nếu filename không truyền thì tự tìm file .mp3 trong cwd."""
        try:
            # Khởi mixer nếu chưa khởi
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            # Nếu không thể init mixer thì bỏ qua
            # đảm bảo các thuộc tính tồn tại
            self.music_path = None
            self.muted = True
            self.music_volume = volume
            return

        music_path = None
        # Nếu truyền tên file và tồn tại -> dùng nó
        if filename:
            if os.path.isabs(filename):
                if os.path.exists(filename):
                    music_path = filename
            else:
                cand = os.path.join(SCRIPT_DIR, filename)
                if os.path.exists(cand):
                    music_path = cand

        # Nếu không có filename, tìm file .mp3 đầu tiên trong thư mục Music
        if music_path is None:
            music_dir = os.path.join(SCRIPT_DIR, "Music")
            if os.path.isdir(music_dir):
                for f in os.listdir(music_dir):
                    if f.lower().endswith(".mp3"):
                        music_path = os.path.join(music_dir, f)
                        break

        if music_path:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(volume)  # 0.0 - 1.0
                pygame.mixer.music.play(-1)  # lặp vô hạn
                self.music_path = music_path
                self.muted = False
                self.music_volume = volume
                # Set icon ban đầu
                self.set_initial_mute_icon()
            except Exception:
                # Nếu load/ play lỗi thì bỏ qua
                self.music_path = None
                self.muted = True
                self.music_volume = volume
        else:
            self.music_path = None
            self.muted = True
            self.music_volume = volume
            # Set icon mute nếu không có nhạc
            self.set_initial_mute_icon()

    def get_current_speed(self):
        # Tăng tốc độ dựa trên điểm số, tối đa 6.0
        return min(self.base_pipe_speed + self.score * 0.15, 6.0)

    def start_countdown(self):
        """Bắt đầu countdown trước khi chơi game"""
        self.countdown_timer = self.countdown_duration
        # Reset game objects trước
        selected_path = self.skin_selector.get_selected_skin_path()
        if selected_path:
            self.bird = Bird(80, SCREEN_HEIGHT // 2, selected_path)
        else:
            self.bird = Bird(80, SCREEN_HEIGHT // 2, self.skin_selector.selected_skin)
        self.pipes = []
        self.score = 0
        self.pipe_timer = 0
        self.ground_scroll = 0
        self.background_y = 0
        # Khởi tạo level
        self.level = 1
        self.state = "COUNTDOWN"
        # Reset coin scheduling
        try:
            self.coins = []
            self.coins_collected = 0
            self.next_coin_score = self.score + random.randint(5, 7)
            self.spawn_coin_for_next_pipe = False
            # Reset revive
            self.revive_used = False
        except Exception:
            pass
        
    def reset_game(self):
        # Reset tất cả game objects
        selected_path = self.skin_selector.get_selected_skin_path()
        if selected_path:
            self.bird = Bird(80, SCREEN_HEIGHT // 2, selected_path)
        else:
            self.bird = Bird(80, SCREEN_HEIGHT // 2, self.skin_selector.selected_skin)
        self.pipes = []
        self.score = 0
        self.pipe_timer = 0
        self.ground_scroll = 0
        self.background_y = 0
        # Reset level
        self.level = 1
        self.state = "PLAYING"
        # Reset coin scheduling
        try:
            self.coins = []
            self.coins_collected = 0
            self.next_coin_score = self.score + random.randint(5, 7)
            self.spawn_coin_for_next_pipe = False
            # Reset revive
            self.revive_used = False
        except Exception:
            pass
        
    def spawn_pipe(self):
        if self.pipe_timer <= 0:
            current_speed = self.get_current_speed()
            # Lấy map type hiện tại
            selected_map = self.map_selector.get_selected_map_path()
            map_type = "default"
            if selected_map and selected_map != "default":
                map_type = selected_map
            new_pipe = Pipe(SCREEN_WIDTH + 50, speed=current_speed, map_type=map_type)
            self.pipes.append(new_pipe)
            # Nếu có flag yêu cầu spawn coin cho pipe tiếp theo -> spawn coin cùng pipe
            if getattr(self, 'spawn_coin_for_next_pipe', False):
                try:
                    gap_center_y = new_pipe.top_height + new_pipe.gap / 2
                    coin_x = new_pipe.x + new_pipe.width + 24
                    coin = Coin(coin_x, gap_center_y, image=getattr(self, 'coin_image', None), speed=current_speed)
                    self.coins.append(coin)
                except Exception:
                    pass
                # reset flag và đặt ngưỡng tiếp theo
                self.spawn_coin_for_next_pipe = False
                self.next_coin_score = self.score + random.randint(5, 7)

            # Nếu có flag yêu cầu spawn X2 cho pipe tiếp theo -> spawn X2 cùng pipe
            if getattr(self, 'spawn_x2_for_next_pipe', False):
                try:
                    gap_center_y = new_pipe.top_height + new_pipe.gap / 2
                    x2_x = new_pipe.x + new_pipe.width + 24
                    x2 = X2Item(x2_x, gap_center_y, image=getattr(self, 'x2_image', None), speed=current_speed)
                    self.x2_items.append(x2)
                except Exception:
                    pass
                # reset flag
                self.spawn_x2_for_next_pipe = False
            self.pipe_timer = self.pipe_spawn_rate
        else:
            self.pipe_timer -= 1
    
    def update_level(self):
        # Không còn chuyển mùa, chỉ tăng level để tăng độ khó
        pass

    def update(self):
        # Cập nhật background manager
        self.background_manager.update()
        
        # Cập nhật mây (luôn cập nhật)
        for cloud in self.clouds:
            cloud.update()
        
        # Cập nhật logo animation
        if self.state == "MENU":
            self.logo.update()
        
        if self.state == "COUNTDOWN":
            # Giảm countdown timer
            self.countdown_timer -= 1
            if self.countdown_timer <= 0:
                # Kết thúc countdown, bắt đầu game
                self.state = "PLAYING"
                
        # Revive prompt countdown handling (pause game while waiting)
        if self.state == "REVIVE_PROMPT":
            try:
                if getattr(self, 'revive_countdown_frames', 0) > 0:
                    self.revive_countdown_frames -= 1
                    # Nếu hết thời gian -> kết thúc game và không cho hồi sinh nữa
                    if self.revive_countdown_frames <= 0:
                        self.play_die_sound()
                        self.state = "GAME_OVER"
                        # SET revive_used = True vì đã hết thời gian, không cho phép hồi sinh nữa
                        self.revive_used = True
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.save_high_score()
                return
            except Exception:
                # On error, fallback to game over
                self.play_die_sound()
                self.state = "GAME_OVER"
                self.revive_used = True
                return
        if self.state == "PLAYING":
            # Cập nhật chim
            self.bird.update()
            # Cập nhật bộ đếm bất tử nếu có
            try:
                if getattr(self, 'invulnerable_frames', 0) > 0:
                    self.invulnerable_frames -= 1
                # Cập nhật timer X2 nếu đang active
                if getattr(self, 'x2_frames', 0) > 0:
                    self.x2_frames -= 1
                    if self.x2_frames <= 0:
                        try:
                            self.x2_active = False
                        except Exception:
                            self.x2_active = False
            except Exception:
                pass
            
            # Cập nhật ground scroll với tốc độ tăng dần
            self.ground_scroll -= self.get_current_speed()
            
            # Cập nhật background scroll cho mây
            self.background_y += 1
            
            # Kiểm tra va chạm với đáy màn hình và trần
            if self.bird.y + self.bird.size >= SCREEN_HEIGHT or self.bird.y - self.bird.size <= 0:
                # Treat boundary collisions like pipe collisions: show revive prompt
                try:
                    # Ignore if currently invulnerable
                    if getattr(self, 'invulnerable_frames', 0) > 0:
                        pass
                    else:
                        # Start revive prompt
                        self.state = "REVIVE_PROMPT"
                        self.revive_countdown_frames = 15 * FPS
                        return
                except Exception:
                    # Fallback to game over on unexpected errors
                    self.play_die_sound()
                    self.state = "GAME_OVER"
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self.save_high_score()
                    
            # Spawn pipes
            self.spawn_pipe()
            
            # Cập nhật pipes
            for pipe in self.pipes[:]:
                pipe.speed = self.get_current_speed()  # cập nhật speed cho pipe hiện tại
                pipe.update()
                
                # Kiểm tra va chạm
                if (pipe.get_top_rect().colliderect(self.bird.get_rect()) or 
                    pipe.get_bottom_rect().colliderect(self.bird.get_rect())):
                    # Nếu đang ở trạng thái bất tử nhờ hồi sinh -> bỏ qua va chạm
                    try:
                        if getattr(self, 'invulnerable_frames', 0) > 0:
                            continue
                    except Exception:
                        pass
                    # Always show revive prompt on collision (user requested)
                    try:
                        # Enter revive prompt state; accept handler will enforce
                        # whether revive is possible (coins/revive_used).
                        self.state = "REVIVE_PROMPT"
                        self.revive_countdown_frames = 15 * FPS
                        return
                    except Exception:
                        pass
                    # Không thể hồi sinh -> kết thúc game
                    self.play_die_sound()
                    self.state = "GAME_OVER"
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self.save_high_score()
                        
                # Cập nhật điểm
                if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                    # Nếu đạt tới ngưỡng điểm ngẫu nhiên -> đánh dấu spawn coin cho pipe tiếp theo
                    try:
                        if self.score >= getattr(self, 'next_coin_score', 999999):
                            self.spawn_coin_for_next_pipe = True
                    except Exception:
                        pass

                    # Random chance to spawn an X2 power-up for the next pipe
                    try:
                        if random.random() < 0.12:  # ~12% chance when scoring
                            self.spawn_x2_for_next_pipe = True
                    except Exception:
                        pass

                # Xóa pipes đã qua màn hình
                if pipe.x + pipe.width < 0:
                    self.pipes.remove(pipe)
                    
            self.update_level()

            # Cập nhật các coin: di chuyển, kiểm tra thu thập bởi chim
            for coin in self.coins[:]:
                try:
                    coin.update(self.get_current_speed())
                except Exception:
                    # fallback: giảm x bằng speed nếu có lỗi
                    try:
                        coin.x -= self.get_current_speed()
                    except Exception:
                        pass

                # Nếu chim chạm coin -> tăng bộ đếm và xóa coin
                try:
                    if coin.get_rect().colliderect(self.bird.get_rect()):
                        # Determine coin gain (double if X2 active)
                        gain = 2 if getattr(self, 'x2_active', False) else 1
                        # Tăng xu lượt chơi
                        self.coins_collected += gain
                        # Tăng xu tích lũy (persistent) và lưu
                        try:
                            self.total_coins = getattr(self, 'total_coins', 0) + gain
                            self.save_total_coins()
                        except Exception:
                            pass
                        try:
                            self.coins.remove(coin)
                        except ValueError:
                            pass
                        continue
                except Exception:
                    pass

                # Xóa coin ra khỏi màn hình khi đã đi qua
                if coin.x + getattr(coin, 'size', 20) < 0:
                    try:
                        self.coins.remove(coin)
                    except ValueError:
                        pass

            # Cập nhật các X2 items: di chuyển, kiểm tra thu thập bởi chim
            for x2 in getattr(self, 'x2_items', [])[:]:
                try:
                    x2.update(self.get_current_speed())
                except Exception:
                    try:
                        x2.x -= self.get_current_speed()
                    except Exception:
                        pass
                try:
                    if x2.get_rect().colliderect(self.bird.get_rect()):
                        # Activate X2 power-up for duration
                        try:
                            self.x2_active = True
                            self.x2_frames = int(self.x2_duration_seconds * FPS)
                        except Exception:
                            self.x2_active = True
                            self.x2_frames = int(30 * FPS)
                        try:
                            self.x2_items.remove(x2)
                        except ValueError:
                            pass
                        continue
                except Exception:
                    pass
                # Remove x2 if it goes off-screen
                if x2.x + getattr(x2, 'size', 40) < 0:
                    try:
                        self.x2_items.remove(x2)
                    except ValueError:
                        pass
            
    def draw_background(self):
        # Sử dụng background manager để vẽ background
        self.background_manager.draw(self.screen)
        # Vẫn vẽ mây để tạo hiệu ứng động
        self.draw_clouds()
    
    def draw_clouds(self):
        """Vẽ mây di chuyển với hiệu ứng đẹp hơn"""
        # Sử dụng hệ thống mây từ may.py
        for cloud in self.clouds:
            cloud.update()
            cloud.draw(self.screen)
        
        
    def init_ground_surface(self):
        """Khởi tạo surface cho mặt đất (chỉ gọi 1 lần)"""
        self.ground_block = pygame.Surface((40, 100))
        # Vẽ mặt đất
        self.ground_block.fill(BROWN)
        # Vẽ cỏ
        pygame.draw.rect(self.ground_block, DARK_GREEN, (0, 0, 40, 10))
        # Convert để tối ưu blitting
        self.ground_block = self.ground_block.convert()
        
    def draw_ground(self):
        # Vẽ mặt đất di chuyển liền mạch
        ground_width = 40
        # Tính số lượng block cần vẽ (thêm 2 để đảm bảo không bị hở)
        num_blocks = (SCREEN_WIDTH // ground_width) + 3
        

    # (no-op) alias removed - Button handles its own cache methods
        for i in range(num_blocks):
            x = (i * ground_width) + (self.ground_scroll % ground_width) - ground_width
            # Vẽ mặt đất chính
            pygame.draw.rect(self.screen, BROWN, 
                           (x, self.ground_y, ground_width, 100))
            
            # Vẽ cỏ trên mặt đất
            pygame.draw.rect(self.screen, DARK_GREEN, 
                           (x, self.ground_y, ground_width, 10))
            
    def draw_menu(self):
        self.draw_background()
        
        # Vẽ logo thay vì text
        self.logo.draw(self.screen)
        
        # Vẽ chim ở menu với skin đã chọn (nếu có) - di chuyển xuống dưới
        selected_path = self.skin_selector.get_selected_skin_path()
        if selected_path:
            menu_bird = Bird(80, SCREEN_HEIGHT // 2 + 20, selected_path, size=34)
        else:
            menu_bird = Bird(80, SCREEN_HEIGHT // 2 + 20, self.skin_selector.selected_skin, size=34)
        menu_bird.draw(self.screen)
        
        self.play_button.draw(self.screen)
        self.skin_button.draw(self.screen)
        self.map_button.draw(self.screen)
        if self.high_score > 0:
            draw_text_with_outline(
                self.screen, 
                self.big_font, 
                f"Điểm cao nhất: {self.high_score}", 
                (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60), 
                (255, 215, 0),  # Màu vàng gold sáng
                outline_color=BLACK, 
                outline_width=3, 
                center=True
            )
            
    def draw_game(self):
        self.draw_background()
        
        # Vẽ pipes
        for pipe in self.pipes:
            pipe.draw(self.screen)
        # Vẽ coin (nằm trong đường bay)
        for coin in self.coins:
            try:
                coin.draw(self.screen)
            except Exception:
                pass
            
        # Vẽ chim
        self.bird.draw(self.screen)
        # Nếu đang bất tử do hồi sinh, vẽ hiệu ứng quanh chim (ef.png)
        try:
            # Draw effect if invulnerable
            if getattr(self, 'shield_effect_image', None) and getattr(self, 'invulnerable_frames', 0) > 0:
                # Larger visual when invulnerable
                try:
                    scale_factor = 4.2
                    eff_size = max(int(self.bird.size * scale_factor), 64)
                    eff = pygame.transform.smoothscale(self.shield_effect_image, (eff_size, eff_size)).convert_alpha()

                    # Create pulsing/blinking alpha using time-based sine wave
                    try:
                        t = pygame.time.get_ticks() / 200.0
                        freq = 2.5
                        pulse = (math.sin(t * freq) + 1.0) / 2.0  # 0..1
                        base = 160
                        alpha = max(30, min(255, int(base + pulse * 95)))
                        eff.set_alpha(alpha)
                    except Exception:
                        # fall back to fully opaque
                        try:
                            eff.set_alpha(200)
                        except Exception:
                            pass
                except Exception:
                    eff = self.shield_effect_image
                eff_rect = eff.get_rect(center=(int(self.bird.x), int(self.bird.y)))
                self.screen.blit(eff, eff_rect)
        except Exception:
            pass
        
        # Vẽ điểm lớn, dày, nằm trong ô chữ nhật dọc màu xanh da trời nhạt với viền xanh dương đậm
        try:
            score_s = str(self.score)
            # Create a font roughly half the visual size of the huge font to make score smaller
            try:
                base_font = getattr(self, 'huge_font', getattr(self, 'big_font', self.font))
                base_h = base_font.size("0")[1]
                new_size = max(10, int(base_h * 0.5))
                font_for_score = pygame.font.Font(pygame.font.get_default_font(), new_size)
            except Exception:
                font_for_score = getattr(self, 'big_font', self.font)

            # measure text using the new smaller font
            text_w, text_h = font_for_score.size(score_s)
            # box dims: make box smaller (about half the previous size)
            PAD_X = 6
            PAD_Y = 6
            box_w = max(50, text_w + PAD_X * 2)
            box_h = text_h + PAD_Y * 2
            box_x = SCREEN_WIDTH // 2 - box_w // 2
            box_y = 12
            box_fill = SKY_COLOR
            box_border = (0, 60, 140)
            try:
                pygame.draw.rect(self.screen, box_fill, (box_x, box_y, box_w, box_h), border_radius=10)
                pygame.draw.rect(self.screen, box_border, (box_x, box_y, box_w, box_h), 3, border_radius=10)
            except Exception:
                pygame.draw.rect(self.screen, box_fill, (box_x, box_y, box_w, box_h))
                pygame.draw.rect(self.screen, box_border, (box_x, box_y, box_w, box_h), 3)

            # Draw score text centered inside the box with a thinner outline
            try:
                center_x = box_x + box_w // 2
                center_y = box_y + box_h // 2
                draw_text_with_outline(self.screen, font_for_score, score_s, (center_x, center_y), WHITE, outline_color=box_border, outline_width=2, center=True)
            except Exception:
                txt = font_for_score.render(score_s, True, WHITE)
                txt_r = txt.get_rect(center=(box_x + box_w // 2, box_y + box_h // 2))
                self.screen.blit(txt, txt_r)
        except Exception:
            # fallback to previous simple render
            try:
                score_text = self.font.render(f"{self.score}", True, WHITE)
                score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
                self.screen.blit(score_text, score_rect)
            except Exception:
                pass

        # Vẽ ô item hiển thị số xu ở góc trái trên (hình chữ nhật bo góc, nền xanh lá nhạt, viền xanh lá đậm)
        try:
            PADDING_X = 10
            PADDING_Y = 8
            ICON_SIZE = 36
            MARGIN = 12
            text_color = DARK_GREEN

            # prepare text surface to measure width
            coins_text = str(self.coins_collected)
            text_w, text_h = self.font.size(coins_text)

            # compute box dimensions to enclose icon + padding + text
            content_w = ICON_SIZE + 8 + text_w
            box_w = content_w + PADDING_X * 2
            box_h = max(ICON_SIZE, text_h) + PADDING_Y * 2
            box_x = MARGIN
            box_y = MARGIN

            box_fill = (180, 235, 180)  # xanh lá nhạt
            box_border = DARK_GREEN    # xanh lá đậm

            # Draw rounded rect for the box (fallback if border_radius not available)
            try:
                pygame.draw.rect(self.screen, box_fill, (box_x, box_y, box_w, box_h), border_radius=8)
                pygame.draw.rect(self.screen, box_border, (box_x, box_y, box_w, box_h), 3, border_radius=8)
            except Exception:
                pygame.draw.rect(self.screen, box_fill, (box_x, box_y, box_w, box_h))
                pygame.draw.rect(self.screen, box_border, (box_x, box_y, box_w, box_h), 3)

            # Draw icon and text inside box
            if getattr(self, 'coin_image', None):
                try:
                    icon = pygame.transform.smoothscale(self.coin_image, (ICON_SIZE, ICON_SIZE))
                    icon_rect = icon.get_rect(left=box_x + PADDING_X, centery=box_y + box_h // 2)
                    self.screen.blit(icon, icon_rect)
                    # text position to the right of icon
                    text_x = icon_rect.right + 8
                    text_y = box_y + box_h // 2
                    # draw outlined text centered vertically
                    draw_text_with_outline(self.screen, self.font, coins_text, (text_x, text_y - (text_h // 2)), text_color, outline_color=box_border, outline_width=2, center=False)
                except Exception:
                    draw_text_with_outline(self.screen, self.font, coins_text, (box_x + box_w // 2, box_y + box_h // 2), text_color, outline_color=box_border, outline_width=2, center=True)
            else:
                draw_text_with_outline(self.screen, self.font, coins_text, (box_x + box_w // 2, box_y + box_h // 2), text_color, outline_color=box_border, outline_width=2, center=True)
        except Exception:
            pass
        # Vẽ ô tổng xu tích lũy ở góc phải trên (hình chữ nhật bo góc, nền xanh lá nhạt, viền xanh lá đậm)
        try:
            PADDING_X = 10
            PADDING_Y = 8
            ICON_SIZE = 36
            MARGIN = 12
            text_color = DARK_GREEN

            total = getattr(self, 'total_coins', 0)
            total_text_s = str(total)
            text_w, text_h = self.font.size(total_text_s)

            content_w = ICON_SIZE + 8 + text_w
            box_w = content_w + PADDING_X * 2
            box_h = max(ICON_SIZE, text_h) + PADDING_Y * 2
            box_x = SCREEN_WIDTH - MARGIN - box_w
            box_y = MARGIN

            box_fill = (180, 235, 180)  # xanh lá nhạt
            box_border = DARK_GREEN    # xanh lá đậm

            try:
                pygame.draw.rect(self.screen, box_fill, (box_x, box_y, box_w, box_h), border_radius=8)
                pygame.draw.rect(self.screen, box_border, (box_x, box_y, box_w, box_h), 3, border_radius=8)
            except Exception:
                pygame.draw.rect(self.screen, box_fill, (box_x, box_y, box_w, box_h))
                pygame.draw.rect(self.screen, box_border, (box_x, box_y, box_w, box_h), 3)

            # Draw icon and total text
            if getattr(self, 'coin_image', None):
                try:
                    icon = pygame.transform.smoothscale(self.coin_image, (ICON_SIZE, ICON_SIZE))
                    icon_rect = icon.get_rect(left=box_x + PADDING_X, centery=box_y + box_h // 2)
                    self.screen.blit(icon, icon_rect)
                    text_x = icon_rect.right + 8
                    text_y = box_y + box_h // 2
                    draw_text_with_outline(self.screen, self.font, total_text_s, (text_x, text_y - (text_h // 2)), text_color, outline_color=box_border, outline_width=2, center=False)
                except Exception:
                    draw_text_with_outline(self.screen, self.font, total_text_s, (box_x + box_w // 2, box_y + box_h // 2), text_color, outline_color=box_border, outline_width=2, center=True)
            else:
                draw_text_with_outline(self.screen, self.font, total_text_s, (box_x + box_w // 2, box_y + box_h // 2), text_color, outline_color=box_border, outline_width=2, center=True)

            # Vẽ trạng thái X2 (nếu active) ngay phía dưới ô tổng xu
            try:
                if getattr(self, 'x2_active', False):
                    if getattr(self, 'x2_image', None):
                        x2_img = pygame.transform.smoothscale(self.x2_image, (20, 20))
                        x2_rect = x2_img.get_rect(topright=(box_x + box_w, box_y + box_h + 34))
                        self.screen.blit(x2_img, x2_rect)
                        secs = max(0, int((getattr(self, 'x2_frames', 0) + FPS - 1) // FPS))
                        x2_text = self.font.render(str(secs), True, WHITE)
                        x2_text_rect = x2_text.get_rect(topright=(x2_rect.left - 6, x2_rect.top + 2))
                        self.screen.blit(x2_text, x2_text_rect)
                    else:
                        x2_text = self.font.render("X2", True, WHITE)
                        x2_text_rect = x2_text.get_rect(topright=(box_x + box_w, box_y + box_h + 34))
                        self.screen.blit(x2_text, x2_text_rect)
            except Exception:
                pass

        except Exception:
            pass
        except Exception:
            pass
        
        # Vẽ countdown overlay nếu đang trong countdown
        if self.state == "COUNTDOWN":
            self.draw_countdown_overlay()
        
    def draw_game_over(self):
        """Vẽ màn hình Game Over với bố cục ĐẸP HƠN"""
        self.draw_background()
        
        # Vẽ pipes và chim (đã chết) - làm mờ đi một chút
        for pipe in self.pipes:
            pipe.draw(self.screen)
        self.bird.draw(self.screen)

        # Dark overlay để làm nổi bật panel
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        # === PANEL CHÍNH ===
        panel_w = 400
        panel_h = 420
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2 - 20
        
        # Shadow cho panel
        shadow_offset = 6
        shadow_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        try:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100), (0, 0, panel_w, panel_h), border_radius=25)
        except:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100), (0, 0, panel_w, panel_h))
        self.screen.blit(shadow_surf, (panel_x + shadow_offset, panel_y + shadow_offset))
        
        # Panel background với gradient
        try:
            pygame.draw.rect(self.screen, (255, 255, 255), (panel_x, panel_y, panel_w, panel_h), border_radius=25)
            pygame.draw.rect(self.screen, (100, 100, 100), (panel_x, panel_y, panel_w, panel_h), 4, border_radius=25)
        except:
            pygame.draw.rect(self.screen, (255, 255, 255), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(self.screen, (100, 100, 100), (panel_x, panel_y, panel_w, panel_h), 4)

        # === HEADER "GAME OVER" ===
        header_y = panel_y + 30
        if self.game_over_image:
            game_over_rect = self.game_over_image.get_rect(center=(SCREEN_WIDTH // 2, header_y))
            self.screen.blit(self.game_over_image, game_over_rect)
        else:
            # Fallback với text đẹp hơn
            try:
                game_over_text = self.big_font.render("GAME OVER", True, (220, 50, 50))
            except:
                game_over_text = self.font.render("GAME OVER", True, (220, 50, 50))
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, header_y))
            
            # Vẽ outline
            for offset_x in [-3, 0, 3]:
                for offset_y in [-3, 0, 3]:
                    if offset_x != 0 or offset_y != 0:
                        try:
                            outline = self.big_font.render("GAME OVER", True, (150, 30, 30))
                        except:
                            outline = self.font.render("GAME OVER", True, (150, 30, 30))
                        self.screen.blit(outline, (game_over_rect.x + offset_x, game_over_rect.y + offset_y))
            self.screen.blit(game_over_text, game_over_rect)

        # === SCORE PANEL (Điểm số hiện tại) ===
        score_panel_y = panel_y + 110
        score_panel_h = 70
        
        # Background cho score panel với gradient đỏ nhạt
        score_panel_rect = pygame.Rect(panel_x + 20, score_panel_y, panel_w - 40, score_panel_h)
        try:
            pygame.draw.rect(self.screen, (255, 240, 240), score_panel_rect, border_radius=15)
            pygame.draw.rect(self.screen, (255, 150, 150), score_panel_rect, 3, border_radius=15)
        except:
            pygame.draw.rect(self.screen, (255, 240, 240), score_panel_rect)
            pygame.draw.rect(self.screen, (255, 150, 150), score_panel_rect, 3)
        
        # Label "Điểm số"
        try:
            label_text = self.font.render("Điểm số", True, (100, 100, 100))
        except:
            label_text = self.font.render("Điểm số", True, (100, 100, 100))
        label_rect = label_text.get_rect(center=(SCREEN_WIDTH // 2, score_panel_y + 20))
        self.screen.blit(label_text, label_rect)
        
        # Score lớn
        try:
            score_text = self.big_font.render(str(self.score), True, (220, 50, 50))
        except:
            score_text = self.font.render(str(self.score), True, (220, 50, 50))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, score_panel_y + 48))
        self.screen.blit(score_text, score_rect)

        # === HIGH SCORE PANEL (Điểm cao nhất) ===
        high_score_panel_y = score_panel_y + score_panel_h + 15
        high_score_panel_h = 70
        
        # Background cho high score panel với gradient vàng
        high_panel_rect = pygame.Rect(panel_x + 20, high_score_panel_y, panel_w - 40, high_score_panel_h)
        try:
            pygame.draw.rect(self.screen, (255, 250, 220), high_panel_rect, border_radius=15)
            pygame.draw.rect(self.screen, (255, 215, 0), high_panel_rect, 3, border_radius=15)
        except:
            pygame.draw.rect(self.screen, (255, 250, 220), high_panel_rect)
            pygame.draw.rect(self.screen, (255, 215, 0), high_panel_rect, 3)
        
        # Icon cúp/medal
        crown_y = high_score_panel_y + high_score_panel_h // 2
        self.draw_crown_icon(panel_x + 40, crown_y)
        
        # Label "Cao nhất"
        try:
            high_label = self.font.render("Cao nhất", True, (150, 120, 0))
        except:
            high_label = self.font.render("Cao nhất", True, (150, 120, 0))
        high_label_rect = high_label.get_rect(center=(SCREEN_WIDTH // 2, high_score_panel_y + 20))
        self.screen.blit(high_label, high_label_rect)
        
        # High score lớn với hiệu ứng
        try:
            high_score_text = self.big_font.render(str(self.high_score), True, (255, 215, 0))
        except:
            high_score_text = self.font.render(str(self.high_score), True, (255, 215, 0))
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, high_score_panel_y + 48))
        
        # Outline cho high score
        for offset_x in [-2, 0, 2]:
            for offset_y in [-2, 0, 2]:
                if offset_x != 0 or offset_y != 0:
                    try:
                        outline = self.big_font.render(str(self.high_score), True, (200, 170, 0))
                    except:
                        outline = self.font.render(str(self.high_score), True, (200, 170, 0))
                    self.screen.blit(outline, (high_score_rect.x + offset_x, high_score_rect.y + offset_y))
        self.screen.blit(high_score_text, high_score_rect)

        # === BUTTONS AREA ===
        buttons_y = panel_y + panel_h - 130
        button_w = 160
        button_h = 40
        button_spacing = 10
        
        # Kiểm tra xem có thể hồi sinh không
        can_revive = (not getattr(self, 'revive_used', False)) and getattr(self, 'total_coins', 0) >= 10
        
        if can_revive:
            # 3 nút: Chơi lại, Hồi sinh, Về menu (sắp xếp dọc)
            
            # Nút CHƠI LẠI (xanh dương)
            restart_y = buttons_y
            restart_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, restart_y, button_w, button_h)
            self.draw_custom_button(restart_rect, "CHƠI LẠI", (33, 150, 243), (25, 118, 210))
            self.restart_button.rect = restart_rect
            
            # Nút HỒI SINH (xanh lá - nổi bật)
            revive_y = restart_y + button_h + button_spacing
            revive_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, revive_y, button_w, button_h)
            self.draw_custom_button(revive_rect, "HỒI SINH (10 xu)", (76, 175, 80), (56, 142, 60), highlight=True)
            self.revive_button.rect = revive_rect
            
            # Nút VỀ MENU (xám)
            menu_y = revive_y + button_h + button_spacing
            menu_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, menu_y, button_w, button_h)
            self.draw_custom_button(menu_rect, "VỀ MENU", (158, 158, 158), (117, 117, 117))
            self.menu_button.rect = menu_rect
        else:
            # 2 nút: Chơi lại và Về menu (sắp xếp dọc, căn giữa)
            
            # Nút CHƠI LẠI (xanh dương - nổi bật hơn)
            restart_y = buttons_y + 20
            restart_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, restart_y, button_w, button_h)
            self.draw_custom_button(restart_rect, "CHƠI LẠI", (33, 150, 243), (25, 118, 210), highlight=True)
            self.restart_button.rect = restart_rect
            
            # Nút VỀ MENU (xám)
            menu_y = restart_y + button_h + button_spacing
            menu_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, menu_y, button_w, button_h)
            self.draw_custom_button(menu_rect, "VỀ MENU", (158, 158, 158), (117, 117, 117))
            self.menu_button.rect = menu_rect
    
    def draw_crown_icon(self, x, y, size=24):
        """Vẽ icon vương miện/cúp đơn giản"""
        # Vẽ cúp vàng
        points = [
            (x - size//2, y + size//2),
            (x - size//3, y - size//2),
            (x, y),
            (x + size//3, y - size//2),
            (x + size//2, y + size//2),
        ]
        pygame.draw.polygon(self.screen, (255, 215, 0), points)
        pygame.draw.polygon(self.screen, (218, 165, 32), points, 2)
        
        # Chân cúp
        pygame.draw.rect(self.screen, (255, 215, 0), (x - size//4, y + size//2, size//2, size//4))
        pygame.draw.rect(self.screen, (218, 165, 32), (x - size//4, y + size//2, size//2, size//4), 2)
    
    def draw_custom_button(self, rect, text, color, border_color, highlight=False):
        """Vẽ button tùy chỉnh đẹp hơn với hiệu ứng hover"""
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)
        
        # Màu sáng hơn khi hover
        if is_hover:
            btn_color = tuple(min(255, c + 30) for c in color)
        else:
            btn_color = color
        
        # Vẽ button với viền bo tròn
        try:
            pygame.draw.rect(self.screen, btn_color, rect, border_radius=10)
            
            # Viền đậm hơn nếu highlight
            border_width = 4 if highlight else 3
            pygame.draw.rect(self.screen, border_color, rect, border_width, border_radius=10)
        except:
            pygame.draw.rect(self.screen, btn_color, rect)
            border_width = 4 if highlight else 3
            pygame.draw.rect(self.screen, border_color, rect, border_width)
        
        # Text với font phù hợp
        font_size = 18 if len(text) > 10 else 20
        try:
            # Tìm font hỗ trợ tiếng Việt
            font_candidates = ["Segoe UI", "Arial", "Tahoma", "Calibri"]
            font_path = None
            for fname in font_candidates:
                try:
                    path = pygame.font.match_font(fname)
                    if path:
                        font_path = path
                        break
                except:
                    pass
            
            if font_path:
                btn_font = pygame.font.Font(font_path, font_size)
            else:
                btn_font = pygame.font.Font(None, font_size)
        except:
            btn_font = self.font
        
        try:
            btn_text = btn_font.render(text, True, WHITE)
        except:
            btn_text = self.font.render(text, True, WHITE)
        btn_text_rect = btn_text.get_rect(center=rect.center)
        self.screen.blit(btn_text, btn_text_rect)
        
        # Hiệu ứng sáng khi highlight
        if highlight and not is_hover:
            try:
                shine_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shine_surf, (255, 255, 255, 30), (0, 0, rect.width, rect.height // 2), border_top_left_radius=10, border_top_right_radius=10)
                self.screen.blit(shine_surf, (rect.x, rect.y))
            except:
                pass

    def draw_revive_prompt(self):
        """Vẽ modal hỏi người chơi có dùng 10 xu để hồi sinh hay không - GIAO DIỆN MỚI ĐẸP HƠN"""
        # Dark overlay với hiệu ứng mờ đẹp hơn
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Tối hơn một chút để làm nổi bật panel
        self.screen.blit(overlay, (0, 0))

        # Panel lớn hơn, đẹp hơn
        panel_w, panel_h = 520, 340
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        
        # Vẽ shadow cho panel (hiệu ứng đổ bóng)
        shadow_offset = 8
        shadow_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        try:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 80), (0, 0, panel_w, panel_h), border_radius=20)
        except:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 80), (0, 0, panel_w, panel_h))
        self.screen.blit(shadow_surf, (panel_x + shadow_offset, panel_y + shadow_offset))
        
        # Panel background chính với viền bo tròn
        try:
            pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), border_radius=20)
            # Viền ngoài màu vàng nổi bật
            pygame.draw.rect(self.screen, (255, 200, 0), (panel_x, panel_y, panel_w, panel_h), 4, border_radius=20)
        except Exception:
            pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(self.screen, (255, 200, 0), (panel_x, panel_y, panel_w, panel_h), 4)

        # === HEADER với gradient (vẽ bằng nhiều rectangles) ===
        header_h = 70
        for i in range(header_h):
            # Gradient từ vàng sang cam
            ratio = i / header_h
            r = int(255 * (1 - ratio * 0.2))
            g = int(200 - ratio * 50)
            b = int(0)
            try:
                pygame.draw.rect(self.screen, (r, g, b), 
                               (panel_x, panel_y + i, panel_w, 1))
            except:
                pass
        
        # Bo góc trên của header
        try:
            pygame.draw.rect(self.screen, (255, 200, 0), (panel_x, panel_y, panel_w, header_h), border_top_left_radius=20, border_top_right_radius=20)
            # Vẽ lại gradient sau khi có border radius
            for i in range(header_h - 4):
                ratio = i / header_h
                r = int(255 * (1 - ratio * 0.2))
                g = int(200 - ratio * 50)
                b = int(0)
                if i < 16:  # Bo góc
                    offset = int((16 - i) * 0.8)
                    pygame.draw.rect(self.screen, (r, g, b), 
                                   (panel_x + offset, panel_y + i + 2, panel_w - offset * 2, 1))
                else:
                    pygame.draw.rect(self.screen, (r, g, b), 
                                   (panel_x, panel_y + i + 2, panel_w, 1))
        except:
            pass

        # Title với icon
        try:
            title_text = self.big_font.render("HỒI SINH", True, WHITE)
        except Exception:
            title_text = self.font.render("HỒI SINH", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 28))
        
        # Vẽ outline cho text để nổi bật hơn
        for offset_x in [-2, 0, 2]:
            for offset_y in [-2, 0, 2]:
                if offset_x != 0 or offset_y != 0:
                    try:
                        outline_text = self.big_font.render("HỒI SINH", True, (200, 150, 0))
                    except:
                        outline_text = self.font.render("HỒI SINH", True, (200, 150, 0))
                    self.screen.blit(outline_text, (title_rect.x + offset_x, title_rect.y + offset_y))
        self.screen.blit(title_text, title_rect)

        # Icon xu và số xu ở header
        coin_balance = getattr(self, 'total_coins', 0)
        try:
            balance_text = self.font.render(f"Số dư: {coin_balance} xu", True, WHITE)
        except:
            balance_text = self.font.render(f"Số dư: {coin_balance} xu", True, WHITE)
        balance_rect = balance_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 52))
        self.screen.blit(balance_text, balance_rect)
        
        # Icon xu bên cạnh số dư
        if getattr(self, 'coin_image', None):
            try:
                coin_icon = pygame.transform.smoothscale(self.coin_image, (24, 24))
                self.screen.blit(coin_icon, (balance_rect.left - 30, balance_rect.centery - 12))
            except:
                pass

        # === PHẦN GIỮA: Countdown với vòng tròn tiến trình ===
        countdown_center_y = panel_y + header_h + 80
        
        # Vẽ vòng tròn nền
        pygame.draw.circle(self.screen, (240, 240, 240), 
                          (SCREEN_WIDTH // 2, countdown_center_y), 60)
        pygame.draw.circle(self.screen, (200, 200, 200), 
                          (SCREEN_WIDTH // 2, countdown_center_y), 60, 3)
        
        # Vẽ vòng tròn tiến trình (countdown)
        secs = max(0, int((getattr(self, 'revive_countdown_frames', 0) + FPS - 1) // FPS))
        max_secs = 15  # Tổng thời gian countdown
        progress = secs / max_secs
        
        # Vẽ arc cho countdown (từ đỏ -> vàng -> xanh theo thời gian còn lại)
        if progress > 0.6:
            arc_color = (76, 175, 80)  # Xanh lá
        elif progress > 0.3:
            arc_color = (255, 193, 7)  # Vàng
        else:
            arc_color = (244, 67, 54)  # Đỏ
        
        # Vẽ arc (pygame không hỗ trợ arc dễ dàng, dùng vòng tròn nhiều đoạn)
        if progress > 0:
            import math
            radius = 58
            thickness = 6
            segments = 60
            angle_per_segment = (2 * math.pi) / segments
            total_segments = int(segments * progress)
            
            for i in range(total_segments):
                angle1 = -math.pi / 2 + i * angle_per_segment
                angle2 = -math.pi / 2 + (i + 1) * angle_per_segment
                
                x1 = SCREEN_WIDTH // 2 + radius * math.cos(angle1)
                y1 = countdown_center_y + radius * math.sin(angle1)
                x2 = SCREEN_WIDTH // 2 + radius * math.cos(angle2)
                y2 = countdown_center_y + radius * math.sin(angle2)
                
                pygame.draw.line(self.screen, arc_color, (x1, y1), (x2, y2), thickness)
        
        # Số đếm ngược lớn ở giữa vòng tròn
        try:
            countdown_text = self.big_font.render(f"{secs}s", True, arc_color)
        except:
            countdown_text = self.font.render(f"{secs}s", True, arc_color)
        countdown_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, countdown_center_y))
        self.screen.blit(countdown_text, countdown_rect)

        # === PHẦN THÔNG TIN ===
        revive_possible = (not getattr(self, 'revive_used', False)) and coin_balance >= 10
        
        if revive_possible:
            info_msg = "Bạn có đủ xu để hồi sinh!"
            info_color = (76, 175, 80)  # Xanh lá
        else:
            if getattr(self, 'revive_used', False):
                info_msg = "Đã sử dụng hồi sinh trong lượt này"
                info_color = (244, 67, 54)  # Đỏ
            else:
                info_msg = f"✗ Còn thiếu {10 - coin_balance} xu"
                info_color = (244, 67, 54)  # Đỏ
        
        try:
            info_text = self.font.render(info_msg, True, info_color)
        except:
            info_text = self.font.render(info_msg, True, info_color)
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + header_h + 165))
        
        # Background cho info message
        info_bg_rect = pygame.Rect(info_rect.x - 10, info_rect.y - 5, 
                                   info_rect.width + 20, info_rect.height + 10)
        try:
            pygame.draw.rect(self.screen, (255, 255, 255, 200), info_bg_rect, border_radius=8)
            pygame.draw.rect(self.screen, info_color, info_bg_rect, 2, border_radius=8)
        except:
            pygame.draw.rect(self.screen, (250, 250, 250), info_bg_rect)
            pygame.draw.rect(self.screen, info_color, info_bg_rect, 2)
        self.screen.blit(info_text, info_rect)

        # === BUTTONS AREA (2 nút cạnh nhau) ===
        button_y = panel_y + panel_h - 60
        button_w = 200
        button_h = 45
        button_spacing = 20
        
        # Button ĐỒNG Ý (Xanh lá) - Bên trái
        confirm_x = SCREEN_WIDTH // 2 - button_w - button_spacing // 2
        
        if revive_possible:
            # Vẽ nút đẹp với gradient xanh lá
            confirm_color = (76, 175, 80)
            confirm_hover_color = (104, 195, 108)
            
            # Kiểm tra hover
            mouse_pos = pygame.mouse.get_pos()
            confirm_rect = pygame.Rect(confirm_x, button_y, button_w, button_h)
            is_confirm_hover = confirm_rect.collidepoint(mouse_pos)
            
            btn_color = confirm_hover_color if is_confirm_hover else confirm_color
            
            try:
                pygame.draw.rect(self.screen, btn_color, confirm_rect, border_radius=10)
                pygame.draw.rect(self.screen, (60, 140, 64), confirm_rect, 3, border_radius=10)
            except:
                pygame.draw.rect(self.screen, btn_color, confirm_rect)
                pygame.draw.rect(self.screen, (60, 140, 64), confirm_rect, 3)
            
            # Text "ĐỒNG Ý" với icon xu
            try:
                confirm_text = self.font.render("ĐỒNG Ý (10 xu)", True, WHITE)
            except:
                confirm_text = self.font.render("ĐỒNG Ý (10 xu)", True, WHITE)
            confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
            self.screen.blit(confirm_text, confirm_text_rect)
            
            # Update button rect cho click detection
            if hasattr(self, 'revive_button'):
                self.revive_button.rect = confirm_rect
        else:
            # Vẽ nút disabled
            confirm_rect = pygame.Rect(confirm_x, button_y, button_w, button_h)
            disabled_color = (189, 189, 189)
            
            try:
                pygame.draw.rect(self.screen, disabled_color, confirm_rect, border_radius=10)
                pygame.draw.rect(self.screen, (158, 158, 158), confirm_rect, 3, border_radius=10)
            except:
                pygame.draw.rect(self.screen, disabled_color, confirm_rect)
                pygame.draw.rect(self.screen, (158, 158, 158), confirm_rect, 3)
            
            try:
                confirm_text = self.font.render("ĐỒNG Ý (10 xu)", True, (150, 150, 150))
            except:
                confirm_text = self.font.render("ĐỒNG Ý (10 xu)", True, (150, 150, 150))
            confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
            self.screen.blit(confirm_text, confirm_text_rect)

        # Button TỪ CHỐI (Đỏ) - Bên phải
        decline_x = SCREEN_WIDTH // 2 + button_spacing // 2
        decline_rect = pygame.Rect(decline_x, button_y, button_w, button_h)
        
        # Kiểm tra hover
        mouse_pos = pygame.mouse.get_pos()
        is_decline_hover = decline_rect.collidepoint(mouse_pos)
        
        decline_color = (244, 67, 54)
        decline_hover_color = (229, 115, 115)
        btn_color = decline_hover_color if is_decline_hover else decline_color
        
        try:
            pygame.draw.rect(self.screen, btn_color, decline_rect, border_radius=10)
            pygame.draw.rect(self.screen, (198, 40, 40), decline_rect, 3, border_radius=10)
        except:
            pygame.draw.rect(self.screen, btn_color, decline_rect)
            pygame.draw.rect(self.screen, (198, 40, 40), decline_rect, 3)
        
        try:
            decline_text = self.font.render("TỪ CHỐI", True, WHITE)
        except:
            decline_text = self.font.render("TỪ CHỐI", True, WHITE)
        decline_text_rect = decline_text.get_rect(center=decline_rect.center)
        self.screen.blit(decline_text, decline_text_rect)
        
        # Update button rect cho click detection
        if hasattr(self, 'revive_decline_button'):
            self.revive_decline_button.rect = decline_rect

    def draw_countdown_overlay(self):
        """Vẽ countdown overlay trên màn hình game"""
        # Tính số đếm ngược (3, 2, 1) trong 3 giây
        if self.countdown_timer > 120:
            seconds_left = 3
        elif self.countdown_timer > 60:
            seconds_left = 2
        else:
            seconds_left = 1
        
        # Vẽ số đếm ngược lớn ở giữa màn hình
        countdown_text = self.big_font.render(str(seconds_left), True, RED)
        countdown_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        # Thêm hiệu ứng nhấp nháy cho số cuối cùng
        if seconds_left <= 1:
            # Tạo hiệu ứng nhấp nháy
            alpha = int(255 * (self.countdown_timer % 20) / 20)
            countdown_surface = pygame.Surface(countdown_text.get_size(), pygame.SRCALPHA)
            countdown_surface.blit(countdown_text, (0, 0))
            countdown_surface.set_alpha(alpha)
            self.screen.blit(countdown_surface, countdown_rect)
        else:
            self.screen.blit(countdown_text, countdown_rect)

    def draw_skin_selection(self):
        """Vẽ màn hình chọn skin với GIAO DIỆN ĐẸP HƠN và hiệu ứng NHÚNG NHÚNG"""
        self.draw_background()
        
        # Tạo fonts cache (chỉ tạo 1 lần)
        if not hasattr(self, '_skin_fonts_cached'):
            try:
                font_candidates = ["Segoe UI", "Arial", "Tahoma", "Calibri"]
                font_path = None
                for fname in font_candidates:
                    try:
                        path = pygame.font.match_font(fname)
                        if path:
                            font_path = path
                            break
                    except:
                        pass
                
                if font_path:
                    self._skin_title_font = pygame.font.Font(font_path, 42)
                    self._skin_name_font = pygame.font.Font(font_path, 36)
                    self._skin_number_font = pygame.font.Font(font_path, 22)
                    self._skin_badge_font = pygame.font.Font(font_path, 18)
                else:
                    self._skin_title_font = pygame.font.Font(None, 42)
                    self._skin_name_font = pygame.font.Font(None, 36)
                    self._skin_number_font = pygame.font.Font(None, 22)
                    self._skin_badge_font = pygame.font.Font(None, 18)
            except:
                self._skin_title_font = self.big_font
                self._skin_name_font = self.big_font
                self._skin_number_font = self.font
                self._skin_badge_font = self.font
            
            self._skin_fonts_cached = True
        
        # Cập nhật animation bounce
        self.skin_bounce_offset += self.skin_bounce_speed * self.skin_bounce_direction
        if self.skin_bounce_offset > 15:
            self.skin_bounce_direction = -1
        elif self.skin_bounce_offset < 0:
            self.skin_bounce_direction = 1
        
        # === PANEL CHÍNH ===
        panel_w = 450
        panel_h = 540  # Tăng từ 500 lên 540 để có đủ không gian
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2 - 20
        
        # Shadow
        shadow_offset = 6
        shadow_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        try:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 80), (0, 0, panel_w, panel_h), border_radius=30)
        except:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 80), (0, 0, panel_w, panel_h))
        self.screen.blit(shadow_surf, (panel_x + shadow_offset, panel_y + shadow_offset))
        
        # Panel background
        try:
            pygame.draw.rect(self.screen, (255, 255, 255), (panel_x, panel_y, panel_w, panel_h), border_radius=30)
            pygame.draw.rect(self.screen, (100, 100, 255), (panel_x, panel_y, panel_w, panel_h), 5, border_radius=30)
        except:
            pygame.draw.rect(self.screen, (255, 255, 255), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(self.screen, (100, 100, 255), (panel_x, panel_y, panel_w, panel_h), 5)
        
        # === HEADER với gradient ===
        header_h = 80
        for i in range(header_h):
            ratio = i / header_h
            r = int(100 + ratio * 50)
            g = int(100 + ratio * 50)
            b = int(255 - ratio * 50)
            try:
                pygame.draw.rect(self.screen, (r, g, b), (panel_x, panel_y + i, panel_w, 1))
            except:
                pass
        
        # Bo góc header
        try:
            for i in range(header_h - 4):
                ratio = i / header_h
                r = int(100 + ratio * 50)
                g = int(100 + ratio * 50)
                b = int(255 - ratio * 50)
                if i < 26:
                    offset = int((26 - i) * 0.8)
                    pygame.draw.rect(self.screen, (r, g, b), 
                                   (panel_x + offset, panel_y + i + 2, panel_w - offset * 2, 1))
                else:
                    pygame.draw.rect(self.screen, (r, g, b), 
                                   (panel_x, panel_y + i + 2, panel_w, 1))
        except:
            pass
        
        # Title với font cached
        title_str = "CHỌN SKIN CHIM"
        title_text = self._skin_title_font.render(title_str, True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 35))
        
        # Outline cho title
        for offset_x in [-2, 0, 2]:
            for offset_y in [-2, 0, 2]:
                if offset_x != 0 or offset_y != 0:
                    outline = self._skin_title_font.render(title_str, True, (70, 70, 200))
                    self.screen.blit(outline, (title_rect.x + offset_x, title_rect.y + offset_y))
        self.screen.blit(title_text, title_rect)
        
        # === PREVIEW AREA (Chim lớn với animation bounce) ===
        preview_area_y = panel_y + header_h + 25  # Giảm từ 30 xuống 25
        preview_area_h = 190  # Giảm từ 200 xuống 190
        
        # Background cho preview
        preview_bg_rect = pygame.Rect(panel_x + 30, preview_area_y, panel_w - 60, preview_area_h)
        try:
            pygame.draw.rect(self.screen, (240, 245, 255), preview_bg_rect, border_radius=20)
            pygame.draw.rect(self.screen, (150, 150, 255), preview_bg_rect, 3, border_radius=20)
        except:
            pygame.draw.rect(self.screen, (240, 245, 255), preview_bg_rect)
            pygame.draw.rect(self.screen, (150, 150, 255), preview_bg_rect, 3)
        
        # Vẽ preview skin với hiệu ứng NHÚNG NHÚNG
        preview_size = 110  # Giảm từ 120 xuống 110 để vừa với preview area nhỏ hơn
        current_path = self.skin_selector.get_current_skin_path()
        
        # Tạo preview với size lớn VÀ XÓA NỀN
        cache_key = (current_path, preview_size)
        if cache_key not in self.skin_selector.preview_cache:
            if current_path:
                try:
                    img = pygame.image.load(current_path).convert_alpha()
                    # XÓA NỀN ẢNH
                    try:
                        img = remove_image_background(img, tol=80)
                    except:
                        pass
                    preview = pygame.transform.smoothscale(img, (preview_size, preview_size))
                    self.skin_selector.preview_cache[cache_key] = preview
                except:
                    # Fallback
                    preview = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)
                    pygame.draw.circle(preview, (255, 200, 0), (preview_size//2, preview_size//2), preview_size//2)
                    self.skin_selector.preview_cache[cache_key] = preview
            else:
                preview = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)
                pygame.draw.circle(preview, (255, 200, 0), (preview_size//2, preview_size//2), preview_size//2)
                self.skin_selector.preview_cache[cache_key] = preview
        
        preview = self.skin_selector.preview_cache[cache_key]
        
        # Vẽ với offset bounce (nhúng nhúng)
        preview_center_y = preview_area_y + preview_area_h // 2 + int(self.skin_bounce_offset)
        preview_rect = preview.get_rect(center=(SCREEN_WIDTH // 2, preview_center_y))
        
        # Vẽ shadow cho chim
        shadow_bird = pygame.Surface((preview_size + 10, preview_size + 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_bird, (0, 0, 0, 50), (0, 0, preview_size + 10, preview_size + 10))
        shadow_rect = shadow_bird.get_rect(center=(SCREEN_WIDTH // 2, preview_center_y + 5))
        self.screen.blit(shadow_bird, shadow_rect)
        
        self.screen.blit(preview, preview_rect)
        
        # === SKIN INFO (Tên và số thứ tự) ===
        info_y = preview_area_y + preview_area_h + 15
        
        # Background cho skin info - nhỏ gọn hơn
        info_bg_w = panel_w - 80
        info_bg_h = 75  # Giảm từ 80 xuống 75
        info_bg_rect = pygame.Rect(panel_x + 40, info_y - 5, info_bg_w, info_bg_h)
        try:
            pygame.draw.rect(self.screen, (250, 250, 255), info_bg_rect, border_radius=15)
            pygame.draw.rect(self.screen, (200, 200, 255), info_bg_rect, 2, border_radius=15)
        except:
            pygame.draw.rect(self.screen, (250, 250, 255), info_bg_rect)
            pygame.draw.rect(self.screen, (200, 200, 255), info_bg_rect, 2)
        
        # Tên skin với font cached
        skin_name = (self.skin_selector.skin_names[self.skin_selector.current_skin - 1]
                     if self.skin_selector.skin_names and self.skin_selector.total_skins > 0
                     else "Mặc định")
        
        skin_text = self._skin_name_font.render(skin_name, True, (40, 40, 100))
        skin_rect = skin_text.get_rect(center=(SCREEN_WIDTH // 2, info_y + 10))
        self.screen.blit(skin_text, skin_rect)
        
        # Số thứ tự với font cached
        number_text = f"{self.skin_selector.current_skin} / {max(1, self.skin_selector.total_skins)}"
        number_surface = self._skin_number_font.render(number_text, True, (100, 100, 255))
        number_rect = number_surface.get_rect(center=(SCREEN_WIDTH // 2, info_y + 48))
        
        # Background pill cho số thứ tự
        pill_padding = 10  # Giảm từ 12 xuống 10
        pill_rect = pygame.Rect(
            number_rect.x - pill_padding,
            number_rect.y - pill_padding // 2,
            number_rect.width + pill_padding * 2,
            number_rect.height + pill_padding
        )
        try:
            pygame.draw.rect(self.screen, (220, 220, 255), pill_rect, border_radius=15)
            pygame.draw.rect(self.screen, (180, 180, 255), pill_rect, 2, border_radius=15)
        except:
            pygame.draw.rect(self.screen, (220, 220, 255), pill_rect)
            pygame.draw.rect(self.screen, (180, 180, 255), pill_rect, 2)
        
        self.screen.blit(number_surface, number_rect)
        
        # Nếu skin đang được chọn, vẽ dấu tick
        if self.skin_selector.current_skin == self.skin_selector.selected_skin:
            # Vẽ badge "ĐANG DÙNG" với font cached
            badge_text = "✓ ĐANG DÙNG"
            badge_surface = self._skin_badge_font.render(badge_text, True, WHITE)
            badge_rect = badge_surface.get_rect(center=(SCREEN_WIDTH // 2 + 140, preview_area_y + 20))
            
            # Background cho badge
            badge_bg = pygame.Rect(
                badge_rect.x - 10,
                badge_rect.y - 5,
                badge_rect.width + 20,
                badge_rect.height + 10
            )
            try:
                pygame.draw.rect(self.screen, (255, 140, 0), badge_bg, border_radius=12)
                pygame.draw.rect(self.screen, (200, 100, 0), badge_bg, 3, border_radius=12)
            except:
                pygame.draw.rect(self.screen, (255, 140, 0), badge_bg)
                pygame.draw.rect(self.screen, (200, 100, 0), badge_bg, 3)
            
            self.screen.blit(badge_surface, badge_rect)
        
        # === NÚT PREV/NEXT (Mũi tên tròn đẹp, ở 2 bên preview area) ===
        arrow_y = preview_area_y + preview_area_h // 2
        arrow_size = 55
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Nút PREV (Mũi tên trái) - Bên trái preview area
        prev_x = preview_bg_rect.left - arrow_size - 15
        prev_rect = pygame.Rect(prev_x, arrow_y - arrow_size // 2, arrow_size, arrow_size)
        
        is_prev_hover = prev_rect.collidepoint(mouse_pos)
        prev_color = (120, 170, 255) if is_prev_hover else (80, 130, 240)
        prev_border = (60, 110, 220)
        
        # Vẽ nút tròn
        try:
            pygame.draw.circle(self.screen, prev_color, prev_rect.center, arrow_size // 2)
            pygame.draw.circle(self.screen, prev_border, prev_rect.center, arrow_size // 2, 4)
        except:
            pygame.draw.circle(self.screen, prev_color, (int(prev_rect.centerx), int(prev_rect.centery)), arrow_size // 2)
            pygame.draw.circle(self.screen, prev_border, (int(prev_rect.centerx), int(prev_rect.centery)), arrow_size // 2, 4)
        
        # Vẽ mũi tên trái (tam giác chỉ trái)
        arrow_points = [
            (prev_rect.centerx + 10, prev_rect.centery - 14),
            (prev_rect.centerx - 10, prev_rect.centery),
            (prev_rect.centerx + 10, prev_rect.centery + 14)
        ]
        pygame.draw.polygon(self.screen, WHITE, arrow_points)
        
        # Vẽ outline cho mũi tên
        pygame.draw.polygon(self.screen, prev_border, arrow_points, 2)
        
        self.prev_skin_button.rect = prev_rect
        
        # Nút NEXT (Mũi tên phải) - Bên phải preview area
        next_x = preview_bg_rect.right + 15
        next_rect = pygame.Rect(next_x, arrow_y - arrow_size // 2, arrow_size, arrow_size)
        
        is_next_hover = next_rect.collidepoint(mouse_pos)
        next_color = (120, 170, 255) if is_next_hover else (80, 130, 240)
        next_border = (60, 110, 220)
        
        # Vẽ nút tròn
        try:
            pygame.draw.circle(self.screen, next_color, next_rect.center, arrow_size // 2)
            pygame.draw.circle(self.screen, next_border, next_rect.center, arrow_size // 2, 4)
        except:
            pygame.draw.circle(self.screen, next_color, (int(next_rect.centerx), int(next_rect.centery)), arrow_size // 2)
            pygame.draw.circle(self.screen, next_border, (int(next_rect.centerx), int(next_rect.centery)), arrow_size // 2, 4)
        
        # Vẽ mũi tên phải (tam giác chỉ phải)
        arrow_points = [
            (next_rect.centerx - 10, next_rect.centery - 14),
            (next_rect.centerx + 10, next_rect.centery),
            (next_rect.centerx - 10, next_rect.centery + 14)
        ]
        pygame.draw.polygon(self.screen, WHITE, arrow_points)
        
        # Vẽ outline cho mũi tên
        pygame.draw.polygon(self.screen, next_border, arrow_points, 2)
        
        self.next_skin_button.rect = next_rect
        
        # === BUTTONS ===
        # Tính toán vị trí buttons dựa trên info area để tránh chồng lấn
        buttons_start_y = info_y + info_bg_h + 15  # Cách info area 15px
        button_w = 200
        button_h = 48  # Giảm từ 50 xuống 48 để tiết kiệm không gian
        
        # Kiểm tra skin đã được chọn chưa
        is_selected = self.skin_selector.current_skin == self.skin_selector.selected_skin
        
        # Button CHỌN/ĐÃ CHỌN
        select_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, buttons_start_y, button_w, button_h)
        
        if is_selected:
            self.draw_custom_button(select_rect, "✓ ĐÃ CHỌN", (255, 140, 0), (200, 100, 0), highlight=True)
            self.select_skin_button.text = "ĐÃ CHỌN"
        else:
            self.draw_custom_button(select_rect, "CHỌN SKIN", (76, 175, 80), (56, 142, 60), highlight=True)
            self.select_skin_button.text = "CHỌN"
        self.select_skin_button.rect = select_rect
        
        # Button QUAY LẠI
        back_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, buttons_start_y + button_h + 10, button_w, button_h)
        self.draw_custom_button(back_rect, "QUAY LẠI", (158, 158, 158), (117, 117, 117))
        self.back_button.rect = back_rect

    def draw_map_selection(self):
        """Vẽ màn hình chọn map với BỐ CỤC ĐẸP HƠN"""
        # Vẽ background map hiện tại (làm mờ)
        current_map_path = self.map_selector.get_current_map_path()
        if current_map_path and current_map_path != "default":
            try:
                map_img = pygame.image.load(current_map_path)
                map_img = pygame.transform.smoothscale(map_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.screen.blit(map_img, (0, 0))
            except:
                self.draw_background()
        else:
            self.draw_background()
        
        # Overlay tối để làm nổi bật panel
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # === PANEL CHÍNH ===
        panel_w = 400  # Thu nhỏ để gọn hơn
        panel_h = 480  # Thu nhỏ để vừa vặn
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2 - 10
        
        # Shadow
        shadow_offset = 6
        shadow_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        try:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100), (0, 0, panel_w, panel_h), border_radius=30)
        except:
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100), (0, 0, panel_w, panel_h))
        self.screen.blit(shadow_surf, (panel_x + shadow_offset, panel_y + shadow_offset))
        
        # Panel background
        try:
            pygame.draw.rect(self.screen, (255, 255, 255), (panel_x, panel_y, panel_w, panel_h), border_radius=30)
            pygame.draw.rect(self.screen, (255, 140, 0), (panel_x, panel_y, panel_w, panel_h), 5, border_radius=30)
        except:
            pygame.draw.rect(self.screen, (255, 255, 255), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(self.screen, (255, 140, 0), (panel_x, panel_y, panel_w, panel_h), 5)
        
        # === HEADER với gradient ===
        header_h = 80
        for i in range(header_h):
            ratio = i / header_h
            r = int(255 - ratio * 50)
            g = int(140 + ratio * 40)
            b = int(0 + ratio * 50)
            try:
                pygame.draw.rect(self.screen, (r, g, b), (panel_x, panel_y + i, panel_w, 1))
            except:
                pass
        
        # Bo góc header
        try:
            for i in range(header_h - 4):
                ratio = i / header_h
                r = int(255 - ratio * 50)
                g = int(140 + ratio * 40)
                b = int(0 + ratio * 50)
                if i < 26:
                    offset = int((26 - i) * 0.8)
                    pygame.draw.rect(self.screen, (r, g, b), 
                                   (panel_x + offset, panel_y + i + 2, panel_w - offset * 2, 1))
                else:
                    pygame.draw.rect(self.screen, (r, g, b), 
                                   (panel_x, panel_y + i + 2, panel_w, 1))
        except:
            pass
        
        # Title
        draw_text_with_outline(
            self.screen, 
            self.big_font, 
            "CHỌN MAP", 
            (SCREEN_WIDTH // 2, panel_y + 30), 
            WHITE,
            outline_color=(200, 100, 0), 
            outline_width=2, 
            center=True
        )
        
        # Số xu ở góc header
        total_coins = getattr(self, 'total_coins', 0)
        draw_text_with_outline(
            self.screen, 
            self.font, 
            f"Xu: {total_coins}", 
            (SCREEN_WIDTH // 2, panel_y + 60), 
            WHITE,
            outline_color=(200, 100, 0), 
            outline_width=2, 
            center=True
        )
        
        # === PREVIEW AREA ===
        preview_size = 180  # Giảm từ 220 xuống 180
        preview_y = panel_y + header_h + 15  # Giảm spacing
        preview_x = panel_x + (panel_w - preview_size) // 2
        
        # Background cho preview
        preview_bg = pygame.Rect(preview_x - 10, preview_y - 10, preview_size + 20, preview_size + 20)
        try:
            pygame.draw.rect(self.screen, (240, 240, 240), preview_bg, border_radius=15)
            pygame.draw.rect(self.screen, (200, 200, 200), preview_bg, 3, border_radius=15)
        except:
            pygame.draw.rect(self.screen, (240, 240, 240), preview_bg)
            pygame.draw.rect(self.screen, (200, 200, 200), preview_bg, 3)
        
        # Vẽ preview map
        current_idx = self.map_selector.current_map
        is_locked = not self.map_selector.is_map_unlocked(current_idx)
        
        if current_map_path and current_map_path != "default":
            try:
                preview_img = pygame.image.load(current_map_path)
                preview_img = pygame.transform.smoothscale(preview_img, (preview_size, preview_size))
                self.screen.blit(preview_img, (preview_x, preview_y))
            except:
                pygame.draw.rect(self.screen, (128, 128, 128), (preview_x, preview_y, preview_size, preview_size))
        else:
            pygame.draw.rect(self.screen, SKY_COLOR, (preview_x, preview_y, preview_size, preview_size))
        
        # Nếu bị khóa, vẽ overlay
        if is_locked:
            overlay = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (preview_x, preview_y))
            
            # Icon khóa
            lock_size = 50
            lock_x = preview_x + (preview_size - lock_size) // 2
            lock_y = preview_y + (preview_size - lock_size) // 2
            pygame.draw.rect(self.screen, (200, 200, 200), (lock_x, lock_y, lock_size, lock_size), border_radius=10)
            pygame.draw.rect(self.screen, (150, 150, 150), (lock_x + 10, lock_y + 25, lock_size - 20, lock_size - 25), border_radius=5)
            pygame.draw.arc(self.screen, (150, 150, 150), (lock_x + 12, lock_y + 5, lock_size - 24, 30), 0, 3.14159, 5)
        
        # === MAP INFO ===
        info_y = preview_y + preview_size + 15
        
        # Background cho map info
        info_bg = pygame.Rect(panel_x + 30, info_y, panel_w - 60, 80)
        try:
            pygame.draw.rect(self.screen, (250, 250, 255), info_bg, border_radius=15)
            pygame.draw.rect(self.screen, (200, 200, 255), info_bg, 2, border_radius=15)
        except:
            pygame.draw.rect(self.screen, (250, 250, 255), info_bg)
            pygame.draw.rect(self.screen, (200, 200, 255), info_bg, 2)
        
        # Tên map
        map_name = (self.map_selector.map_names[self.map_selector.current_map]
                   if self.map_selector.map_names and self.map_selector.total_maps > 0
                   else "Mặc định")
        draw_text_with_outline(
            self.screen, 
            self.big_font, 
            map_name, 
            (SCREEN_WIDTH // 2, info_y + 18), 
            (50, 50, 50),
            outline_color=(200, 200, 200), 
            outline_width=1, 
            center=True
        )
        
        # Số thứ tự - chỉ hiển thị nếu map KHÔNG bị khóa
        if not is_locked:
            map_number = f"{self.map_selector.current_map + 1} / {max(1, self.map_selector.total_maps)}"
            draw_text_with_outline(
                self.screen, 
                self.font, 
                map_number, 
                (SCREEN_WIDTH // 2, info_y + 55), 
                (100, 100, 150),
                outline_color=(200, 200, 200), 
                outline_width=1, 
                center=True
            )
        
        # Giá nếu bị khóa - HIỂN THỊ THAY CHO SỐ THỨ TỰ
        if is_locked:
            map_price = self.map_selector.get_map_price(current_idx)
            # Font nhỏ hơn và không có emoji để tránh che chữ
            price_text = self.font.render(f"{map_price} xu", True, (255, 215, 0))
            price_rect = price_text.get_rect(center=(SCREEN_WIDTH // 2, info_y + 55))
            # Vẽ outline
            outline_text = self.font.render(f"{map_price} xu", True, BLACK)
            for offset_x in [-2, 0, 2]:
                for offset_y in [-2, 0, 2]:
                    if offset_x != 0 or offset_y != 0:
                        self.screen.blit(outline_text, (price_rect.x + offset_x, price_rect.y + offset_y))
            self.screen.blit(price_text, price_rect)
        
        # === NÚT PREV/NEXT ===
        arrow_y = preview_y + preview_size // 2
        arrow_size = 55
        mouse_pos = pygame.mouse.get_pos()
        
        # Prev button
        prev_x = preview_x - arrow_size - 15
        prev_rect = pygame.Rect(prev_x, arrow_y - arrow_size // 2, arrow_size, arrow_size)
        is_prev_hover = prev_rect.collidepoint(mouse_pos)
        prev_color = (255, 180, 100) if is_prev_hover else (255, 140, 0)
        
        try:
            pygame.draw.circle(self.screen, prev_color, prev_rect.center, arrow_size // 2)
            pygame.draw.circle(self.screen, (200, 100, 0), prev_rect.center, arrow_size // 2, 4)
        except:
            pygame.draw.circle(self.screen, prev_color, (int(prev_rect.centerx), int(prev_rect.centery)), arrow_size // 2)
            pygame.draw.circle(self.screen, (200, 100, 0), (int(prev_rect.centerx), int(prev_rect.centery)), arrow_size // 2, 4)
        
        arrow_points = [(prev_rect.centerx + 10, prev_rect.centery - 14), (prev_rect.centerx - 10, prev_rect.centery), (prev_rect.centerx + 10, prev_rect.centery + 14)]
        pygame.draw.polygon(self.screen, WHITE, arrow_points)
        pygame.draw.polygon(self.screen, (200, 100, 0), arrow_points, 2)
        self.prev_map_button.rect = prev_rect
        
        # Next button
        next_x = preview_x + preview_size + 15
        next_rect = pygame.Rect(next_x, arrow_y - arrow_size // 2, arrow_size, arrow_size)
        is_next_hover = next_rect.collidepoint(mouse_pos)
        next_color = (255, 180, 100) if is_next_hover else (255, 140, 0)
        
        try:
            pygame.draw.circle(self.screen, next_color, next_rect.center, arrow_size // 2)
            pygame.draw.circle(self.screen, (200, 100, 0), next_rect.center, arrow_size // 2, 4)
        except:
            pygame.draw.circle(self.screen, next_color, (int(next_rect.centerx), int(next_rect.centery)), arrow_size // 2)
            pygame.draw.circle(self.screen, (200, 100, 0), (int(next_rect.centerx), int(next_rect.centery)), arrow_size // 2, 4)
        
        arrow_points = [(next_rect.centerx - 10, next_rect.centery - 14), (next_rect.centerx + 10, next_rect.centery), (next_rect.centerx - 10, next_rect.centery + 14)]
        pygame.draw.polygon(self.screen, WHITE, arrow_points)
        pygame.draw.polygon(self.screen, (200, 100, 0), arrow_points, 2)
        self.next_map_button.rect = next_rect
        
        # === BUTTONS ===
        buttons_y = info_y + 95
        button_w = 200
        button_h = 48
        
        # Button SELECT/MUA
        select_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, buttons_y, button_w, button_h)
        
        if is_locked:
            map_price = self.map_selector.get_map_price(current_idx)
            if total_coins >= map_price:
                self.draw_custom_button(select_rect, f"MUA ({map_price} xu)", (76, 175, 80), (56, 142, 60), highlight=True)
                self.select_map_button.text = "MUA"
                self.select_map_button.color = (76, 175, 80)
            else:
                self.draw_custom_button(select_rect, "CHƯA ĐỦ XU", (189, 189, 189), (158, 158, 158))
                self.select_map_button.text = "CHƯA ĐỦ XU"
                self.select_map_button.color = (189, 189, 189)
        else:
            if self.map_selector.current_map == self.map_selector.selected_map:
                self.draw_custom_button(select_rect, "✓ ĐÃ CHỌN", (255, 140, 0), (200, 100, 0), highlight=True)
                self.select_map_button.text = "ĐÃ CHỌN"
                self.select_map_button.color = (255, 140, 0)
            else:
                self.draw_custom_button(select_rect, "CHỌN MAP", (76, 175, 80), (56, 142, 60), highlight=True)
                self.select_map_button.text = "CHỌN"
                self.select_map_button.color = (76, 175, 80)
        
        self.select_map_button.rect = select_rect
        
        # Button QUAY LẠI
        back_rect = pygame.Rect(panel_x + (panel_w - button_w) // 2, buttons_y + button_h + 10, button_w, button_h)
        self.draw_custom_button(back_rect, "QUAY LẠI", (158, 158, 158), (117, 117, 117))
        self.back_button.rect = back_rect

    def toggle_music(self):
        """Toggle mute/unmute nhạc nền và cập nhật icon của nút."""
        try:
            if not pygame.mixer.get_init() or self.music_path is None:
                return
        except:
            return

        if getattr(self, "muted", False):
            # Unmute
            try:
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.unpause()
            except:
                pass
            self.muted = False
            # Set icon volume
            if hasattr(self, 'volume_icon') and self.volume_icon:
                self.mute_button.icon = self.volume_icon
                # Force init của button để cập nhật cache surfaces
                self.mute_button.init_cached_surfaces()
        else:
            # Mute
            try:
                pygame.mixer.music.pause()
                pygame.mixer.music.set_volume(0)
            except:
                pass
            self.muted = True
            # Set icon mute và đảm bảo nó hiển thị ngay
            if hasattr(self, 'mute_icon') and self.mute_icon:
                self.mute_button.icon = self.mute_icon
                # Force init của button để cập nhật cache surfaces
                self.mute_button.init_cached_surfaces()

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "COUNTDOWN" or self.state == "PLAYING":
            self.draw_game()
        elif self.state == "GAME_OVER":
            self.draw_game_over()
        elif self.state == "REVIVE_PROMPT":
            # Draw the current game frame as background then overlay the prompt
            self.draw_game()
            self.draw_revive_prompt()
        elif self.state == "SKIN_SELECTION":
            self.draw_skin_selection()
        elif self.state == "MAP_SELECTION":
            self.draw_map_selection()
        # Vẽ nút bật/tắt nhạc ở trên cùng (chỉ hiển thị ở menu, ẩn khi đang chơi)
        if getattr(self, "mute_button", None) and self.state not in ["PLAYING", "COUNTDOWN"]:
            self.mute_button.draw(self.screen)
        # Không gọi flip() ở đây. Flip đã được thực hiện trong vòng lặp run().
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Xử lý click chuột cho các button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Kiểm tra nút tắt/bật nhạc (luôn phản hồi)
                    if getattr(self, "mute_button", None) and self.mute_button.rect.collidepoint(event.pos):
                        self.toggle_music()
                        continue
                    # Nếu đang hiển thị prompt hồi sinh, xử lý chọn có/không
                    if self.state == "REVIVE_PROMPT":
                        try:
                            # Đồng ý hồi sinh
                            if hasattr(self, 'revive_button') and self.revive_button.rect.collidepoint(event.pos):
                                if (not getattr(self, 'revive_used', False)) and getattr(self, 'total_coins', 0) >= 10:
                                    self.total_coins -= 10
                                    try:
                                        self.save_total_coins()
                                    except Exception:
                                        pass
                                    self.revive_used = True
                                    # Hồi sinh và tiếp tục chơi
                                    self.state = "PLAYING"
                                    try:
                                        self.bird.y = SCREEN_HEIGHT // 2
                                        self.bird.velocity = -6
                                        self.bird.rotation = -20
                                    except Exception:
                                        pass
                                    # Give temporary invulnerability for revive
                                    try:
                                        self.invulnerable_frames = self.revive_invul_seconds * FPS
                                    except Exception:
                                        pass
                                    # reset revive prompt countdown
                                    self.revive_countdown_frames = 0
                                    continue
                            # Từ chối hồi sinh
                            if hasattr(self, 'revive_decline_button') and self.revive_decline_button.rect.collidepoint(event.pos):
                                self.play_die_sound()
                                self.state = "GAME_OVER"
                                # Reset countdown khi từ chối
                                self.revive_countdown_frames = 0
                                # SET revive_used = True vì người chơi đã từ chối, không cho phép hồi sinh nữa
                                self.revive_used = True
                                if self.score > self.high_score:
                                    self.high_score = self.score
                                    self.save_high_score()
                                continue
                        except Exception:
                            pass
                    if self.state == "MENU":
                        if self.play_button.rect.collidepoint(event.pos):
                            self.start_countdown()
                        elif self.skin_button.rect.collidepoint(event.pos):
                            # Rescan skins each time user opens skin selector so newly
                            # added files are detected immediately.
                            try:
                                self.skin_selector.rescan()
                            except Exception:
                                pass
                            self.state = "SKIN_SELECTION"
                        elif self.map_button.rect.collidepoint(event.pos):
                            self.state = "MAP_SELECTION"
                    
                    elif self.state == "SKIN_SELECTION":
                        if self.prev_skin_button.rect.collidepoint(event.pos):
                            self.skin_selector.prev_skin()
                        elif self.next_skin_button.rect.collidepoint(event.pos):
                            self.skin_selector.next_skin()
                        elif self.select_skin_button.rect.collidepoint(event.pos):
                            self.skin_selector.select_current_skin()
                            self.state = "MENU"
                        elif self.back_button.rect.collidepoint(event.pos):
                            self.state = "MENU"
                    
                    elif self.state == "MAP_SELECTION":
                        if self.prev_map_button.rect.collidepoint(event.pos):
                            self.map_selector.prev_map()
                        elif self.next_map_button.rect.collidepoint(event.pos):
                            self.map_selector.next_map()
                        elif self.select_map_button.rect.collidepoint(event.pos):
                            current_idx = self.map_selector.current_map
                            is_locked = not self.map_selector.is_map_unlocked(current_idx)
                            
                            if is_locked:
                                # Map bị khóa - thử mua
                                map_price = self.map_selector.get_map_price(current_idx)
                                total_coins = getattr(self, 'total_coins', 0)
                                
                                if total_coins >= map_price:
                                    # Đủ xu - mua map
                                    self.total_coins -= map_price
                                    self.save_total_coins()
                                    self.map_selector.unlock_map(current_idx)
                                    # Chọn map vừa mua
                                    self.map_selector.select_current_map()
                                    # Pre-load map mới được chọn
                                    selected_map = self.map_selector.get_selected_map_path()
                                    if selected_map:
                                        self.map_selector.preload_map_image(selected_map)
                                    print(f"Đã mua map {self.map_selector.map_names[current_idx]} với giá {map_price} xu")
                                    self.state = "MENU"
                                else:
                                    # Không đủ xu
                                    print(f"Không đủ xu! Cần {map_price} xu, hiện có {total_coins} xu")
                            else:
                                # Map đã mở khóa - chọn bình thường
                                self.map_selector.select_current_map()
                                # Pre-load map mới được chọn
                                selected_map = self.map_selector.get_selected_map_path()
                                if selected_map:
                                    self.map_selector.preload_map_image(selected_map)
                                self.state = "MENU"
                        elif self.back_button.rect.collidepoint(event.pos):
                            self.state = "MENU"
                    
                    elif self.state == "GAME_OVER":
                        # Revive button: chỉ khi chưa dùng và có đủ xu
                        if hasattr(self, 'revive_button') and self.revive_button.rect.collidepoint(event.pos):
                            try:
                                # Dùng tổng xu tích lũy để hồi sinh
                                if (not getattr(self, 'revive_used', False)) and getattr(self, 'total_coins', 0) >= 10:
                                    # Tiêu 10 xu và hồi sinh
                                    self.total_coins -= 10
                                    try:
                                        self.save_total_coins()
                                    except Exception:
                                        pass
                                    self.revive_used = True
                                    # Đặt lại trạng thái chơi, giữ nguyên score và pipes
                                    self.state = "PLAYING"
                                    # Đặt vị trí chim ở giữa và cho một nhảy nhẹ
                                    try:
                                        self.bird.y = SCREEN_HEIGHT // 2
                                        self.bird.velocity = -6
                                        self.bird.rotation = -20
                                    except Exception:
                                        pass
                                    continue
                            except Exception:
                                pass
                        if self.restart_button.rect.collidepoint(event.pos):
                            self.start_countdown()
                        elif self.menu_button.rect.collidepoint(event.pos):
                            self.state = "MENU"
            
            # Xử lý hover cho tất cả button
            if event.type == pygame.MOUSEMOTION:
                if getattr(self, "mute_button", None):
                    self.mute_button.handle_event(event)
                if self.state == "MENU":
                    self.play_button.handle_event(event)
                    self.skin_button.handle_event(event)
                    self.map_button.handle_event(event)
                elif self.state == "SKIN_SELECTION":
                    self.prev_skin_button.handle_event(event)
                    self.next_skin_button.handle_event(event)
                    self.select_skin_button.handle_event(event)
                    self.back_button.handle_event(event)
                elif self.state == "MAP_SELECTION":
                    self.prev_map_button.handle_event(event)
                    self.next_map_button.handle_event(event)
                    self.select_map_button.handle_event(event)
                    self.back_button.handle_event(event)
                elif self.state == "GAME_OVER":
                    self.restart_button.handle_event(event)
                    self.menu_button.handle_event(event)
                
            # Điều khiển bằng phím và chuột cho game play
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.key_pressed:
                    self.key_pressed = True
                    current_time = pygame.time.get_ticks()
                    
                    if self.state == "PLAYING":
                        # Chim nhảy với âm thanh
                        self.bird.jump(self)
                    elif self.state == "GAME_OVER":
                        # Kiểm tra double space trong game over screen
                        if current_time - self.last_space_time < self.double_space_threshold:
                            # Double space detected - chơi lại
                            self.start_countdown()
                        self.last_space_time = current_time

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.key_pressed = False

            # Thêm điều khiển chuột - click trái để bay
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.state == "PLAYING":
                        # Chim nhảy với âm thanh
                        self.bird.jump(self)
                        
        return True
        
    def run(self):
        # Thiết lập display mode với double buffering
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
        
        running = True
        while running:
            # Giới hạn số lần cập nhật mỗi giây
            self.clock.tick(FPS)
            
            running = self.handle_events()
            self.update()
            self.draw()
            
            # Dùng flip thay vì update cho double buffering
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()


    def load_high_score(self):
        try:
            filepath = os.path.join(SCRIPT_DIR, "highscore.txt")
            with open(filepath, "r") as f:
                return int(f.read())
        except:
            return 0

    def save_high_score(self):
        try:
            filepath = os.path.join(SCRIPT_DIR, "highscore.txt")
            with open(filepath, "w") as f:
                f.write(str(self.high_score))
        except:
            pass

    def load_total_coins(self):
        """Load total accumulated coins from coins.txt (persistent)."""
        try:
            filepath = os.path.join(SCRIPT_DIR, "coins.txt")
            with open(filepath, "r") as f:
                return int(f.read())
        except:
            return 0

    def save_total_coins(self):
        """Save total accumulated coins to coins.txt."""
        try:
            filepath = os.path.join(SCRIPT_DIR, "coins.txt")
            with open(filepath, "w") as f:
                f.write(str(getattr(self, 'total_coins', 0)))
        except:
            pass


if __name__ == "__main__":
    game = Game()
    game.run()
