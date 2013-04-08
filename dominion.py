import math

# This set stores all cards available in a game of dominion as strings
# The strings should be exact matches of the isotropic names
# But, it looks like some mechanism will need to be put in place to unpluralize names
cards = set()
# This maps the case insensitive, spacing and puctuation removed, card to the proper casing
clean_cards = {}
# This maps the card plurals to the singular
plural_cards = {}
pluralizer = {}

action_cards = set()
victory_cards = set()
treasure_cards = set()
curse_cards = set()
prize_cards = set()

plus_action_cards = set()
plus_buy_cards = set()
drawing_cards = set()
cursing_cards = set()
trashing_cards = set()
attack_cards = set()
supply_cards = set()
potion_cards = set()

victory_point_symbol = unichr(9660) # u"\u25BC"
potion_cost_symbol = unichr(9673) # u"\u25C9"

# This does not check plural cards - the card must be sanitized if its plural
def is_card(card):
    return card in cards

def clean_card(card):
    if card in cards:
        return card
    else:
        card = card.replace(' ', '').replace('-', '').replace("'", '').replace('_', '').lower()
        if card in clean_cards:
            return clean_cards[card]
        else:
            return None
    
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
        
def pluralize_card(card):
    if card in pluralizer:
        return pluralizer[card]
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
        # Should thi assert be ignored? Masquerade can cause unknown things to happen in the state.
        #assert False, 'Decrementing card pile that doesn\'t exist: {0}'.format(val)
        pass
    
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
        
def print_deck(deck):
    for card in deck.keys():
        print '{1} {0}(s)'.format(card, deck[card])
        
def compare_decks(expected, actual):
    ret = []
    # Make sure everything that was expected is there
    for (card, count) in expected.iteritems():
        if card not in actual:
            ret.append('{0}: Expected {1} Found None'.format(card, count))
        else:
            # The expected card was found in the actual deck, check counts
            if count != actual[card]:
                ret.append('{0}: Expected {1} Found {2}'.format(card, count, actual[card]))
    # Look for cards that are there that shouldn't be
    for (card, count) in actual.iteritems():
        if card not in expected and count != 0:
            ret.append('{0}: Unexpected {1}'.format(card, count))
    return ret
    
