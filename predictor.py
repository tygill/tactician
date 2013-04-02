import json
import math
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
            self.load_input(label, Feature.sql_names[label].extract(game))
        
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
        for card in self.networks:
            network = self.networks[card]
            network.mark_stale()
            network.load_inputs(game)
            scores.append((self.unnormalize_score(network.get_output()), card))
        scores = sorted(scores)
        print scores

if __name__ == '__main__':
    game = DominionGame()
    game.add_card_to_supply('Adventurer')
    game.add_card_to_supply('Baron')
    game.add_card_to_supply('Council Room')
    game.add_card_to_supply('Moneylender')
    game.add_card_to_supply('Great Hall')
    game.add_card_to_supply('Throne Room')
    game.add_card_to_supply('Woodcutter')
    game.add_card_to_supply('Village')
    game.add_card_to_supply('Moat')
    game.add_card_to_supply('Chapel')
    
    game.add_player('Tyler')
    game.add_player('Wayne')
    
    game.init_game()
    
    game.start_new_turn('Tyler', 0) #increment_turn=True
    
    predictor = DominionBackpropPredictor()
    json_file = open('Chapel.json')
    json_str = json_file.read()
    json_file.close()
    predictor.add_network('Chapel', json_str)
    
    predictor.pick_card(game)
    