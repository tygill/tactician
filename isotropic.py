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
# Designed to be used with finditer().
# Extracts a card name from its typical <span> wrapper, with a preceeding quantitiy
# Extracts:
#  card: Name of card (Note: might be plural!)
#  count: Number prefixing card (Note that it might be a or an as well as a number)
card_count_regex = re.compile('(?:(?P<count>[an\d]+) )?<[\\w=\\-"\' ]+>(?P<card>[\\w\\-\' ]+)<[/\\w=\\-"\' ]+>')

# Card list regex piece. This regex is never used, but the pieces of it are used in many other regexes.
#  cards
#card_list_regex = re.compile('(?P<cards>(?:(?:\d+|an?) <[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>,? ?)+(?:(?:and )?(?:\d+|an?) <[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>)?)')
card_list_regex_piece = u'(?P<cards>(?:(?:\d+|an?) (?:<[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>|\u25BC),? ?)+(?:(?:and )?(?:\d+|an?) (?:<[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>|\u25BC))?)'
card_list_no_count_regex_piece = '(?P<cards>(?:<[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>,? ?)+(?:(?:and )?<[\\w=\\-"\' ]+>[\\w\\-\' ]+<[/\\w=\\-"\' ]+>)?)'

# Matches the prefix to the line (the ...s)
prefix_piece = r'\s*(?:\.{3} )*'


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
#  score: Players final score (None, if they resigned)
#  cards: List of cards and counts (can be extraced with card_count_regex) (None, if the resigned)
#  turns: Number of turns the player had
#  resigned: Order of resignation
player_first_line_regex = re.compile(r'<b>#(?P<place>\d) (?P<player>.+)</b>: (?:(?P<score>[\d\-]+) points \(' + card_list_regex_piece + r'\)|resigned \((?P<resigned>\d+)\w+\)); (?P<turns>\d+) turns')
# Matches: (admittedly, card_regex could just be run on the whole line with the same result...)
#  card_one, card_two
player_second_line_regex = re.compile(r'\s*opening: (?P<card_one>.+) / (?P<card_two>.+)')
#  deck_size: Number of cards in deck (total)
#  cards: List of cards and counts in deck
player_third_line_regex = re.compile(r'\s*\[(?P<deck_size>\d+) cards?\] ' + card_list_regex_piece)

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
possessed_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w]+\\?s=40&d=identicon&r=PG" width=40 height=40 class=avatar><b>&mdash; (?P<possessee>.+)\'s turn \\(possessed by (?P<possessor>.+)\\) &mdash;</b>')
#  player: Player who got an extra turn
outpost_turn_header_regex = re.compile('\\s*<img src="http://www\\.gravatar\\.com/avatar/[\w]+\\?s=40&d=identicon&r=PG" width=40 height=40 class=avatar><b>&mdash; (?P<player>.+)\'s extra turn \\(from <span class=card-duration>Outpost</span>\\) &mdash;</b>')

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
        game.add_actions(int(match.group('actions')))
    if 'buys' in match.groupdict():
        game.add_buys(int(match.group('buys')))
    if 'money' in match.groupdict():
        game.add_money(int(match.group('money')))
    if 'vp' in match.groupdict():
        game.add_vp(int(match.group('vp')))
    if 'cost' in match.groupdict():
        game.reduce_cost(int(match.group('cost')))
    # Anything else is ignored.
    
def nothing_matcher(game = None, match = None, player = None):
    pass

def add_game_regex(regex_string, matcher = None):
    regex = re.compile(prefix_piece + regex_string)
    game_log_regexes.append((regex, matcher if matcher else nothing_matcher))
    return regex

# These are here to allow them to be used in callbacks
# Parses an extracted count into a number
def parse_count(count):
    if count == 'a' or count == 'an': # or count == 'the' # Does the ever get used?
        return 1
    elif count is not None:
        return int(count)
    else:
        return None
        
# Helper method for printing from lambda functions
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
#  player: Player who drew
#  cards: List of cards drawn (extract with card_count_regex)
draw_hand_regex = add_game_regex('<span class=logonly>\\((?P<player>.+)(?:\'s first hand| draws): ' + card_list_regex_piece + '\\.\\)</span>')

