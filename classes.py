import pygame, random, os
from constants import *

# image/font loading (with emergency placeholder)
_image_cache = {}
def load_image(path, size = None, emergency_color = (120, 120, 140)):
    """
    Load an image and cache it.
    If the file is missing, draw a placeholder rect instead.
    """   
    key = (path, size)
    if key in _image_cache:
        return _image_cache[key]

    try:
        image = pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        # placeholder
        w, h = size if size else (60, 60)
        image  = pygame.Surface((w, h), pygame.SRCALPHA)
        image.fill(emergency_color)
        pygame.draw.rect(image, WHITE, image.get_rect(), 2)

    if size:
        image = pygame.transform.scale(image, size)

    _image_cache[key] = image
    return image

def make_tag(text, font, color, outline = (0, 0, 0), thickness = 2):
    # render text with outline
    text_surf = font.render(text, True,   color)
    out_surf  = font.render(text, True, outline)

    w, h = text_surf.get_size()
    pad  = thickness
    tag  = pygame.Surface((w + pad * 2, h + pad * 2),
                          pygame.SRCALPHA)

    # stamps outline in 8 dir
    for dx in (-pad, 0, pad):
        for dy in (-pad, 0, pad):
            if dx or dy:
                tag.blit(out_surf, (dx + pad, dy + pad))

    # main txt on top
    tag.blit(text_surf, (pad, pad))
    return tag

# scaling
def present():
    # scale the virtual surface onto the real window with letterboxing
    global view_scale, view_x, view_y

    win_w, win_h = win.get_size()
    if win_w == 0 or win_h == 0:
        return

    view_scale = min(win_w / SCRN_WIDTH, win_h / SCRN_HEIGHT)
    view_x     = (win_w - SCRN_WIDTH  * view_scale) / 2
    view_y     = (win_h - SCRN_HEIGHT * view_scale) / 2

    win.fill((0, 0, 0))
    scaled = pygame.transform.smoothscale(
        scrn, (int(SCRN_WIDTH * view_scale), int(SCRN_HEIGHT * view_scale))
    )
    win.blit(scaled, (view_x, view_y))
    pygame.display.flip()

def virtual(pos):
    # real mouse pos to virtual surface coord
    x, y = pos
    return(
        (x-view_x)/view_scale,
        (y-view_y)/view_scale)

# audio
def audio_pause():
    if not AUDIO_ENABLED:
        return # exit function if no audio
    CH_BGM.pause()

def audio_unpause():
    if not AUDIO_ENABLED:
        return # exit function if no audio
    CH_BGM.unpause()

def audio_fx(effect):
    if not AUDIO_ENABLED:
        return                         # exit function if no audio

    match effect:                      # easily handles playing & switching audio & channels
        case "bought"    : CH_FX1.play(buy)
        case "button"    : CH_FX1.play(click)
        case "pick_card" : CH_FX1.play(pick)
        case "sold"      : CH_FX1.play(sell)
        case "shuffle"   : CH_FX2.play(shuffle)
        case "defeat"    : CH_FX2.play(lose)
        case "win_round" : CH_FX2.play(win_rnd)

def audio_bgm(city):                   # loops bgm based on city_name
    global current_bgm

    if not AUDIO_ENABLED: return False # exit function if no audio

    if not city:                       # if there is no city, then play this
        track, name = HOME_BGM, "home"
    else:
        match city:
            case "The Vogue City"   : track, name = VOGUE, "vogue"
            case "The Mercury City" : track, name = MERCURY, "mercury"
            case "City of Fools"    : track, name = FOOLS, "fools"
            case "City of Tears"    : track, name = TEARS, "tears"
            case _                  : track, name = HOME_BGM, "home"

    # do nothing if already playing the same input
    if current_bgm == name:
        return

    current_bgm = name
    CH_BGM.play(track, loops = -1)

# classes
class Menu_Bg(pygame.sprite.Sprite):
    def __init__(self,groups):
        super().__init__(groups)
        self.image = load_image('Assets/Images/background.png',
                             (SCRN_WIDTH,SCRN_HEIGHT))
        self.rect  = self.image.get_rect(topleft = (0, 0))

