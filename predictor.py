import json
import math
import sys
import os
import os.path
from features import *
from dominion import *

class BackpropNode(object):
    def __init__(self, network, id):
        self.network = network
        self.id = id
        
    def get_output(self):
        pass
        
class BiasNode(BackpropNode):
    def __init__(self, network, id):
        super(BiasNode, self).__init__(network, id)
        
    def get_output(self):
        return 1
        
class InputNode(BackpropNode):
    def __init__(self, network, id, label):
        super(InputNode, self).__init__(network, id)
        self.label = label
        self.out = 0.0
        
    def set_output(self, out):
        self.out = out
        
    def get_output(self):
        return self.out
        
class HiddenNode(BackpropNode):
    def __init__(self, network, id, weights):
        super(HiddenNode, self).__init__(network, id)
        self.weights = {}
        for key in weights:
            self.weights[int(key)] = weights[key]
        self.stale = True
        self.out = 0.0
        
    def mark_stale(self):
        self.stale = True
        
    def get_output(self):
        if self.stale:
            net = 0.0
            for node in self.weights:
                net += self.weights[node] * self.network.get_node(node).get_output()
            # Convert to sigmoid output
            self.out = 1.0 / (1.0 + math.exp(-net))
            self.stale = False
        return self.out
        
class OutputNode(BackpropNode):
    def __init__(self, network, id, weights):
        super(OutputNode, self).__init__(network, id)
        self.weights = {}
        for key in weights:
            self.weights[int(key)] = weights[key]
        self.stale = True
        self.out = 0.0
        
    def mark_stale(self):
        self.stale = True
        
    def get_output(self):
        if self.stale:
            net = 0.0
            for node in self.weights:
                net += self.weights[node] * self.network.get_node(node).get_output()
            # Leave continuous output
            self.out = net
            self.stale = False
        return self.out
        
class BackpropNetwork:
    def __init__(self, card, json_str):
        # Input nodes are mapped to by label. This makes updating based on the current state of the game easier.
        self.inputs = {}
        # Nodes that can be marked stale (hidden and output)
        self.staleable_nodes = []
        # Assume a single output node
        self.output = None
        # All nodes in the system are here, indexed by id.
        self.nodes = {}
        
        self.card = card
        self.load_json(json_str)
        
    def load_json(self, json_str):
        json_object = json.loads(json_str)
        # Read in the bias node
        for json_node in json_object['bias']:
            node = BiasNode(self, json_node['id'])
            self.nodes[node.id] = node
        # Read in the input nodes
        for json_node in json_object['inputs']:
            node = InputNode(self, json_node['id'], json_node['label'])
            self.nodes[node.id] = node
            self.inputs[node.label] = node
        # Read in the hidden nodes
        for json_node in json_object['hidden']:
            node = HiddenNode(self, json_node['id'], json_node['weights'])
            self.nodes[node.id] = node
            self.staleable_nodes.append(node)
        # Read in the output node
        for json_node in json_object['output']:
            node = OutputNode(self, json_node['id'], json_node['weights'])
            self.nodes[node.id] = node
            self.staleable_nodes.append(node)
            self.output = node
            
    def get_node(self, id):
        return self.nodes[id]
        
    def load_input(self, label, val):
        self.inputs[label].set_output(val)
        
    def load_inputs(self, game):
        for label in self.inputs:
            self.load_input(label, Feature.sql_names[label].extract(game, self.card))
        
    def mark_stale(self):
        for node in self.staleable_nodes:
            node.mark_stale()
            
    def get_output(self):
        return self.output.get_output()

class DominionBackpropPredictor:
    def __init__(self):
        self.networks = {}
        self.average = 38.25765735;
        self.stddev = 18.68538455;
        self.normalization_min = self.average - (2 * self.stddev)
        self.normalization_max = self.average + (2 * self.stddev)
        
    def add_network(self, card, json_str):
        self.networks[card] = BackpropNetwork(card, json_str)
        
    def unnormalize_score(self, score):
        return (score * (self.normalization_max - self.normalization_min)) + self.normalization_min
        
    def pick_card(self, game):
        scores = []
        for card in game.get_cards_in_supply(): #self.networks:
            network = self.networks[card]
            network.mark_stale()
            network.load_inputs(game)
            scores.append((self.unnormalize_score(network.get_output()), card))
        scores.sort()
        scores.reverse()
        return scores
    
#def predict(game, count):
#    
        
# Game loop regexes
# (more of them....)
predictor_loop_regexes = []

def add_predictor_regex(regex_string, matcher, msg):
    regex = re.compile(r'\s*' + regex_string + r'\s*')
    predictor_loop_regexes.append((regex, matcher, msg))
    return regex
    
#add_predictor_regex(,
#    lambda game, match, player: predict(game, int(match.group('count')) if match.group('count') else 5),
#    lambda match, player: None)
add_predictor_regex(r'(?:(?P<player>.*) )?(?:add )?actions?(?: (?P<actions>-?\d+))?',
    lambda game, match, player: game.add_actions(int(match.group('actions'))) if match.group('actions') else game.add_actions(1),
    lambda match, player: "Adding {0} actions".format(int(match.group('actions')) if match.group('actions') else 1))
