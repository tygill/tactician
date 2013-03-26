from dominion import *
import re

# General Purpose

# Designed to be used with finditer().
# Extracts a card name from its typical <span> wrapper
# Extracts:
#  card: Name of card (Note: might be plural!)
card_regex = re.compile('<[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>')
card_regex_piece = '<[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>'
card_regex_piece_formatable = '<[\\w=\\-"\' ]+>(?P<{0}>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>'
card_regex_piece_no_name = '<[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>'
                         
# Designed to be used with finditer().
# Extracts a card name from its typical <span> wrapper, with a preceeding quantitiy
# Extracts:
#  card: Name of card (Note: might be plural!)
#  count: Number prefixing card (Note that it might be a or an as well as a number)
card_count_regex = re.compile('(?:(?P<count>[thean\d]+) )?<[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>')

# Card list regex piece. This regex is never used, but the pieces of it are used in many other regexes.
#  cards
#card_list_regex = re.compile('(?P<cards>(?:(?:\d+|an?) <[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>,? ?)+(?:(?:and )?(?:\d+|an?) <[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>)?)')
# Added the 'and then' clause for Venture
card_list_regex_piece = '(?P<cards>(?:(?:the )?(?:\d+|an?|the) ' + card_regex_piece_no_name + ',? ?)+(?:(?:and )?(?:the )?(?:\d+|an?|the) ' + card_regex_piece_no_name + ')?(?:(?: and then )?(?:the )?(?:\d+|an?|the) ' + card_regex_piece_no_name + ')?|nothing)'
card_list_no_count_regex_piece = '(?P<cards>(?:' + card_regex_piece_no_name + ',? ?)+(?:(?:and )?' + card_regex_piece_no_name + ')?(?:(?: and then )?' + card_regex_piece_no_name + ')?|nothing)'

# Used to match the score list
score_card_regex_piece = u'(?:<[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>(?: \[\d+(?: victory| different| action)? cards?\])?|\u25BC)'
score_card_list_regex_piece = u'(?P<cards>(?:(?:\d+|an?|the) ' + score_card_regex_piece + u',? ?)+(?:(?:and )?(?:\d+|an?) ' + score_card_regex_piece + u')?|nothing)'

# Matches the prefix to the line (the ...s)
prefix_piece = r'\s*(?:\.{3} )*'


# Specific Regexes
# ----------------

# Header

# Matches: First line of the document
#  game_id: The id of the game
#  winner: player who won the game
first_line_regex = re.compile(r'<html><head><link rel="stylesheet" href="/semistatic/log\.css"><title>Dominion Game #(?P<game_id>\d+)</title></head><body><pre>(?:(?P<winner>.+) wins!|.+ rejoice in their shared victory!)')

# Player info

# Matches: Player lines in the second section of the log
#  place: Rank in game
#  player: Name of player
#  score: Players final score (None, if they resigned)
#  cards: List of cards and counts (can be extraced with card_count_regex) (None, if the resigned)
#  turns: Number of turns the player had
#  resigned: Order of resignation
player_first_line_regex = re.compile(r'<b>#(?P<place>\d) (?P<player>.+)</b>: (?:(?P<score>[\d\-]+) points? \(' + score_card_list_regex_piece + r'\)|resigned \((?P<resigned>\d+)\w+\)); (?P<turns>\d+) turns')
# Matches: (admittedly, card_regex could just be run on the whole line with the same result...)
#  card_one, card_two
player_second_line_regex = re.compile(r'\s*opening: (?P<card_one>.+) / (?P<card_two>.+)')
#  deck_size: Number of cards in deck (total)
#  cards: List of cards and counts in deck
player_third_line_regex = re.compile(r'\s*\[(?P<deck_size>\d+) cards?\](?: ' + card_list_regex_piece + ')?')

# Game log

# These regexes pull out the turn orderings for each different number of players.
# Making a single regex that combined all of these proved too much.
#  first, second, third, fourth, fifth, sixth, seventh, eighth: Player orders
# 2p
turn_order_2p_regex = re.compile(r'Turn order is (?P<first>.+) and then (?P<second>.*)\.')
# 3p
turn_order_3p_regex = re.compile(r'Turn order is (?P<first>.+), (?P<second>.+), and then (?P<third>.+)\.')
# 4p
turn_order_4p_regex = re.compile(r'Turn order is (?P<first>.+), (?P<second>.+), (?P<third>.+), and then (?P<fourth>.+)\.')
# 5p
turn_order_5p_regex = re.compile(r'Turn order is (?P<first>.+), (?P<second>.+), (?P<third>.+), (?P<fourth>.+), and then (?P<fifth>.+)\.')
# 6p
turn_order_6p_regex = re.compile(r'Turn order is (?P<first>.+), (?P<second>.+), (?P<third>.+), (?P<fourth>.+), (?P<fifth>.+), and then (?P<sixth>.+)\.')
# 7p
turn_order_7p_regex = re.compile(r'Turn order is (?P<first>.+), (?P<second>.+), (?P<third>.+), (?P<fourth>.+), (?P<fifth>.+), (?P<sixth>.+), and then (?P<seventh>.+)\.')
# 8p
turn_order_8p_regex = re.compile(r'Turn order is (?P<first>.+), (?P<second>.+), (?P<third>.+), (?P<fourth>.+), (?P<fifth>.+), (?P<sixth>.+), (?P<seventh>.+), and then (?P<eighth>.+)\.')
#turn_order_regex = re.compile(r'Turn order is (?P<first>.*),? (?:and then )?(?P<second>.*)(?:,? (?:and then )?(?P<third>.*))?(?:,? (?:and then )?(?P<fourth>.*))?(?:,? (?:and then )?(?P<fifth>.*))?(?:,? (?:and then )?(?P<sixth>.*))?(?:,? (?:and then )?(?P<seventh>.*))?(?:,? (?:and then )?(?P<eighth>.*))?')

# Matches: The n chosen cards are <cards>
#  count: Number of chosen cards
#  cards: Cards chosen
chosen_cards_regex = re.compile(r'The (?P<count>\d+) chosen cards are ' + card_list_no_count_regex_piece + r'\.')
# Matches: <player> vetoes <card>.
#  player: Player vetoing
#  card: Vetoed card
veto_card_regex = re.compile(r'(?P<player>.+) vetoes ' + card_regex_piece + r'\.')


# Game Regexes
# ------------

# Turn header extraction (for regular, possessed, and outpost turns)
#  player: Player name whose turn it now is
#  turn: Turn number
turn_header_regex = re.compile('\\s*&mdash; (?P<player>.+)\'s turn (?P<turn>\\d+) &mdash;')
#  possessee: Player whose hand is being possessed
#  possessor: Player doing the possessing
possessed_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w\d=&?]+" width=40 height=40 class=avatar><b>&mdash; (?P<possessee>.+)\'s turn \\(possessed by (?P<possessor>.+)\\) &mdash;</b>')
#  player: Player who got an extra turn
outpost_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w\d=&?]+" width=40 height=40 class=avatar><b>&mdash; (?P<player>.+)\'s extra turn \\(from <span class=card-duration>Outpost</span>\\) &mdash;</b>')