class Button(pygame.sprite.Sprite):
    def __init__(self, groups, norm_path, pressed_path, center):
        super().__init__(groups)
        self.norm_path    = norm_path
        self.pressed_path = pressed_path
        self.hover        = False
        self.image        = load_image(norm_path, BTN_SIZE)
        self.rect         = self.image.get_rect(center = center)

    def hit(self,vpos):
        return self.rect.collidepoint(vpos)

    def update_hover(self, vpos):
        hover = self.rect.collidepoint(vpos)
        if hover != self.hover:
            self.hover = hover
            path       = self.pressed_path if hover else self.norm_path
            self.image = load_image(path, BTN_SIZE)
            self.rect  = self.image.get_rect(center = self.rect.center)

class UI_Button:
    # small clickable image (used for pause, sell, shuffle, etc)
    def __init__(self, path, center, size):
        self.image = load_image(path, size)
        self.rect  = self.image.get_rect(center = center)

    def hit(self, vpos):
        return self.rect.collidepoint(vpos)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Card(pygame.sprite.Sprite):
    _base_cache = {}

    def __init__(self, name, type, market, sell, *groups,
                 w = CARD_WIDTH, h = CARD_HEIGHT, pad = PADDING):
        super().__init__(*groups)
        self.name   = name
        self.type   = type
        self.market = market
        self.sell   = sell

        # per-instance size (defaults to deck size)
        self.w       = w
        self.h       = h
        self.pad     = pad
        self.frame_w = w + pad * 2
        self.frame_h = h + pad * 2
        
        self.base_pos = None
        self.image    = None
        self.rect     = pygame.Rect(0, 0, self.frame_w, self.frame_h)
        self.refresh()

    @classmethod
    def _base_art(cls, name, w, h): # load and scale the card art once
        # cache by (name, w, h), same art at two sizes loads once each
        key = (name, w, h)
        if key not in cls._base_cache:
            raw = pygame.image.load(
                os.path.join('Assets', 'Cards', f'{name}.png')
            ).convert_alpha()
            cls._base_cache[key] = pygame.transform.scale(raw, (w, h))
        return cls._base_cache[key]

    def refresh(self): # refreshes card art and labels, called if sell changes
        self.image = pygame.Surface((self.frame_w, self.frame_h),
                                    pygame.SRCALPHA)
        base = self._base_art(self.name, self.w, self.h)
        self.image.blit(base, (self.pad, self.pad))

        # selling price, scale with card width
        price_size = max(10, int(self.w * 0.25))
        f_price    = Fonts.get("ANTEORS.ttf", price_size)
        price_tag  = make_tag(f"₱{self.sell}", f_price, GREEN)
        self.image.blit(price_tag, price_tag.get_rect(
            bottomright = (self.frame_w - 2, self.frame_h - 5)))

        # card type
        icon_size  = max(18, int(self.w * 0.35))
        icon       = load_image(f"Assets/Images/{self.type}.png",
                                (icon_size, icon_size))
        self.image.blit(icon, icon.get_rect(
            bottomleft  = (4, self.frame_h - 7)))

    @classmethod
    def spawn(cls, name, *groups,
              w = CARD_WIDTH, h = CARD_HEIGHT, pad = PADDING):
        row = next(r for r in CARD_DATA if r[0] == name)
        return cls(row[0], row[1], row[2], row[3], *groups,
                   w = w, h = h, pad = pad)

    def hit(self, vpos):
        art        = pygame.Rect(0, 0, self.w, self.h)
        art.center = self.rect.center
        return art.collidepoint(vpos)

    def place(self, slot):
        if 1 <= slot <= SLOTS:
            step  = self.frame_w + GAP
            total = SLOTS * self.frame_w + (SLOTS - 1) * GAP
            left  = (SCRN_WIDTH - total - 150) / 2
            self.base_pos    = (left + self.frame_w / 2 + (slot - 1)
                             * step, CARD_Y)
            self.rect.center = self.base_pos

    def hide(self):
        self.base_pos = None
        self.rect.center = (-1000, -1000) # lmao, inakyat nlng para ma-hide suri

    def raise_up(self):
        if self.base_pos:
            self.rect.center = (self.base_pos[0], self.base_pos[1] - RAISE_Y)


    def lower(self):
        if self.base_pos:
            self.rect.center = self.base_pos

