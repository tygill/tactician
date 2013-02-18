
# This set stores all cards available in a game of dominion as strings
# The strings should be exact matches of the isotropic names
# But, it looks like some mechanism will need to be put in place to unpluralize names
cards = set()
# This maps the card plurals to the singular
plural_cards = {}
action_cards = set()
victory_cards = set()
treasure_cards = set()
curse_cards = set()

# This does not check plural cards - the card must be sanitized if its plural
def is_card(card):
    return card in cards
    
def assert_card(card):
    assert is_card(card), "invalid card: {0}".format(card)
        
# Converts plural cards to singular, and returns None if the card is not valid
def sanitize_card(card):
    if is_card(card):
        return card
    elif card in plural_cards:
        return plural_cards[card]
    else:
        return None

def is_action(card):
    return card in action_cards

def is_victory(card):
    return card in victory_cards

def is_treasure(card):
    return card in treasure_cards

def is_curse(card):
    return card in curse_cards

def incr_value(map, val):
    if val in map:
        map[val] += 1
    else:
        map[val] = 1
        
def decr_value(map, val):
    if val in map:
        map[val] -= 1
    else:
        assert False, "Decrementing card pile that doesn't exist"
    
class dominion_player:
    
    def __init__(self, name):
        self.name = name
        # Piles are implemented as a dictionary from card names to how many of them are in the pile
        self.deck = {}
        self.discard = {}
        self.hand = {}
        # Duration cards, actions/money during turn, etc.
        self.in_play = {}
        # Island, Haven, Native Villiage, etc.
        self.out_of_play = {}
        
    def set_final_score(self, score):
        self.final_score = score
        
    def gain_card(self, card):
        incr_value(self.discard, card)
    
# This class stores information about the state of a game of dominion
class dominion_game:
    
    def __init__(self):
        self.supply = {}
        self.players = {}
        self.num_players = 0
        self.trash = {}
        
        # Game meta-data
        self.empty_piles = []
        self.winner = None
        self.game_id = None
        
    # Game Initialization functions
    # -----------------------------
    
    def add_player(self, player):
        self.players[player] = dominion_player(player)
        self.num_players = len(self.players)
        
    def set_final_score(self, player, score):
        player = self.get_player(player)
        if player:
            player.set_final_score(score)
            
    def add_empty_pile(self, pile):
        assert is_card(pile), "Empty pile is not a valid card type: {0}".format(pile)
        self.empty_piles.append(pile)
        
    def set_winner(self, player):
        # The players list hasn't been filled yet, so just take this on faith.
        #assert player in self.players, "Winning player doesn't exist in the player list"
        self.winner = player
        
    def set_game_id(self, game_id):
        self.game_id = game_id
        
    def add_card_to_supply(self, card):
        assert_card(card)
        self.supply[card] = 0
        
    # This sets up the initial card counts for each of the cards in the supply, and players decks and such
    def init_game(self):
        # Add the basic cards (calling class is responsible for adding Colonies/Platinums and Potions, etc.)
        self.add_card_to_supply('Copper')
        self.add_card_to_supply('Silver')
        self.add_card_to_supply('Gold')
        self.add_card_to_supply('Estate')
        self.add_card_to_supply('Duchy')
        self.add_card_to_supply('Province')
        self.add_card_to_supply('Curse')
        # Setup initial supply counts for each card in the supply
        for card in self.supply.keys():
            if is_victory(card):
                self.supply[card] = self.victory_card_initial_supply(card)
            elif is_curse(card):
                self.supply[card] = self.curse_card_initial_supply()
            elif is_treasure(card):
                self.supply[card] = self.treasure_card_initial_supply(card)
            else:
                # All other cards start with 10 in the supply (except some from Dark Ages, but those aren't supported)
                self.supply[card] = 10
        for player in self.players.values():
            for i in range(7):
                self.gain_card_from_supply(player, 'Copper')
            for i in range(3):
                self.gain_card_from_supply(player, 'Estate')
                
                
    # Game state manipulation functions
    # ---------------------------------
    
    # Gives a card from the supply to a player
    def gain_card_from_supply(self, player, card):
        assert_card(card)
        decr_value(self.supply, card)
        self.get_player(player).gain_card(card)
        
                
    # Utility methods
    # ---------------
    
    def get_player(self, player):
        if type(player) is str:
            return self.players[player]
        else:
            # Otherwise, assume its the actual player object
            return player
    
    # Depending on the number of players, the victory card piles start with different sizes
    def victory_card_initial_supply(self, card):
        if self.num_players == 2:
            return 8
        elif self.num_players == 3 or self.num_players == 4:
            return 12
        elif self.num_players == 5 or self.num_players == 6:
            # As per Intrigue's instructions, there are more Provinces in 5 and 6 player games.
            # Other victory cards are unaffected.
            # Even though I couldn't find proof of this, I'll assume the same applies for colonies
            # Though as isotropic doesn't support 5 or 6 player games, we shouldn't ever hit this case now anyway.
            if card == 'Province' or card == 'Colony':
                if self.num_players == 5:
                    return 15
                elif self.num_players == 6:
                    return 18
            else:
                return 12
        assert False, "Failed to get victory card initial supply"
        
    def curse_card_initial_supply(self):
        return (self.num_players - 1) * 10
        
    def treasure_card_initial_supply(self, card):
        if card == 'Potion':
            return 16
        if card == 'Platinum':
            return 12
        if card == 'Harem':
            return self.victory_card_initial_supply(card)
        if self.num_players <= 4:
            if card == 'Copper':
                return 60
            elif card == 'Silver':
                return 40
            elif card == 'Gold':
                return 30
            else:
                # Other treasures must be kingdom cards
                return 10
        else:
            if card == 'Copper':
                return 120
            elif card == 'Silver':
                return 80
            elif card == 'Gold':
                return 60
            else:
                return 10
            
