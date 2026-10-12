import pygame, random, sys
from constants import *
from classes   import *

# initiation
pygame.init()
pygame.display.set_caption('Caravan')

# misc functions
def clear_selection():
    # lower every picked card and empty the list
    for card in picked:
        card.lower()
    picked.clear()

def check_lose_condition():
    # returns True if no sell AND score < quota, no cards AND score < quota
    if     SCORE >= QUOTA:
        return False
    if     sells == 0:
        return True
    if len(deck) == 0:
        return True

def draw_bonuses(surf):
    if not city_name: # if not in city, end function
        return

    # reads city bonus for buffs and debuffs
    bonuses  = CITY_BONUS.get(city_name, {})
    buffed   = None
    debuffed = None
    for card_type, mult in bonuses.items():
        if mult > 1.0:
            buffed   = card_type
        if mult < 1.0:
            debuffed = card_type

    # icons list
    icons = []
    if buffed:
        icons.append((f"Assets/Images/{buffed}.png", GREEN))
        icons.append((f"Assets/Images/arrow_up.png", GREEN))
    if debuffed:
        icons.append((f"Assets/Images/{debuffed}.png", RED))
        icons.append((f"Assets/Images/arrow_down.png", RED))

    # render
    icon_s   = 30
    gap      = 3
    total_w  = len(icons) * icon_s + (len(icons) - 1) * gap
    x        = SCRN_WIDTH - 20 - total_w
    y        = 6
    for path, color in icons:
        icon = load_image(path, (icon_s, icon_s), emergency_color = color)
        surf.blit(icon, (x, y))
        x += icon_s + gap

