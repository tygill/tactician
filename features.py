from dominion import *
from isotropic import *
import sys
import traceback
import os
import time
from optparse import OptionParser
import sqlite3
import re

def pr(s):
    print s.encode('utf-8')
    
def clean(s):
    return s.replace("'", "").replace(" ", "_")
    
def sqlclean(s):
    return re.sub(r'[\W]+', '', s.replace(" ", "_").lower())
    
    
class Feature:
    features = []
    sql_names = {}
    
    def __init__(self, name, func, values):
        self.name = name
        self.arff_name = clean(name)
        self.sql_name = sqlclean(name)
        Feature.sql_names[self.sql_name] = self
        self.func = func
        self.values = values
        
    def extract(self, game, bought):
        return self.func(game, bought)

def add_feature(func, name, values = 'REAL'):
    Feature.features.append(Feature(name, func, values))
    
def add_card_feature(card):
    add_feature(lambda game, bought: 1 if game.is_card_in_supply(card) else 0, '{0} in Supply?'.format(card), [0, 1])
    
def add_card_acquired_feature(card):
    add_feature(lambda game, bought: game.get_card_acquired_count(card) / game.card_initial_supply(card) if game.card_initial_supply(card) != 0 else 0, "{0} Acquired".format(pluralize_card(card)))
    
def add_my_card_feature(card):
    add_feature(lambda game, bought: game.get_player(game.possessor).get_card_count(card) / game.card_initial_supply(card) if game.card_initial_supply(card) != 0 else 0, "{0} In Player Deck".format(pluralize_card(card)))
    
# Binners
# Bins money to 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12+
def bin_money_feature(money):
    if money >= 12:
        money = 12
    money -= 1
    return money / 11.0
        
# Bins buys to 1, 2, 3, 4, 5+
def bin_buys_feature(buys):
    if buys >= 5:
        buys = 5
    buys -= 1
    return buys / 4.0
        
# Bins actions to 1, 2-4, 5-7, 8-10, 11-15, 16-20, 21-29, 30+
def bin_actions_feature(actions):
    if actions <= 1:
        ret = 0
    elif actions <= 4:
        ret = 1
    elif actions <= 7:
        ret = 2
    elif actions <= 10:
        ret = 3
    elif actions <= 15:
        ret = 4
    elif actions <= 20:
        ret = 5
    elif actions <= 29:
        ret = 6
    else:
        ret = 7
    return ret / 7.0
    
# Game features
# Add the cards features
for card in sorted(supply_cards):
    # Python lambda's make this need to be a separate function. That way, card is a new scope.
    #add_card_feature(card)
    pass
add_feature(lambda game, bought: game.get_num_players() / 6.0, "Number of Players")
add_feature(lambda game, bought: 1 if game.supply_contains_any(plus_action_cards) else 0, "+Action Cards in Supply?", [0, 1]) # +2 Action or more cards only. Chaining cards (+1 Action) don't count.
add_feature(lambda game, bought: 1 if game.supply_contains_any(plus_buy_cards) else 0, "+Buy Cards in Supply?", [0, 1])
add_feature(lambda game, bought: 1 if game.supply_contains_any(drawing_cards) else 0, "Drawing Cards in Supply?", [0, 1]) # +2 Cards or more only. 
add_feature(lambda game, bought: 1 if game.supply_contains_any(cursing_cards) else 0, "Cursing Cards in Supply?", [0, 1])
add_feature(lambda game, bought: 1 if game.supply_contains_any(trashing_cards) else 0, "Trashing Cards in Supply?", [0, 1])
add_feature(lambda game, bought: 1 if game.supply_contains_any(attack_cards) else 0, "Attack Cards in Supply?", [0, 1])
add_feature(lambda game, bought: 1 if game.supply_contains_any(potion_cards) else 0, "Potion Cards in Supply?", [0, 1])

