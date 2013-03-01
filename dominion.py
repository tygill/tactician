
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
prize_cards = set()

victory_point_symbol = unichr(9660)

def get_victory_symbol():
    return victory_point_symbol

# This does not check plural cards - the card must be sanitized if its plural
def is_card(card):
    return card in cards
    
def assert_card(card):
    assert is_card(card), "invalid card: {0}".format(card)
        
# Converts plural cards to singular, and returns None if the card is not valid
# This should be called by the parser before passing cards in
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
        assert False, 'Decrementing card pile that doesn\'t exist: {0}'.format(val)
    
def move_card(a, b, card):
    decr_value(a, card)
    incr_value(b, card)
    
# Moves all cards from a to b
def move_cards(a, b):
    for key in a.keys():
        if key in b:
            b[key] += a[key]
        else:
            b[key] = a[key]
        a[key] = 0
    
class dominion_player:
    
    def __init__(self, game, name):
        self.game = game
        self.name = name
        # Piles are implemented as a dictionary from card names to how many of them are in the pile
        # Because drawing doesn't tell us exactly what they drew, this will now just hold the deck.
        self.deck = {}
        #self.discard_pile = {}
        #self.hand = {}
        # Duration cards, actions/money during turn, etc.
        #self.in_play = {}
        # Island, Haven, Native Villiage, etc.
        #self.out_of_play = {}
        ##self.cards_in_hand = 0
        self.vp = 0
        self.output_weight = None
        self.action_card_ratio = 0
        self.victory_card_ratio = 0
        self.treasure_card_ratio = 0
        
    def set_final_score(self, score):
        self.final_score = score
        
    def get_final_score(self):
        return self.final_score
        
    def set_output_weight(self, weight):
        self.output_weight = weight
        
    def get_output_weight(self):
        return self.output_weight
        
    def get_action_card_ratio(self):
        return self.action_card_ratio
        
    def get_victory_card_ratio(self):
        return self.victory_card_ratio
        
    def get_treasure_card_ratio(self):
        return self.treasure_card_ratio
        
    def update_ratios(self):
        actions = 0.0
        victories = 0.0
        treasures = 0.0
        total = 0.0
        for card in self.deck.keys():
            cards = self.deck[card]
            if is_action(card):
                actions += cards
            if is_victory(card):
                victories += cards
            if is_treasure(card):
                treasures += cards
            total += cards
        self.action_card_ratio = actions / total
        self.victory_card_ratio = victories / total
        self.treasure_card_ratio = treasures / total
        
    # Game State Modifiers
    
    def reshuffle(self):
        #move_cards(self.discard_pile, self.deck)
        pass
    
    def draw(self, card = None):
        # Attempt to automatically reshuffle if things aren't quite in sync
        # This will mean that the discard pile is not truly what it is, but it should be close enough
        # for current purposes.
        # TODO: If we choose to include a 'cards in discard pile' or similar feature, this can be made better.
        #if self.deck[card] == 0:
        #    self.reshuffle()
        #move_card(self.deck, self.hand, card)
        ##if card is None or isinstance(card, basestring):
        ##    cards = 1
        ##else:
        ##    cards = card
        ##self.cards_in_hand += cards
        pass
        
    def discard(self, card = None):
        #move_card(self.hand, self.discard_pile, card)
        ##if card is None or isinstance(card, basestring):
        ##    cards = 1
        ##else:
        ##    cards = card
        ##self.cards_in_hand -= cards
        pass
        
    def cleanup(self):
        #move_cards(self.in_play, self.discard_pile) # Yes, this moves duration cards as well, but for out purposes this is fine.
        #move_cards(self.hand, self.discard_pile)
        ##self.cards_in_hand = 0
        pass
        
    def play(self, card):
        #move_card(self.hand, self.in_play, card)
        ##self.cards_in_hand -= 1
        pass
        
    def gain(self, card):
        #incr_value(self.discard_pile, card)
        incr_value(self.deck, card)
        
    def trash(self, card):
        decr_value(self.deck, card)
        
    def add_vp(self, vp):
        self.vp += vp
    