####################
# Game Log Regexes #
####################
# All of the following regexes are the ones that will read each line of game logs.
# In order to elimiate some duplicate code, these regexes will be stored and matched
# with a lambda expression (or regular function if its longer than one line) telling
# how the game state should be changed.

game_log_regexes = []

# This is the default game log regex matcher, and should be sufficient for most cases.
# It checks for groups named 'actions', 'buys', 'money', 'vp', and 'cost' (reduced cost - Bridge, Princess, Highway).
# It does NOT, however, do anything with 'card' or 'cards', as they have many other things that can happen to them.
def default_matcher(game, match, player = None):
    if 'actions' in match.groupdict():
        if match.group('actions'):
            game.add_actions(int(match.group('actions')))
    if 'buys' in match.groupdict():
        if match.group('buys'):
            game.add_buys(int(match.group('buys')))
    if 'money' in match.groupdict():
        if match.group('money'):
            game.add_money(int(match.group('money')))
    if 'vp' in match.groupdict():
        if match.group('vp'):
            game.add_vp(int(match.group('vp')))
    if 'cost' in match.groupdict():
        if match.group('cost'):
            game.reduce_cost(int(match.group('cost')))
    # Anything else is ignored.
    
def trash_matcher(game, match, player = None):
    if 'card' in match.groupdict():
        game.trash(match.group('card'), player)
    if 'cards' in match.groupdict():
        foreach_card(match.group('cards'), lambda card: game.trash(card, player))
    # Anything else is ignored
    
def gain_matcher(game, match, player = None):
    if 'card' in match.groupdict():
        if match.group('card'):
            game.gain(match.group('card'), player)
    if 'cards' in match.groupdict():
        if match.group('cards'):
            foreach_card(match.group('cards'), lambda card: game.gain(card, player))
    # Anything else is ignored
    
def nothing_matcher(game = None, match = None, player = None):
    pass

def add_game_regex(regex_string, matcher = None):
    regex = re.compile(prefix_piece + regex_string)
    game_log_regexes.append((regex, matcher if matcher else nothing_matcher))
    return regex

# These are here to allow them to be used in callbacks
# Parses an extracted count into a number
def parse_count(count):
    if count == 'a' or count == 'an' or count == 'the': # The is used when a list of a single item is used (for example, trashing the Embargo)
        return 1
    elif count is not None:
        return int(count)
    else:
        return None
        
# Helper method for printing from lambda functions
def pr(s, func = None):
    print s
    if func:
        func(s)

# This is a utility function that makes running some action on a list of cards much simpler.
# It accepts the string list of cards and a function taking a single card as a parameter.
# It then calls func on each card in the list the appropriate number of times.
# For example, the string of '2 Coppers and 1 Silver' would call func twice with Copper, and onces with Silver.
# It will also look at cards in a string without the prefixed counts
def foreach_card(cards, func):
    for card_match in card_count_regex.finditer(cards):
        count = parse_count(card_match.group('count'))
        card = sanitize_card(card_match.group('card'))
        if card: # Make sure this is a valid card (Young Witch adds <span class=bane-star>&diams;</span> to the supply, which gets pulled as a card
            if count is not None:
                for i in range(count):
                    func(card)
            else:
                func(card)
        elif card_match.group('card') != '&diams;':
            print 'Unexpected card in card list: "{0}"'.format(card_match.group('card'))
            
# Similar to foreach_card(), except it passes the count to the func as well as the card
def foreach_cards(cards, func):
    for card_match in card_count_regex.finditer(cards):
        count = parse_count(card_match.group('count'))
        card = card_match.group('card')
        func(count, card)


# Matches: (<player> draws: <cards>)
draw_hand_regex = add_game_regex(r"<span class=logonly>\((?P<player>.+)(?:\'s first hand| draws): " + card_list_regex_piece + r'\.\)</span>')

# Matches: <player> plays <cards>.
add_game_regex(r'(?:and )?(?:(?P<player>.+) )?play(?:ing|s) ' + card_list_regex_piece + r'(?: again| a third time| first| second)?\.', lambda game, match, player: foreach_card(match.group('cards'), lambda card: game.play(card)))

# Matches: <player> buys a <card>.
add_game_regex(r'(?P<player>.+) buys an? ' + card_regex_piece + r'\.', lambda game, match, player: game.buy(match.group('card'), player))

# Matches: ... [<player>] gain[ing|s] a <card>[ in/on (top of )? the <where>hand/deck].
add_game_regex(r'(?:(?P<player>.+) )?gain(?:ing|s) an? ' + card_regex_piece + r'(?: [io]n (?:top of )?(?:the )?(?P<where>hand|deck)| and put(?:ting)? it on the deck)?\.', gain_matcher)

# Noble Brigand (This was moved here because it needs to be run before the following regex.)
# Matches: ... <player> gains the <card>. (Possession also makes this show up when buying/gaining occurs. If there is a possessing player, buys and gains are ignored.)
add_game_regex(r'(?P<player>.+) gains the ' + card_regex_piece + r'\.', lambda game, match, player: game.gain(match.group('card'), player, 'trash'))

# Matches: ... <player> gain[ing|s] n <cards> [on the deck].
add_game_regex(r'(?:(?P<player>.+) )?gain(?:ing|s) ' + card_list_regex_piece + r'(?: on the deck)?\.', gain_matcher)

# Matches: ... There's nothing for <player> to gain.
add_game_regex(r"There's nothing for (?P<player>.+) to gain\.")

# Matches: ... <player> gain[ing|s] nothing.
add_game_regex(r'(?:(?P<player>.+) )?gain(?:ing|s) nothing\.')

# Matches: ... [<player>] trash[ing|es] <cards> [from the play area|from hand]. (from play area is from Mint, from hand from Treasure Map)
add_game_regex(r'(?:(?P<player>.+) )?trash(?:ing|es) ' + card_list_regex_piece + r'(?: from the play area| from hand)?\.', trash_matcher)

# Matches: ... <player> trashes nothing.
add_game_regex(r'(?P<player>.+) trashes nothing\.')

# Matches: (<player> reshuffles.)
add_game_regex(r'\((?P<player>.+) reshuffles\.\)')

# Ordering of basic gettings (in an attempt to consolidate all of these)
#  draws, buys
#  draws, actions
#  draws, money
#  buys, money
#  money, vp
#  draw, action, buy, money
# Doesn't work...and it lets too much through.
#basic_gets_regex = add_game_regex(r'\s*(?:\.{3} )*(?:(?P<player>.+) )?(?:draw(?:ing|s) (?P<cards>\d+) cards?(?: and )?)?(?:get(?:ting|s) \+(?P<actions>\d+) actions?,?)?(?:(?:get(?:ting|s))? \+(?P<buys>\d+) buys?,?)?(?:(?:get(?:ting|s))? \+\$(?P<money>\d+))?\.')

# Matches: ... getting +$n.
add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+\$(?P<money>\d+)(?: from the <span class=card-duration>(?:Merchant Ship|Lighthouse)</span>)?\.', default_matcher)

