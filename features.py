from dominion import *
from isotropic import *
import sys
import os

# This class handles logging features to be trained on
class feature_extractor:
    
    def __init__(self, filename):
        self.file = open(filename, 'w')
        self.features = []
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
            
            
        # Add a separator
        ##self.add_feature(lambda game: "Outputs")
        
        # This adds lots of more finely weighted output features
        # Add the outputs (plural! a single, continuous output for every card that can be bought!)
        ##for card in sorted_cards:
        ##    self.add_card_output_feature(card)
        
    def add_feature(self, func, name):
        self.file.write("Adding feature: {0}\n".format(name))
        self.features.append(func)
        
    def add_card_in_supply_feature(self, card):
        self.add_feature(lambda game: 1 if game.is_card_in_supply(card) else 0, card)
        
    def add_card_output_feature(self, card):
        self.add_feature(lambda game: game.calc_output_weight() if card in game.get_cards_bought() else 0, "Output: {0}".format(card))
        
    def parsing_line_handler(self, game, line_num, line):
        #print 'Parsing line: {0}'.format(line)
        pass
        
    def turn_complete_handler(self, game):
        # Each card bought is a separate instance
        if game.get_cards_bought():
            for card_bought in game.get_cards_bought():
                self.write_instance(game, card_bought)
        else:
            self.write_instance(game, 'None')
        
    def write_instance(self, game, output):
        # Extract the information from the current game state and log it
        for feature in self.features:
            self.file.write(str(feature(game)) + ',')
        # Write the output (its not a traditional feature!)
        self.file.write('{0},{1}\n'.format(output, game.calc_output_weight()))
        self.instances += 1
        
    def unhandled_line_handler(self, game, line_num, line):
        print '{0}: Unhandled line: {1}'.format(line_num, line.encode('utf-8'))
        
    def unexpected_line_handler(self, game, line_num, line, regex = None):
        print
        if regex:
            print '{0}: Unexpected line: {1} (Expected: {2})'.format(line_num, line.encode('utf-8'), regex.encode('utf-8'))
        else:
            print '{0}: Unexpected line: {1}'.format(line_num, line.encode('utf-8'))
            
    def parse_complete_handler(self, game):
        self.files += 1
        
if __name__ == '__main__':
    parser = isotropic_parser()
    features = feature_extractor('features.txt')
    parser.register_handler(parsing_line_event, features.parsing_line_handler)
    parser.register_handler(turn_complete_event, features.turn_complete_handler)
    parser.register_handler(unhandled_line_event, features.unhandled_line_handler)
    parser.register_handler(unexpected_line_event, features.unexpected_line_handler)
    parser.register_handler(parse_complete_event, features.parse_complete_handler)
    
    log_path = 'games'
    subdir_path = '{0:04}/{1:02}/{2:02}'
    abort_path = 'ignored'
    if not os.path.exists(abort_path):
        os.makedirs(abort_path)
    # Iterate over all files in the log path
    # http://stackoverflow.com/questions/120656/directory-listing-in-python
    for dirname, dirnames, filenames in os.walk(log_path):
        for filename in filenames:
            file = os.path.join(dirname, filename)
            print 'Parsing: {0}'.format(file)
            error = parser.read(file)
            if error > 0:
                print '{0} unhandled lines in file: {1}'.format(error, file)
                # Move unmatched files to the root so they get found quicker in the future
                os.rename(file, os.path.join(log_path, filename))
                #exit(0)
            elif error < 0:
                print 'Aborting: {0}'.format(abort_string(error))
                if error != assertion_abort and error != invalid_end_state_abort:
                    print 'Moving {0} to {1}'.format(filename, abort_path)
                    os.rename(file, os.path.join(abort_path, filename))
                else:
                    # Move unmatched files to the root so they get found quicker in the future
                    os.rename(file, os.path.join(log_path, filename))
                    #exit(0)
                    pass
            else:
                match = re.match(r'game-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-\d{6}-[\d\w]{8}\.html', filename)
                if match:
                    year = int(match.group('year'))
                    month = int(match.group('month'))
                    day = int(match.group('day'))
                    full_file = os.path.join(log_path, subdir_path.format(year, month, day), filename)
                    if full_file != file:
                        os.rename(file, full_file)
    
    features.close()
    print 'Finished building features.'
    print 'Built {0} instances from {1} files.'.format(features.instances, files)