class DominionPlayer:
    
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.final_deck = {}
        # Piles are implemented as a dictionary from card names to how many of them are in the pile
        # Because drawing doesn't tell us exactly what they drew, this will now just hold the deck.
        self.deck = {}
        self.deck_backup = {}
        #self.discard_pile = {}
        #self.hand = {}
        # Duration cards, actions/money during turn, etc.
        #self.in_play = {}
        # Island, Haven, Native Villiage, etc.
        #self.out_of_play = {}
        ##self.cards_in_hand = 0
        self.vp = 0
        self.pirate_ship_tokens = 0
        
        self.output_weight = None
        self.action_card_count = 0
        self.victory_card_count = 0
        self.treasure_card_count = 0
        self.deck_size = 0
        self.current_score = 0
        
    def set_final_score(self, score):
        self.final_score = score
        
    def get_final_score(self):
        return self.final_score
        
    def add_final_deck(self, card):
        incr_value(self.final_deck, card)
        
    def check_deck(self):
        ret = []
        errors = compare_decks(self.final_deck, self.deck)
        if errors:
            ret.append('Mismatch in player deck: {0}'.format(self.name.encode('utf-8')))
            for error in errors:
                ret.append(' {0}'.format(error))
        return ret
        
    def set_output_weight(self, weight):
        self.output_weight = weight
        
    def get_output_weight(self):
        return self.output_weight
        
    def get_action_card_count(self):
        return self.action_card_count
        
    def get_victory_card_count(self):
        return self.victory_card_count
        
    def get_treasure_card_count(self):
        return self.treasure_card_count
        
    def get_deck_size(self):
        return self.deck_size
        
    def get_current_score(self):
        return self.current_score
        
    def update_properties(self):
        self.action_card_count = 0.0
        self.victory_card_count = 0.0
        self.treasure_card_count = 0.0
        self.deck_size = 0.0
        self.deck_backup.clear()
        for card in self.deck.keys():
            if self.deck[card] > 0:
                self.deck_backup[card] = self.deck[card]
            cards = self.deck[card]
            if is_action(card):
                self.action_card_count += cards
            if is_victory(card):
                self.victory_card_count += cards
            if is_treasure(card):
                self.treasure_card_count += cards
            self.deck_size += cards
        # Get the number of points in the deck
        self.current_score = self.vp
        for victory_card in victory_cards:
            if victory_card in self.deck_backup:
                self.current_score += self.deck[victory_card] * self.get_card_points(victory_card)
                
    # Assumes the current action, treasure, victory, etc. card counts cached are correct
    # Uses the deck backup to count specific cards.
    def get_card_points(self, card):
        if card == 'Estate':
            return 1
        elif card == 'Duchy':
            return 3
        elif card == 'Province':
            return 6
        elif card == 'Colony':
            return 10
        elif card == 'Gardens':
            return math.floor(self.deck_size / 10.0)
        elif card == 'Great Hall':
            return 1
        elif card == 'Duke':
            if 'Duchy' in self.deck_backup:
                return self.deck_backup['Duchy']
            else:
                return 0
        elif card == 'Harem':
            return 2
        elif card == 'Nobles':
            return 2
        elif card == 'Island':
            return 2
        elif card == 'Vineyard':
            return math.floor(self.action_card_count / 3.0)
        elif card == 'Fairgrounds':
            return math.floor(len(self.deck_backup.keys()) / 5.0)
        elif card == 'Silk Road':
            return math.floor(self.victory_card_count / 4.0)
        elif card == 'Farmland':
            return 2
        else:
            return 0
        
    def get_card_count(self, card):
        if card in self.deck_backup:
            return self.deck_backup[card]
        else:
            return 0
        
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
        
    def add_pirate_ship_token(self, tokens):
        self.pirate_ship_tokens += tokens
    
