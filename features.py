from dominion import *
from isotropic import *
import sys
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

# This class handles logging features to be trained on
class feature_extractor:
    
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
            sql = "CREATE INDEX card_bought_index ON instances (card_bought);"
            self.db.execute(sql)
            
            self.dbcon.commit()
            self.dbcon.close()
        
    def init_features(self):
        # Get a sorted list of all cards
        sorted_supply_cards = sorted(supply_cards)
            
        # Add the features
        
        # Game features
        # Add the cards features
        for card in sorted_supply_cards:
            # Python lambda's make this need to be a separate function. That way, card is a new scope.
            self.add_card_feature(card)
        self.add_feature(lambda game: game.get_num_players(), "Number of Players")
        self.add_feature(lambda game: 1 if game.supply_contains_any(plus_action_cards) else 0, "+Action Cards in Supply?", [0, 1]) # +2 Action or more cards only. Chaining cards (+1 Action) don't count.
        self.add_feature(lambda game: 1 if game.supply_contains_any(plus_buy_cards) else 0, "+Buy Cards in Supply?", [0, 1])
        self.add_feature(lambda game: 1 if game.supply_contains_any(drawing_cards) else 0, "Drawing Cards in Supply?", [0, 1]) # +2 Cards or more only. 
        self.add_feature(lambda game: 1 if game.supply_contains_any(cursing_cards) else 0, "Cursing Cards in Supply?", [0, 1])
        self.add_feature(lambda game: 1 if game.supply_contains_any(trashing_cards) else 0, "Trashing Cards in Supply?", [0, 1])
        self.add_feature(lambda game: 1 if game.supply_contains_any(attack_cards) else 0, "Attack Cards in Supply?", [0, 1])
        
        # Move context features
        self.add_feature(lambda game: game.turn_number, "Turn Number")
        self.add_feature(lambda game: game.money, "Money")
        self.add_feature(lambda game: game.buys, "Buys")
        self.add_feature(lambda game: game.actions, "Actions")
        
        # Game state features
        self.add_feature(lambda game: game.get_num_empty_piles(), "Number of Empty Piles")
        # Add features for how many of each victory card are left in the supply (in games where they aren't in the supply, I've set them to instead be however many there would to start if they would be in the supply)
        for card in sorted(victory_cards):
            # Again, this needs to be in a separate function to make the card get stored in the closure
            self.add_card_left_feature(card)
        self.add_feature(lambda game: game.get_supply_count('Curse', True), "Curses Left")
        
        # Player deck stats
        # Using game.get_player(game.possessor) gets the stats for the controlling player - either the possessor, or the regular player (as it will be None if there isn't a possessor, in which case the regular player will be retrieved.)
        self.add_feature(lambda game: game.get_player(game.possessor).get_deck_size(), "Deck Size")
        self.add_feature(lambda game: game.get_player(game.possessor).get_action_card_ratio(), "Deck Action Card Ratio")
        self.add_feature(lambda game: game.get_player(game.possessor).get_victory_card_ratio(), "Deck Victory Card Ratio")
        self.add_feature(lambda game: game.get_player(game.possessor).get_treasure_card_ratio(), "Deck Treasure Card Ratio")
        
            
        if self.arff:
            # Output features are hard coded in.
            self.file.write("@ATTRIBUTE 'Card_Bought' {None," + ','.join(map(clean, sorted_supply_cards)) + '}\n')
            self.file.write("@ATTRIBUTE 'Card_Output_Weight' REAL\n")
            
            # Close the features
            self.file.write('\n@DATA:\n')
        
    def add_feature(self, func, name, values = 'REAL'):
        if self.arff:
            self.file.write("@ATTRIBUTE '{0}' {1}\n".format(clean(name), values if isinstance(values, basestring) else '{' + ','.join(map(str, values)) + '}'))
        self.features.append((name, func, clean(name), sqlclean(name), values))
        
    def add_card_feature(self, card):
        self.add_feature(lambda game: 1 if game.is_card_in_supply(card) else 0, '{0} in Supply?'.format(card), [0, 1])
        
    def add_card_left_feature(self, card):
        self.add_feature(lambda game: game.get_supply_count(card, True), "{0} Left".format(pluralize_card(card)))
        
    def init_db(self):
        self.dbcon = sqlite3.connect("features.sql3")
        self.db = self.dbcon.cursor()
        
        # Create the table
        sql = """
            CREATE TABLE IF NOT EXISTS instances (
                id INTEGER PRIMARY KEY,
                {0}
                card_bought TEXT,
                card_output_weight REAL
            );
        """.format(''.join(self.get_sql_create_columns())) # '\n                '
        
        #print sql
        self.db.execute(sql)
        
        # Delete everything from the table
        sql = "DELETE FROM instances;"
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
        for name, func, arff, sql, values in self.features:
            cols.append('{0} {1},'.format(sql, self.get_sql_type(values)))
        return cols
        
    def add_sql_instance(self, instance):
        sql = """
            INSERT INTO instances VALUES (
                NULL,
                {0}
            );
        """.format(''.join(self.get_sql_values(instance))) # '\n                '
        
        #print sql
        self.db.execute(sql)
        
    def get_sql_values(self, instance):
        cols = []
        for i in range(len(self.features)):
            if self.features[i][4] == 'TEXT':
                cols.append("'{0}',".format(instance[i]))
            else:
                cols.append('{0},'.format(instance[i]))
        cols.append("'{0}',".format(instance[-2]))
        cols.append('{0}'.format(instance[-1]))
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
        instance = [feature(game) for name, feature, arff, sql, values in self.features]
        instance.append(clean(card))
        instance.append(game.calc_output_weight(game.possessor)) # Using game.possessor will use either the possessing player, or the current player if there isn't a possessor.
        #instance = ','.join() + ',{0},{1}'.format(clean(card), game.calc_output_weight(game.possessor))
        self.pending_instances.append(instance)
        
    def flush_instances(self):
        for instance in self.pending_instances:
            self.instances += 1
            if self.arff:
                self.file.write(','.join([str(feature) for feature in instance]) + '\n')
            if self.sql:
                self.add_sql_instance(instance)
                if self.instances % 100 == 0:
                    self.dbcon.commit()
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
ignore_path = os.path.join(log_path, 'ignored')
error_path = os.path.join(log_path, 'error')
unhandled_path = os.path.join(log_path, 'unhandled')
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
                os.remote(new)
            # Now try again
            os.rename(old, new)
    