def add_card(card, plural = None):
    cards.add(card)
    if plural == None:
        # By default, the plural of a card is just an 's' added to the end
        plural = card + 's'
    plural_cards[plural] = card

def add_action_card(card, plural = None):
    action_cards.add(card)
    add_card(card, plural)

def add_victory_card(card, plural = None):
    victory_cards.add(card)
    add_card(card, plural)
    
def add_treasure_card(card, plural = None):
    treasure_cards.add(card)
    add_card(card, plural)

def add_curse_card(card, plural = None):
    curse_cards.add(card)
    add_card(card, plural)

def add_victory_treasure_card(card, plural = None):
    victory_cards.add(card)
    treasure_cards.add(card)
    add_card(card, plural)
    
def add_victory_action_card(card, plural = None):
    victory_cards.add(card)
    action_cards.add(card)
    add_card(card, plural)

add_action_card('Moat')
add_action_card('Adventurer')
add_action_card('Bureaucrat')
add_action_card('Cellar')
add_action_card('Chancellor')
add_action_card('Chapel')
add_action_card('Council Room')
add_action_card('Feast')
add_action_card('Festival')
add_action_card('Laboratory', 'Laboratories')
add_action_card('Library', 'Libraries')
add_action_card('Market')
add_action_card('Militia')
add_action_card('Mine')
add_action_card('Money Lender')
add_action_card('Remodel')
add_action_card('Smithy', 'Smithies')
add_action_card('Spies')
add_action_card('Thief', 'Thieves')
add_action_card('Throne Room')
add_action_card('Village')
add_action_card('Witch', 'Witches')
add_action_card('Woodcutter')
add_action_card('Workshop')

add_action_card('Secret Chamber')
add_action_card('Coppersmith')
add_action_card('Courtyard')
add_action_card('Torturer')
add_action_card('Baron')
add_action_card('Bridge')
add_action_card('Conspirator')
add_action_card('Ironworks', 'Ironworks')
add_action_card('Masquerade')
add_action_card('Mining Village')
add_action_card('Minion')
add_action_card('Pawn')
add_action_card('Saboteur')
add_action_card('Shanty Town')
add_action_card('Scout')
add_action_card('Steward')
add_action_card('Swindler')
add_action_card('Trading Post')
add_action_card('Wishing Well')
add_action_card('Upgrade')
add_action_card('Tribute')

add_action_card('Haven')
add_action_card('Sea Hag')
add_action_card('Tactician')
add_action_card('Caravan')
add_action_card('Lighthouse')
add_action_card('Fishing Village')
add_action_card('Wharf', 'Wharves')
add_action_card('Merchant Ship')
add_action_card('Outpost')
add_action_card('Ghost Ship')
add_action_card('Salvager')
add_action_card('Pirate Ship')
add_action_card('Native Village')
add_action_card('Cutpurse')
add_action_card('Bazaar')
add_action_card('Smugglers', 'Smugglers')
add_action_card('Explorer')
add_action_card('Pearl Diver')
add_action_card('Treasure Map')
add_action_card('Navigator')
add_action_card('Treasury', 'Treasuries')
add_action_card('Lookout')
add_action_card('Ambassador')
add_action_card('Warehouse')
add_action_card('Embargo', 'Embargoes')

add_action_card('Alchemist')
add_action_card('Apothecary', 'Apothecaries')
add_action_card('Apprentice')
add_action_card('Familiar')
add_action_card('Golem')
add_action_card('Herbalist')
add_action_card('Possession')
add_action_card('Scrying Pool')
add_action_card('Transmute')
add_action_card('University', 'Universities')

add_action_card('Bishop')
add_action_card('City', 'Cities')
add_action_card('Counting House')
add_action_card('Expand')
add_action_card('Forge')
add_action_card('Goons', 'Goons')
add_action_card('Grand Market')
add_action_card('King\'s Court')
add_action_card('Mint')
add_action_card('Monument')
add_action_card('Mountebank')
add_action_card('Peddler')
add_action_card('Rabble')
add_action_card('Trade Route')
add_action_card('Vault')
add_action_card('Venture')
add_action_card('Watch Tower')
add_action_card('Worker\'s Village')