# This class stores information about the state of a game of dominion
class DominionGame:
    
    def __init__(self):
        self.supply = {}
        self.players = {}
        self.num_players = 0
        self.trash_pile = {}
        self.prizes = {}
        self.embargoes = {}
        
        self.final_trash = {}
        
        # Game meta-data
        self.empty_piles = []
        self.winner = None
        self.game_id = None
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.second = None
        self.masquerade_used = False
        
        # Turn context
        self.current_player = None
        self.possessor = None
        self.turn_number = 0
        self.money = 0
        self.actions = 1
        self.buys = 1
        self.cards_gained = []
        self.cards_bought = []
        self.last_player_to_gain = None # Used to store state for Watchtower
        self.last_card_gained = None # Used to store state for Watchtower
        self.copper_value = 1 # Coppersmith
        self.noble_brigand_thief_gain_pending = False
        #self.fools_gold_value = 1 # Fool's Gold
        self.prohibited = [] # Prohibited cards (Contraband)
        self.cost_reduction = 0
        self.revealed = []
        self.last_reveal_player = None # Used by Saboteur
        
    def set_timestamp(self, year, month, day, hour, minute, second):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        
    # Game Initialization functions
    # -----------------------------
    
    def add_player(self, player):
        self.players[player] = DominionPlayer(self, player)
        self.num_players = len(self.players)
        
    def set_final_score(self, player, score):
        player = self.get_player(player)
        if player:
            player.set_final_score(score)
            
    def add_final_deck(self, card, player):
        assert_card(card)
        player = self.get_player(player)
        if player:
            player.add_final_deck(card)
        
    def add_final_trash(self, card):
        assert_card(card)
        incr_value(self.final_trash, card)
        
    def get_average_final_score(self):
        total = 0.0
        for p in self.players.values():
            total += p.get_final_score()
        average = total / self.num_players
        return average
        
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
            difference = (player.get_final_score() - average)
            weight = (1 if difference >= 0 else -1) * (difference * difference) / (average if average != 0 else 1)
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
            self.supply[card] = self.card_initial_supply(card)
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
        # Reset the embargoes
        self.embargoes = {}
        
    def validate_final_state(self):
        # Masquerade does strange, unknowable things to the game's state. Just assume that 
        if not self.masquerade_used:
            ret = []
            # Validate that the empty piles are empty
            # Note that this can't check the non-empty piles.
            for card in self.empty_piles:
                if self.supply[card] != 0:
                    ret.append('Mismatch: {0} supply pile should be empty - has {1} left'.format(card, self.supply[card]))
            # Validate the trash
            errors = compare_decks(self.final_trash, self.trash_pile)
            if errors:
                ret.append('Mismatch in trash pile')
                for error in errors:
                    ret.append(' {0}'.format(error))
            # Validate each players final deck
            for (name, player) in self.players.iteritems():
                errors = player.check_deck()
                for error in errors:
                    ret.append(error)
            return ret
        else:
            return None
                
    # Game state manipulation functions
    # ---------------------------------
    
    # Turn context modifiers
    # ----
    
    # Resets all the turn context variables
    def start_new_turn(self, player, turn_number = None, possessor = None, increment_turn = False):
        self.current_player = player
        self.possessor = possessor
        # If the turn number is None, then we don't modify it. We leave it what it was before.
        if turn_number is not None:
            self.turn_number = turn_number
        elif increment_turn:
            self.turn_number += 1
            
        # Update the counts in the current players deck
        self.get_player().update_properties()
        if self.possessor:
            self.get_player(self.possessor).update_properties()
        
        self.money = 0 # Current money
        self.actions = 1
        self.buys = 1
        
        del self.cards_gained[:]
        del self.cards_bought[:]
        self.last_player_to_gain = None
        self.last_card_gained = None
        
        self.copper_value = 1 # Coppersmith
        #self.fools_gold_value = 1 # Fool's Gold (must be updated when a treasure card is 'played')
        self.cost_reduction = 0 # Bridge, Princess, Highway
        del self.prohibited[:]
        
        self.reset_revealed()
    
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
    
    def set_copper_value(self, value = 1):
        self.copper_value = value
        
    def prohibit(self, card):
        assert_card(card)
        self.prohibited.append(card)
    
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
        # Remember when Noble Brigand is played for gain redirection from trash
        self.noble_brigand_thief_gain_pending = (card == 'Noble Brigand' or card == 'Thief')
        
    def buy(self, card, player = None, source = 'supply'):
        assert_card(card)
        # TODO: Should this decrement the available money based on the cost of the card bought?
        self.cards_bought.append(card)
        if self.possessor and self.get_player() is self.get_player(player):
            # Possessed players can't buy anything
            # The possessor will gain the card on the next line.
            return
        self.gain(card, player, source)
        # Noble brigand's effect occurs on buy as well, so it might be pending after a buy too.
        self.noble_brigand_thief_gain_pending = (card == 'Noble Brigand' or card == 'Thief')
    
    # Gives a card from the supply to a player
    def gain(self, card, player = None, source = 'supply', end_of_possession = False):
        assert_card(card)
        # If someone gets a Masquerade, then remember it, as it means we can't validate the final game state.
        if card == 'Masquerade':
            self.masquerade_used = True
        current = True # Assume the player gaining is the current controlling player (possessor in possession turns)
        # If there was a border village played, the player that gained the border village should gain the new card.
        if self.last_card_gained == 'Border Village':
            player = self.last_player_to_gain
        if self.current_player: # If the game's started
            if self.get_player() is self.get_player(player):
                self.cards_gained.append(card)
                self.last_player_to_gain = player # Remember the current player as the other player
                self.last_card_gained = card
            else:
                # Another player gained a card.
                # Store the most recent gained card here for Watchtower (to trash it)
                self.last_player_to_gain = self.get_player(player)
                self.last_card_gained = card
                current = False
        # The 'current' player can't gain anything while being possessed, except at the end of their turn, when they gain back any cards that were trashed during the turn.
        if self.possessor and current and not end_of_possession:
            return
        # Check the source of the card to be gained
        if source == 'trash':
            # If this is a Noble Brigand or Thief, then this is indeed the trash.
            # However, Possession causes this to be called too (they are seemingly indistinguishable except by looking at the state)
            # So, when there is a possessing player, any gains will be automatically redirected.
            if self.noble_brigand_thief_gain_pending:
                decr_value(self.trash_pile, card)
            else:
                if not end_of_possession:
                    # This is the possession case.
                    decr_value(self.supply, card)
                else:
                    # This is a card being discarded at the end of a possession turn, so it was already trashed, and should now be moved back to the players deck who lost it.
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
        # If a watchtower was revealed just before this,
        if player is None and len(self.revealed) == 1 and self.revealed[0] == 'Watchtower':
            # The card being trashed should match the card that was being gained before
            # This assert is skipped because if multiple cards are gained at once and both are watchtowered (e.g., Copper and Curse from Mountebank), this would fail.
            #assert self.last_card_gained == card, "Redirecting trashing a {0} to player '{1}' after Watchtower: Expected {2}".format(card, self.get_player(self.last_player_to_gain).name, self.last_card_gained)
            # Then this card should be trashed by another player
            player = self.last_player_to_gain
        incr_value(self.trash_pile, card)
        # Cards trashed by possession are returned to the players deck at the end of their turn
        self.get_player(player).trash(card)
        
    def add_vp(self, vp = 1, player = None):
        self.get_player(player).add_vp(vp)
        
    def add_pirate_ship_token(self, tokens = 1, player = None):
        self.get_player(player).add_pirate_ship_token(tokens)
        
    def embargo(self, card):
        incr_value(self.embargoes, card)
        
    def reset_revealed(self):
        self.revealed = []
        self.last_reveal_player = None
        
    # Used by Ambassador to return a card from a player's deck to the supply
    def return_to_supply(self, card, player = None, trader = False):
        assert_card(card)
        # If this is a trader, and there was no line showing that the card being returned was actually gained just before this, then don't return it.
        # Trader has this problem when combined with Ill-Gotten Gains' free Copper.
        # But, to prevent the case of Mountebank's two consequtive gains, additionally check to see if the player returning a card isn't the same as the current player
        if self.last_card_gained != card and self.get_player() is self.get_player(player) and trader:
            return
        self.get_player(player).trash(card)
        incr_value(self.supply, card)
        
    def reveal(self, card, player):
        assert_card(card)
        self.revealed.append(card)
        self.last_reveal_player = player
                
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
        
    def get_last_reveal_player(self):
        return self.last_reveal_player
        
    def get_cards_bought(self):
        return self.cards_bought
        
    def get_cards_in_supply(self):
        return self.supply.keys()
            
    def is_card_in_supply(self, card):
        return card in self.supply.keys()
        
    def get_supply_count(self, card, use_initial_value = False):
        if card in self.supply.keys():
            return self.supply[card]
        else:
            if use_initial_value:
                return self.victory_card_initial_supply(card)
            else:
                return None
                
    def get_card_acquired_count(self, card):
        if card in self.supply.keys():
            initial_supply = self.card_initial_supply(card)
            # Estates and Copper start lower, so factor that in
            if card == 'Estate':
                initial_supply -= 3 * self.num_players
            elif card == 'Copper':
                initial_supply -= 7 * self.num_players
            return initial_supply - self.supply[card]
        else:
            # If the card isn't in the supply, then don't count it as being acquired
            # (This doesn't deal super well with Black Market, but that should be fine)
            return 0
                
    def supply_contains_any(self, cards):
        for card in self.supply.keys():
            if card in cards:
                return True
        return False
        
    def get_num_empty_piles(self):
        total = 0
        for count in self.supply.values():
            if count == 0:
                total += 1
        return total
        
    def get_revealed(self):
        return self.revealed
    
    def card_initial_supply(self, card):
        if is_victory(card):
            return self.victory_card_initial_supply(card)
        elif is_curse(card):
            return self.curse_card_initial_supply()
        elif is_treasure(card):
            return self.treasure_card_initial_supply(card)
        else:
            # All other cards start with 10 in the supply (except some from Dark Ages, but those aren't supported)
            return 10
    
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
        # Fool's Gold has a +$n line following it.
        #elif card == 'Fool\'s Gold':
        #    return self.fools_gold_value
        elif card == 'Ill-Gotten Gains':
            return 1
        elif card == 'Diadem':
            return 2
        elif card == 'Stash':
            return 2
        # There are other treasure cards, but they have variable values, so there should be a +$x line following them
        else:
            return 0
            