# Move context features
# This is normalized by looking at the max in the 8 gb dataset. 61 was the max, so this should be good.
add_feature(lambda game, bought: (game.turn_number - 1.0) / 50.0, "Turn Number")
add_feature(lambda game, bought: bin_money_feature(game.money), "Money")
add_feature(lambda game, bought: bin_buys_feature(game.buys), "Buys")
add_feature(lambda game, bought: bin_actions_feature(game.actions), "Actions")

# Game state features
add_feature(lambda game, bought: game.get_num_empty_piles() / 3.0, "Empty Piles")
# Add features for how many of each victory card have been bought so far (in games where they aren't in the supply, they are now set to 0 to indicate that none have been bought)
for card in sorted(victory_cards):
    # Again, this needs to be in a separate function to make the card get stored in the closure
    add_card_acquired_feature(card)
add_card_acquired_feature('Curse')

# Player deck stats
# Using game.get_player(game.possessor) gets the stats for the controlling player - either the possessor, or the regular player (as it will be None if there isn't a possessor, in which case the regular player will be retrieved.)
# This will need to be normalized by the runner
# Again, these are normalized by looking at the max of the large dataset
add_feature(lambda game, bought: game.get_player(game.possessor).get_deck_size() / 100.0, "Player Deck Size")
add_feature(lambda game, bought: game.get_player(game.possessor).get_action_card_count() / 40.0, "Player Deck Action Cards")
add_feature(lambda game, bought: game.get_player(game.possessor).get_victory_card_count() / 20.0, "Player Deck Victory Cards")
add_feature(lambda game, bought: game.get_player(game.possessor).get_treasure_card_count() / 60.0, "Player Deck Treasure Cards")
add_feature(lambda game, bought: game.get_player(game.possessor).get_action_card_count() / (game.get_player(game.possessor).get_deck_size() if game.get_player(game.possessor).get_deck_size() != 0 else 1), "Player Deck Action Card Ratio")
add_feature(lambda game, bought: game.get_player(game.possessor).get_victory_card_count() / (game.get_player(game.possessor).get_deck_size() if game.get_player(game.possessor).get_deck_size() != 0 else 1), "Player Deck Victory Card Ratio")
add_feature(lambda game, bought: game.get_player(game.possessor).get_treasure_card_count() / (game.get_player(game.possessor).get_deck_size() if game.get_player(game.possessor).get_deck_size() != 0 else 1), "Player Deck Treasure Card Ratio")
# How many of each card are in my deck?
for card in sorted(cards):
    #add_my_card_feature(card)
    pass
# How many of the card that was bought are already in my deck?
add_feature(lambda game, bought: game.get_player(game.possessor).get_card_count(bought) / game.card_initial_supply(bought) if bought != "None" else 0, "Already In Player Deck")
    
# Output features
add_feature(lambda game, bought: game.get_player(game.possessor).get_current_score(), "Player Current Score")
add_feature(lambda game, bought: game.get_player(game.possessor).get_final_score() - game.get_player(game.possessor).get_current_score(), "Player Score Increase")
add_feature(lambda game, bought: game.get_player(game.possessor).get_final_score(), "Player Final Score")
add_feature(lambda game, bought: game.get_average_final_score(), "Average Final Score")

# Timestamp features
add_feature(lambda game, bought: int(game.game_id, 16), "Game Id")
add_feature(lambda game, bought: game.year, "Game Year")
add_feature(lambda game, bought: game.month, "Game Month")
add_feature(lambda game, bought: game.day, "Game Day")
add_feature(lambda game, bought: game.hour, "Game Hour")
add_feature(lambda game, bought: game.minute, "Game Minute")
add_feature(lambda game, bought: game.second, "Game Second")

    
    