class City:
    _cache = {}
    _bag   = []

    @classmethod
    def get(cls, name):
        if name not in cls._cache:
            path = os.path.join('Assets','Images', f'{name}.png')
            raw  = pygame.image.load(path).convert_alpha()
            image  = pygame.transform.scale(raw, (SCRN_WIDTH, SCRN_HEIGHT))
            cls._cache[name] = {'name': name, 'image': image}
        return cls._cache[name]

    @classmethod
    def change(cls):
        if not cls._bag:
            cls._bag = list(CITY)
            random.shuffle(cls._bag)
        return cls.get(cls._bag.pop())

class Deck:
    def __init__(self, group):
        self.cards = []
        self.group = group

    def buy(self, name):
        card = Card.spawn(name, self.group)
        self.cards.append(card)
        return card

    def destroy(self, card):
        if card in self.cards:
            self.cards.remove(card)
        card.kill()

    def __len__(self):
        return len(self.cards)
    def __iter__(self):
        return iter(self.cards)
    def __getitem__(self, i):
        return self.cards[i]

class Fonts:
    _fonts_cache = {}

    @classmethod
    def get(cls, file, size):
        key = (file, size)
        if key not in cls._fonts_cache:
            path = os.path.join('Assets', 'Fonts', f'{file}')
            cls._fonts_cache[key] = pygame.font.Font(path, size)
        return cls._fonts_cache[key]

class Market:
    def __init__(self, group, size = MARKET_COUNT):
        self.cards = []
        self.group = group
        self.size  = size
        group.empty()

    def roll(self, city_name): # refill with weighted random cards for the city
        self.clear()
        pool    = []

        weights = dict(CITY_DATA.get(city_name, {}))
        if "Charisma" in owned_traits:
            weights["Entertainment"] = max(weights.get("Entertainment", 0), 5)

        for row in CARD_DATA:
            name, card_type = row[0], row[1]
            w = weights.get(card_type, 0)
            if w > 0:
                pool.append((name, w))

        if not pool:
            return

        names, weight_col = zip(*pool)
        picks = random.choices(names, weights = weight_col, k = self.size)

        for name in picks:
            self.cards.append(Card.spawn(
                name, self.group, w = MARKET_W, h = MARKET_H, pad = MARKET_PAD))
            
        self.layout()

    def layout(self): # places market cards in a grid
        if not self.cards:
            return

        step_x  = MARKET_FRAME_W + MARKET_GAP_X
        step_y  = MARKET_FRAME_H + MARKET_GAP_Y
        total_w = MARKET_COLS    * MARKET_FRAME_W + (MARKET_COLS - 1) * MARKET_GAP_X
        total_h = MARKET_ROWS    * MARKET_FRAME_H + (MARKET_ROWS - 1) * MARKET_GAP_Y
        left    = MARKET_X - total_w / 2
        top     = MARKET_Y - total_h / 2

        for i, card in enumerate(self.cards):
            row = i // MARKET_COLS
            col = i %  MARKET_COLS
            card.rect.center = (
                left + MARKET_FRAME_W / 2 + col * step_x,
                top  + MARKET_FRAME_H / 2 + row * step_y
            )

    def click(self, vpos):
        for card in self.cards:
            if card.hit(vpos):
                return card
        return None

    def remove(self, card):
        if card in self.cards:
            self.cards.remove(card)
        card.kill()

    def clear(self):
        for c in self.cards:
            c.kill()
        self.cards.clear()