def add_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=True, potion=False):
    cards.add(card)
    clean_cards[card.replace(' ', '').replace('-', '').replace("'", '').replace('_', '').lower()] = card
    if plural is None:
        # By default, the plural of a card is just an 's' added to the end
        plural = card + 's'
    plural_cards[plural] = card
    pluralizer[card] = plural
    if actions:
        plus_action_cards.add(card)
    if buys:
        plus_buy_cards.add(card)
    if draws:
        drawing_cards.add(card)
    if curse:
        cursing_cards.add(card)
    if trash:
        trashing_cards.add(card)
    if attack:
        attack_cards.add(card)
    if supply:
        supply_cards.add(card)
    if potion:
        potion_cards.add(card)

def add_action_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=True, potion=False):
    action_cards.add(card)
    add_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)

def add_victory_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=True, potion=False):
    victory_cards.add(card)
    add_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)
    
def add_treasure_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=True, potion=False):
    treasure_cards.add(card)
    add_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)

def add_curse_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=True, potion=False):
    curse_cards.add(card)
    add_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)

def add_victory_treasure_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=True, potion=False):
    victory_cards.add(card)
    treasure_cards.add(card)
    add_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)
    
def add_victory_action_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=True, potion=False):
    victory_cards.add(card)
    action_cards.add(card)
    add_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)
    