def process_file(dirname, filename):
    match = re.match(r'game-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-\d{6}-[\d\w]{8}\.html', filename)
    if match:
        year = int(match.group('year'))
        month = int(match.group('month'))
        day = int(match.group('day'))
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
    parser = isotropic_parser()
    features = feature_extractor('features.arff', '-no-arff' not in sys.argv, '-sql' in sys.argv)
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
    process_main = '-ng' not in sys.argv
    if '-h' in sys.argv:
        print 'Command line args:'
        print ' -i: Reprocess ignored directory'
        print ' -u: Reprocess unhandled directory'
        print ' -e: Reprocess error directory'
        print ' -n: Don\'t process the main directory'
        print ' -sql: Export to sqlite db'
        print ' -no-arff: Don\'t export an arff file'
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
                for filename in filenames:
                    process_file(dirname, filename)
                # Don't walk over the other paths, as they are iterated separately.
                # This assumes that these folders are all subfolders of the main log folder, which should currently be the case.
                if ignore_path in dirnames:
                    dirnames.remove(ignore_path)
                if error_path in dirnames:
                    dirnames.remove(error_path)
                if unhandled_path in dirnames:
                    dirnames.remove(unhandled_path)
                # Walk over the directories in reverse order (this will search 2013 before 2012, 31 before 01, etc. This makes sure it starts the feature extraction with the most recent data.)
                dirnames.sort(reverse=True)
    except KeyboardInterrupt:
        print 'Bailing out due to Ctrl-C'
    except Exception, e:
        print 'Catching {0}'.format(e)
        
    features.close()
    print 'Finished building features. (Took {0} minutes)'.format((time.time() - start) / 60.0)
    print 'Built {0} instances from {1} files.'.format(features.instances, features.files)
    print 'Ignored {0} files.'.format(features.ignored_files)