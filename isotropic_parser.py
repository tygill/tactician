from dominion import *
import re

# General Purpose

# Designed to be used with finditer().
# Extracts a card name from its typical <span> wrapper
# Extracts:
#  card: Name of card (Note: might be plural!)
card_regex = re.compile('<[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>')
# Designed to be used with finditer().
# Extracts a card name from its typical <span> wrapper, with a preceeding quantitiy
# Extracts:
#  card: Name of card (Note: might be plural!)
#  count: Number prefixing card (Note that it might be a or an as well as a number)
card_count_regex = re.compile('(?:(?P<count>[an\d]+) )?<[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>')


# Specific Regexes
# ----------------

# Header

# Matches: First line of the document
#  game_id: The id of the game
#  winner: player who won the game
first_line_regex = re.compile(r'<html><head><link rel="stylesheet" href="/semistatic/log\.css"><title>Dominion Game #(?P<game_id>\d+)</title></head><body><pre>(?P<winner>.+) wins!')

# Player info

# Matches: Player lines in the second section of the log
#  place: Rank in game
#  player: Name of player
#  score: Players final score
#  cards: List of cards and counts (can be extraced with card_count_regex)
#  turns: Number of turns the player had
player_first_line_regex = re.compile(r'<b>#(?P<place>\d) (?P<player>.+)</b>: (?P<score>[\d\-]+) points \((?P<cards>.+)\); (?P<turns>\d+) turns')
# Matches: (admittedly, card_regex could just be run on the whole line with the same result...)
#  cards: List of cards bought on the openning turns (card_regex can pull them out)
player_second_line_regex = re.compile(r'\s*opening: (?P<cards>)')
#  deck_size: Number of cards in deck (total)
#  cards: List of cards and counts in deck
player_third_line_regex = re.compile(r'\s*\[(?P<deck_size>\d+) cards?\] (?P<cards>.*)')

# Game log

# These regexes pull out the turn orderings for each different number of players.
# Making a single regex that combined all of these proved too much.
#  first, second, third, fourth, fifth, sixth, seventh, eighth: Player orders
# 2p
turn_order_2p_regex = re.compile(r'Turn order is (?P<first>.*) and then (?P<second>.*)\.')
# 3p
turn_order_3p_regex = re.compile(r'Turn order is (?P<first>.*), (?P<second>.*), and then (?P<third>.*)\.')
# 4p
turn_order_4p_regex = re.compile(r'Turn order is (?P<first>.*), (?P<second>.*), (?P<third>.*), and then (?P<fourth>.*)\.')
# 5p
turn_order_5p_regex = re.compile(r'Turn order is (?P<first>.*), (?P<second>.*), (?P<third>.*), (?P<fourth>.*), and then (?P<fifth>.*)\.')
# 6p
turn_order_6p_regex = re.compile(r'Turn order is (?P<first>.*), (?P<second>.*), (?P<third>.*), (?P<fourth>.*), (?P<fifth>.*), and then (?P<sixth>.*)\.')
# 7p
turn_order_7p_regex = re.compile(r'Turn order is (?P<first>.*), (?P<second>.*), (?P<third>.*), (?P<fourth>.*), (?P<fifth>.*), (?P<sixth>.*), and then (?P<seventh>.*)\.')
# 8p
turn_order_8p_regex = re.compile(r'Turn order is (?P<first>.*), (?P<second>.*), (?P<third>.*), (?P<fourth>.*), (?P<fifth>.*), (?P<sixth>.*), (?P<seventh>.*), and then (?P<eighth>.*)\.')
#turn_order_regex = re.compile(r'Turn order is (?P<first>.*),? (?:and then )?(?P<second>.*)(?:,? (?:and then )?(?P<third>.*))?(?:,? (?:and then )?(?P<fourth>.*))?(?:,? (?:and then )?(?P<fifth>.*))?(?:,? (?:and then )?(?P<sixth>.*))?(?:,? (?:and then )?(?P<seventh>.*))?(?:,? (?:and then )?(?P<eighth>.*))?')

# Game Regexes
# ------------

