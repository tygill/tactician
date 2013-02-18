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




separator = '----------------------\n'


# Parses an extracted count into a number
def parse_count(count):
    if count == 'a' or count == 'an':
        return 1
    else:
        return int(count)

class isotropic_parser:
    
    def __init__(self, filename):
        self.file = open(filename)
        self.game = dominion_game()
        
        self.read_header()
        self.read_scores()
        self.read_cards_in_supply()
        
    def read_header(self):
        first_line = self.file.next() # Read the first line
        match = first_line_regex.match(first_line)
        if match:
            self.game.set_game_id(match.group('game_id'))
            self.game.set_winner(match.group('winner'))
            
        # Get the piles that signalled the end of the game
        empty_piles = self.file.next() # Read the line with the ending conditions
        for match in card_regex.finditer(empty_piles):
            self.game.add_empty_pile(sanitize_card(match.group('card')))
            
        self.file.next() # Skip line 3
        
        cards_in_supply = self.file.next()
        for match in card_regex.finditer(cards_in_supply):
            self.game.add_card_to_supply(match.group('card'))
            
        self.file.next() # Skip line 5
        
        end = self.file.next() # Read the separator
        assert end == separator, "Header not complete: {0}".format(end)
        
    def read_scores(self):
        self.file.next() # Skip blank line
        # Loop until the separator is found, at which point the method returns
        while True:
            player_first_line = self.file.next() # Read the player first line (points)
            if player_first_line == separator:
                return
            match = player_first_line_regex.match(player_first_line)
            if match:
                place = int(match.group('place'))
                player = match.group('player')
                score = int(match.group('score'))
                turns = int(match.group('turns'))
                print player
                cards = match.group('cards')
                for card_match in card_count_regex.finditer(cards):
                    count = parse_count(card_match.group('count'))
                    card = card_match.group('card')
                    singular_card = sanitize_card(card)
                    print '{0} {1} ({2})'.format(count, card, singular_card)
                self.game.add_player(player)
                self.game.set_final_score(player, score)
                
            player_second_line = self.file.next() # Read players 2nd line (openning move)
            # This is skipped for now - its not needed
            
            player_third_line = self.file.next()
            match = player_third_line_regex.match(player_third_line)
            if match:
                deck_size = parse_count(match.group('deck_size'))
                cards = match.group('cards')
                print 'Deck size: {0}'.format(deck_size)
                for card_match in card_count_regex.finditer(cards):
                    count = parse_count(card_match.group('count'))
                    card = card_match.group('card')
                    singular_card = sanitize_card(card)
                    print '{0} {1} ({2})'.format(count, card, singular_card)
                    
            self.file.next() # Read the blank line that follows each player
        
    def read_cards_in_supply(self):
        self.game.init_game()
    
    
if __name__ == '__main__':
    parser = isotropic_parser('test.html')
    