def add_treasure_prize_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=False, potion=False):
    prize_cards.add(card)
    add_treasure_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)
    
def add_action_prize_card(card, plural = None, actions=False, buys=False, draws=False, curse=False, trash=False, attack=False, supply=False, potion=False):
    prize_cards.add(card)
    add_action_card(card, plural, actions, buys, draws, curse, trash, attack, supply, potion)

# Base
add_action_card('Adventurer')
add_action_card('Bureaucrat', attack=True)
add_action_card('Cellar', draws=True)
add_action_card('Chancellor')
add_action_card('Chapel', trash=True)
add_action_card('Council Room', draws=True, buys=True)
add_action_card('Feast')
add_action_card('Festival', actions=True, buys=True)
add_victory_card('Gardens', 'Gardens')
add_action_card('Laboratory', 'Laboratories', draws=True)
add_action_card('Library', 'Libraries', draws=True)
add_action_card('Market', buys=True)
add_action_card('Militia', attack=True)
add_action_card('Mine')
add_action_card('Moat', draws=True)
add_action_card('Moneylender')
add_action_card('Remodel', trash=True)
add_action_card('Smithy', 'Smithies', draws=True)
add_action_card('Spy', 'Spies', attack=True)
add_action_card('Thief', 'Thieves', attack=True)
add_action_card('Throne Room', actions=True, draws=True) # Not quite sure on this one, but Throne Room combined with lots of other cards can give you extra actions and draws, so I'll count it. Better to round up.
add_action_card('Village', actions=True)
add_action_card('Witch', 'Witches', draws=True, attack=True, curse=True)
add_action_card('Woodcutter', buys=True)
add_action_card('Workshop')

