from dominion import *
from isotropic import *
import sys
import os
from optparse import OptionParser

def pr(s):
    print s.encode('utf-8')
    
def clean(card):
    return card.replace("'", "").replace(" ", "_")

# This class handles logging features to be trained on
class feature_extractor:
    
    def __init__(self, filename):
        self.file = open(filename, 'w')
        self.file.write('@RELATION dominion\n\n')

        self.features = []
        self.pending_instances = []
        self.files = 0
        self.instances = 0
        
        self.init_features()
        
    def close(self):
        self.file.close()
        
    def init_features(self):
        # Get a sorted list of all cards
        sorted_cards = sorted(cards)
        # Add the cards features
        for card in sorted_cards:
            self.add_card_in_supply_feature(card)
            
        # Add the ratio features
        self.add_feature(lambda game: game.get_player().get_action_card_ratio(), "Deck Action Card Ratio")
        self.add_feature(lambda game: game.get_player().get_victory_card_ratio(), "Deck Victory Card Ratio")
        self.add_feature(lambda game: game.get_player().get_treasure_card_ratio(), "Deck Treasure Card Ratio")
        self.add_feature(lambda game: game.turn_number, "Turn Number")
        self.add_feature(lambda game: game.money, "Money")
        self.add_feature(lambda game: game.buys, "Buys")
        self.add_feature(lambda game: game.actions, "Actions")
        
            
        # Add a separator
        ##self.add_feature(lambda game: "Outputs")
        
        # This adds lots of more finely weighted output features
        # Add the outputs (plural! a single, continuous output for every card that can be bought!)
        ##for card in sorted_cards:
        ##    self.add_card_output_feature(card)
        
        # Output features are hard coded in.
        self.file.write("@ATTRIBUTE 'Card_Bought' {None," + ','.join(map(clean, cards)) + '}\n')
        self.file.write("@ATTRIBUTE 'Card_Output_Weight' REAL\n")
        
        # Close the features
        self.file.write('\n@DATA:\n')
        
    def add_feature(self, func, name, values = 'REAL'):
        self.file.write("@ATTRIBUTE '{0}' {1}\n".format(clean(name), values if isinstance(values, basestring) else '{' + ','.join(map(str, values)) + '}'))
        self.features.append(func)
        
    def add_card_in_supply_feature(self, card):
        self.add_feature(lambda game: 1 if game.is_card_in_supply(card) else 0, card, [0, 1])
        
    #def add_card_output_feature(self, card):
    #    self.add_feature(lambda game: game.calc_output_weight() if card in game.get_cards_bought() else 0, "Output: {0}".format(card), [])
        
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
        instance = ','.join([str(feature(game)) for feature in self.features]) + ',{0},{1}'.format(clean(card), game.calc_output_weight())
        self.pending_instances.append(instance)
        
    def unhandled_line_handler(self, game, line_num, line):
        pr('{0}: Unhandled line: {1}'.format(line_num, line))
        
    def unexpected_line_handler(self, game, line_num, line, regex = None):
        print
        if regex:
            pr('{0}: Unexpected line: {1} (Expected: {2})'.format(line_num, line, regex))
        else:
            pr('{0}: Unexpected line: {1}'.format(line_num, line))
            
    def parse_started_handler(self, game):
        pass
            
    def parse_complete_handler(self, game):
        self.files += 1
        for instance in self.pending_instances:
            self.file.write(instance)
            self.file.write('\n')
            self.instances += 1
        del self.pending_instances[:]
        
    def parse_aborted_handler(self, game, line_num, error):
        del self.pending_instances[:]
        
log_path = 'games'
subdir_path = os.path.join('{0:04}', '{1:02}', '{2:02}')
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
        try:
            os.rename(old, new)
        except OSError:
            # The file must have already existed, so try to delete the old file and replace it
            if os.path.exists(new):
                os.remote(new)
            # Now try again
            os.rename(old, new)
    
def process_file(dirname, filename):
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
            rename(filename, dirname, ignore_path)
    else:
        match = re.match(r'game-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-\d{6}-[\d\w]{8}\.html', filename)
        if match:
            year = int(match.group('year'))
            month = int(match.group('month'))
            day = int(match.group('day'))
            rename(filename, dirname, os.path.join(log_path, subdir_path.format(year, month, day)))
    
if __name__ == '__main__':
    parser = isotropic_parser()
    features = feature_extractor('features.arff')
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
        print ' -ng: Don\'t process the main directory'
        exit(0)
    
    # Process ignored files
    if process_ignored:
        for filename in os.listdir(ignore_path):
            if os.path.isfile(os.path.join(ignore_path, filename)):
                process_file(ignore_path, filename)
    
    # Process errored files
    if process_errors:
        for filename in os.listdir(error_path):
            if os.path.isfile(os.path.join(error_path, filename)):
                process_file(error_path, filename)
    
    # Process unhandled files
    if process_unhandled:
        for filename in os.listdir(unhandled_path):
            if os.path.isfile(os.path.join(unhandled_path, filename)):
                process_file(unhandled_path, filename)
    
    # Iterate over all files in the log path
    # http://stackoverflow.com/questions/120656/directory-listing-in-python
    if process_main:
        for dirname, dirnames, filenames in os.walk(log_path):
            for filename in filenames:
                process_file(dirname, filename)
            # Don't walk over the other paths, as they are iterated separately.
            if ignore_path in dirnames:
                dirnames.remove(ignore_path)
            if error_path in dirnames:
                dirnames.remove(error_path)
            if unhandled_path in dirnames:
                dirnames.remove(unhandled_path)
    
    features.close()
    print 'Finished building features.'
    print 'Built {0} instances from {1} files.'.format(features.instances, features.files)