# Turn header extraction (for regular, possessed, and outpost turns)
#  player: Player name whose turn it now is
#  turn: Turn number
turn_header_regex = re.compile('\\s*&mdash; (?P<player>.*)\'s turn (?P<turn>\\d+) &mdash;')
#  possessee: Player whose hand is being possessed
#  possessor: Player doing the possessing
possessed_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w]+\\?s=40&d=identicon&r=PG" width=40 height=40 class=avatar><b>&mdash; (?P<possessee>.*)\'s turn \\(possessed by (?P<possessor>.*)\\) &mdash;</b>')
#  player: Player who got an extra turn
outpost_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w]+\\?s=40&d=identicon&r=PG" width=40 height=40 class=avatar><b>&mdash; (?P<player>.*)\'s extra turn \\(from <span class=card-duration>Outpost</span>\\) &mdash;</b>')

# Matches: (<player> draws: <cards>)
#  player: Player who drew
#  cards: List of cards drawn (extract with card_count_regex)
draw_hand_regex = re.compile('\\s*<span class=logonly>\\((?P<player>.*)(?:\'s first hand| draws): (?P<cards>.*)\\.\\)</span>')

# Matches: <player> plays <cards>.
#  player: Player who played the cards
#  cards: List of cards played (may be multiple, especially for treasures, both in quantity and type. e.g., 2 Coppers and a Silver)
play_cards_regex = re.compile(r'\s*(?P<player>.*) plays (?P<cards>.*)\.')

# Matches: <player> buys a <card>.
#  player: Player who played the cards
#  card: Card purchased
buy_card_regex = re.compile('\\s*(?P<player>.*) buys a <[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>\\.')

# Matches: (<player> reshuffles.)
#  player: Player who reshuffled
reshuffle_regex = re.compile(r'\s*(?:\.{3} )*\((?P<player>.*) reshuffles\.\)')

# Matches: ... getting +$n.
#  money: Amount of money added to the turn context
get_money_regex = re.compile(r'\s*(?:\.{3} )*getting \+\$(?P<money>\d+)\.')

# Matches: ... getting +n action(s).
#  actions: Number of actions added
get_actions_regex = re.compile(r'\s*(?:\.{3} )*getting \+(?P<actions>\d+) actions?\.')

# Matches: ... getting +n buy(s).
#  buys: Number of buys added
get_buys_regex = re.compile(r'\s*(?:\.{3} )*getting \+(?P<buys>\d+) buys?\.')

# Matches: ... [<player>] draw[ing|s] n card(s).
#  player: Player who draws (if None, it means the current player)
#  cards: Number of cards drawn
draw_cards_regex = re.compile(r'\s*(?:\.{3} )*(?:(?P<player>.*) )?draw(?:ing|s) (?P<cards>\d+) cards?\.')

# Matches: ... drawing n card(s) and getting +n buy(s).
#  player: Player (or None, meaning current player. Wharf gives a player)
#  cards: Number of cards drawn
#  buys: Number of buys added
draw_cards_get_buys_regex = re.compile(r'\s*(?:(?P<player>.*) )?draw(?:ing|s) (?P<cards>\d+) cards? and get(?:ting|s) \+(?P<buys>\d+) buys?(?: from the <span class=card-duration>Wharf</span>)?\.')

# Matches: ... [<player>] discard[ing|s] <cards>.
#  player: Player, or None for current player
#  cards: List of cards discarded (may be from deck or hand or who knows where)
discard_cards_regex = re.compile(r'\s*(?:(?P<player>.*) )?discard(?:ing|s) (?P<cards>.*)\.')

# Matches: ... [<player>] gain[ing|s] a <card>.
#  player: Player who gains something (if None, it means the current player)
#  card: The card gained.
gain_cards_regex = re.compile('\\s*(?:\\.{3} )*(?:(?P<player>.*) )?gain(?:ing|s) an? <[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>\\.')

# Matches: ... [<player>] trash[ing|es] <cards>.
#  player: Player who trashed a card (or None, meaning current player)
#  cards: Cards trashed
trash_cards_regex = re.compile(r'\s*(?:\.{3} )*(?:(?P<player>.*) )?trash(?:ing|es) (?P<cards>.*)\.')

# Used by Fortune Teller, Pirate Ship, etc...
# Matches: ... <player> reveals <cards>.
#  player: Player who reveals cards
#  cards: Cards revealed
reveal_cards_regex = re.compile(r'\s*(?:\.{3} )*(?P<player>.*) reveals (?P<cards>.*)\.')



# Card Specific Regexes
# ---------------------