# This class handles logging features to be trained on
class FeatureExtractor:
    
    def __init__(self, filename, arff=True, sql=False):
        self.dbcon = None
        self.db = None
        
        self.features = []
        self.pending_instances = []
        self.files = 0
        self.ignored_files = 0
        self.instances = 0
        
        self.arff = arff
        if self.arff:
            self.file = open(filename, 'w')
            self.file.write('@RELATION dominion\n\n')

        self.init_features()
        
        self.sql = sql
        if self.sql:
            self.init_db()
        
    def close(self):
        if self.arff:
            self.file.close()
        if self.sql:
            # Create the indexes
            sql = "CREATE INDEX IF NOT EXISTS card_bought_index ON instances (card_bought);"
            self.db.execute(sql)
            #sql = "CREATE INDEX IF NOT EXISTS use_index ON instances (use);"
            #self.db.execute(sql)
            sql = "CREATE INDEX IF NOT EXISTS game_second_index ON instances (game_second);"
            self.db.execute(sql)
            
            self.dbcon.commit()
            self.dbcon.close()
        
    def init_features(self):
        # Add the features
        for feature in Feature.features:
            self.add_feature(feature)
        
        if self.arff:
            # Output features are hard coded in.
            self.file.write("@ATTRIBUTE 'Card_Bought' {None," + ','.join(map(clean, sorted(supply_cards))) + '}\n')
            self.file.write("@ATTRIBUTE 'Card_Output_Weight' REAL\n")
            #self.file.write("@ATTRIBUTE 'Player_Final_Score' REAL\n")
            #self.file.write("@ATTRIBUTE 'Average_Final_Score' REAL\n")
            
            # Close the features
            self.file.write('\n@DATA:\n')
        
    def add_feature(self, feature):
        if self.arff:
            self.file.write("@ATTRIBUTE '{0}' {1}\n".format(feature.arff_name, feature.values if isinstance(feature.values, basestring) else '{' + ','.join(map(str, features.values)) + '}'))
        self.features.append(feature)
        
    def init_db(self):
        self.dbcon = sqlite3.connect("features.sql3")
        self.db = self.dbcon.cursor()
        
        # Drop the table if it was already there
        sql = "DROP TABLE IF EXISTS instances;"
        self.db.execute(sql)
        
        # Create the table
        sql = """
            CREATE TABLE IF NOT EXISTS instances (
                id INTEGER PRIMARY KEY,
                {0}
                card_bought TEXT,
                card_output_weight REAL,
                use TEXT DEFAULT NULL,
                randomizer INT
            );
        """.format('\n                '.join(self.get_sql_create_columns())) # '\n                '
        #player_final_score REAL,
        #average_final_score REAL,
        
        #print sql
        self.db.execute(sql)
        
        # Shrink the db size back down
        sql = "VACUUM;"
        self.db.execute(sql)
        
    def get_sql_type(self, values):
        if isinstance(values, basestring) and (values.lower() == 'real' or values.lower() == 'continuous'):
            return 'REAL'
        elif isinstance(values, list) and len(values) > 0:
            if isinstance(values[0], int):
                return 'INT'
            elif isinstance(values[0], str):
                return 'TEXT'
        return None
        
    def get_sql_create_columns(self):
        cols = []
        for feature in self.features:
            cols.append('{0} {1},'.format(feature.sql_name, self.get_sql_type(feature.values)))
        return cols
        
    def add_sql_instance(self, instance):
        sql = """
            INSERT INTO instances VALUES (
                NULL,
                {0},
                NULL,
                NULL
            );
        """.format(''.join(self.get_sql_values(instance))) # '\n                '
        
        #print sql
        self.db.execute(sql)
        
    def get_sql_values(self, instance):
        cols = []
        for i in range(len(self.features)):
            if self.features[i].values == 'TEXT':
                cols.append("'{0}',".format(instance[i]))
            else:
                cols.append('{0},'.format(instance[i]))
        cols.append("'{0}',".format(instance[-2]))
        cols.append('{0}'.format(instance[-1]))
        #cols.append('{0},'.format(instance[-2]))
        #cols.append('{0}'.format(instance[-1]))
        return cols
        
    def parsing_line_handler(self, game, line_num, line):
        #print 'Parsing line: {0}'.format(line)
        pass
        
    def turn_complete_handler(self, game):
        # Each card bought is a separate instance
        if game.get_cards_bought():
            for card in game.get_cards_bought():
                self.write_instance(game, card)
        else:
            self.write_instance(game, 'None')
        
    def write_instance(self, game, card):
        # Extract the information from the current game state and log it
        instance = [feature.extract(game, card) for feature in self.features]
        instance.append(clean(card))
        instance.append(game.calc_output_weight(game.possessor)) # Using game.possessor will use either the possessing player, or the current player if there isn't a possessor.
        #instance.append(game.get_player(game.possessor).get_final_score())
        #instance.append(game.get_average_final_score())
        #instance = ','.join() + ',{0},{1}'.format(clean(card), game.calc_output_weight(game.possessor))
        self.pending_instances.append(instance)
        
    def flush_instances(self):
        for instance in self.pending_instances:
            self.instances += 1
            if self.arff:
                self.file.write(','.join([str(feature) for feature in instance]) + '\n')
            if self.sql:
                self.add_sql_instance(instance)
                #if self.instances % 100 == 0:
                #    self.dbcon.commit()
        del self.pending_instances[:]
        
    def unhandled_line_handler(self, game, line_num, line):
        pr(u'{0}: Unhandled line: {1}'.format(line_num, line))
        
    def unexpected_line_handler(self, game, line_num, line, regex = None):
        print
        if regex:
            pr(u'{0}: Unexpected line: {1} (Expected: {2})'.format(line_num, line, regex))
        else:
            pr(u'{0}: Unexpected line: {1}'.format(line_num, line))
            
    def parse_started_handler(self, game):
        pass
            
    def parse_complete_handler(self, game):
        self.files += 1
        self.flush_instances()
        
    def parse_aborted_handler(self, game, line_num, error):
        self.ignored_files += 1
        del self.pending_instances[:]
        