add_predictor_regex(r'(?:(?P<player>.*) )?plays?(?: (?P<actions>-?\d+))?',
    lambda game, match, player: game.add_actions(-int(match.group('actions'))) if match.group('actions') else game.add_actions(-1),
    lambda match, player: "Subtracting {0} actions".format(int(match.group('actions')) if match.group('actions') else 1))
add_predictor_regex(r'(?:(?P<player>.*) )?(?:add )?buys?(?: (?P<buys>-?\d+))?',
    lambda game, match, player: game.add_buys(int(match.group('buys'))) if match.group('buys') else game.add_buys(1),
    lambda match, player: "Giving {0} buys".format(int(match.group('buys')) if match.group('buys') else 1))
add_predictor_regex(r'(?:(?P<player>.*) )?(?:add )?(?:money|coin)s?(?: (?P<money>-?\d+))?',
    lambda game, match, player: game.add_money(int(match.group('money'))) if match.group('money') else game.add_money(1),
    lambda match, player: "Giving {0} money".format(int(match.group('money')) if match.group('money') else 1))
add_predictor_regex(r'(?:(?P<player>.*) )?(?:add )?vps?(?: (?P<vp>-?\d+))?',
    lambda game, match, player: game.add_vp(int(match.group('vp')), player) if match.group('vp') else game.add_vp(1, player),
    lambda match, player: "Giving {0} vp tokens to player {1}".format(int(match.group('vp')) if match.group('vp') else 1, player.name))
add_predictor_regex(r'(?:(?P<player>.*) )?(?:reduce )?costs?(?: by)?(?: (?P<cost>-?\d+))?',
    lambda game, match, player: game.reduce_cost(int(match.group('cost'))) if match.group('cost') else game.reduce_cost(1),
    lambda match, player: "Reducing costs by {0}".format(int(match.group('cost')) if match.group('actions') else 1))
add_predictor_regex(r'(?:(?P<player>.*) )?gains? (?P<card>.*)',
    lambda game, match, player: game.gain(clean_card(match.group('card')), player),
    lambda match, player: "{0} gaining a {1}".format(player.name, clean_card(match.group('card'))))
add_predictor_regex(r'(?:(?P<player>.*) )?trashe?s? (?P<card>.*)',
    lambda game, match, player: game.trash(clean_card(match.group('card')), player),
    lambda match, player: "{0} trashing a {1}".format(player.name, clean_card(match.group('card'))))


if __name__ == '__main__':
    # Setup the predictor
    predictor = DominionBackpropPredictor()
    # Assume backprop, as thats what we know how to load
    folder = sys.argv[1] if len(sys.argv) >1 else 'Backprop'
    for file in os.listdir(folder):
        card, ext = os.path.splitext(file)
        card = clean_card(card)
        if not card:
            card = 'None'
        if ext == '.json':
            #print 'Loading {0} predictor'.format(card)
            json_file = open(os.path.join(folder, file))
            json_str = json_file.read()
            json_file.close()
            predictor.add_network(card, json_str)
    
    # Setup the game
    game = DominionGame()
    
    print 'Setup the initial supply'
    done = False
    while not done:
        line = raw_input(' Add card: ')
        card = clean_card(line)
        if line is '' or line.lower() == 'done':
            done = True
        elif card:
            game.add_card_to_supply(card)
            print '  Adding {0} to supply'.format(card)
        else:
            print '  Unrecognized card: {0}'.format(line)
            print "   Enter 'done' to finish"
            
    print
    print 'Setup players'
    done = False
    players = []
    while not done:
        line = raw_input(' Add player: ')
        if line is '' or line.lower() == 'done':
            if players:
                done = True
            else:
                print '  Add at least one player first'
        else:
            players.append(line)
            game.add_player(line)
    
    # Start the game
    print
    print 'Starting Game!'
    game.init_game()
    
    # Bootstrap the game
    cur_player = 0
    game.start_new_turn(players[0], 1) #increment_turn=True
    
    # Game lop
    predict_regex = re.compile(r'predict(?: (?P<count>\d+))?')
    done = False
    while not done:
        print
        print "{0}'s turn {1}, {2} actions {3} buys ${4}".format(game.get_player(game.possessor).name, game.turn_number, game.actions, game.buys, game.money)
        line = raw_input("> ")
        
        if line == 'quit':
            done = True
            continue
        
        if line == 'next turn' or line == 'turn':
            cur_player = (cur_player + 1) % len(players)
            game.start_new_turn(players[cur_player], increment_turn=cur_player == 0)
            continue
        
        match = predict_regex.match(line)
        if match:
            count = int(match.group('count')) if match.group('count') else 5
            scores = predictor.pick_card(game)
            print ' Predictions:'
            for i in range(count):
                print '  {0} ({1})'.format(scores[i][1], scores[i][0])
        
        for regex, matcher, msg_func in predictor_loop_regexes:
            match = regex.match(line)
            if match:
                player = game.possessor
                if 'player' in match.groupdict():
                    if match.group('player'):
                        player = match.group('player')
                player = game.get_player(player)
                matcher(game, match, player)
                msg = msg_func(match, player)
                if msg:
                    print ' {0}'.format(msg)
        
    
    #print 'Predictions:'
    #scores = predictor.pick_card(game)
    #
    #for score in scores:
    #    print ' {0} ({1})'.format(score[1], score[0])