# Swindler
#  player: Player who trashes something
#  card: Card trashed
swindler_trash_regex = re.compile('\\s*(?:\\.{3} )*(?P<player>.*) turns up an? <[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+> and trashes it\\.')
#  player: Player whose cards were replaced
#  old_card: Card trashed (same as card extracted from trash_regex above)
#  new_card: New card gained to replace it
swindler_replace_regex = re.compile('\\**(?:\\.{3} )*replacing (?P<player>.*)\'s <[\\w=\\-"\' ]+>(?P<old_card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+> with an? <[\\w=\\-"\' ]+>(?P<new_card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>\\.')

# Fortune Teller - others?
# Matches: <player> puts the <card> back onto the deck.
#  player
#  card
fortune_teller_put_cards_on_deck_regex = re.compile('\\s*(?:\\.{3} )*(?P<player>.*) puts the <[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+> back onto the deck\\.')





br_regex = re.compile(r'\s*<br>$')
separator = '----------------------'



# Parses an extracted count into a number
def parse_count(count):
    if count == 'a' or count == 'an': # or count == 'the' # Does the ever get used?
        return 1
    elif count is not None:
        return int(count)
    else:
        return None
        
def pr(s):
    print s

# This is a utility function that makes running some action on a list of cards much simpler.
# It accepts the string list of cards and a function taking a single card as a parameter.
# It then calls func on each card in the list the appropriate number of times.
# For example, the string of '2 Coppers and 1 Silver' would call func twice with Copper, and onces with Silver.
# It will also look at cards in a string without the prefixed counts
def foreach_card(cards, func):
    for card_match in card_count_regex.finditer(cards):
        count = parse_count(card_match.group('count'))
        card = sanitize_card(card_match.group('card'))
        if count is not None:
            for i in range(count):
                func(card)
        else:
            func(card)
            
# Similar to foreach_card(), except it passes the count to the func as well as the card
def foreach_cards(cards, func):
    for card_match in card_count_regex.finditer(cards):
        count = parse_count(card_match.group('count'))
        card = card_match.group('card')
        func(count, card)