# This class stores information about the state of a game of dominion
class dominion_game:
    
    def __init__(self):
        self.supply = {}
        self.players = {}
        self.num_players = 0
        self.trash_pile = {}
        self.prizes = {}
        
        # Game meta-data
        self.empty_piles = []
        self.winner = None
        self.game_id = None
        
        # Turn context
        self.current_player = None
        self.turn_number = 0
        self.money = 0
        self.actions = 1
        self.buys = 1
        self.cards_gained = []
        self.cards_bought = []
        self.copper_value = 1 # Coppersmith
        self.fools_gold_value = 1 # Fool's Gold
        self.cost_reduction = 0
        
    # Game Initialization functions
    # -----------------------------
    
    def add_player(self, player):
        self.players[player] = dominion_player(self, player)
        self.num_players = len(self.players)
        
    def set_final_score(self, player, score):
        player = self.get_player(player)
        if player:
            player.set_final_score(score)
        
    # This calculates the score ratio for each player for the game
    def calc_output_weight(self, player = None):
        player = self.get_player(player)
        if player.get_output_weight():
            return player.get_output_weight()
        else:
            total = 0.0
            for p in self.players.values():
                total += p.get_final_score()
            average = total / self.num_players
            weight = (player.get_final_score() - average) / average
            player.set_output_weight(weight)
            return weight
            
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
        # Initialize the players starting decks
        for player in self.players.values():
            for i in range(7):
                self.gain('Copper', player)
            for i in range(3):
                self.gain('Estate', player)
            player.reshuffle()
        # Initialize the prizes (even if Tournament isn't in play. It might be in the Black Market deck or something. No harm in setting it up.)
        for card in prize_cards:
            self.prizes[card] = 1
                
                
    # Game state manipulation functions
    # ---------------------------------
    
    # Turn context modifiers
    # ----
    
    # Resets all the turn context variables
    def start_new_turn(self, player, turn_number = None):
        self.current_player = player
        # If the turn number is None, then we don't modify it. We leave it what it was before.
        if turn_number is not None:
            self.turn_number = turn_number
            
        # Update the ratios in the current players deck
        self.get_player().update_ratios()
        
        self.money = 0 # Current money
        self.actions = 1
        self.buys = 1
        
        del self.cards_gained[:]
        del self.cards_bought[:]
        
        self.copper_value = 1 # Coppersmith
        self.fools_gold_value = 1 # Fool's Gold (must be updated when a treasure card is 'played')
        self.cost_reduction = 0 # Bridge, Princess, Highway
    
    # This should not be used for treasure cards with non-variable values (e.g., Copper, Quarry, etc.)
    # Treasure cards with variable costs should use this (e.g., Bank, Philosopher's Stone)
    def add_money(self, money):
        self.money += money
        
    def add_actions(self, actions = 1):
        self.actions += actions
        
    def add_buys(self, buys = 1):
        self.buys += buys
        
    def reduce_cost(self, cost = 1):
        self.cost_reduction += cost
    
    # Game Modifiers
    # ----
    
    def reshuffle(self, player = None):
        self.get_player(player).reshuffle()
    
    # Moves a card from a players deck to their hand (this may not be necessary...)
    # Draw and discard can accept either:
    #  None (implies a single card)
    #  string (name of a type of card)
    #  int (number of cards to draw - unknown what they are)
    def draw(self, card = None, player = None):
        if isinstance(card, basestring):
            assert_card(card)
        self.get_player(player).draw(card)
            
    def discard(self, card = None, player = None):
        if isinstance(card, basestring):
            assert_card(card)
        self.get_player(player).discard(card)
        
    def cleanup(self):
        self.get_player().cleanup()
        
    def play(self, card):
        assert_card(card)
        self.get_player().play(card)
        # If the card isn't a treasure, this will return 0, so this is safe for any card played.
        # At some point, some things might need to be processed here, but I don't know for sure now.
        # We'll see how the logs look.
        self.money += self.treasure_card_value(card)
        
    def buy(self, card, player = None, source = 'supply'):
        assert_card(card)
        # TODO: Should this decrement the available money based on the cost of the card bought?
        self.cards_bought.append(card)
        self.gain(card)
    
    # Gives a card from the supply to a player
    def gain(self, card, player = None, source = 'supply'):
        assert_card(card)
        self.cards_gained.append(card)
        if source == 'trash':
            decr_value(self.trash_pile, card)
        elif source == 'prizes':
            decr_value(self.prizes, card)
        else:
            # If this card is not in the supply it must be from the black market deck
            if card in self.supply.keys():
                decr_value(self.supply, card)
            else:
                assert 'Black Market' in self.supply.keys(), "Gaining card from 'supply' which is not in the supply, and Black Market is not in the supply."
        self.get_player(player).gain(card)
        
    def trash(self, card, player = None):
        assert_card(card)
        incr_value(self.trash_pile, card)
        self.get_player(player).trash(card)
        
    def add_vp(self, vp = 1, player = None):
        self.get_player(player).add_vp(vp)
                
    # Utility methods
    # ---------------
    
    def get_players(self):
        return self.players.keys()
    
    def get_player(self, player = None):
        if player is None:
            return self.players[self.current_player]
        elif isinstance(player, basestring):
            return self.players[player]
        else:
            # Otherwise, assume its the actual player object
            return player
            
    def get_num_players(self):
        return self.num_players
        
    def get_cards_bought(self):
        return self.cards_bought
            
    def is_card_in_supply(self, card):
        return card in self.supply.keys()
    
    # Depending on the number of players, the victory card piles start with different sizes
    def victory_card_initial_supply(self, card):
        if card == 'Province':
            if self.num_players == 2:
                return 8
            elif self.num_players == 3 or self.num_players == 4:
                return 12
            # As per Intrigue's instructions, there are more Provinces in 5 and 6 player games.
            # Other victory cards are unaffected.
            elif self.num_players == 5:
                return 15
            elif self.num_players == 6:
                return 18
            # It appears isotropic supports up to 8 players, and it just uses 21 provinces
            else:
                return 21
        
        # Estates need to have enough cards to give each player 3, and still have 8 or 12 left
        if card == 'Estate':
            if self.num_players == 2:
                return 8 + 6
            else:
                return 12 + self.num_players * 3
        
        if self.num_players == 2:
            return 8
        else:
            return 12
        
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
                
    def treasure_card_value(self, card):
        if card == 'Copper':
            return self.copper_value
        elif card == 'Silver':
            return 2
        elif card == 'Gold':
            return 3
        elif card == 'Platinum':
            return 5
        elif card == 'Harem':
            return 2
        elif card == 'Contraband':
            return 3
        elif card == 'Hoard':
            return 2
        elif card == 'Loan':
            return 1
        elif card == 'Quarry':
            return 1
        elif card == 'Royal Seal':
            return 2
        elif card == 'Talisman':
            return 1
        elif card == 'Cache':
            return 3
        elif card == 'Fool\'s Gold':
            return self.fools_gold_value
        elif card == 'Ill-Gotten Gains':
            return 1
        elif card == 'Diadem':
            return 2
        elif card == 'Stash':
            return 2
        # There are other treasure cards, but they have variable values, so there should be a +$x line following them
        else:
            return 0
            
def add_card(card, plural = None):
    cards.add(card)
    if plural is None:
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
    
def add_treasure_prize_card(card, plural = None):
    prize_cards.add(card)
    add_treasure_card(card)
    
def add_action_prize_card(card, plural = None):
    prize_cards.add(card)
    add_action_card(card)

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
add_action_card('Spy', 'Spies')
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

add_victory_action_card('Nobles', 'Nobles')
add_victory_action_card('Great Hall')
add_victory_action_card('Island')
add_victory_action_card('Tunnel')

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
add_treasure_prize_card('Diadem')
add_action_prize_card('Bag of Gold')
add_action_prize_card('Followers', 'Followers')
add_action_prize_card('Princess', 'Princesses')
add_action_prize_card('Trusty Steed')


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