# Matches: <player> plays <cards>.
#  player: Player who played the cards, or None
#  cards: List of cards played (may be multiple, especially for treasures, both in quantity and type. e.g., 2 Coppers and a Silver)
play_cards_regex = add_game_regex(r'(?:(?P<player>.+) )?play(?:ing|s) ' + card_list_regex_piece + r'\.', lambda game, match, player: foreach_card(match.group('cards'), lambda card: game.play(card)))

# Matches: <player> buys a <card>.
#  player: Player who played the cards
#  card: Card purchased
buy_card_regex = add_game_regex(r'(?P<player>.+) buys an? ' + card_regex_piece + r'\.', lambda game, match, player: game.buy(match.group('card'), player))

# Matches: (<player> reshuffles.)
#  player: Player who reshuffled
reshuffle_regex = add_game_regex(r'\((?P<player>.+) reshuffles\.\)')

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
#  money: Amount of money added to the turn context
get_money_regex = add_game_regex(r'getting \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... getting +n action(s).
#  actions: Number of actions added
get_actions_regex = add_game_regex(r'getting \+(?P<actions>\d+) actions?\.', default_matcher)

# Matches: ... getting +n buy(s).
#  buys: Number of buys added
get_buys_regex = add_game_regex(r'getting \+(?P<buys>\d+) buys?\.', default_matcher)

# Matches: ... [<player>] draw[ing|s] n card(s).
#  player: Player who draws (if None, it means the current player)
#  cards: Number of cards drawn
draw_cards_regex = add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?P<cards>\d+) cards?(?: from the <span class=card-duration>Caravan</span>)?\.')

# Matches: ... drawing nothing.
drawing_nothing_regex = add_game_regex(r'drawing nothing\.')

# Matches: ... drawing n card[s] and getting +n buy[s].
#  player: Player (or None, meaning current player. Wharf gives a player)
#  cards: Number of cards drawn
#  buys: Number of buys added
draw_cards_get_buys_regex = add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?P<cards>\d+) cards? and get(?:ting|s) \+(?P<buys>\d+) buys?(?: from the <span class=card-duration>Wharf</span>)?\.', default_matcher)

# Matches: ... drawing n card[s] and getting +n action[s].
#  player: Player (or None. Not sure if anything will give a player.
#  cards: Cards drawn
#  actions: Actions added
draw_cards_get_actions_regex = add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?P<cards>\d+) cards? and get(?:ting|s) \+(?P<actions>\d+) actions?\.', default_matcher)