class isotropic_parser:

    # Since this is the most interesting function (it's where each line gets processed),
    # it's at the top to make getting to it easier.
    # It should ALWAYS return True if the line was matched, that way the caller knows to
    # print other lines to warn that they weren't processed.
    def read_line(self, line):
        # Check the line to see what occurred.
        # Please keep the common/generic type lines first, for efficiencies sake.
        # Card specific checks should happen last, as they will only occur in games where that card is.
        
        # Check for played cards (actions, treasures)
        match = play_cards_regex.match(line)
        if match:
            self.assert_current_player(match.group('player'))
            foreach_card(match.group('cards'), lambda card: self.game.play(card))
            return True
            
        # Check for purchased cards
        match = buy_card_regex.match(line)
        if match:
            self.assert_current_player(match.group('player'))
            self.game.buy(match.group('card'))
            return True
            
        # Check for the cleanup phase
        match = draw_hand_regex.match(line)
        if match:
            self.game.cleanup()
            foreach_card(match.group('cards'), lambda card: self.game.draw(card, match.group('player')))
            return True
            
        # Check for reshuffling
        match = reshuffle_regex.match(line)
        if match:
            self.game.reshuffle(match.group('player'))
            return True
            
        # Check for +$
        match = get_money_regex.match(line)
        if match:
            self.game.add_money(int(match.group('money')))
            return True
        
        # Check for +actions
        match = get_actions_regex.match(line)
        if match:
            self.game.add_actions(int(match.group('actions')))
            return True
            
        # Check for +buys
        match = get_buys_regex.match(line)
        if match:
            self.game.add_buys(int(match.group('buys')))
            return True
        
        # Check for drawing cards
        match = draw_cards_regex.match(line)
        if match:
            self.game.draw(int(match.group('cards')), match.group('player'))
            return True
        
        # Check for drawing combined with buys
        match = draw_cards_get_buys_regex.match(line)
        if match:
            self.game.draw(int(match.group('cards')))
            self.game.add_buys(int(match.group('buys')))
            return True
        
        # Check for discarding cards
        match = discard_cards_regex.match(line)
        if match:
            foreach_card(match.group('cards'), lambda card: self.game.discard(card))
            return True
        
        # Check for gained cards
        match = gain_cards_regex.match(line)
        if match:
            self.game.gain(match.group('card'), match.group('player'))
            return True
            
        # Check for trashed cards
        match = trash_cards_regex.match(line)
        if match:
            foreach_card(match.group('cards'), lambda card: self.game.trash(card))
            return True
            
        # Check for revealing cards (but don't do anything with them)
        match = reveal_cards_regex.match(line)
        if match:
            # This doesn't do anything about the game state
            return True
        
        
        
        # Specific cards
        match = swindler_trash_regex.match(line)
        if match:
            self.game.trash(match.group('card'), match.group('player'))
            return True
            
        match = swindler_replace_regex.match(line)
        if match:
            # Ignore the old_card group, as it was already trashed
            self.game.gain(match.group('new_card'), match.group('player'))
            return True
            
        match = fortune_teller_put_cards_on_deck_regex.match(line)
        if match:
            # As we did nothing with the revealed cards, do nothing here
            return True
            
            
        # Default return
        return False
    
    def __init__(self):
        self.game = dominion_game()
        
    def read(self, filename):
        self.file = open(filename)
        
        self.read_header()
        self.read_scores()
        self.read_game()
        
    def read_header(self):
        # Get some game metadata from the first line
        first_line = self.next() # Read the first line
        match = first_line_regex.match(first_line)
        if match:
            self.game.set_game_id(match.group('game_id'))
            self.game.set_winner(match.group('winner'))
        else:
            self.unmatched_line(first_line, first_line_regex)
            
        # Get the piles that signalled the end of the game
        empty_piles = self.next() # Read the line with the ending conditions
        foreach_card(empty_piles, lambda card: self.game.add_empty_pile(sanitize_card(card)))
            
        self.next() # Skip line 3
        
        # Read the cards that will be in the supply
        cards_in_supply = self.next()
        foreach_card(cards_in_supply, lambda card: self.game.add_card_to_supply(card))
            
        self.next() # Skip line 5
        
        end = self.next() # Read the separator
        if end != separator:
            print "Header not complete: {0}".format(end)
        
    def read_scores(self):
        self.next() # Skip blank line
        # Loop until the separator is found, at which point the method returns
        while True:
            player_first_line = self.next() # Read the player first line (points)
            # If this line is the separator, we have read all the players
            if player_first_line == separator:
                return
            
            match = player_first_line_regex.match(player_first_line)
            if match:
                place = int(match.group('place'))
                player = match.group('player')
                score = int(match.group('score'))
                turns = int(match.group('turns'))
                cards = match.group('cards')
                #foreach_cards(cards, lambda count, card: pr('  {0} {1} ({2})'.format(count, card, sanitize_card(card))))
                self.game.add_player(player)
                self.game.set_final_score(player, score)
            else:
                self.unmatched_line(player_first_line, player_first_line_regex)
                
            player_second_line = self.next() # Read players 2nd line (opening move)
            # This is skipped for now - its not needed
            
            # Read the third line for the player - this holds the final contents of their entire deck
            player_third_line = self.next()
            match = player_third_line_regex.match(player_third_line)
            if match:
                deck_size = parse_count(match.group('deck_size'))
                cards = match.group('cards')
                #foreach_cards(cards, lambda count, card: pr('  {0} {1} ({2})'.format(count, card, sanitize_card(card))))
            else:
                self.unmatched_line(player_third_line, player_third_line_regex)
                    
            self.next() # Read the blank line that follows each player
        
    def read_game(self):
        # Initialize the game (this should be called after all the supply piles are established though)
        self.game.init_game()
        
        self.next() # Read the blank line after the separator

        # Read the contents of the trash
        trash_line = self.next() # Read the trash line
        #foreach_cards(trash_line, lambda count, card: pr('  {0} {1} ({2})'.format(count, card, sanitize_card(card))))
        
        self.next() # Read the blank line after the trash
        
        game_log_line = self.next() # Read the game log line
        if game_log_line != '<hr/><b>Game log</b>':
            self.unmatched_line(game_log_line, '<hr/><b>Game log</b>')
            
        self.next() # Read the blank line after the game log
        
        # Read the turn order
        # This calls out a separate function, as making a single regex proved difficult. This was simpler.
        turn_order_line = self.next() # Read the turn order line
        match = self.match_turn_order(turn_order_line)
        if match:
            #`print 'Players (in order): {0}'.format(match.groups())
            pass
        else:
            self.unmatched_line(turn_order_line, turn_order_regex)
            
        self.next() # Read the blank line after the turn order
        
        for player in self.game.get_players():
            starting_hand = self.next()
            match = draw_hand_regex.match(starting_hand)
            if match:
                player = match.group('player')
                cards = match.group('cards')
                foreach_card(cards, lambda card: self.game.draw(card, player))
            else:
                self.unmatched_line(starting_hand, draw_hand_regex)
            
        line = self.next() # Read the <br> line after each players starting hands
        if not br_regex.match(line):
            self.unmatched_line(line, br_regex)
        
        # Read each turn (read_turn() returns true until there's no more turns to read - thanks <br> tags)
        while (self.read_turn()):
            pass
            
        print 'Parsing complete.'
        # TODO: Read the footer? It doesn't really have any new information though.
            
    def match_turn_order(self, turn_order_line):
        # Making a single regex for any number of players didn't work out so well
        num_players = len(self.game.get_players())
        if num_players == 2:
            match = turn_order_2p_regex.match(turn_order_line)
        elif num_players == 3:
            match = turn_order_3p_regex.match(turn_order_line)
        elif num_players == 4:
            match = turn_order_4p_regex.match(turn_order_line)
        elif num_players == 5:
            match = turn_order_5p_regex.match(turn_order_line)
        elif num_players == 6:
            match = turn_order_6p_regex.match(turn_order_line)
        elif num_players == 7:
            match = turn_order_7p_regex.match(turn_order_line)
        elif num_players == 8:
            match = turn_order_8p_regex.match(turn_order_line)
        else:
            match = None
        return match
        
    def read_turn(self):
        self.read_turn_header()
        
        line = 'Make sure the loop starts by making this a non-zero length string. It will get reset before it gets parsed anyway.'
        # This loops until an empty line is found (which only occurs at the very end of the document), and then returns false, indicating there is not another turn to be read.
        # Otherwise, this will break out when a <br> has been found, which will cause this to return true.
        while len(line) != 0:
            line = self.next() # Read the next line
            
            # Check to see if the turn is over
            if br_regex.match(line):
                return True
                
            print 'Parsing line: {0}'.format(line)
            
            success = self.read_line(line)
            
            # If the line was not successfully read, print it so it can be added.
            if not success:
                print
                print 'Unknown line: {0}'.format(line)
                print
                exit(0) # Until a more complete set of parsing is built up, add things in one at a time
        # There is no more turn to read
        return False
        
    def read_turn_header(self):
        turn_first_line = self.next()
        print 'Parsing line: {0}'.format(turn_first_line)
        match = turn_header_regex.match(turn_first_line)
        if match:
            player = match.group('player')
            turn = int(match.group('turn'))
            self.game.start_new_turn(player, turn)
        else:
            # Maybe this is a possessed turn?
            match = possessed_turn_header_regex.match(turn_first_line)
            if match:
                player = match.group('possessor')
                self.game.start_new_turn(player)
            else:
                match = outpost_turn_header_regex.match(turn_first_line)
                if match:
                    player = match.group('player')
                    self.game.start_new_turn(player)
                else:
                    self.unmatched_line(turn_first_line, turn_header_regex)
                    self.unmatched_line(turn_first_line, possessed_turn_header_regex)
                    self.unmatched_line(turn_first_line, outpost_turn_header_regex)
                    
    def unmatched_line(self, line, regex = None):
        if regex is None:
            print 'Line didn\'t match:\n Line: {0}'.format(line)
        elif type(regex) == str:
            print 'Line didn\'t match:\n Line: {0}\n Pattern: {1}'.format(line, regex)
        else:
            print 'Line didn\'t match:\n Line: {0}\n Pattern: {1}'.format(line, regex.pattern)
            
    def assert_current_player(self, player):
        assert self.game.get_player(player) is self.game.get_player(), "Acting player was not expected!"
    
    def next(self):
        return self.file.next().strip()

        
        
# This class handles logging features to be trained on
class feature_logger:
    
    def __init__(self, game, filename):
        self.game = game
        #self.file = open(filename, 'w')
        
        
    
if __name__ == '__main__':
    parser = isotropic_parser()
    logger = feature_logger(parser.game, 'features.txt')
    parser.read('test.html')
    