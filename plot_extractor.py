import math
import re
import os
import os.path

def unnormalize(val, min, max):
    return (val * (max - min)) + min

if __name__ == "__main__":
    
    #instance_count_regex = re.compile(r'(?P<card>.+): (?P<total>\d+) Instances \((?P<training>\d+) training, (?P<validation>\d+) validation, (?P<testing>\d+) testing\)')
    #training_sse_regex = re.compile(r' SSE \(training set\):   (?P<sse>\d+\.\d+)')
    #validation_sse_regex = re.compile(r' SSE \(validation set\): (?P<sse>\d+\.\d+)')
    #testing_sse_regex = re.compile(r' SSE \(testing set\):    (?P<sse>\d+\.\d+)')
    #epoch_regex = re.compile(r' Trained on (?P<trained>\d+) instances over (?P<epochs>\d+) epochs')
    testing_mse_regex = re.compile(r' MSE \(testing set\):    (?P<mse>\d*\.\d*) \(\d*\.\d*\)')
    
    #total_count = 0
    #training_count = 0
    #validation_count = 0
    #testing_count = 0
    #
    #training_sse = 0.0
    #validation_sse = 0.0
    #testing_sse = 0.0
    #trained_count = 0
    
    files = 0
    epochs = 0
    for filename in os.listdir('.'):
        name, ext = os.path.splitext(filename)
        if ext == '.txt':
            files += 1
            file = open(filename, 'r')
            for line in file:
                #match = instance_count_regex.match(line)
                #if match:
                #    total_count += int(match.group('total'))
                #    training_count += int(match.group('training'))
                #    validation_count += int(match.group('validation'))
                #    testing_count += int(match.group('testing'))
                #match = training_sse_regex.match(line)
                #if match:
                #    training_sse += float(match.group('sse'))
                #match = validation_sse_regex.match(line)
                #if match:
                #    validation_sse += float(match.group('sse'))
                #match = testing_sse_regex.match(line)
                #if match:
                #    testing_sse += float(match.group('sse'))
                #match = epoch_regex.match(line)
                #if match:
                #    trained_count += int(match.group('trained'))
                #    epochs += int(match.group('epochs'))
                match = testing_mse_regex.match(line)
                if match:
                    print '{0}\t{1}'.format(name, match.group('mse'))
            file.close()
    
    #min = 0.88688825
    #max = 75.62842645
    #print " Trained a total of {0} instances over {1} epochs".format(trained_count, epochs)
    #print " Trained an average of {0} instances over {1} epochs".format(round(float(trained_count) / files), round(float(epochs) / files, 2))
    #print " Total SSE (training sets):   {0:.3f} ({1:.3f})".format(round(training_sse, 3), round(unnormalize(math.sqrt(training_sse), min, max), 3))
    #print " Total SSE (validation sets): {0:.3f} ({1:.3f})".format(round(validation_sse, 3), round(unnormalize(math.sqrt(validation_sse), min, max), 3))
    #print " Total SSE (testing sets):    {0:.3f} ({1:.3f})".format(round(testing_sse, 3), round(unnormalize(math.sqrt(testing_sse), min, max), 3))
    #print " Total MSE (training sets):   {0:.3f} ({1:.3f})".format(round(training_sse / training_count, 3), round(unnormalize(math.sqrt(training_sse / training_count), min, max), 3))
    #print " Total MSE (validation sets): {0:.3f} ({1:.3f})".format(round(validation_sse / validation_count, 3), round(unnormalize(math.sqrt(validation_sse / validation_count), min, max), 3))
    #print " Total MSE (testing sets):    {0:.3f} ({1:.3f})".format(round(testing_sse / testing_count, 3), round(unnormalize(math.sqrt(testing_sse / testing_count), min, max), 3))