def draw_hud(surf):
    # top-center HUD: level, deck count, money
    f       = Fonts.get("ANTEORS.ttf", 26)
    hud_txt = f"Level {LEVEL}      Current Revenue: ₱{SCORE}      Stock: {len(deck)}      Money:  ₱{MONEY}"
    tag     = make_tag(hud_txt, f, WHITE)
    surf.blit(tag, tag.get_rect(
        midtop = (SCRN_WIDTH // 2, 5)))

def draw_quota(surf):
    # bottom-right quota
    f       = Fonts.get("ANTEORS.ttf", 65)
    hud_txt = f"₱{QUOTA}"
    tag     = make_tag(hud_txt, f, BLACK, thickness = 0)
    surf.blit(tag, tag.get_rect(
        midtop = (SCRN_WIDTH - 140, SCRN_HEIGHT - 130)))

def draw_traits(surf):
    # long press an icon to remove
    x, y = 80, 55

    for trait_name in owned_traits:
        icon = load_image(f"Assets/Traits/{trait_name}.png",
                          TRAIT_ICON_SIZE, emergency_color = GOLD)
        surf.blit(icon, (x, y))
        x += TRAIT_ICON_SIZE[0] + TRAIT_ICON_GAP

def draw_uses(surf):
    # use count below sell and shuffle buttons
    f       = Fonts.get("ANTEORS.ttf", 20)

    if ui_sell:
        tag = make_tag(str(sells), f, WHITE)
        surf.blit(tag, tag.get_rect(
            center = (ui_sell.rect.centerx, ui_sell.rect.bottom + 14)))
    if ui_shuffle:
        tag = make_tag(str(shuffles), f, WHITE)
        surf.blit(tag, tag.get_rect(
            center = (ui_shuffle.rect.centerx, ui_shuffle.rect.bottom + 14)))

def get_sell_value(card, picked_cards):
    # final sell price = base * city bonus * trait mult
    # called every sell, traits are reflected instantly
    value = float(card.sell)

    # helper counts
    # functions inside functions
    def picked_count(name):
        return sum(1 for c in picked_cards if c.name == name)
    def picked_type(type):
        return sum(1 for c in picked_cards if c.type == type)
    def stock_type(type):
        return sum(1 for c in deck.cards   if c.type == type)

    if "Full Attire" in owned_traits and card.type == "Clothing": # the owned_trait will affect the card.type
        n = stock_type("Clothing")                                # counts stock_type as n
        value *= (1 + 0.5 * n)

    if "Too Dark" in owned_traits and card.name == "Shades":
        n = picked_count("Shades")                                # counts picked_count as n
        if n > 0:
            value *= 2 ** n                                       # x2 every n

    if "Pajamas" in owned_traits and card.type == "Clothing":
        value *= 2

    if "Marathon" in owned_traits and card.type == "Clothing":
        value += marathon

    if "Pears 4Sale" in owned_traits and card.type == "Food":
        pair = picked_type("Food")
        if pair >= 2:
            value *= 3

    if "Buffet" in owned_traits and card.type == "Food":
        value *= 2

    # trait mults
    if "Worshipper" in owned_traits:
        value *= 1.5

    if "Inflation" in owned_traits and card.type == "Medicine":
        value *= 2

    if "Emergency" in owned_traits:
        names = {c.name for c in picked_cards}
        if {"Bandage", "First-Aid", "Band-Aid"} <= names:         # as long as these cards are included
            value *= 6

    if "Vegan" in owned_traits and card.name == "Herbs":
        value += 150

    if "Illegal Vendor" in owned_traits:
        base_bonus = CITY_BONUS.get(city_name, {}).get(card.type, 1.0) # gets the buff/debuff data for a card.type
        if base_bonus < 1.0:
            value *= 2

    # city bonus/debuff (charisma trait overrides)
    city_mult = CITY_BONUS.get(city_name, {}).get(card.type, 1.0)
    if "Charisma" in owned_traits and card.type == "Entertainment":
        city_mult = max(city_mult, 2.0)
    value *= city_mult

    if "Gambler" in owned_traits and card.name == "Dice":
        if random.random() < 1/6:
            value *= 6

    if "Mascot" in owned_traits and card.name == "Miffy":         # the owned_trait will affect the card.name
        value *= 3.5

    if "Book Worm" in owned_traits and card.type == "School":
        value *= 2

    return max(0, int(value))

def market_price(card):
    # final market cost after traits
    # vegan's free herbs
    if "Vegan" in owned_traits and card.name == "Herbs":
        return 0

    # negotiator's 50% discount
    cost = card.market
    if "Negotiator" in owned_traits:
        cost = int(cost * 0.5)
    return cost

def outline_image(image, color = GOLD, thickness = 2):
    # silhouette
    mask           = pygame.mask.from_surface(image)
    outline        = mask.to_surface(                      # maskes the surface so that it clears out original colors
        setcolor   = (color[0], color[1], color[2], 255),
        unsetcolor = (0, 0, 0, 0))

    w, h = image.get_size()
    pad  = thickness
    out  = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

    # 8 dir
    for dx in (-pad, 0, pad):     # left to right
        for dy in (-pad, 0, pad): # up to down
            if dx or dy:
                out.blit(outline, (dx + pad, dy + pad))

    # original image on top
    out.blit(image, (pad, pad))
    return out

def reflow():
    # put the first deck card in slots, hide the rest
    if deck is None:
        return
    for i, card in enumerate(deck.cards):
        if i < SLOTS:
            card.place(i + 1)
        else:
            card.hide()

# initiation
def setup_home():
    global menu_group, btn_play, btn_tutorial, btn_exit
    # create menu sprites
    
    menu_group = pygame.sprite.Group()
    Menu_Bg(menu_group)

    btn_play   = Button(menu_group,
                       "Assets/Images/play.png",    "Assets/Images/play_pressed.png",
                       (SCRN_WIDTH // 2, SCRN_HEIGHT * 0.62))
    btn_tutorial = Button(menu_group,
                       "Assets/Images/tutorial.png", "Assets/Images/tutorial_pressed.png",
                       (SCRN_WIDTH // 2, SCRN_HEIGHT * 0.74))
    btn_exit    = Button(menu_group,
                       "Assets/Images/exit.png",    "Assets/Images/exit_pressed.png",
                       (SCRN_WIDTH // 2, SCRN_HEIGHT * 0.86))

def setup_game_ui():
    global ui_docker, ui_pause, ui_sell, ui_shuffle
    # create in-game ui

    ui_docker  = load_image("Assets/Images/ui_docker.png", (1280, 720))
    
    ui_pause   = UI_Button("Assets/Images/ui_pause.png", (27, 30), (50, 50))
    ui_sell    = UI_Button("Assets/Images/ui_sell.png",
                         (60, SCRN_HEIGHT - 95),  (80, 80))
    ui_shuffle = UI_Button("Assets/Images/ui_shuffle.png",
                         (60, SCRN_HEIGHT - 210), (80, 80))

def setup_level():
    global SCORE, QUOTA, sells, shuffles, in_play, picked
    # reset per-level state: score = 0, quota = scaled
    # sell/shuffle = 3 (+trait bonus), pick  city, roll market

    SCORE = 0
    if LEVEL == 1:
        QUOTA = 500
    else:
        QUOTA = 500 + 25 * LEVEL * (LEVEL - 2) 

    sells    = 3
    shuffles = 3

    for trait_name in owned_traits:
        bonus  = TRAIT_DEFS[trait_name].get("bonus_sells", 0)
        sells += bonus

    picked = []
    market.clear()
    if next_special == "MARKET": market.roll(city_name)

    in_play = True
    reflow()

def next_event():
    global event_cooldown, next_special, GAME_FLOW
    # called after level clear, decides what event to go to
    # market, pick trait, or next level
    # every 2 levels, triggers one event, alternating
    event_cooldown -= 1

    if event_cooldown > 0:
        GAME_FLOW = "NEXT_LEVEL"
        return

    event_cooldown = 2

    if next_special == "MARKET":
        next_special = "TRAIT_PICK"
        transition_in()
        GAME_FLOW    = "MARKET"
        return
    else:
        next_special = "MARKET"
        GAME_FLOW    = "TRAIT_PICK"

# game states
def home():
    global RUNNING, GAME_FLOW, AUDIO_ENABLED, menu_group

    audio_bgm(None)

    if menu_group is None:
        setup_home()

    # if the tutorial window is open, override all inputs
    if tutor.active:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                RUNNING = False
            else:
                tutor.events(e)

        if tutor.under:
            scrn.blit(tutor.under, (0, 0))

        tutor.draw(scrn)
        present()
        clock.tick(60)
        return

    for e in pygame.event.get():
        if e.type   == pygame.QUIT:
            RUNNING  = False
            continue
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            RUNNING = False
            continue
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            vpos     = virtual(e.pos)
            if btn_play.hit(vpos):
                audio_fx("button")
                transition_in()
                GAME_FLOW = "NEW_GAME"
                home.entered = False
                return
            elif btn_tutorial.hit(vpos):
                audio_fx("button")
                tutor.open(scrn)        # open as overlay, no need for GAME_FLOW change
                return
            elif btn_exit.hit(vpos):
                audio_fx("button")
                RUNNING   = False

    mouse = virtual(pygame.mouse.get_pos())
    for b in (btn_play, btn_tutorial, btn_exit):
        b.update_hover(mouse)

    scrn.fill((30, 30, 40))
    menu_group.draw(scrn)

    if not home.entered:
        transition_out(scrn.copy())     # menu already drawn -> reveal it
        home.entered = True
    else:
        present()
    
    present()
    clock.tick(60)
home.entered = False

def new_game():
    global GAME_FLOW, deck, market, menu_group, marathon
    global LEVEL, MONEY, SCORE, owned_traits, city_name
    global event_cooldown, next_special

    # init a fresh run
    menu_group = None
    marathon   = 0
    sprites.empty()

    deck   = Deck(sprites)
    market = Market(market_group)

    for name in STARTING_DECK:
        deck.buy(name)

    LEVEL          = 1
    MONEY          = 0
    SCORE          = 0
    owned_traits   = []
    event_cooldown = 2
    next_special   = "MARKET"

    city_name = City.change()['name']
    
    audio_bgm(city_name)
    setup_game_ui()
    setup_level()
    GAME_FLOW = "PLAY"

def play():
    global RUNNING, GAME_FLOW, PAUSE, picked
    global SCORE, MONEY, sells, shuffles
    global trait_press, trait_time, entered

    # tutorial overlay has priority
    if tutor.active:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                RUNNING = False
            else:
                tutor.events(e)

        if tutor.under:
            scrn.blit(tutor.under, (0, 0))

        tutor.draw(scrn)
        present()
        clock.tick(60)
        return

    # checks lose cons
    if SCORE < QUOTA:
        if check_lose_condition():
            GAME_FLOW = "GAME_OVER"
            audio_fx("defeat")
            return

    for e in pygame.event.get():
        # quit input
        if e.type   == pygame.QUIT:
            RUNNING = False
            continue

        # keyboard input
        # quit
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            RUNNING = False
            continue

        # pause
        if e.type   == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            audio_fx("button")
            PAUSE = not PAUSE
            if PAUSE: audio_pause()
            else:   audio_unpause()
            continue

        # mouse input
        if e.type   == pygame.MOUSEBUTTONDOWN and e.button == 1:
            vpos = virtual(e.pos)

            #pause
            if ui_pause.hit(vpos):
                audio_fx("button")
                PAUSE = not PAUSE
                if PAUSE: audio_pause()
                else:   audio_unpause()
                continue

            # if paused, only pause menu buttons respond
            if PAUSE:
                action = pause_menu_click(vpos)
                PAUSE = True
                if action == "RESUME":
                    PAUSE = False
                    audio_unpause()
                    audio_fx("button")
                elif action == "TUTORIAL":
                    audio_fx("button")
                    tutor.open(scrn)       # PAUSE should stay True so we can go back to it after tutorial exit
                elif action == "EXIT":
                    PAUSE = False
                    audio_unpause()
                    audio_fx("button")
                    transition_in()
                    home.entered = False
                    GAME_FLOW = "HOME"
                    return
                continue
                
            # long-press tracking on trait
            trait_press = trait_hit(vpos)
            if trait_press:
                audio_fx("button")
                trait_time = pygame.time.get_ticks()
                continue

            # sell
            if ui_sell.hit(vpos) and picked and sells > 0:
                audio_fx("sold")
                # every boot sold adds +50 to all clothing
                if "Marathon" in owned_traits:
                    boots_sold = sum(1 for c in picked if c.name == "Boots")
                    marathon  += 50 * boots_sold

                # selling a boat instantly wins
                flood = False
                if "Flood Control" in owned_traits:
                    for c in picked:
                        if c.name == "Boat":
                            flood = True
                            break

                total = 0
                for card in picked:
                    total += get_sell_value(card, picked)
                    deck.destroy(card)
                SCORE += total
                MONEY += total * 0.8
                sells -= 1
                picked = []
                reflow()

                if flood:
                    SCORE = max(SCORE, QUOTA) # forced quota met

                if SCORE  >= QUOTA:
                    audio_fx("win_round")
                    next_event()
                    return

            # shuffle
            if ui_shuffle.hit(vpos) and shuffles > 0:
                audio_fx("shuffle")
                shuffles -= 1
                random.shuffle(deck.cards)
                clear_selection()
                reflow()
                continue

            # pick (max 3)
            hit = None
            for card in deck.cards[:SLOTS]:
                if card.hit(vpos):
                    hit = card
                    break

            if hit:
                if hit in picked:
                    audio_fx("pick_card")
                    picked.remove(hit)
                    hit.lower()
                elif len(picked) < 3:
                    audio_fx("pick_card")
                    picked.append(hit)
                    hit.raise_up()
                continue

            # clicking empty space also clears
            clear_selection()

        # mouse release on long press
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if trait_press is not None:
                duration = pygame.time.get_ticks() - trait_time
                if duration >= 1000:
                    if trait_press in owned_traits:
                        owned_traits.remove(trait_press)
                trait_press = None

    # render
    if city_name:
        scrn.blit(City.get(city_name)['image'], (0, 0))

    if ui_docker:
        scrn.blit(ui_docker, ui_docker.get_rect(
            bottomright = (SCRN_WIDTH, SCRN_HEIGHT)))

    # draw selection highlight
    for card in picked:
        card_outlined = outline_image(card.image, GOLD)
        scrn.blit(card_outlined, card_outlined.get_rect(
            center = card.rect.center))

    sprites.draw    (scrn)
    ui_pause.draw   (scrn)
    ui_sell.draw    (scrn)
    ui_shuffle.draw (scrn)
    draw_uses       (scrn)
    draw_hud        (scrn)
    draw_bonuses    (scrn)
    draw_traits     (scrn)
    draw_quota      (scrn)

    # pause overlay: resume / tutorial / exit
    if PAUSE:
        pause_menu(scrn)

    if not entered:
        new_scene = scrn.copy() # snapshot of new scene
        transition_out(new_scene)
        entered = True
    else:
        present()               

    present()
    clock.tick(60)

def trait_hit(vpos):
    # return the trait name under vpos, or None
    # used for long-press
    x = 12
    y = 48

    for trait_name in owned_traits:
        rect = pygame.Rect(x, y, *TRAIT_ICON_SIZE)
        if rect.collidepoint(vpos):
            return trait_name
        x += TRAIT_ICON_SIZE[0] + TRAIT_ICON_GAP
    return None

def pause_menu(surf):
    # transparent overlay + 3 buttons
    overlay = pygame.Surface((SCRN_WIDTH, SCRN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    surf.blit(overlay, (0, 0))

    # pause txt
    f_title = Fonts.get("The Wildeast.ttf", 75)
    title   = f_title.render("PAUSED", True, WOOD)
    surf.blit(title, title.get_rect(
        center = (SCRN_WIDTH // 2, 250)))

    # buttons
    for path, y in PAUSE_BUTTONS:
        btn = load_image(path, BTN_SIZE, emergency_color = WOOD)
        surf.blit(btn, btn.get_rect(
            center = (SCRN_WIDTH // 2, y)))

def pause_menu_click(vpos):
    # return 'RESUME', 'TUTORIAL', 'EXIT', or None based on click
    # called in play() when PAUSE is True
    # "invisible" buttons
    labels = ["RESUME", "TUTORIAL", "EXIT"]

    for i, (path, y) in enumerate(PAUSE_BUTTONS):
        rect        = pygame.Rect(0, 0, *BTN_SIZE)
        rect.center = (SCRN_WIDTH // 2, y)
        if rect.collidepoint(vpos):
            return labels[i]
    return None

def market_screen():
    global RUNNING, GAME_FLOW, MONEY, entered
    # market page, press NEXT to next level
    for e in pygame.event.get():
        if e.type   == pygame.QUIT:
            RUNNING  = False
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            vpos     = virtual(e.pos)

            # NEXT button
            next_rect        = pygame.Rect(0, 0, 195, 50)
            next_rect.center = (SCRN_WIDTH - 120, SCRN_HEIGHT - 40)
            if next_rect.collidepoint(vpos):
                audio_fx("button")
                market.clear()
                GAME_FLOW = "NEXT_LEVEL"
                return

            # buy market card
            mcard = market.click(vpos)
            if mcard:
                cost = market_price(mcard)
                if MONEY >= cost:
                    MONEY -= cost
                    audio_fx("bought")
                    deck.buy(mcard.name)
                    market.remove(mcard)

    # render
    bg_path = "Assets/Images/market.png"
    bg      = load_image(bg_path, (SCRN_WIDTH, SCRN_HEIGHT),
                         emergency_color = BLUE)
    scrn.blit(bg, (0, 0))

    # money
    fm          = Fonts.get("ANTEORS.ttf", 26)
    money_tag   = make_tag(f"Money: ₱{MONEY}", fm, WHITE, GREEN, thickness = 2)
    scrn.blit(money_tag, money_tag.get_rect(
        topright = (SCRN_WIDTH - 45, 45)))

    # cards + price
    fp = Fonts.get("ANTEORS.ttf", 20)
    for card in market.cards:
        cost       = market_price(card)
        color      = WHITE if MONEY >= cost else RED
        price_tag  = make_tag(f"₱{cost}", fp, color)

        # place price below the card's frame
        price_rect = price_tag.get_rect(
            midtop = (card.rect.centerx, card.rect.bottom - 10))
        scrn.blit(price_tag, price_rect)

    market_group.draw(scrn)

    # next button
    next_path   = "Assets/Images/next.png"
    next_button = load_image(next_path, (195, 50),
                    emergency_color = WOOD)
    scrn.blit(next_button, next_button.get_rect(
        center = (SCRN_WIDTH - 120, SCRN_HEIGHT - 40)))

    if not entered:
        new_scene = scrn.copy() # snapshot of new scene
        transition_out(new_scene)
        entered = True
    else:
        present()

    clock.tick(60)

def trait_screen():
    global RUNNING, GAME_FLOW, owned_traits
    global trait_choices, city_name

    if trait_screen.under is None:
        trait_screen.under = scrn.copy()

    trait_path = "Assets/Traits/{name}.png"

    # on entry, pick 3 random traits the player doesn't already own
    if not trait_choices:
        available = [name for name in TRAIT_DEFS if name not in owned_traits]
        if not available:
            GAME_FLOW = "NEXT_LEVEL"
            return
        count         = min(3, len(available))
        trait_choices = random.sample(available, count)

    # event
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            RUNNING = False

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            vpos = virtual(e.pos)

            # click an owned trait -> drop it
            hit_x, hit_y = 60, 160
            for trait_name in owned_traits:
                rect = pygame.Rect(hit_x, hit_y, *TRAIT_ICON_SIZE)
                if rect.collidepoint(vpos):
                    audio_fx("button")
                    owned_traits.remove(trait_name)
                    return
                hit_x += TRAIT_ICON_SIZE[0] + TRAIT_ICON_GAP

            # click an offer -> add it (if under 5)
            for i, trait_name in enumerate(trait_choices):
                cx = SCRN_WIDTH * (0.2 + i * 0.3)
                cy = SCRN_HEIGHT * 0.5 - 80
                rect        = pygame.Rect(0, 0, *OFFER_ICON_SIZE)
                rect.center = (cx, cy)
                if rect.collidepoint(vpos):
                    if len(owned_traits) < 5:
                        audio_fx("button")
                        owned_traits.append(trait_name)
                        city_name     = City.change()['name']
                        audio_bgm(city_name)
                        trait_choices = []
                        trait_screen.under = None
                        GAME_FLOW     = "NEXT_LEVEL"
                        return

            # click skip
            skip_rect         = pygame.Rect(0, 0, *BTN_SIZE)
            skip_rect.center  = (SCRN_WIDTH // 2, SCRN_HEIGHT - 60)
            if skip_rect.collidepoint(vpos):
                audio_fx("button")
                city_name     = City.change()['name']
                audio_bgm(city_name)
                trait_choices = []
                trait_screen.under = None
                GAME_FLOW     = "NEXT_LEVEL"
                return

    # render
    overlay = pygame.Surface((SCRN_WIDTH, SCRN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    scrn.blit(trait_screen.under, (0, 0))
    scrn.blit(overlay, (0, 0))

    f_title = Fonts.get("The Wildeast.ttf", 45)
    f_name  = Fonts.get("ANTEORS.ttf", 30)
    f_desc  = Fonts.get("ANTEORS.ttf", 25)

    title = make_tag("CHOOSE A TRAIT", f_title, WOOD, thickness=3)
    scrn.blit(title, title.get_rect(
        midtop=(SCRN_WIDTH // 2, 40)))

    # owned traits row
    draw_x, draw_y = 60, 160
    for trait_name in owned_traits:
        icon = load_image(trait_path.format(name=trait_name),
                          TRAIT_ICON_SIZE, emergency_color = BLUE)
        scrn.blit(icon, (draw_x, draw_y))
        draw_x += TRAIT_ICON_SIZE[0] + TRAIT_ICON_GAP

    # offer choices
    for i, trait_name in enumerate(trait_choices):
        definition = TRAIT_DEFS[trait_name]
        cx = SCRN_WIDTH * (0.2 + i * 0.3)
        cy = SCRN_HEIGHT * 0.5

        # icon
        icon = load_image(trait_path.format(name=trait_name),
                          OFFER_ICON_SIZE, emergency_color = BLUE)
        scrn.blit(icon, icon.get_rect(center=(cx, cy - 80)))

        # name
        name_txt = f_name.render(trait_name, True, WHITE)
        scrn.blit(name_txt, name_txt.get_rect(midtop=(cx, cy + 10)))

        # description (wrapped)
        words  = definition["desc"].split()
        line   = ""
        line_y = cy + 50
        for word in words:
            test = line + word + " "
            if f_desc.size(test)[0] > 300:
                surf = f_desc.render(line, True, WHITE)
                scrn.blit(surf, surf.get_rect(
                    midtop = (cx, line_y)))
                line_y += 26
                line = word + " "
            else:
                line = test
        if line:
            surf = f_desc.render(line, True, WHITE)
            scrn.blit(surf, surf.get_rect(midtop=(cx, line_y)))

    # skip button
    skip_image = load_image("Assets/Images/skip.png", BTN_SIZE,
                            emergency_color = WOOD)
    scrn.blit(skip_image, skip_image.get_rect(
        center = (SCRN_WIDTH // 2, SCRN_HEIGHT - 60)))

    # max traits warning
    if len(owned_traits) >= 5:
        warn     = Fonts.get("ANTEORS.ttf", 20)
        warn_tag = make_tag("Max traits reached!", warn, RED)
        scrn.blit(warn_tag, warn_tag.get_rect(
            midtop = (SCRN_WIDTH // 2, 110)))

    present()
    clock.tick(60)    
trait_screen.under = None

def _transition_slide(start_y, end_y, under_scene):
    # slide the transition curtain from start_y to end_y over the screen
    transition_path = "Assets/Images/ui_transition.png"
    transition_spd  = 15
    curtain = load_image(transition_path, (SCRN_WIDTH, SCRN_HEIGHT),
                         emergency_color = RED)

    # if end_y < start_y, slide up; otherwise slide down
    step = transition_spd if end_y > start_y else -transition_spd
    y = start_y

    while True:
        # draw the previous frame of scrn, then stamp the curtain on top
        scrn.blit(under_scene, (0, 0))   # redraw the scene first
        scrn.blit(curtain, (0, y))   # curtain on top at current offset
        present()
        clock.tick(60)

        if (step > 0 and y >= end_y) or (step < 0 and y <= end_y):
            return
        y += step

def transition_in():
    global entered

    transition_path = "Assets/Images/ui_transition.png"
    transition_stop = 10
    curtain = load_image(transition_path, (SCRN_WIDTH, SCRN_HEIGHT),
                         emergency_color = RED)
    
    entered = False
    under   = scrn.copy()
    _transition_slide(-SCRN_HEIGHT, 0, under)


    # pause
    for _ in range(transition_stop):
        scrn.blit(curtain, (0, 0))
        present()
        clock.tick(60)

def transition_out(scene):
    transition_path = "Assets/Images/ui_transition.png"
    transition_spd  = 15
    transition_stop = 10
    curtain = load_image(transition_path, (SCRN_WIDTH, SCRN_HEIGHT),
                         emergency_color = RED)

    # pause
    for _ in range(transition_stop):
        scrn.blit(curtain, (0, 0))
        present()
        clock.tick(60)

    # raise
    y = 0
    while y > -SCRN_HEIGHT:
        scrn.blit(scene,   (0, 0))
        scrn.blit(curtain, (0, y))
        present()
        clock.tick(60)
        y -= transition_spd

def next_level():
    global LEVEL, GAME_FLOW, picked
    # set up the next level

    LEVEL    += 1
    picked    = []
    setup_level()
    GAME_FLOW = "PLAY"

def game_over():
    global RUNNING, GAME_FLOW, AUDIO_ENABLED, entered
    # gameover screen with stats

    CH_BGM.stop()
    if game_over.under is None:
        game_over.under = scrn.copy()
    if game_over.y is None:
        game_over.y     = -SCRN_HEIGHT // 2
        game_over.a     = 0

    for e in pygame.event.get():
        if e.type    == pygame.QUIT:
            RUNNING   = False
            return
        elif e.type  == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
            game_over.under = None
            game_over.y     = None
            game_over.a     = None
            transition_in()
            GAME_FLOW       = "HOME"
            return

    if game_over.y < (0):
        game_over.y += 15
    if game_over.a < 230:
        game_over.a += 15
        if game_over.a > 230:
            game_over.a = 230

    overlay = pygame.Surface((SCRN_WIDTH, SCRN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, game_over.a))
    
    scrn.blit(game_over.under, (0, 0))
    scrn.blit(overlay, (0, 0))

    lose_path = "Assets/Images/lose_screen.png"
    lose_sign = load_image(lose_path, (SCRN_WIDTH // 2, SCRN_HEIGHT // 2),
                           emergency_color = WOOD)

    f      = Fonts.get("ANTEORS.ttf", 26)
    levels = make_tag(f"You've Reached Level {LEVEL}, Congratulations!", f, WOOD)
    press  = make_tag("Press any key to return", f, WOOD)


    scrn.blit(game_over.under, (0, 0))          # redraw the scene first
    scrn.blit(overlay, (0, 0))                  # darkens background
    scrn.blit(lose_sign, (SCRN_WIDTH // 4, game_over.y))  # lose sign on top at current offset

    scrn.blit(levels, levels.get_rect(
        midtop = (SCRN_WIDTH // 2, SCRN_HEIGHT - 250)))
    scrn.blit(press, press.get_rect(
        midtop = (SCRN_WIDTH // 2, SCRN_HEIGHT - 210)))

    if not entered:
        new_scene = scrn.copy() # snapshot of new scene
        transition_out(new_scene)
        entered = True
    else:
        present()
    
    present()
    clock.tick(60)
game_over.under = None
game_over.y     = None
game_over.a     = None

def main():
    global GAME_FLOW, entered

    prev_gameflow = GAME_FLOW
    while RUNNING:
        if prev_gameflow != GAME_FLOW:
            prev_gameflow = GAME_FLOW
        match GAME_FLOW:
            case "HOME"       : home()
            case "NEW_GAME"   : new_game()
            case "PLAY"       : play()
            case "MARKET"     : market_screen()
            case "TRAIT_PICK" : trait_screen()
            case "NEXT_LEVEL" : next_level()
            case "GAME_OVER"  : game_over()

    pygame.mouse.set_visible(True)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()