# Matches: ... drawing n card[s] and getting +$n.
#  player: Player (or None. Not sure if anything will give a player.
#  cards: Cards drawn
#  money: Money added
draw_cards_get_money_regex = add_game_regex(r'(?:(?P<player>.+) )?draw(?:ing|s) (?P<cards>\d+) cards? and get(?:ting|s) \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... drawing n cards and getting +n actions and +$n.
#  cards
#  actions
#  buys
#  money
draw_cards_get_actions_money_regex = add_game_regex(r'drawing (?P<cards>\d+) cards? and getting \+(?P<actions>\d+) actions? and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... drawing n cards and getting +n actions, +n buys, and +$n.
#  cards
#  actions
#  buys
#  money
draw_cards_get_actions_buys_money_regex = add_game_regex(r'drawing (?P<cards>\d+) cards? and getting \+(?P<actions>\d+) actions?, \+(?P<buys>\d+) buys?, and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... getting +b buys and +$n.
#  player
#  buys
#  money
get_buys_money_regex = add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+(?P<buys>\d+) buys? and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... getting +n actions, +n buys, and +$n.
#  actions
#  buys
#  money
get_actions_buys_money_regex = add_game_regex(r'getting \+(?P<actions>\d+) actions?, \+(?P<buys>\d+) buys?, and \+\$(?P<money>\d+)\.', default_matcher)

# Matches: ... getting +n vpsym.
#  player
#  vp
get_vp_regex = add_game_regex(r'(?:(?P<player>.+) )?get(?:ting|s) \+(?P<vp>\d+) ' + get_victory_symbol() + r'\.', default_matcher)

# Matchs: ... getting +$2 and +1 vpsym.
#  money
#  mp
get_money_vp_regex = add_game_regex(r'getting \+\$(?P<money>\d+) and \+(?P<vp>\d+) ' + get_victory_symbol() + r'\.', default_matcher)

# Matches: ... [making] [<player>] discard[ing|s] <cards>. ('making' is from Scrying Pool, and perhaps others)
#  player: Player, or None for current player
#  cards: List of cards discarded (may be from deck or hand or who knows where)
discard_cards_regex = add_game_regex(r'(?:making )?(?:(?P<player>.+) )?discard(?:ing|s|) ' + card_list_regex_piece + r'\.')

# Matches: ... <player> discards [n|a] cards.
#  player
#  cards: Number of cards discarded (may be 'a'!)
discard_count_regex = add_game_regex(r'(?:(?P<player>.+) )?discard(?:ing|s) (?P<cards>[\d|a]+) cards?\.')

# Matches: ... [<player>] put[ting|s] <cards> back on the deck.
#  player
#  cards
#  order: First on top part
put_cards_on_deck_regex = add_game_regex(r'(?:(?P<player>.+) )?put(?:ting|s) ' + card_list_regex_piece + r' back on the deck(?: \((?P<order>first on top)\))?\.')

# Matches: ... [<player>] put[ting|s] [n|a] cards back on the deck[ (first on top)].
#  player
#  cards: Number of cards (might be 'a'!)
put_count_on_deck_regex = add_game_regex(r'(?:(?P<player>.+) )?put(?:ting|s) (?P<cards>[\da]+) cards? back on the deck\.')

# Matches: ... [<player>] gain[ing|s] a <card>[ in/on the hand/deck].
#  player: Player who gains something (if None, it means the current player)
#  card: The card gained.
#  where: Where the card is gained (None means discard. Others: hand (Ill-Gotten Gains), deck (Fool's Gold))
gain_cards_regex = add_game_regex(r'(?:(?P<player>.+) )?gain(?:ing|s) an? ' + card_regex_piece + r'(?: [io]n (?:the )?(?P<where>hand|deck))?\.', lambda game, match, player: game.gain(match.group('card'), player))

# Matches: ... There's nothing for <player> to gain.
#  player: Player who didn't gain anything
nothing_to_gain_regex = add_game_regex(r"There's nothing for (?P<player>.+) to gain\.")

# Matches: ... [<player>] trash[ing|es] <cards>.
#  player: Player who trashed a card (or None, meaning current player)
#  cards: Cards trashed
trash_cards_regex = add_game_regex(r'(?:(?P<player>.+) )?trash(?:ing|es) ' + card_list_regex_piece + r'\.', lambda game, match, player: foreach_card(match.group('cards'), lambda card: game.trash(card, player)))

# Matches: ... <player> trashes nothing.
#  player: Player who didn't trash anything
nothing_to_trash_regex = add_game_regex(r'(?P<player>.+) trashes nothing\.')

# Used by Fortune Teller, Pirate Ship, Scrying Pool, etc...
# Matches: ... [<player>] reveal[int|s] <cards>[ and putting them in the hand| and keeping it| and discarding it].
#  player: Player who reveals cards (or None if current player)
#  cards: Cards revealed
#  where: Where they are put (None for doesn't move)
reveal_cards_regex = add_game_regex(r'(?:(?P<player>.+) )?reveal(?:ing|s) ' + card_list_regex_piece + r'(?: and put(?:ting|s) (?:them|it) [io]n the (?P<where>hand)| and keeping (?:them|it)| and discarding (?:them|it))?\.')

# Matches: ... <player> does nothing.
#  player
does_nothing_regex = add_game_regex(r'(?P<player>.+) does nothing\.')


# Card Specific Regexes
# ---------------------

# Swindler
#  player: Player who trashes something
#  card: Card trashed
swindler_trash_regex = add_game_regex(r'(?P<player>.+) turns up an? ' + card_regex_piece + r' and trashes it\.', lambda game, match, player: game.trash(match.group('card'), player))
#  player: Player whose cards were replaced
#  old_card: Card trashed (same as card extracted from trash_regex above)
#  new_card: New card gained to replace it
def swindler_replace_matcher(game, match, player):
    game.trash(match.group('old_card'), player)
    game.gain(match.group('new_card'), player)
swindler_replace_regex = add_game_regex(r"replacing (?P<player>.+)'s " + card_regex_piece_formatable.format('old_card') + r' with an? ' + card_regex_piece_formatable.format('new_card') + r'\.', swindler_replace_matcher)

# Fortune Teller - others?
# Matches: <player> puts the <card> back onto the deck.
#  player
#  card
fortune_teller_put_cards_on_deck_regex = add_game_regex(r'(?P<player>.+) puts the ' + card_regex_piece + r' back onto the deck\.')

# Farming Village
# Matches: ... putting the <card> into the hand.
#  card
farming_village_put_cards_in_hand_regex = add_game_regex(r'putting the ' + card_regex_piece + r' into the hand\.')

# Talisman
# Matches: ... gaining another <card>.
#  card
talisman_gaining_another_regex = add_game_regex(r'gaining another ' + card_regex_piece + r'\.', lambda game, match, player: game.gain(match.group('card'), player))

# Jack of All Trades (and perhaps others? Sea Hag maybe?)
# Matches: ... discarding the top card of the deck.
jack_of_all_trades_discarding_top_card_regex = add_game_regex(r'discarding the top card of the deck\.')

# Noble Brigand (perhaps others?)
# Matches: ... <player> reveals and discards <cards>.
#  player
#  cards: Cards revealed and discarded
noble_brigand_reveal_and_discard_regex = add_game_regex(r'(?P<player>.+) reveals and discards ' + card_list_regex_piece + r'\.')
# Matches: ... <player> draws and reveals <cards, trashing a <card>.
#  player
#  cards: Cards revealed and discarded
#  card: Card trashed
noble_brigand_draw_reveal_trash_regex = add_game_regex(r'(?P<player>.+) draws and reveals ' + card_list_regex_piece + r', trashing an? ' + card_regex_piece + r'\.', lambda game, match, player: game.trash(match.group('card'), player))
# Matches: ... <player> gains the <card>.
#  player
#  card
noble_brigand_gain_from_trash_regex = add_game_regex(r'(?P<player>.+) gains the ' + card_regex_piece + r'\.', lambda game, match, player: game.gain(match.group('card'), player, 'trash'))

# Mining Village (slightly more generic than mining village requires, might catch other cards.)
# Matches: ... trashing the <span class=card-none>Mining Village</span> for +$2.
def mining_village_matcher(game, match, player):
    game.trash(match.group('card'), player)
    game.add_money(int(match.group('money')))
mining_village_trashing_regex = add_game_regex(r'trashing the ' + card_regex_piece + r' for \+\$(?P<money>\d+)\.', mining_village_matcher)

# Bank (and Philosopher's Stone)
#  money
#  deck_size
#  discard_size
bank_philosophers_stone_worth_regex = add_game_regex(r'which is worth \+\$(?P<money>\d+)(?: \((?P<deck_size>\d+) cards in deck, (?P<discard_size>\d+) cards in discard\))?\.', default_matcher)

# Royal Seal
#  card
royal_seal_putting_on_deck_regex = add_game_regex(r'putting the ' + card_regex_piece + r' on top of the deck\.')

# Tournament
#  player
#  discard: Card discarded
#  gain: Card gained
tournament_gain_prize_regex = add_game_regex(r'(?P<player>.+) discards an? ' + card_regex_piece_formatable.format('discard') + r' and gains an? ' + card_regex_piece_formatable.format('gain') + r' on the deck\.', lambda game, match, player: game.gain(match.group('gain'), player, 'prizes' if match.group('gain') != 'Duchy' else 'supply'))

# Bag of Gold
#  card: Should be a Gold
bag_of_gold_gain_gold_regex = add_game_regex(r'gaining a ' + card_regex_piece + r' on the deck\.', lambda game, match, player: game.gain(match.group('card'), player))

# Only has 3 (n) cards (Goons, Militia, Ghost Ship, etc.)
#  player
#  cards: Number of cards
only_has_n_cards_regex = add_game_regex(r'(?P<player>.+) only has (?P<cards>\d+) cards?\.')

# Reducing all costs by n (Princess, Highway)
#  cost: How much everything is reduced by
reducing_all_costs_regex = add_game_regex(r'reducing all costs by \$(?P<cost>\d+)\.', default_matcher)

# Bridge
#  buys
#  money
#  cost: Reduction
bridge_regex = add_game_regex(r'getting \+(?P<buys>\d+) buys?, \+\$(?P<money>\d+), and reducing all costs by \$(?P<cost>\d+)\.', default_matcher)

# Black Market
#  cards
black_market_draw_regex = add_game_regex(r'drawing ' + card_list_regex_piece + r' from the <span class=card-none>Black Market</span> deck\.')
#  player
#  card
#black_market_buy_regex = add_game_regex(r'(?P<player>.+) buys a ' + card_regex_piece + r'\.')
#  cards
black_market_return_regex = add_game_regex(r'returning ' + card_list_regex_piece + r' to the bottom of the <span class=card-none>Black Market</span> deck\.')

# Bishop
#  card: Card trashed
#  vp: VP received
def bishop_trash_matcher(game, match, player):
    game.trash(match.group('card'), player)
    game.add_vp(int(match.group('vp')))
bishop_trash_regex = add_game_regex(r'(?P<player>.+) trashes an? ' + card_regex_piece + r' and gets \+(?P<vp>\d+) ' + get_victory_symbol() + r'\.', bishop_trash_matcher)

# Salvager
#  card: Card trashed
#  money: Money received
#  vp: VP received
def salvager_trash_regex(game, match, player):
    game.trash(match.group('card'), player)
    # Call the default matcher for money and buys
    default_matcher(game, match, player)
salvager_trash_regex = add_game_regex(r'trashing an? ' + card_regex_piece + r' for \+\$(?P<money>\d+) and \+(?P<buys>\d+) buys?\.')

# Scrying Pool (discarding is built into the main discarder)
#  card: Card kept on the deck
scrying_pool_keep_regex = add_game_regex(r'letting (?P<player>.+) keep an? ' + card_regex_piece + r'\.')

# Nomad Camp
nomad_camp_put_on_deck_regex = add_game_regex(r'putting it on the deck\.')




# Separator matchers
br_regex = re.compile(r'\s*<br>$')
separator = '----------------------'

# Events that can be registered. This isn't documented super well now, but the features.py file
# has an example listener for each of these events.
parsing_line_event = 'parsing_line' # Two arg (line_num, line)
turn_complete_event = 'turn_complete' # No args
unhandled_line_event = 'unhandled_line' # Two arg (line_num, line)
unexpected_line_event = 'unexpected_line' # Three arg (line_num, line and regex [regex may be None])
parse_complete_event = 'parse_complete' # No args

# Reasons for aborting
single_player_abort = -1
resignation_abort = -2

def abort_string(abort):
    if abort == single_player_abort:
        return "Single Player Game"
    elif abort == resignation_abort:
        return "Player Resigned"
    else:
        return "Unknown Reason"

class isotropic_parser:

    # Since this is the most interesting function (it's where each line gets processed),
    # it's at the top to make getting to it easier.
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
                matcher(self.game, match, player)
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
    
    def __init__(self):
        self.event_handlers = {}
        self.allow_single_player_games = False
        self.allow_games_with_resign = False
        
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
        
        self.read_header()
        if not self.abort:
            self.read_scores()
        if not self.abort:
            self.read_game()
        self.file.close()
        if not self.abort:
            return self.unhandled_lines # Return the number of lines that were not matched
        else:
            return self.abort # Aborting means this file should be skipped, as it is invalid for some reason (single player, players resigned, unprocessed cards)
        
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
                score = int(match.group('score'))
                turns = int(match.group('turns'))
                cards = match.group('cards')
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
            
        line = self.next() # Read the <br> line after each players starting hands
        if not br_regex.match(line):
            self.unmatched_line(line, br_regex)
        
        # Read each turn (read_turn() returns true until there's no more turns to read - thanks <brmoneyags)
        while (self.read_turn()):
            # If the turn spawned an abort error, bail out
            if self.abort:
                return
            
        #print 'Parsing complete.'
        self.handle_event(parse_complete_event)
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
            self.handle_event(unexpected_line_event, self.line_num, line, None)
            #print 'Line didn\'t match:\n Line: {0}'.format(line)
        elif isinstance(regex, basestring):
            self.handle_event(unexpected_line_event, self.line_num, line, regex)
            #print 'Line didn\'t match:\n Line: {0}\n Pattern: {1}'.format(line, regex)
        else:
            self.handle_event(unexpected_line_event, self.line_num, line, regex.pattern)
            #print 'Line didn\'t match:\n Line: {0}\n Pattern: {1}'.format(line, regex.pattern)
            
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
    