# Intrigue
add_action_card('Baron', buys=True)
add_action_card('Bridge', buys=True)
add_action_card('Conspirator')
add_action_card('Coppersmith')
add_action_card('Courtyard', draws=True)
add_victory_card('Duke')
add_victory_action_card('Great Hall')
add_victory_treasure_card('Harem')
add_action_card('Ironworks', 'Ironworks')
add_action_card('Masquerade', draws=True)
add_action_card('Mining Village', actions=True)
add_action_card('Minion', draws=True, attack=True)
add_victory_action_card('Nobles', 'Nobles', actions=True, draws=True)
add_action_card('Pawn', buys=True)
add_action_card('Saboteur', attack=True)
add_action_card('Scout')
add_action_card('Secret Chamber')
add_action_card('Shanty Town', actions=True, draws=True)
add_action_card('Steward', draws=True, trash=True)
add_action_card('Swindler', attack=True, curse=True) # Swindling Coppers can make you gain Curses, so this counts.
add_action_card('Torturer', draws=True, attack=True, curse=True)
add_action_card('Trading Post', trash=True)
add_action_card('Tribute', actions=True, draws=True)
add_action_card('Upgrade', trash=True)
add_action_card('Wishing Well', draws=True) # On this and cards like it, if it has the potential to give you more cards or actions than it took to play it, it counts as giving actions or draws. Chaining cards (Scout, Upgrade, etc.) don't count, as they don't let you have more than a single action or increase the size of your hand.

# Seaside
add_action_card('Ambassador', attack=True, trash=True) # Not quite truly trashing...but essentially the same idea. It gets cards out of your deck.
add_action_card('Bazaar', actions=True)
add_action_card('Caravan', draws=True)
add_action_card('Cutpurse', attack=True)
add_action_card('Embargo', 'Embargoes')
add_action_card('Explorer')
add_action_card('Fishing Village', actions=True)
add_action_card('Ghost Ship', draws=True, attack=True)
add_action_card('Haven')
add_victory_action_card('Island')
add_action_card('Lighthouse')
add_action_card('Lookout', trash=True)
add_action_card('Merchant Ship')
add_action_card('Native Village', actions=True, draws=True)
add_action_card('Navigator')
add_action_card('Outpost')
add_action_card('Pearl Diver')
add_action_card('Pirate Ship', attack=True)
add_action_card('Salvager', buys=True, trash=True)
add_action_card('Sea Hag', attack=True, curse=True)
add_action_card('Smugglers', 'Smugglers')
add_action_card('Tactician', actions=True, buys=True, draws=True)
add_action_card('Treasure Map')
add_action_card('Treasury', 'Treasuries')
add_action_card('Warehouse', draws=True) # This doesn't let you have more cards in your hand, but it does let you draw and then choose what to discard, so it counts.
add_action_card('Wharf', 'Wharves', draws=True, buys=True)

# Alchemy
add_action_card('Alchemist', draws=True, potion=True)
add_action_card('Apothecary', 'Apothecaries', potion=True)
add_action_card('Apprentice', draws=True, trash=True)
add_action_card('Familiar', attack=True, curse=True, potion=True)
add_action_card('Golem', actions=True, potion=True) # It lets you play multiple actions in a single turn, so....I think I'll try counting this here.
add_action_card('Herbalist')
add_treasure_card('Philosopher\'s Stone', potion=True)
add_action_card('Possession', potion=True)
add_action_card('Scrying Pool', draws=True, attack=True, potion=True)
add_action_card('Transmute', trash=True, potion=True)
add_action_card('University', 'Universities', actions=True, potion=True)
add_victory_card('Vineyard', potion=True)

