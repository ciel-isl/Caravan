import pygame

# constants
SCRN_WIDTH, SCRN_HEIGHT = 1280, 720
CARD_WIDTH, CARD_HEIGHT = 145, 220

# padding on card
PADDING      = 17
FRAME_WIDTH  = CARD_WIDTH  + PADDING * 2
FRAME_HEIGHT = CARD_HEIGHT + PADDING * 2

# market cards
MARKET_W       = 95
MARKET_H       = 135
MARKET_PAD     = 7
MARKET_FRAME_W = MARKET_W + MARKET_PAD * 2
MARKET_FRAME_H = MARKET_H + MARKET_PAD * 2

# market shelf
MARKET_COLS  = 5
MARKET_ROWS  = 3
MARKET_COUNT = MARKET_COLS * MARKET_ROWS
MARKET_GAP_X = 55
MARKET_GAP_Y = 42
MARKET_X     = SCRN_WIDTH  * 0.5
MARKET_Y     = SCRN_HEIGHT * 0.58

# card slots
GAP      = 7
SLOTS    = 5
CARD_Y   = SCRN_HEIGHT * (4/5)
RAISE_Y  = 40
DOCKER_Y = SCRN_HEIGHT * 0.80

# traits
TRAIT_ICON_SIZE = (55, 55)
TRAIT_ICON_GAP  = 8
OFFER_ICON_SIZE = (140, 140)

# menu
BTN_SIZE      = (SCRN_WIDTH * 0.20 - 5, SCRN_HEIGHT * 0.10 - 5)
PAUSE_BUTTONS = [
    ("Assets/Images/play.png",    340),
    ("Assets/Images/tutorial.png", 420),
    ("Assets/Images/exit.png",    500),
]

# tutorial
TUTORIAL_SLIDES = [
    "Assets/Tutorial/slide1.png",
    "Assets/Tutorial/slide2.png",
    "Assets/Tutorial/slide3.png",
    "Assets/Tutorial/slide4.png",
    "Assets/Tutorial/slide5.png",
    "Assets/Tutorial/slide6.png",
    "Assets/Tutorial/slide7.png",
    "Assets/Tutorial/slide8.png",
    "Assets/Tutorial/slide9.png"
]

# colours
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GOLD  = (240, 200,  60)
GREEN = ( 41, 158,  93)
BLUE  = ( 37, 118, 162)
RED   = (185,  63,  63)
WOOD  = ( 22, 159,  81)

# game state
RUNNING   = True
PAUSE     = False
GAME_FLOW = "HOME"
in_play   = False

# window
win          = pygame.display.set_mode((SCRN_WIDTH, SCRN_HEIGHT), pygame.RESIZABLE)
scrn         = pygame.Surface((SCRN_WIDTH, SCRN_HEIGHT))
sprites      = pygame.sprite.Group()
market_group = pygame.sprite.Group()
clock        = pygame.time.Clock()

entered    = False
view_scale = 1.0
view_x     = 0.0
view_y     = 0.0

# cards
deck      = None
market    = None
picked    = []

# game stats
LEVEL = 1
SCORE = 0
QUOTA = 500
MONEY = 0.00
sells         = 3
shuffles      = 3

# special events
event_cooldown = 2  # every 2 levels, one special screen
next_special   = "MARKET"

# traits
owned_traits   = []
trait_choices  = [] # 3 offered traits on level clear
trait_press    = None
trait_time     = 0

# menu
menu_group = None
btn_play = btn_tutorial = btn_exit = None

# in-game uis
ui_docker  = None
ui_pause   = None
ui_sell    = None
ui_shuffle = None

# city
city_name = None # current city

CITY       = ["The Vogue City", "The Mercury City", "City of Fools", "City of Tears"]

# how often each card type appears in each city's market
CITY_DATA  = {
    "The Vogue City":   {"Clothing":      5, "Entertainment": 2, "School":   2, "Food": 2},
    "The Mercury City": {"Medicine":      5, "Entertainment": 2, "School":   2, "Food": 2},
    "City of Fools":    {"Entertainment": 5, "Clothing":      2, "Medicine": 2, "Food": 2},
    "City of Tears":    {"School":        5, "Clothing":      2, "Medicine": 2, "Food": 2},
}