# Matches: ... <player> get[ting|s] +n action(s).
add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+(?P<actions>\d+) actions?\.', default_matcher)

# Matches: ... getting +n buy(s).
add_game_regex(r'getting \+(?P<buys>\d+) buys?\.', default_matcher)

# Matches: ... [<player>] draw[ing|s] n card(s).
add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?:(?P<cards>\d+) cards?|nothing)(?: from the <span class=card-duration>Caravan</span>)?\.')

# Matches: ... drawing nothing.
add_game_regex(r'drawing nothing\.')

# Matches: ... drawing n card[s] and getting +n buy[s].
add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?:(?P<cards>\d+) cards?|nothing) and get(?:ting|s) \+(?P<buys>\d+) buys?(?: from the <span class=card-duration>Wharf</span>)?\.', default_matcher)

# Matches: ... drawing n card[s] and getting +n action[s].
add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?:(?P<cards>\d+) cards?|nothing) and get(?:ting|s) \+(?P<actions>\d+) actions?\.', default_matcher)

# Matches: ... drawing n card[s] and getting +$n.
add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?:(?P<cards>\d+) cards?|nothing) and get(?:ting|s) \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... drawing n cards and getting +n actions and +$n.
add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?:(?P<cards>\d+) cards?|nothing) and get(?:ting|s) \+(?P<actions>\d+) actions? and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... [<player>] drawing n cards and getting +n actions and +n buys [from the <span class=card-duration>Tactician</span>].
add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?:(?P<cards>\d+) cards?|nothing) and get(?:ting|s) \+(?P<actions>\d+) actions? and \+(?P<buys>\d+) buys?(?: from the <span class=card-duration>Tactician</span>)?\.', default_matcher)