subdir_path = os.path.join('{0:04}', '{1:02}', '{2:02}')
log_path = 'games'
ignore_folder = 'ignored'
ignore_path = os.path.join(log_path, ignore_folder)
error_folder = 'error'
error_path = os.path.join(log_path, error_folder)
unhandled_folder = 'unhandled'
unhandled_path = os.path.join(log_path, unhandled_folder)
if not os.path.exists(ignore_path):
    os.makedirs(ignore_path)
if not os.path.exists(error_path):
    os.makedirs(error_path)
if not os.path.exists(unhandled_path):
    os.makedirs(unhandled_path)
    
def rename(filename, src, dest):
    old = os.path.join(src, filename)
    new = os.path.join(dest, filename)
    if old != new:
        print 'Moving {0} from\n {1}\n to\n {2}'.format(filename, src, dest)
        if not os.path.exists(dest):
            os.makedirs(dest)
        try:
            os.rename(old, new)
        except OSError:
            # The file must have already existed, so try to delete the old file and replace it
            if os.path.exists(new):
                os.remove(new)
            # Now try again
            os.rename(old, new)
    
def process_file(dirname, filename):
    match = re.match(r'game-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})-[\d\w]{8}\.html', filename)
    if match:
        year = int(match.group('year'))
        month = int(match.group('month'))
        day = int(match.group('day'))
        hour = int(match.group('hour'))
        minute = int(match.group('minute'))
        second = int(match.group('second'))
    file = os.path.join(dirname, filename)
    print 'Parsing: {0}'.format(file)
    error = parser.read(file)
    if error > 0:
        print '{0} unhandled lines in file: {1}'.format(error, file)
        rename(filename, dirname, unhandled_path)
    elif error < 0:
        print 'Aborting: {0}'.format(abort_string(error))
        if error == assertion_abort or error == invalid_end_state_abort:
            rename(filename, dirname, error_path)
        elif error == incomplete_file_abort:
            # Delete the file, as reextracting it will put the complete file here.
            os.remove(file)
        else:
            rename(filename, dirname, os.path.join(ignore_path, subdir_path.format(year, month, day)))
    else:
        rename(filename, dirname, os.path.join(log_path, subdir_path.format(year, month, day)))
    