# city multiplier price bonuses/debuffs
CITY_BONUS = {
    "The Vogue City":   {"Medicine":      2.0, "School":        0.5},
    "The Mercury City": {"Clothing":      2.0, "Entertainment": 0.5},
    "City of Fools":    {"School":        2.0, "Clothing":      0.5},
    "City of Tears":    {"Entertainment": 2.0, "Medicine":      0.5}
}

# card catalogue
CARD_DATA     = [
    ("Shades",          "Clothing",       100, 200),
    ("Fedora",          "Clothing",       250, 350),
    ("Belt",            "Clothing",       400, 500),
    ("T-shirt",         "Clothing",        400, 600),
    ("Baggy Pants",     "Clothing",       500, 700),
    ("Boots",           "Clothing",      700, 1000),

    ("Chips",           "Food",           100, 150),
    ("Water",           "Food",           100, 200),
    ("Eggs",            "Food",           150, 300),
    ("Chocolate",       "Food",           250, 450),
    ("Baguette",        "Food",           350, 500),
    ("Peanut Butter",   "Food",           600, 800),

    ("Paracetamol",     "Medicine",       300, 400),
    ("Alcohol",         "Medicine",       200, 300),
    ("Bandage",         "Medicine",       250, 350),
    ("First-Aid",       "Medicine",       600, 800),
    ("Band-Aid",        "Medicine",        50, 150),
    ("Herbs",           "Medicine",       250, 500),

    ("Miffy",           "Entertainment",  600, 900),
    ("Rubiks",          "Entertainment",  300, 450),
    ("Dice",            "Entertainment",  150, 250),
    ("Basketball",      "Entertainment",  500, 650),
    ("Toy Car",         "Entertainment",  300, 500),
    ("Barbie",          "Entertainment",  300, 500),

    ("Pen & Paper",     "School",          50, 150),
    ("Boat",            "School",     10000, 99999),
    ("Bag",             "School",         450, 600),
    ("Flask",           "School",         550, 700),
    ("Stapler",         "School",         100, 250),
    ("Books",           "School",       1000, 1500),]

STARTING_DECK = ["Chips", "Water", "Eggs", "Chocolate", "Baguette", "Peanut Butter"]

# trait definitions (change)
marathon = 0
TRAIT_DEFS = {
    "Full Attire":      {"desc": "x1.5 for each 'Clothing'\nyou have in stock."},
    "Too Dark":         {"desc": "x2 for each 'Shades'\nsold in a hand."},
    "Pajamas":          {"desc": "x2 to all 'Clothing'."},
    "Marathon":         {"desc": "+50 to all 'Clothing'\nwhen selling 'Boots'."},
    "Peards 4Sale":     {"desc": "x3 when selling pairs of 'Food'."},
    "Fasting":          {"desc": "+3 sell chances but 'Food' sells for 0",
                         "type_mult": ("Food", 0), "bonus_sells": 3},
    "Buffet":           {"desc": "x2 to all 'Food'."},
    "Worshipper":       {"desc": "x1.5 to all products."},
    "Inflation":        {"desc": "x2 to all 'Medicine'."},
    "Emergency":        {"desc": "x6 when selling 'Bandage',\n'First-Aid', and 'Band-Aid'."},
    "Vegan":            {"desc": "'Herbs' are free in the market\nand sell for +150"},
    "Illegal Vendor":   {"desc": "x2 when selling 'Debuffed' products."},
    "Charisma":         {"desc": "Every city now have 'Entertainment'\nstocked-up and 'Buffed'."},
    "Gambler":          {"desc": "1/6 chance to gain x6\nwhen selling 'Dice'."},
    "Mascot":           {"desc": "x3.5 to all 'Miffy'."},
    "Negotiator":       {"desc": "50%" "discount at the market."},
    "Flood Control":    {"desc": "Selling a boat wins the round."},
    "Book Worm":        {"desc": "x2 to all 'School'."}
}