add_action_card('Farming Village')
add_action_card('Fortune Teller')
add_action_card('Hamlet')
add_action_card('Harvest')
add_action_card('Horse Traders', 'Horse Traders')
add_action_card('Hunting Party', 'Hunting Parties')
add_action_card('Jester')
add_action_card('Menagerie')
add_action_card('Remake')
add_action_card('Tournament')
add_action_card('Young Witch', 'Young Witches')

add_action_card('Border Village')
add_action_card('Cartographer')
add_action_card('Crossroads', 'Crossroads')
add_action_card('Develop')
add_action_card('Duchess', 'Duchesses')
add_action_card('Embassy', 'Embassies')
add_action_card('Haggler')
add_action_card('Highway', 'Highways')
add_action_card('Inn')
add_action_card('Jack of All Trades', 'Jacks of All Trades')
add_action_card('Mandarin')
add_action_card('Margrave')
add_action_card('Noble Brigand')
add_action_card('Nomad Camp')
add_action_card('Oasis', 'Oases')
add_action_card('Oracle')
add_action_card('Scheme')
add_action_card('Spice Merchant')
add_action_card('Stables', 'Stables')
add_action_card('Trader')

# Victory Cards
add_victory_card('Gardens', 'Gardens')
add_victory_card('Duke')
add_victory_card('Vineyard')
add_victory_card('Fairgrounds', 'Fairgrounds')
add_victory_card('Farmland')
add_victory_card('Silk Road')

# Dual Victory Cards
add_victory_treasure_card('Harem')

add_victory_treasure_card('Nobles', 'Nobles')
add_victory_treasure_card('Great Hall')
add_victory_treasure_card('Island')
add_victory_treasure_card('Tunnel')

# Treasure Cards
add_treasure_card('Philosopher\'s Stone')
add_treasure_card('Contraband')
add_treasure_card('Bank')
add_treasure_card('Hoard')
add_treasure_card('Loan')
add_treasure_card('Quarry', 'Quarries')
add_treasure_card('Royal Seal')
add_treasure_card('Talisman')
add_treasure_card('Horn of Plenty', 'Horns of Plenty')
add_treasure_card('Cache')
add_treasure_card('Fool\'s Gold')
add_treasure_card('Ill-Gotten Gains', 'Ill-Gotten Gains')

# Basic Cards
add_treasure_card('Platinum')
add_treasure_card('Gold')
add_treasure_card('Silver')
add_treasure_card('Copper')
add_treasure_card('Potion')

add_victory_card('Colony', 'Colonies')
add_victory_card('Province')
add_victory_card('Duchy', 'Duchies')
add_victory_card('Estate')

add_curse_card('Curse')

# Promo Cards (I don't know if Stash is used, but the others are)
add_treasure_card('Stash')
add_action_card('Envoy', 'Envoys')
add_action_card('Governor')
add_action_card('Walled Village')
add_action_card('Black Market')

# Prize Cards
add_treasure_card('Diadem')
add_action_card('Bag of Gold')
add_action_card('Followers', 'Followers')
add_action_card('Princess', 'Princesses')
add_action_card('Trusty Steed')


# It would seem that isotropic doesn't have Dark Ages cards publicly available, so sadly, these cards
# will likely never be seen or trained...
if False:
    cards.add('Band Of Misfits')
    cards.add('Altar')
    cards.add('Armory')
    cards.add('Bandit Camp')
    cards.add('Beggar')
    cards.add('Catacombs')
    cards.add('Count')
    cards.add('Counterfeit')
    cards.add('Death Cart')
    cards.add('Feodum')
    cards.add('Forager')
    cards.add('Fortress')
    cards.add('Graverobber')
    cards.add('Hunting Grounds')
    cards.add('Ironmonger')
    cards.add('Junk Dealer')
    cards.add('Market Square')
    cards.add('Mystic')
    cards.add('Pillage')
    cards.add('Poor House')
    cards.add('Procession')
    cards.add('Rats')
    cards.add('Rebuild')
    cards.add('Rogue')
    cards.add('Sage')
    cards.add('Scavenger')
    cards.add('Squire')
    cards.add('Storeroom')
    cards.add('Wandering Minstrel')
    cards.add('Cultist')
    cards.add('Urchin')
    cards.add('Marauder')
    cards.add('Hermit')
    cards.add('Vagrant')
    
    cards.add('Necropolis')
    cards.add('Hovel')
    cards.add('Overgrown Estate')
    cards.add('Spoils')
    cards.add('Mercenary')
    cards.add('Madman')
    cards.add('Abandoned Mine')
    cards.add('Ruined Library')
    cards.add('Ruined Market')
    cards.add('Ruined Village')
    cards.add('Survivors')
    cards.add('Dame Anna')
    cards.add('Dame Josephine')
    cards.add('Dame Molly')
    cards.add('Dame Natalie')
    cards.add('Dame Sylvia')
    cards.add('Sir Bailey')
    cards.add('Sir Destry')
    cards.add('Sir Martin')
    cards.add('Sir Michael')
    cards.add('Sir Vander')

    #cards.add('VirtualKnight')
    #cards.add('VirtualRuins')