# Prosperity
add_treasure_card('Bank')
add_action_card('Bishop', trash=True)
add_action_card('City', 'Cities', actions=True, draws=True)
add_treasure_card('Contraband', buys=True)
add_action_card('Counting House')
add_action_card('Expand', trash=True)
add_action_card('Forge', trash=True)
add_action_card('Goons', 'Goons', buys=True, attack=True)
add_action_card('Grand Market', buys=True)
add_treasure_card('Hoard')
add_action_card('King\'s Court', actions=True, draws=True) # See my justification for Throne Room for this classification. Combining with +Actions and +Cards cards causes this to give both of them, so I'll count this here to be safe.
add_treasure_card('Loan')
add_action_card('Mint')
add_action_card('Monument')
add_action_card('Mountebank', attack=True, curse=True)
add_action_card('Peddler')
add_treasure_card('Quarry', 'Quarries')
add_action_card('Rabble', draws=True, attack=True)
add_treasure_card('Royal Seal')
add_treasure_card('Talisman')
add_action_card('Trade Route', buys=True, trash=True)
add_action_card('Vault', draws=True)
add_action_card('Venture')
add_action_card('Watchtower', draws=True)
add_action_card('Worker\'s Village', actions=True)

# Cornucopia
add_victory_card('Fairgrounds', 'Fairgrounds')
add_action_card('Farming Village', actions=True)
add_action_card('Fortune Teller', attack=True)
add_action_card('Hamlet', actions=True, buys=True)
add_action_card('Harvest')
add_treasure_card('Horn of Plenty', 'Horns of Plenty')
add_action_card('Horse Traders', 'Horse Traders', buys=True)
add_action_card('Hunting Party', 'Hunting Parties', draws=True)
add_action_card('Jester', trash=True, curse=True)
add_action_card('Menagerie', draws=True)
add_action_card('Remake', trash=True)
add_action_card('Tournament') # But at the same time...they aren't common in the supply, so I'll pass here...., actions=True, draws=True, buys=True, attack=True, curse=True) # This is because of the prizes that tournament brings with it. It isn't an attack or anything, but its presence in the supply indicates that these things can appear.
add_action_card('Young Witch', 'Young Witches', draws=True, attack=True, curse=True)
# Prize Cards
add_action_prize_card('Bag of Gold')
add_treasure_prize_card('Diadem')
add_action_prize_card('Followers', 'Followers', draws=True, attack=True, curse=True)
add_action_prize_card('Princess', 'Princesses', buys=True)
add_action_prize_card('Trusty Steed', draws=True, actions=True)

# Hinterlands
add_action_card('Border Village', actions=True)
add_treasure_card('Cache')
add_action_card('Cartographer')
add_action_card('Crossroads', 'Crossroads', actions=True, draws=True)
add_action_card('Develop', trash=True)
add_action_card('Duchess', 'Duchesses')
add_action_card('Embassy', 'Embassies', draws=True)
add_victory_card('Farmland', trash=True)
add_treasure_card('Fool\'s Gold')
add_action_card('Haggler')
add_action_card('Highway', 'Highways')
add_treasure_card('Ill-Gotten Gains', 'Ill-Gotten Gains', curse=True)
add_action_card('Inn', actions=True, draws=True)
add_action_card('Jack of All Trades', 'Jacks of All Trades', draws=True, trash=True)
add_action_card('Mandarin')
add_action_card('Margrave', draws=True, buys=True, attack=True)
add_action_card('Noble Brigand', attack=True)
add_action_card('Nomad Camp', buys=True)
add_action_card('Oasis', 'Oases')
add_action_card('Oracle', draws=True, attack=True)
add_action_card('Scheme')
add_victory_card('Silk Road')
add_action_card('Spice Merchant', draws=True, buys=True)
add_action_card('Stables', 'Stables', draws=True)
add_action_card('Trader', trash=True)
add_victory_action_card('Tunnel')

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
add_treasure_card('Stash', 'Stashes')
add_action_card('Envoy', 'Envoys', draws=True)
add_action_card('Governor', draws=True, trash=True)
add_action_card('Walled Village', actions=True)
add_action_card('Black Market')


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
