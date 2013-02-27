from dominion import *
from isotropic import *
import sys
import os

# This class handles logging features to be trained on
class feature_extractor:
    
    def __init__(self, filename):
        #self.file = open(filename, 'w')
        pass
        
    def parsing_line_handler(self, game, line_num, line):
        #print 'Parsing line: {0}'.format(line)
        pass
        
    def turn_complete_handler(self, game):
        # Extract the information from the current game state and log it
        pass
        
    def unhandled_line_handler(self, game, line_num, line):
        print '{0}: Unhandled line: {1}'.format(line_num, line.encode('utf-8'))
        
    def unexpected_line_handler(self, game, line_num, line, regex = None):
        print
        if regex:
            print '{0}: Unexpected line: {1} (Expected: {2})'.format(line_num, line.encode('utf-8'), regex)
        else:
            print '{0}: Unexpected line: {1}'.format(line_num, line.encode('utf-8'))
            
    def parse_complete_handler(self, game):
        print 'File complete.'
        
if __name__ == '__main__':
    parser = isotropic_parser()
    features = feature_extractor('features.txt')
    parser.register_handler(parsing_line_event, features.parsing_line_handler)
    parser.register_handler(turn_complete_event, features.turn_complete_handler)
    parser.register_handler(unhandled_line_event, features.unhandled_line_handler)
    parser.register_handler(unexpected_line_event, features.unexpected_line_handler)
    parser.register_handler(parse_complete_event, features.parse_complete_handler)
    
    log_path = 'games'
    # Iterate over all files in the log path
    # http://stackoverflow.com/questions/120656/directory-listing-in-python
    for dirname, dirnames, filenames in os.walk(log_path):
        for filename in filenames:
            file = os.path.join(dirname, filename)
            print 'Parsing: {0}'.format(file)
            errors = parser.read(file)
            if errors != 0:
                print 'Unhandled lines in file: {0}'.format(file)
                exit(0)