class Tutorial:
    global TUTORIAL_SLIDES

    # image paths
    frame_path  = "Assets/Images/tutorial_screen.png"
    arrow_left  = "Assets/Images/arrow_left.png"
    arrow_right = "Assets/Images/arrow_right.png"
    close_path  = "Assets/Images/close.png"

    # sizes
    frame     = (900, 602)
    arrow     = (60, 60)
    slide_s   = (680, 383)
    slide_pos = (SCRN_WIDTH // 2, SCRN_HEIGHT // 2 + 50)
    close_s   = (70, 70)
    close_pos = (SCRN_WIDTH - 200, SCRN_HEIGHT - 560)

    def __init__(self):
        self.active    = False
        self.slide  = 0     # current slide
        self.under  = None  # screenshot of background

    def open(self, under_scene):
        # opens the tutorial as an overlay
        self.active   = True
        self.slide = 0
        self.under = under_scene.copy()

    def close(self):
        self.active   = False
        self.under = None

    def _frame_rect(self):
        # frame where the tutorial slide will sit on
        rect        = pygame.Rect(0, 0, *self.frame)
        rect.center = (SCRN_WIDTH // 2, SCRN_HEIGHT // 2)
        return rect

    def _arrow_rects(self):
        # arrow rects for collidepoints and image pos
        frame            = self._frame_rect()
        arrow_w, arrow_h = self.arrow
        left             = pygame.Rect(0, 0, arrow_w, arrow_h)
        right            = pygame.Rect(0, 0, arrow_w, arrow_h)
        left.center      = (frame.left  - arrow_w // 2 - 10, frame.centery + 65)
        right.center     = (frame.right + arrow_w // 2 + 10, frame.centery + 65)
        return left, right

    def _close_rect(self):
        # close rects for collidepoints and image pos
        rect        = pygame.Rect(0, 0, *self.close_s)
        rect.center = self.close_pos
        return rect

    # input
    def events(self, e):
        if   e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: # close tutorial window
            self.close()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            vpos        = virtual(e.pos)
            left, right = self._arrow_rects()

            # exit
            if self._close_rect().collidepoint(vpos):
                self.close()
                return

            # arrows
            if   left.collidepoint(vpos) and self.slide > 0:
                self.slide -= 1
            elif right.collidepoint(vpos) and self.slide < len(TUTORIAL_SLIDES) - 1:
                self.slide += 1

    # render
    def draw(self, surf):
        # dark overlay
        overlay = pygame.Surface((SCRN_WIDTH, SCRN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))

        panel   = self._frame_rect()

        # frame image scaled to window size
        frame   = load_image(self.frame_path, self.frame, emergency_color = WOOD)
        surf.blit(frame, panel)

        # current tutorial slides
        slide   = load_image(TUTORIAL_SLIDES[self.slide],
                             self.slide_s, emergency_color = BLUE)
        surf.blit(slide, slide.get_rect(
            center = self.slide_pos))

        # arrows (dim arrow when unable to click)
        left_rect, right_rect = self._arrow_rects()
        prev_arrow            = load_image(self.arrow_left,  self.arrow, emergency_color = WOOD)
        next_arrow            = load_image(self.arrow_right, self.arrow, emergency_color = WOOD)

        if self.slide <= 0:
            prev_arrow = prev_arrow.copy(); prev_arrow.set_alpha(70)
        if self.slide >= len(TUTORIAL_SLIDES) - 1:
            next_arrow = next_arrow.copy(); next_arrow.set_alpha(70)

        surf.blit(prev_arrow,  left_rect)
        surf.blit(next_arrow, right_rect)

        # exit button
        close_rect = self._close_rect()
        close_img  = load_image(self.close_path, self.close_s, emergency_color = RED)
        surf.blit(close_img, close_rect)

        # page/slide counter
        f        = Fonts.get("ANTEORS.ttf", 22)
        page_tag = make_tag(f"{self.slide + 1} / {len(TUTORIAL_SLIDES)}", f, WHITE)
        surf.blit(page_tag, page_tag.get_rect(
            midbottom = (panel.centerx, panel.bottom - 8)))  
tutor = Tutorial() # module level instance to initiate Tutorial() class