# Matches: ... drawing n cards and getting +n actions, +n buys, and +$n.
add_game_regex(r'drawing (?:(?P<cards>\d+) cards?|nothing) and getting \+(?P<actions>\d+) actions?, \+(?P<buys>\d+) buys?, and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... getting +b buys and +$n.
add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+(?P<buys>\d+) buys? and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... getting +n actions and +n buys.
add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+(?P<actions>\d+) actions? and \+(?P<buys>\d+) buys?\.', default_matcher)

# Matches: ... getting +n actions and +$n [from the <span class=card-duration>Fishing Village</span>].
add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+(?P<actions>\d+) actions? and \+\$(?P<money>\d+)(?: from the <span class=card-duration>Fishing Village</span>)?\.', default_matcher)

# Matches: ... getting +n actions, +n buys, and +$n.
add_game_regex(r'getting \+(?P<actions>\d+) actions?, \+(?P<buys>\d+) buys?, and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... getting +n {vp}.
add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+(?P<vp>\d+) ' + victory_point_symbol + r'\.', default_matcher)

# Matches: ... getting +$2 and +1 {vp}.
add_game_regex(r'getting \+\$(?P<money>\d+) and \+(?P<vp>\d+) ' + victory_point_symbol + r'\.', default_matcher)

# Matches: ... [making] [<player>] discard[ing|s] <cards>. ('making' is from Scrying Pool, and perhaps others)
add_game_regex(r'(?:making )?(?:(?P<player>.+) )?discard(?:ing|s|) ' + card_list_regex_piece + r'\.')

# Matches: ... <player> discards [n|a] cards.
add_game_regex(r'(?:(?P<player>.+) )?discard(?:ing|s) (?P<cards>[\d|a]+) cards?\.')

# Matches: ... discarding n cards and getting +n buy.
add_game_regex(r'discarding (?:(?P<cards>\d+) cards?|nothing) and getting \+(?P<buys>\d+) buys?\.', default_matcher)

# Matches: ... discarding (n cards?|nothing) and getting +$n.
add_game_regex(r'discarding (?:(?P<cards>\d+) cards?|nothing) and getting \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... discarding (n cards?|nothing) and getting +n actions.
add_game_regex(r'discarding (?:(?P<cards>\d+) cards?|nothing) and getting \+(?P<actions>\d+) actions?\.', default_matcher)

# Matches: ... discarding <cards> [and getting|for] +$n.
add_game_regex(r'discarding ' + card_list_regex_piece + r' (?:and getting|for) \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... [<player>] put[ting|s] <cards> back on the deck[ (first on top)].
add_game_regex(r'(?:(?P<player>.+) )?put(?:ting|s) ' + card_list_regex_piece + r' back on the deck(?: \((?P<order>first on top|in some order)\))?\.')

# Matches: ... [<player>] put[ting|s] [n|a] cards back on the deck.
add_game_regex(r'(?:(?P<player>.+) )?put(?:ting|s) (?P<cards>[\da]+) cards? (?:from hand )?back on the deck\.')

# Matches: ... <player> does nothing.
add_game_regex(r'(?P<player>.+) does nothing\.')

# Used by Fortune Teller, Pirate Ship, Scrying Pool, etc...
# Matches: ... [<player>] reveal[int|s] <cards>[ and putting them in the hand| and keeping it| and discarding it].
#  where: Where they are put (None for doesn't move)
# Revealed cards are now used to store the state for a few cards (namely, Ambassador at present)
def reveal_matcher(game, match, player):
    game.reset_revealed()
    if 'cards' in match.groupdict():
        foreach_card(match.group('cards'), lambda card: game.reveal(card, player))
    if 'card' in match.groupdict():
        game.reveal(match.group('card'), player)
add_game_regex(r'(?:(?P<player>.+) )?reveal(?:ing|s) ' + card_list_regex_piece + r'(?: and put(?:ting|s) (?:them|it) [io]n the hand| and keeping (?:them|it)| and discarding (?:them|it))?\.', reveal_matcher)

# Used by Loan
# Matches: ... drawing and revealing <cards>.
add_game_regex(r'drawing and revealing ' + card_list_regex_piece + r'\.', reveal_matcher)
# Matches: ... revealing <cards> but has no treasure.
add_game_regex(r'revealing ' + card_list_regex_piece + r' but has no treasure\.')
# Matches: ... but has no cards to draw.
add_game_regex(r'but has no cards? to draw\.')
# Matches: ... <player> has no cards to draw.
add_game_regex(r'(?P<player>.+) has no cards? to draw\.')

# Card Specific Regexes
# ---------------------

# Swindler
# Matches: ... <player> turns up a <card> and trashes is.
add_game_regex(r'(?P<player>.+) turns up an? ' + card_regex_piece + r' and trashes it\.', trash_matcher)
# Matches: ... replacing <player>'s <old_card> with a <new_card>.
add_game_regex(r"replacing (?P<player>.+)'s " + card_regex_piece_formatable.format('old_card') + r' with an? ' + card_regex_piece_formatable.format('new_card') + r'\.', lambda game, match, player: game.gain(match.group('new_card'), player))
# Matches: ... No replacement is available.
add_game_regex(r'No replacement is available\.')

# Fortune Teller - others?
# Matches: <player> puts the <card> back onto the deck.
add_game_regex(r'(?P<player>.+) puts the ' + card_regex_piece + r' back onto the deck\.')

# Farming Village
# Matches: ... putting the <card> into the hand.
add_game_regex(r'putting the ' + card_regex_piece + r' into the hand\.')

# Apothecary
# Matches: ... putting <cards> into the hand.
add_game_regex(r'putting (?:the )?' + card_list_regex_piece + r' into the hand\.')

# Talisman
# Matches: ... gaining another <card>.
add_game_regex(r'gaining another ' + card_regex_piece + r'\.', gain_matcher)

# Jack of All Trades (and perhaps others? Sea Hag maybe?)
# Matches: ... discarding the top card of the deck.
add_game_regex(r'discarding the top card of the deck\.')
# Matches: ... leaving the top card of the deck where it is.
add_game_regex(r'leaving the top card of the deck where it is\.')
# Matches: ... but has nothing to trash.
add_game_regex(r'but has nothing to trash\.')

# Noble Brigand (perhaps others?)
# Matches: ... <player> reveals and discards <cards>.
add_game_regex(r'(?P<player>.+) reveals and discards ' + card_list_regex_piece + r'\.')
# Matches: ... <player> draws and reveals <cards>, trashing a <card>.
add_game_regex(r'(?P<player>.+) draws and reveals ' + card_list_regex_piece + r', trashing an? ' + card_regex_piece + r'\.', lambda game, match, player: game.trash(match.group('card'), player))

# Mining Village (slightly more generic than mining village requires, might catch other cards.)
# Matches: ... trashing the <span class=card-none>Mining Village</span> for +$2.
def mining_village_matcher(game, match, player):
    game.trash(match.group('card'), player)
    default_matcher(game, match, player)
add_game_regex(r'trashing the ' + card_regex_piece + r' for \+\$(?P<money>\d+)\.', mining_village_matcher)

# Bank (and Philosopher's Stone)
# Matches: ... which is worth +$n [(n cards in deck, n cards in discard)].
#  deck_size
#  discard_size
add_game_regex(r'which is worth \+\$(?P<money>\d+)(?: \((?:(?P<deck_size>\d+) cards?|nothing) in deck, (?:(?P<discard_size>\d+) cards?|nothing) in discard\))?\.', default_matcher)

# Royal Seal
# Matches: ... putting the <card> on top of the deck.
add_game_regex(r'putting the ' + card_regex_piece + r' on top of the deck\.')

# Tournament
# Matches: ... <player> discards a <discard> and gains a <gain> on the deck.
#  discard: Card discarded
#  gain: Card gained
add_game_regex(r'(?P<player>.+) discards an? ' + card_regex_piece_formatable.format('discard') + r' (?:and|but) gains (?:an? ' + card_regex_piece_formatable.format('gain') + r' on the deck|nothing)\.', lambda game, match, player: game.gain(match.group('gain'), player, 'prizes' if match.group('gain') != 'Duchy' else 'supply') if match.group('gain') else None)

# Bag of Gold
# Matches: ... gaining a <card> on the deck.
add_game_regex(r'gaining a ' + card_regex_piece + r' on the deck\.', gain_matcher)

# Only has 3 (n) cards (Goons, Militia, Ghost Ship, etc.)
# Matches: ... <player> only has n cards.
add_game_regex(r'(?P<player>.+) only has (?:(?P<cards>\d+) cards?|nothing)\.')

# Reducing all costs by n (Princess, Highway)
# Matches: ... reducing all costs by $n.
add_game_regex(r'reducing all costs by \$(?P<cost>\d+)\.', default_matcher)

# Bridge
# Matches: ... getting +n buys, +$n, and reducing all costs by $n.
add_game_regex(r'getting \+(?P<buys>\d+) buys?, \+\$(?P<money>\d+), and reducing all costs by \$(?P<cost>\d+)\.', default_matcher)

# Black Market
# Matches: ... drawing <cards> from the <span class=card-none>Black Market</span> deck.
add_game_regex(r'drawing ' + card_list_regex_piece + r' from the <span class=card-none>Black Market</span> deck\.')
# Matches: ... returning <cards> to the bottom of the <span class=card-none>Black Market</span> deck.
add_game_regex(r'returning ' + card_list_regex_piece + r' to the bottom of the <span class=card-none>Black Market</span> deck\.')

# Bishop
# Matches: ... <player> trashes a <card> and gets +n {vp}.
def bishop_trash_matcher(game, match, player):
    game.trash(match.group('card'), player)
    default_matcher(game, match, player)
add_game_regex(r'(?P<player>.+) trashes an? ' + card_regex_piece + r' and gets \+(?P<vp>\d+) ' + victory_point_symbol + r'\.', bishop_trash_matcher)
# Matches: ... <player> has no cards to trash/in hand.
add_game_regex(r'(?P<player>.+) has no cards (?:to trash|in hand)\.')

# Salvager
# Matches: ... trashing a <card> for +$n and +n buys.
def salvager_trash_regex(game, match, player):
    if match.group('card'):
        game.trash(match.group('card'), player)
    default_matcher(game, match, player)
add_game_regex(r'(?:trashing an? ' + card_regex_piece + r' for \+\$(?P<money>\d+) and|having no card to trash, but getting) \+(?P<buys>\d+) buys?\.', salvager_trash_regex)

# Scrying Pool (discarding is built into the main discarder)
# Matches: ... letting <player> keep a <card>.
add_game_regex(r'letting (?P<player>.+) keep an? ' + card_regex_piece + r'\.')
# Matches: ... revealing nothing (no cards).
add_game_regex(r'revealing nothing \(no cards\)\.')

# Nomad Camp
# Matches: ... putting it on the deck
add_game_regex(r'putting it on the deck\.')

# Walled Village
# Matches: ... <player> returns a <card> to the top of the deck.
add_game_regex(r'(?P<player>.+) returns a ' + card_regex_piece + r' to the top of the deck\.')

# Embargo
# Matches: ... embargoing the <card>.
add_game_regex(r'embargoing the ' + card_regex_piece + r'\.', lambda game, match, player: game.embargo(match.group('card')))

# Alchemist
# Matches: ... <player> returns <cards> to the top of the deck.
add_game_regex(r'(?P<player>.+) returns ' + card_list_regex_piece + r' to the top of the deck\.')

# Venture (revealing and discarding is handled by the basic handlers, as it gets broken into three lines - the reveal, the discard, and the play.)
# Matches: revealing and playing <cards>.
add_game_regex(r'revealing and playing ' + card_list_regex_piece + r'\.', lambda game, match, player: foreach_card(match.group('cards'), lambda card: game.play(card)))

# Native Village
# Matches: ... drawing a card and placing it on the <span class=card-none>Native Village</span> mat.
add_game_regex(r'drawing a card and placing it on the <span class=card-none>Native Village</span> mat\.')
# Matches: ... picking up n cards from the <span class=card-none>Native Village</span> mat.
add_game_regex(r'picking up (?:(?P<cards>\d+) cards?|nothing) from the <span class=card-none>Native Village</span> mat.')
# Matches: ... drawing nothing to put on the <span class=card-none>Native Village</span> mat.
add_game_regex(r'drawing nothing to put on the <span class=card-none>Native Village</span> mat\.')

# Haven
# Matches: ... setting aside a card.
add_game_regex(r'setting aside a card\.')
# Matches: ... <player> picks up a card that was set aside.
add_game_regex(r'(?P<player>.+) picks up a card that was set aside\.')

# Vault
# Matches: ... <player> doesn't discard any cards.
add_game_regex(r"(?P<player>.+) doesn't discard any cards\.")

# Sea Hag
# Matches: ... <player> draws and discards <cards>.
add_game_regex(r'(?P<player>.+) draws and discards ' + card_list_regex_piece + r'\.')

# Scout
# Matches: ... putting nothing into the hand.
add_game_regex(r'putting nothing into the hand\.')

# Develop / Transmute
# Matches: ... but there's no $n[ or $n] card to gain.
add_game_regex(r"but there's no \$(?P<cost1>-?\d+)(?: " + potion_cost_symbol + r")*(?: or \$(?P<cost2>-?\d+)(?: " + potion_cost_symbol + r")*)? card to gain\.")

# Watchtower
# Matches: ... putting the <card> on the deck.
add_game_regex(r'putting the ' + card_regex_piece + r' on the deck\.')

# Lighthouse
# Matches: ... <span class=card-duration>Lighthouse</span> provides <player> immunity to the attack.
add_game_regex(r'<span class=card-duration>Lighthouse</span> provides (?P<player>.+) immunity to the attack\.')

# Island
# Matches: ... setting aside the <span class=card-victory-action>Island</span> with an? <card>.
add_game_regex(r'setting aside the <span class=card-victory-action>Island</span> (?:with an? ' + card_regex_piece + r'|\(no other cards in hand\))\.')
# Matches: ... setting aside nothing.
add_game_regex(r'setting aside nothing\.')

# Mint
# Matches: ... revealing a <card> and gaining another one.
add_game_regex(r'revealing an? ' + card_regex_piece + r' and gaining another one\.', gain_matcher)
# Matches: ... but reveals no treasure card.
add_game_regex(r'but reveals no treasure card\.')

# Pearl Diver
# Matches: ... but leaving the bottom card of the deck where it is.
add_game_regex(r'but leaving the bottom card of the deck where it is\.')
# Matches: ... and moving the bottom card of the deck to the top.
add_game_regex(r'and moving the bottom card of the deck to the top\.')
# Matches: ... but has no cards to look at.
add_game_regex(r'but has no cards to look at\.')

# Thief
# Matches: ... <other_player> trashes one of <player>'s <card>.
add_game_regex(r"(?P<other_player>.+) trashes one of (?P<player>.+)'s " + card_regex_piece + r'\.', lambda game, match, player: game.trash(sanitize_card(match.group('card')), player))
# Matches: ... <player> gains the trashed <card>.
add_game_regex(r'(?P<player>.+) gains the trashed ' + card_regex_piece + r'\.', lambda game, match, player: game.gain(match.group('card'), player, 'trash'))

# Trading Post
# Matches: ... <player> trashes <cards>, gaining a <card> in hand.
def trading_post_matcher(game, match, player):
    foreach_card(match.group('cards'), lambda card: game.trash(card, player))
    game.gain(match.group('card'), player)
add_game_regex(r'(?P<player>.+) trashes ' + card_list_regex_piece + r', gaining a ' + card_regex_piece + r' in hand\.', trading_post_matcher)

# Young Witch
# Matches: ... <player> reveals a Bane card (a <card>).
add_game_regex(r'(?P<player>.+) reveals a Bane card \(an? ' + card_regex_piece + r'\)\.')

# Tactician
# Matches: ... discarding the hand (n cards).
add_game_regex(r'discarding the hand \((?P<cards>\d+) cards?\)\.')
# Matches: ... but has no cards to discard.
add_game_regex(r'but has no cards to discard\.')

# Tunnel
# Matches: ... <player> reveal[ing|s] a <reveal> and gain[ing|s] a <gain>.
add_game_regex(r'(?:(?P<player>.+) )?reveal(?:ing|s) an? ' + card_regex_piece_formatable.format('reveal') + r' and gain(?:ing|s) (?:an? ' + card_regex_piece + r'|nothing)\.', gain_matcher)

# Ambassador
# Matches: ... returning n copies to the supply.
def ambassador_matcher(game, match, player):
    # This should just be a single card
    assert len(game.get_revealed()) > 0, "Unexpected number of revealed cards when playing Ambassador: {0}".format(len(game.get_revealed()))
    #for card in game.get_revealed():
    card = game.get_revealed()[-1]
    if 'copies' in match.groupdict():
        for i in range(int(match.group('copies'))):
            game.return_to_supply(card, player)
    else:
        game.return_to_supply(card, player)
add_game_regex(r'returning (?P<copies>\d+) copies to the supply\.', ambassador_matcher)
# Matches: ... returning it to the supply.
add_game_regex(r'returning it to the supply\.', ambassador_matcher)
# Matches: ... but has no card to reveal.
add_game_regex(r'but has no card to reveal\.')
# Matches: ... which can't be returned to the supply.
add_game_regex(r"which can't be returned to the supply\.")

# Horse Traders
# Matches: ... setting it aside.
add_game_regex(r'setting it aside\.')
# Matches: ... <player> restores the <card> to the hand and draws n cards.
add_game_regex(r'(?P<player>.+) restores the ' + card_regex_piece + r' to the hand and draws (?:(?P<cards>\d+) cards?|nothing)\.')

# Oracle
# Matches: ... <player> draws and reveals <cards>.
add_game_regex(r'(?P<player>.+) draws and reveals ' + card_list_regex_piece + r'\.')
# Matches: ... [<other_player> makes] <player> [puts them back on the deck/discards them].
add_game_regex(r'(?:(?P<other_player>.+) makes )?(?P<player>.+) (?:puts? (?:them|it) back on the deck|discards? (?:them|it))\.')

# Throne Room
# Matches: ... but has no action card to play with it.
add_game_regex(r'but has no action card to play with it\.')

# King's Court
# Matches: ... but plays no action with it.
add_game_regex(r'but plays no action with it\.')
# Matches: ... <player> had played the <card> with a <span class=card-none>King's Court</span>.
add_game_regex(r"(?P<player>.+) had played the " + card_regex_piece + r" with a <span class=card-none>(?:King's Court|Throne Room)</span>\.")

# Harvest
# Matches: ... revealing and discarding <cards> and getting +$n.
add_game_regex(r'revealing and discarding ' + card_list_regex_piece + r' and getting \+\$(?P<money>\d+)\.', default_matcher)

# Envoy
# Matches: ... drawing <cards>.
add_game_regex(r'drawing ' + card_list_regex_piece + r'\.')
# Matches: ... discarding <card> and putting the rest into the hand.
add_game_regex(r'discarding an? ' + card_regex_piece + r' and putting the rest into the hand\.')
# Matches: ... but draws nothing.
add_game_regex(r'but draws nothing\.')

# Navigator
# Matches: ... putting them back on the deck.
add_game_regex(r'putting (?:them|it) back on the deck\.')
# Matches: ... and discarding them.
add_game_regex(r'and discarding (?:them|it)\.')

# Duchess
# Matches: ... <player> draws a card and puts it back.
add_game_regex(r'(?P<player>.+) draws a card and puts it back\.')

# Trader
# Matches: ... <player> reveals a <span class=card-reaction>Trader</span> to gain a <silver> instead of a <card>.
#  The card needs to be returned to the supply, as it was already gained. The silver doesn't need to be gained now though, as it will be gained on the next line.
add_game_regex(r'(?P<player>.+) reveals a <span class=card-reaction>Trader</span> to gain an? ' + card_regex_piece_formatable.format('silver') + r' instead of an? ' + card_regex_piece + r'\.', lambda game, match, player: game.return_to_supply(match.group('card'), player, trader=True))

# Inn
# Matches: ... shuffling <cards> into the draw pile.
add_game_regex(r'shuffling ' + card_list_regex_piece + r' into the draw pile\.')
# Matches: ... but the discard pile has no actions.
add_game_regex(r'but the discard pile has no actions\.')

# Moneylender
# Matches: ... trashing a <card> for +$n.
def moneylender_matcher(game, match, player):
    game.trash(match.group('card'), player)
    default_matcher(game, match, player)
add_game_regex(r'trashing an? ' + card_regex_piece + r' for \+\$(?P<money>\d+)\.', moneylender_matcher)
# Matches: ... but has no <span class=card-treasure>Copper</span> to trash.
add_game_regex(r'but has no <span class=card-treasure>Copper</span> to trash\.')

# Cartographer
# Matches: ... looking at the top n cards of the deck.
add_game_regex(r'looking at the top (?:(?P<cards>\d+) cards?|nothing) of the deck\.')
# Matches: ... discarding n cards and putting n cards back on the deck.
add_game_regex(r'discarding (?:(?P<discards>\d+) cards?|nothing) and putting (?:(?P<put_back>\d+) cards?|nothing) back on the deck\.')

# Coppersmith
# Matches: ... making each <span class=card-treasure>Copper</span> worth $2.
add_game_regex(r'making each <span class=card-treasure>Copper</span> worth \$(?P<value>\d+)\.', lambda game, match, player: game.set_copper_value(int(match.group('value'))))

# Contraband
# Matches: ... <other_player> prohibits <player> from buying <card>.
add_game_regex(r'(?P<other_player>.+) prohibits (?P<player>.+) from buying ' + card_regex_piece + r'\.', lambda game, match, player: game.prohibit(sanitize_card(match.group('card'))))

# Golem
# Matches: ... playing no other action card.
add_game_regex(r'playing no other action card\.')

# Possession
# Matches: ... <player> discards the "trashed" cards? (<cards>).
add_game_regex(r'(?P<player>.+) discards the "trashed" cards? \(' + card_list_regex_piece + r'\)\.', lambda game, match, player: foreach_card(match.group('cards'), lambda card: game.gain(card, player, 'trash', True)))

# Spice Merchant
# Matches: ... but trashes nothing.
add_game_regex(r'but trashes nothing\.')

# Cutpurse
# Matches: ... <player> reveals <cards> (no <card>). (<card> should be Copper)
add_game_regex(r'(?P<player>.+) reveals ' + card_list_regex_piece + r' \(no ' + card_regex_piece + r'\)\.')

# Chancellor
# Matches: ... [not] putting the deck into the discard pile.
add_game_regex(r'(?:not )?putting the deck into the discard pile\.')

# Remake
# Matches: ... <player> has no card to trash.
add_game_regex(r'(?P<player>.+) has no card to trash\.')

# Wishing Well
# Matches: ... wishing for a <card> [and finding one|but finding a <found> instead].
add_game_regex(r'wishing for an? ' + card_regex_piece + r' (?:and finding one|but finding an? ' + card_regex_piece_formatable.format('found') + r' instead)\.')
# Matches: ... <player> has no cards to wish for.
add_game_regex(r'(?P<player>.+) has no cards to wish for\.')

# Saboteur
# Matches: ... <player> reveals a <card> and trashes it.
add_game_regex(r'(?P<player>.+) reveals an? ' + card_regex_piece + r' and trashes it\.', trash_matcher)
# Matches: ... The <card> is trashed. (This has to use some reveal state to know which players card should be trashed.
add_game_regex(r'The ' + card_regex_piece + r' is trashed\.', lambda game, match, player: game.trash(match.group('card'), game.get_last_reveal_player()))
# Matches: ... <player> gains a <card> to replace it.
add_game_regex(r'(?P<player>.+) gains (?:an? ' + card_regex_piece + r'|nothing) to replace it\.', gain_matcher)
# Matches: ... <player> reveals <cards> but has no card to sabotage.
add_game_regex(r'(?P<player>.+) reveals ' + card_list_regex_piece + r' but has no card to sabotage\.')

# Pirate Ship
# Matches: ... attacking the other players.
add_game_regex(r'attacking the other players\.')
# Matches: ... <other_player> trashes <player>'s <card>.
add_game_regex(r"(?P<other_player>.+) trashes (?P<player>.+)'s " + card_regex_piece + r'\.', trash_matcher)
# Matches: ... <player> gains a <span class=card-none>Pirate Ship</span> token.
add_game_regex(r'(?P<player>.+) gains a <span class=card-none>Pirate Ship</span> token\.', lambda game, match, player: game.add_pirate_ship_token(1, player))

# Minion
# Matches: ... <player> discard[ing|s] the hand.
add_game_regex(r'(?:(?P<player>.+) )?discard(?:ing|s) the hand\.')
# Matches: ... <player> has n cards in hand.
add_game_regex(r'(?P<player>.+) has (?P<cards>\d+) cards in hand\.')
# Matches: ... <player> has nothing in hand.
add_game_regex(r'(?P<player>.+) has nothing in hand\.')

# Counting House
# Matches: ... putting <cards> from the discard pile into the hand.
add_game_regex(r'putting ' + card_list_regex_piece + r' from the discard pile into the hand\.')
# Matches: ... but there are no <span class=card-treasure>Coppers</span> in the discard pile.
add_game_regex(r'but there are no <span class=card-treasure>Coppers</span> in the discard pile\.')

# Library
# Matches: ... setting aside a <card>.
add_game_regex(r'setting aside an? ' + card_regex_piece + r'\.')

# Torturer
# Matches: ... <player> gains nothing in hand.
add_game_regex(r'(?P<player>.+) gains nothing in hand\.')

# Secret Chamber
# Matches: ... returning n cards to the deck.
add_game_regex(r'returning (?P<cards>\d+) cards? to the deck\.')

# Jester
# Matches: ... There are no <card> available to gain. (card is plural)
add_game_regex(r'There are no ' + card_regex_piece + r' available to gain\.')

# Trusty Steed
# Matches: ... gaining <cards> and putting the deck into the discard. (cards should be 4 <span class=card-treasure>Silvers</span>)
add_game_regex(r'gaining ' + card_list_regex_piece + r' and putting the deck into the discard\.', lambda game, match, player: foreach_card(match.group('cards'), lambda card: game.gain(card, player)))

# Explorer
# Matches: ... revealing a <card> and gaining a <card> in hand.
add_game_regex(r'revealing a ' + card_regex_piece_formatable.format('revealed') + r' and gaining a ' + card_regex_piece_formatable.format('gain') + r' in hand\.', lambda game, match, player: game.gain(match.group('gain'), player))

# Trade Route
# Matches: ... but has no card to trash.
add_game_regex(r'but has no card to trash\.')

# Expand
# Matches: ... but has nothing to expand.
add_game_regex(r'but has nothing to expand\.')

# Mine
# Matches: ... but has no treasure card to trash.
add_game_regex(r'but has no treasure card to trash\.')

# Remodel
# Matches: ... but has nothing to remodel.
add_game_regex(r'but has nothing to remodel\.')

# Border Village
# Matches: ... gaining nothing with it.
add_game_regex(r'gaining nothing with it\.')

# Transmute
# Matches: ... having no cards to trash.
add_game_regex(r'having no cards to trash\.')

# Spy
# Matches: ... <player> has no card to reveal.
add_game_regex(r'(?P<player>.+) has no card to reveal\.')

# Ill-Gotten Gains
# Matches: ... gaining nothing in the hand.
add_game_regex(r'gaining nothing in the hand\.')
# Matches: ... revealing a <card> and gaining nothing.
add_game_regex(r'revealing an? ' + card_regex_piece + r' but gaining nothing\.')

# Fool's Gold
# Matches: ... revealing a <card> but gaining nothing.
add_game_regex(r'revealing a ' + card_regex_piece + r' but gaining nothing\.')






# Separator matchers
br_regex = re.compile(r'\s*<br>$')
separator = '----------------------'

# Events that can be registered. This isn't documented super well now, but the features.py file
# has an example listener for each of these events.
parsing_line_event = 'parsing_line' # Three arg (game, line_num, line)
turn_complete_event = 'turn_complete' # One arg (game)
unhandled_line_event = 'unhandled_line' # Three arg (game, line_num, line)
unexpected_line_event = 'unexpected_line' # Four arg (game, line_num, line and regex [regex may be None])
parse_started_event = 'parse_start' # One arg (game)
parse_complete_event = 'parse_complete' # One arg (game)
parse_aborted_event = 'parse_abort' # Three arg (game, line_num, abort code)

# Reasons for aborting
assertion_abort = -1
single_player_abort = -2
resignation_abort = -3
tie_abort = -4
invalid_end_state_abort = -5
illegal_player_name_abort = -6
incomplete_file_abort = -7
duplicate_player_name_abort = -8
unhandled_line_abort = -9

# Most recent assertion that failed
assertion_exception = None
end_state_errors = None
illegal_player_name = None

def abort_string(abort):
    if abort == assertion_abort:
        return "Assertion Failed{0}".format(":\n{0}".format(assertion_exception) if assertion_exception else "")
    elif abort == single_player_abort:
        return "Single Player Game"
    elif abort == resignation_abort:
        return "Player Resigned"
    elif abort == tie_abort:
        return "Tie Game"
    elif abort == invalid_end_state_abort:
        return "Invalid End State{0}".format(":\n{0}".format('\n'.join(end_state_errors)) if end_state_errors else "")
    elif abort == illegal_player_name_abort:
        return "Illegal Player Name{0}".format(": '{0}'".format(illegal_player_name) if illegal_player_name else "")
    elif abort == incomplete_file_abort:
        return "Incomplete File (didn't finish extracting, most likely."
    elif abort == duplicate_player_name_abort:
        return "Duplicate player name{0}".format(": '{0}'".format(illegal_player_name) if illegal_player_name else "")
    elif abort == unhandled_line_abort:
        return "Unhandled line"
    else:
        return "Unknown Reason"

class isotropic_parser:

    def __init__(self):
        self.event_handlers = {}
        self.allow_single_player_games = False
        self.allow_games_with_resign = False
        self.allow_ties = False
        self.allow_invalid_end_state = False
        
    def register_handler(self, event, handler):
        self.event_handlers[event] = handler
        
    def handle_event(self, event, arg0 = None, arg1 = None, arg2 = None):
        if event in self.event_handlers:
            if arg0 is None:
                self.event_handlers[event](self.game)
            elif arg1 is None:
                self.event_handlers[event](self.game, arg0)
            elif arg2 is None:
                self.event_handlers[event](self.game, arg0, arg1)
            else:
                self.event_handlers[event](self.game, arg0, arg1, arg2)
        
    def read(self, filename):
        self.file = open(filename, 'rb')
        # Reset the game instance associated with this parser
        self.game = dominion_game()
        self.unhandled_lines = 0
        self.line_num = 0
        self.players = [] # cache list of players for regex player validation
        self.abort = False
        self.handle_event(parse_started_event)
        
        try:
            self.read_header()
            if not self.abort:
                self.read_scores()
            if not self.abort:
                self.read_game()
            if not self.abort:
                errors = self.game.validate_final_state()
                if errors:
                    if not self.allow_invalid_end_state:
                        self.abort = invalid_end_state_abort
                        global end_state_errors
                        end_state_errors = errors
                    else:
                        # If we don't break on these errors, we should at least print them out.
                        for error in errors:
                            print error
        except AssertionError as e:
            global assertion_exception
            assertion_exception = "{0}: {1}".format(self.line_num, e)
            self.abort = assertion_abort
        except StopIteration:
            # The next() iterator on the file most likely raised this because the file wasn't completely extracted
            self.abort = incomplete_file_abort
            
        self.file.close()
        if not self.abort:
            if self.unhandled_lines == 0:
                #print 'Parsing complete.'
                self.handle_event(parse_complete_event)
                return 0
            else:
                self.handle_event(parse_aborted_event, self.line_num, self.unhandled_lines)
                return self.unhandled_lines # Return the number of lines that were not matched
        else:
            self.handle_event(parse_aborted_event, self.line_num, self.abort)
            return self.abort # Aborting means this file should be skipped, as it is invalid for some reason (single player, players resigned, unprocessed cards)
        
    def read_header(self):
        # Get some game metadata from the first line
        first_line = self.next() # Read the first line
        match = first_line_regex.match(first_line)
        if match:
            # If the game was a tie, abort
            if not match.group('winner') and not self.allow_ties:
                self.abort = tie_abort
                return
            self.game.set_game_id(match.group('game_id'))
            self.game.set_winner(match.group('winner'))
        else:
            self.unmatched_line(first_line, first_line_regex)
            
        # Get the piles that signalled the end of the game
        empty_piles = self.next() # Read the line with the ending conditions
        # If this line says that the ending condition was people resigning, then abort
        if (empty_piles == 'All but one player has resigned.' or empty_piles == 'You have resigned.') and not self.allow_games_with_resign:
            self.abort = resignation_abort
            return
        foreach_card(empty_piles, lambda card: self.game.add_empty_pile(sanitize_card(card)))
            
        self.next() # Skip line 3
        
        # Read the cards that will be in the supply
        cards_in_supply = self.next()
        # Young Witch causes <span class=bane-star>&diams;</span> to be added as a 'card', but that will be filtered by the foreach_card
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
                # If only a single player was found, abort. We won't process single player games.
                if self.game.get_num_players() <= 1 and not self.allow_single_player_games:
                    self.abort = single_player_abort
                return
            
            match = player_first_line_regex.match(player_first_line)
            if match:
                resigned = match.group('resigned')
                if resigned and not self.allow_games_with_resign:
                    self.abort = resignation_abort
                    return
                place = int(match.group('place'))
                player = match.group('player')
                global illegal_player_name
                if player.startswith('... ') or player == 'and and and and':
                    illegal_player_name = player
                    self.abort = illegal_player_name_abort
                    return
                score = int(match.group('score'))
                turns = int(match.group('turns'))
                cards = match.group('cards')
                if (player in self.players):
                    # This is a duplicate player name
                    illegal_player_name = player
                    self.abort = duplicate_player_name_abort
                    return
                # Cache the player locally for regex validation
                self.players.append(player)
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
                if cards:
                    # Add the final deck contents for each player (for final validation)
                    foreach_card(cards, lambda card: self.game.add_final_deck(card, player))
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
        # Add the cards that are in the final trash pile (for validation)
        foreach_card(trash_line, lambda card: self.game.add_final_trash(card))
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
            self.unmatched_line(turn_order_line)
            
        self.next() # Read the blank line after the turn order
        
        for player in self.game.get_players():
            line = self.next()
            # Check for choosing/vetoing cards before reading starting hands
            match = chosen_cards_regex.match(line)
            if match:
                # There were chosen cards
                line = self.next() # Get the first veto line
                # We don't need to read the vetoed cards, so skip over all them
                while veto_card_regex.match(line):
                    line = self.next()
            match = draw_hand_regex.match(line)
            if match:
                player = match.group('player')
                cards = match.group('cards')
                foreach_card(cards, lambda card: self.game.draw(card, player))
            else:
                self.unmatched_line(line, draw_hand_regex)
            
        line = self.next() # Read the <brrevealine after each players starting hands
        if not br_regex.match(line):
            self.unmatched_line(line, br_regex)
        
        # Read each turn (read_turn() returns true until there's no more turns to read - thanks <brmoneyags)
        while (self.read_turn()):
            # If the turn spawned an abort error, bail out
            if self.abort:
                return
            
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
        
        line = self.next() # Read the next line
        # This loops until an empty line is found (which only occurs at the very end of the document), and then returns false, indicating there is not another turn to be read.
        # Otherwise, this will break out when a <bractionsas been found, which will cause this to return true.
        while len(line) != 0:
            #print 'Parsing line: {0}'.format(line)
            
            success = self.read_line(line)
            
            # If the line was not successfully read, print it so it can be added.
            if not success:
                self.unhandled_lines += 1
                self.handle_event(unhandled_line_event, self.line_num, line)
                #print
                #print 'Unknown line: {0}'.format(line)
                #print
                #exit(0) # Until a more complete set of parsing is built up, add things in one at a time
            
            line = self.next() # Read the next line
            
            # Check to see if the turn is over
            if br_regex.match(line):
                self.handle_event(turn_complete_event)
                return True
        # There is no more turn to read
        self.handle_event(turn_complete_event)
        return False
        
    def read_turn_header(self):
        turn_first_line = self.next()
        #print 'Parsing line: {0}'.format(turn_first_line)
        match = turn_header_regex.match(turn_first_line)
        if match:
            player = match.group('player')
            turn = int(match.group('turn'))
            self.game.start_new_turn(player, turn)
        else:
            # Maybe this is a possessed turn?
            match = possessed_turn_header_regex.match(turn_first_line)
            if match:
                possessor = match.group('possessor')
                possessee = match.group('possessee')
                self.game.start_new_turn(possessee, possessor=possessor)
            else:
                match = outpost_turn_header_regex.match(turn_first_line)
                if match:
                    player = match.group('player')
                    self.game.start_new_turn(player)
                else:
                    self.unmatched_line(turn_first_line, turn_header_regex)
                    self.unmatched_line(turn_first_line, possessed_turn_header_regex)
                    self.unmatched_line(turn_first_line, outpost_turn_header_regex)
                    
    # It should ALWAYS return True if the line was matched, that way the caller knows to
    # print other lines to warn that they weren't processed.
    def read_line(self, line):
        # Check the line to see what occurred.
        # Please keep the common/generic type lines first, for efficiencies sake.
        # Card specific checks should happen last, as they will only occur in games where that card is.
        
        # Loop through each regex we have for the game log, try it, and if it matches, call its corresponding matcher and return.
        for regex, matcher in game_log_regexes:
            match = regex.match(line)
            player = None
            # Sanity check the player (make sure that the player field doesn't eat parts that make this not really match. The .+ used to grab players is greedy.)
            if match and 'player' in match.groupdict():
                player = match.group('player')
                if player is not None and player not in self.players:
                    match = None
            # If there's still a match, call the matcher function with the game, match, and player (which could be None)
            if match:
                # Check the state of revealed cards - if there were revealed cards before processing this line, they were revealed by the last line and should be reset after this line.
                # This is because revealed cards should only affect the single line after them (its possible that the prefix could provide a better granularity to this...)
                reset_revealed = self.game.get_revealed()
                matcher(self.game, match, player)
                # Reset the revealed cards
                if reset_revealed:
                    self.game.reset_revealed()
                return True
            
        # Default return
        return False
        
    # This matches a regex, and if there is a 'player' group, makes sure the player is valid.
    # This is much easier than refreshing the regexes once the players names are found.
    # Note that as this is not called for the outpost or possession, their use of different names for players is not taken into account
    def regex(self, regex, line):
        match = regex.match(line)
        if match and 'player' in match.groupdict():
            # Sanity check the player (make sure that the player field doesn't eat parts that make this not really match. The .+ used to grab players is greedy.)
            player = match.group('player')
            if player is not None and player not in self.players:
                return None
        return match
    
    def unmatched_line(self, line, regex = None):
        if regex is None:
            self.handle_event(unexpected_line_event, self.line_num, line, None)
            #print 'Line didn\'t match:\n Line: {0}'.format(line)
        elif isinstance(regex, basestring):
            self.handle_event(unexpected_line_event, self.line_num, line, regex)
            #print 'Line didn\'t match:\n Line: {0}\n Pattern: {1}'.format(line, regex)
        else:
            self.handle_event(unexpected_line_event, self.line_num, line, regex.pattern)
            #print 'Line didn\'t match:\n Line: {0}\n Pattern: {1}'.format(line, regex.pattern)
        self.abort = unhandled_line_abort
        return
            
    def assert_current_player(self, player):
        assert self.game.get_player(player) is self.game.get_player(), "Acting player was not expected!"
    
    def next(self):
        s = unicode(self.file.next(), 'utf-8').strip()
        self.line_num += 1
        self.handle_event(parsing_line_event, self.line_num, s)
        return s

        
if __name__ == '__main__':
    parser = isotropic_parser()
    parser.read('test.html')
    