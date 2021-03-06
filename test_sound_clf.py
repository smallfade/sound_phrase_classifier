from gensim.models import KeyedVectors
import numpy as np
from sklearn import svm
import random, nltk, sys, os, re
from gensim.scripts.glove2word2vec import glove2word2vec
from sklearn.externals import joblib
import pickle







def process_doc(filename):
    punctuation = '!"#$%&()*+,-./:;<=>?@[\\]^_{|}~'
    temp_data = []
    raw_file = open(filename, 'r')
    data = ' '.join(raw_file.read().split())
    findings = re.findall('sounds?\sof\s(\S+?\s\S+?)\s', data)

    for phrase in findings:
        tokens = nltk.word_tokenize(phrase)
        tokens = nltk.pos_tag(tokens)

        justtags = map(lambda x: x[1], tokens)
        justtags = list(justtags)

        if justtags[0] == 'DT':
            justtags.pop(0)


        phraselen = 0
        if len(justtags) == 1:
            if justtags[0] == 'VBG':
                phraselen = 1
            elif justtags[0] == 'NN' or justtags[0] == 'NNS':
                phraselen = 1
            else:
                phraselen = 0
        else:
            if justtags[0] == 'VBG':
                if justtags[1] == 'NN' or justtags[1] == 'NNS':
                    phraselen = 2 #(DT) VBG NN(S)
                else:
                    phraselen = 1 # VBG

            elif justtags[0] == 'NN' or justtags[0] == 'NNS':
                if (justtags[1] =='NN' or justtags[1] == 'NNS') and justtags[0] == 'NN':
                    phraselen = 2 # (DT) NN NN(S)
                elif justtags[1] == 'VBG':
                    phraselen = 2 # (DT) NN(S) VBG
                else:
                    phraselen = 1 # (DT) NN(S)

            elif justtags[0] == 'JJ':
                if justtags[1] =='NN' or justtags[1] == 'NNS':
                    phraselen = 2 # (DT) JJ NN(S)
            else:
                phraselen = 0 # did not match

        if phraselen != 0:
            phrase = ' '.join(phrase.split()[:phraselen])
            translator = str.maketrans('','',punctuation)
            phrase = phrase.translate(translator)
            temp_data.append(phrase)

    return temp_data



def vectorify(data, vector_model, glove):
    temp_data = []
    vectors = []

    # goes through all training/testing examples
    for example in data:

        #makes sure dataline is not empty
        if example:
            sound = example.split()


            if len(sound) == 1:
                sound += sound
            assert(len(sound) == 2)


            # Makes lowercase
            if sound[0] not in vector_model:
                sound[0] = sound[0].lower()
            if sound[1] not in vector_model:
                sound[1] = sound[1].lower()


            #Makes sure at least one word is found in embeddings vector dict
            if sound[0] in vector_model or sound[1] in vector_model:
                if sound[0] in vector_model:
                    one = vector_model[sound[0]]

                #unknown word handling
                else:
                    one = vector_model['unk']

                if sound[1] in vector_model:
                    two = vector_model[sound[1]]

                #unknown word handling
                else:
                    two = vector_model['unk']

                #concatenates vectors together
                vector = list(one) + list(two)
                sound = ' '.join(sound)
                temp_data.append(sound)
                vectors.append(vector)

    return(temp_data, vectors)








# Reads command line arguments
if len(sys.argv) != 6:
    sys.exit('Wrong number of arguments - ERROR')
else:
    if sys.argv[1] == 'glove':
        glove = True
    elif sys.argv[1] == 'word2vec':
        glove = False
    else:
        sys.exit("ERROR")

vectors_filename = sys.argv[2]
clf_filename = sys.argv[3]
test_filename = sys.argv[4]
sentences = sys.argv[5].lower()

if sentences == 'true':
    sentences = True
elif sentences == 'false':
    sentences = False
else:
    sys.exit('ERROR - check data filetype (True/False)')





# Loads the vector model (either word2vec or GloVe)
print("Loading vector embeddings...")
if glove:
    if os.path.isfile(vectors_filename+'.word2vec'):
        vector_model = KeyedVectors.load_word2vec_format(vectors_filename+'.word2vec',binary=False)
    else:
        glove2word2vec(vectors_filename, vectors_filename+'.word2vec')
        vector_model = KeyedVectors.load_word2vec_format(vectors_filename+'.word2vec',binary=False)
else:
    vector_model = KeyedVectors.load_word2vec_format(vectors_filename, binary=True)



# Loads the SVM classifier from file
print("Loading SVM sound classifier...")
clf = pickle.load(open(clf_filename, 'rb'))



# Processes test data
print("Processing test data...")
if sentences:
    data = process_doc(test_filename)
else:
    test = open(test_filename,'r')
    data = test.read().split('\n')




(data,vectors) = vectorify(data, vector_model, glove)
num_sounds = len(data)
predictions = clf.predict(vectors)
confidence = clf.decision_function(vectors)
finalsounds = []

assert(len(confidence) == len(predictions))
output_filename = 'results.txt'
output = open(output_filename, 'w')
for index in range(num_sounds):
    if predictions[index]:
        output.write(data[index] + ',' + str(confidence[index]) + '\n')

output.close()


print('List of sounds can be found in ' + output_filename)
