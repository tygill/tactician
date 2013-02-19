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
card_count_regex = re.compile('(?P<count>[an\d]+) <[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>')


# Specific Regexes
# ----------------

# Header

# Extracts:
#  game_id: The id of the game
#  winner: player who won the game
first_line_regex = re.compile(r'<html><head><link rel="stylesheet" href="/semistatic/log\.css"><title>Dominion Game #(?P<game_id>\d+)</title></head><body><pre>(?P<winner>.+) wins!')

# Player info

# Extracts:
#  place: Rank in game
#  player: Name of player
#  score: Players final score
#  cards: List of cards and counts (can be extraced with card_count_regex)
#  turns: Number of turns the player had
player_first_line_regex = re.compile(r'<b>#(?P<place>\d) (?P<player>.+)</b>: (?P<score>[\d\-]+) points \((?P<cards>.+)\); (?P<turns>\d+) turns')
# Extracts: (admittedly, card_regex could just be run on the whole line with the same result...)
#  cards: List of cards bought on the openning turns (card_regex can pull them out)
player_second_line_regex = re.compile(r'\s*opening: (?P<cards>)')
# Extracts:
#  deck_size: Number of cards in deck (total)
#  cards: List of cards and counts in deck
player_third_line_regex = re.compile(r'\s*\[(?P<deck_size>\d+) cards?\] (?P<cards>.*)')

# Game log

# These regexes pull out the turn orderings for each different number of players.
# Making a single regex that combined all of these proved too much.
# Extracts:
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

# Turn Regexes
# ------------

# Extracts
#  player: Player name whose turn it now is
#  turn: Turn number
turn_header_regex = re.compile('\\s*&mdash; (?P<player>.*)\'s turn (?P<turn>\\d+) &mdash;')
# Extracts
#  possessee: Player whose hand is being possessed
#  possessor: Player doing the possessing
possessed_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w]+\\?s=40&d=identicon&r=PG" width=40 height=40 class=avatar><b>&mdash; (?P<possessee>.*)\'s turn \\(possessed by (?P<possessor>.*)\\) &mdash;</b>')
# Extracts
#  player: Player who got an extra turn
outpost_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w]+\\?s=40&d=identicon&r=PG" width=40 height=40 class=avatar><b>&mdash; (?P<player>.*)\'s extra turn \\(from <span class=card-duration>Outpost</span>\\) &mdash;</b>')

br_regex = re.compile(r'\s*<br>$')



separator = '----------------------'


# Parses an extracted count into a number
def parse_count(count):
    if count == 'a' or count == 'an':
        return 1
    else:
        return int(count)

class isotropic_parser:
    
    def __init__(self):
        self.game = dominion_game()
        
    def read(self, filename):
        self.file = open(filename)
        
        self.read_header()
        self.read_scores()
        self.read_game()
        
    def read_header(self):
        first_line = self.next() # Read the first line
        match = first_line_regex.match(first_line)
        if match:
            self.game.set_game_id(match.group('game_id'))
            self.game.set_winner(match.group('winner'))
        else:
            self.unmatched_line(first_line, first_line_regex)
            
        # Get the piles that signalled the end of the game
        empty_piles = self.next() # Read the line with the ending conditions
        for match in card_regex.finditer(empty_piles):
            self.game.add_empty_pile(sanitize_card(match.group('card')))
            
        self.next() # Skip line 3
        
        cards_in_supply = self.next()
        for match in card_regex.finditer(cards_in_supply):
            self.game.add_card_to_supply(match.group('card'))
            
        self.next() # Skip line 5
        
        end = self.next() # Read the separator
        if end != separator:
            print "Header not complete: {0}".format(end)
        
    def read_scores(self):
        self.next() # Skip blank line
        # Loop until the separator is found, at which point the method returns
        while True:
            player_first_line = self.next() # Read the player first line (points)
            if player_first_line == separator:
                return
            match = player_first_line_regex.match(player_first_line)
            if match:
                place = int(match.group('place'))
                player = match.group('player')
                score = int(match.group('score'))
                turns = int(match.group('turns'))
                #print player
                cards = match.group('cards')
                for card_match in card_count_regex.finditer(cards):
                    count = parse_count(card_match.group('count'))
                    card = card_match.group('card')
                    singular_card = sanitize_card(card)
                    #print '  {0} {1} ({2})'.format(count, card, singular_card)
                self.game.add_player(player)
                self.game.set_final_score(player, score)
            else:
                self.unmatched_line(player_first_line, player_first_line_regex)
                
            player_second_line = self.next() # Read players 2nd line (openning move)
            # This is skipped for now - its not needed
            
            player_third_line = self.next()
            match = player_third_line_regex.match(player_third_line)
            if match:
                deck_size = parse_count(match.group('deck_size'))
                cards = match.group('cards')
                #print 'Deck size: {0}'.format(deck_size)
                for card_match in card_count_regex.finditer(cards):
                    count = parse_count(card_match.group('count'))
                    card = card_match.group('card')
                    singular_card = sanitize_card(card)
                    #print '  {0} {1} ({2})'.format(count, card, singular_card)
            else:
                self.unmatched_line(player_third_line, player_third_line_regex)
                    
            self.next() # Read the blank line that follows each player
        
    def read_game(self):
        self.game.init_game()
        
        self.next() # Read the blank line after the separator
        
        #print 'Trash:'
        trash_line = self.next() # Read the trash line
        for match in card_count_regex.finditer(trash_line):
            count = parse_count(match.group('count'))
            card = match.group('card')
            singular_card = sanitize_card(card)
            #print '  {0} {1} ({2})'.format(count, card, singular_card)
        
        self.next() # Read the blank line after the trash
        
        game_log_line = self.next() # Read the game log line
        if game_log_line != '<hr/><b>Game log</b>':
            self.unmatched_line(game_log_line, '<hr/><b>Game log</b>')
            
        self.next() # Read the blank line after the game log
        
        turn_order_line = self.next() # Read the turn order line
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
        if match:
            #`print 'Players (in order): {0}'.format(match.groups())
            pass
        else:
            self.unmatched_line(turn_order_line, turn_order_regex)
            
        self.next() # Read the blank line after the turn order
        
        for player in self.game.get_players():
            self.next() # TODO: Read the players starting hands
            
        line = self.next() # Read the <br> line after each players starting hands
        if not br_regex.match(line):
            self.unmatched_line(line, br_regex)
        
        # Read each turn (read_turn() returns true until there's no more turns to read - thanks <brpossesseeags)
        while (self.read_turn()):
            pass
            
        print 'Parsing complete.'
        # TODO: Read the footer? It doesn't really have any new information though.
            
    def read_turn(self):
        self.read_turn_header()
        
        line = self.next()
        # This loops until an empty line is found (which only occurs at the very end of the document), and then returns false, indicating there is not another turn to be read.
        # Otherwise, this will break out when a <br> has been found, which will cause this to return true.
        while len(line) != 0:
            # Check to see if the turn is over
            if br_regex.match(line):
                return True
            
            # Any other matches that use up the line should continue the loop so this is only called
            # when a line is unprocessed.
            self.unmatched_line(line)
            
            line = self.next()
        # There is no more turn to read
        return False
        
    def read_turn_header(self):
        turn_first_line = self.next()
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
    