if __name__ == '__main__':
    parser = IsotropicParser()
    features = FeatureExtractor('features.arff', '-arff' in sys.argv, '-no-sql' not in sys.argv)
    parser.register_handler(parsing_line_event, features.parsing_line_handler)
    parser.register_handler(turn_complete_event, features.turn_complete_handler)
    parser.register_handler(unhandled_line_event, features.unhandled_line_handler)
    parser.register_handler(unexpected_line_event, features.unexpected_line_handler)
    parser.register_handler(parse_started_event, features.parse_started_handler)
    parser.register_handler(parse_complete_event, features.parse_complete_handler)
    parser.register_handler(parse_aborted_event, features.parse_aborted_handler)
    
    process_ignored = '-i' in sys.argv
    process_unhandled = '-u' in sys.argv
    process_errors = '-e' in sys.argv
    process_main = '-n' not in sys.argv
    if '-h' in sys.argv:
        print 'Command line args:'
        print ' -i: Reprocess ignored directory'
        print ' -u: Reprocess unhandled directory'
        print ' -e: Reprocess error directory'
        print ' -n: Don\'t process the main directory'
        #print ' -sql: Export to sqlite db (default)'
        print ' -no-sql: Don\'t export to sqlite db'
        print ' -arff: Export an arff file'
        #print ' -no-arff: Don\'t export an arff file (default)'
        exit(0)
        
    # Start our overall timer
    start = time.time()
    try:
        
        # Process ignored files
        if process_ignored:
            for dirname, dirnames, filenames in os.walk(ignore_path):
                for filename in filenames:
                    process_file(dirname, filename)
                # Walk over the directories in reverse order (in case they're nested)
                dirnames.sort(reverse=True)
        
        # Process errored files
        if process_errors:
            for dirname, dirnames, filenames in os.walk(error_path):
                for filename in filenames:
                    process_file(dirname, filename)
                # Walk over the directories in reverse order (in case they're nested)
                dirnames.sort(reverse=True)
        
        # Process unhandled files
        if process_unhandled:
            for dirname, dirnames, filenames in os.walk(unhandled_path):
                for filename in filenames:
                    process_file(dirname, filename)
                # Walk over the directories in reverse order (in case they're nested)
                dirnames.sort(reverse=True)
        
        # Iterate over all files in the log path
        # http://stackoverflow.com/questions/120656/directory-listing-in-python
        if process_main:
            for dirname, dirnames, filenames in os.walk(log_path):
                # Filter out everything but a single day
                #if dirname == os.path.join(log_path, '2013', '03', '10'):
                for filename in filenames:
                    process_file(dirname, filename)
                # Don't walk over the other paths, as they are iterated separately.
                # This assumes that these folders are all subfolders of the main log folder, which should currently be the case.
                if ignore_folder in dirnames:
                    dirnames.remove(ignore_folder)
                if error_folder in dirnames:
                    dirnames.remove(error_folder)
                if unhandled_folder in dirnames:
                    dirnames.remove(unhandled_folder)
                # Walk over the directories in reverse order (this will search 2013 before 2012, 31 before 01, etc. This makes sure it starts the feature extraction with the most recent data.)
                dirnames.sort(reverse=True)
    except KeyboardInterrupt:
        print 'Bailing out due to Ctrl-C'
    except Exception, e:
        print 'Catching "{0}" on line {1}'.format(e, sys.exc_info()[-1].tb_lineno)
        ex_type, ex, tb = sys.exc_info()
        traceback.print_tb(tb)
        
    features.close()
    print 'Finished building features. (Took {0} minutes)'.format((time.time() - start) / 60.0)
    print 'Built {0} instances from {1} files.'.format(features.instances, features.files)
    print 'Ignored {0} files.'.format(features.ignored_files)