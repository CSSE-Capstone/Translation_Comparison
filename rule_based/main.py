from collections import Counter
import operator
import copy
import re
import nltk
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.sentiment.util import *
from nltk import tokenize
from nltk.corpus import stopwords
from nltk.tag import PerceptronTagger, UnigramTagger
from nltk.data import find
from nltk.tokenize import word_tokenize
import pandas as pd
import string
import networkx as nx
import matplotlib.pyplot as plt
import nltk.tag, nltk.data

## Download Resources # TODO rm?
nltk.download("vader_lexicon")
nltk.download("stopwords")
nltk.download("averaged_perceptron_tagger")
nltk.download("wordnet")
nltk.download('treebank')
nltk.download('maxent_treebank_pos_tagger')




class RuleBased:
    def __init__(self, noun_grammar, chunker, lemmatizer, stemmer, tagger):
        self.noun_grammar = noun_grammar
        self.chunker = chunker
        self.lemmatizer = lemmatizer
        self.stemmer = stemmer
        self.tagger = tagger
        

    def normalise(self, word):
        """Normalises words to lowercase and stems and lemmatizes it."""
        word = word.lower()
        #word = self.stemmer.stem(word)
        #word = self.lemmatizer.lemmatize(word)
        return word


    def acceptable_word(self, word):
        """Checks conditions for acceptable word: length, stopword."""
        accepted = bool(1 < len(word) <= 40 and word.lower() not in ['the','and','or'])
        return accepted


    def flatten_phrase_lists(self, npTokenList):
        finalList =[]
        for phrase in npTokenList:
            token = ''
            for word in phrase:
                token += word + ' '
            finalList.append(token.rstrip())
        return finalList


    def getPhrases(self, text):
        counter = Counter()
        print('text',text)
        test = self.chunker.parse(self.tagger(re.findall(r'\w+', text)))

        return test


    def POS_tagger(self, subtrees):
        terms = {}
        lvl1 = 0
        p_num = 0

        for test in subtrees:
            phrase = test.label()
            if phrase == 'NP':
                p = {}
                for w in range(len(test.leaves())):
                    p[w] = self.lemmatizer.lemmatize(test.leaves()[w][0])
                terms[lvl1] = {'pos':'N', 'phrase':p}
                lvl1+=1

            elif phrase == 'VP':
                p = {}
                for w in range(len(test.leaves())):
                    p[w] = self.lemmatizer.lemmatize(test.leaves()[w][0])
                terms[lvl1] = {'pos':'V', 'phrase':p}
                lvl1+=1

        return terms


    def get_key_pos_tag(self, phrase):
        phrase = re.split(r'. [A-Z]', phrase)[0]
        #phrase = predictor.coref_resolved(phrase)
        phrase = re.sub(r'[^\w\s]','', phrase)
        phrase = re.sub(r'end of the reporting period','', phrase)
        phrase = re.sub(r'during the reporting period','', phrase)

        phrases = [self.normalise(i) for i in word_tokenize(phrase) if self.acceptable_word(i)]
        print('p',phrases)
        n_phrases = self.getPhrases(' '.join(phrases))
        #print('nphrase', n_phrases)
        terms = self.POS_tagger(n_phrases.subtrees())

        nv_terms = {}
        for t in terms:
            #if terms[t]['pos'] == "N" or terms[t]['pos'] == "V":
            nv_terms[t] = terms[t]
            #capitalize so words are in camecase
            nv_terms[t]['phrase'] = {k:v.title() for k,v in nv_terms[t]['phrase'].items()}
        
        return nv_terms


    def rb_translation(self, t1, ind_code, cids_classes, matched_indicators):
        pos_breakdown = t1

        #default translation components
        translation = {90:{'word':ind_code,'subclassOf':'Indicator'},
                        91:{'subclassOf':'Population', 'forTimeInterval':'ReportingPeriod','word':ind_code+'Population'},
                        92:{'subclassOf':'DateTimeInterval','word':'ReportingPeriod'}}

        word_indices = list(pos_breakdown.keys())
        phenom_key = word_indices[1]

        # first run for nouns
        for word_index in pos_breakdown:
            phrase = pos_breakdown[word_index]['phrase']
            word = ''.join(str(word) for word in pos_breakdown[word_index]['phrase'].values())
            pos = pos_breakdown[word_index]['pos']
            
            if ((word not in translation) and (pos == 'N') and word_index==0):
            # first noun phrase is a quantity
                if ('Value' in word or 'Sum' or 'Amount' in word):
                    translation[word_index] = {'word':'Sum'}
                elif ('Number' in word or 'Count' in word):
                    translation[word_index] = {'word':'Cardinality'}
                elif ('Percentage' in word or 'Ratio' in word):
                    translation[word_index] = {'word':'RatioIndicator'}
                else: #placeholder, use sum as the default quantity measurement
                    translation[word_index] = {'word':'Sum'}
                
                #sets quantity to be a measurement of the population
                translation[90]['subclassOf'] = translation[word_index]['word']
                if translation[90]['subclassOf'] == 'RatioIndicator':
                    translation[91]['word'] = translation[91]['word']+'Numerator'
                    translation[90]['hasNumerator'] = translation[91]['word']
                else:
                    indicator_type = translation[word_index]['word']
                    translation[90][indicator_type[0].lower()+indicator_type[1:]+'Of'] = translation[91]['word']

            # second noun phrase is the phenomenon of the quantity
            if ((word not in translation) and (pos == 'N') and word_index==phenom_key):
                translation[91]['definedBy']=word
                # add variable if not a cardinality
                if translation[90]['subclassOf'] is not 'Cardinality':
                    translation[93] = {'word':word+'Amount', 'subclassOf':'Variable', 'hasName':word+'_amount'}
                    translation[90]['parameterOfVar'] = translation[93]['word']

                # check if a cids class can be assigned
                if word in cids_classes:
                    translation[word_index] = {'word':word}
                elif word in matched_indicators.keys():
                    translation[word_index] = {'word':word, 'subclassOf': matched_indicators[word]}
                else: 
                    translation[word_index] = {'word':word, 'subclassOf':'cidsThing'}
        
            # use the rest of the indicator text to define the population
            if ((word not in translation) and (pos == 'N') and phenom_key<word_index):

                #check if a cids class can be assigned
                if word in cids_classes:
                    translation[word_index] = {'word':word}
                elif word in matched_indicators.keys():
                    translation[word_index] = {'word':word, 'subclassOf': matched_indicators[word]}
                else:
                    translation[word_index] = {'word':word, 'subclassOf':'cidsThing'}
            
        # run again for verbs, do it after nouns because you need to refer to nouns before and after the verb
        translation = self.flip_translation(translation)
        for word_index in pos_breakdown:
            
            phrase = pos_breakdown[word_index]['phrase']
            word = ' '.join(str(word) for word in pos_breakdown[word_index]['phrase'].values())
            pos = pos_breakdown[word_index]['pos']

            if pos == 'V' and word_index+1 in pos_breakdown.keys():
                if pos_breakdown[word_index+1]['pos'] != 'V':
                    i=1
                    while pos_breakdown[word_index-i]['pos'] != 'N':
                        i+=1
                        if joinPhrase(pos_breakdown[word_index-i]) in translation.keys():
                            original_verb_phrase = joinPhrase(pos_breakdown[word_index])
                            verb_phrase = original_verb_phrase[0].lower() + original_verb_phrase[1:]
                            translation[joinPhrase(pos_breakdown[word_index-i])][verb_phrase]=joinPhrase(pos_breakdown[word_index+1])

        return translation

    def joinPhrase(self, input):
        joined = ''.join(str(word) for word in input['phrase'].values())
        return joined

    # swap key and value to get word as the key
    def flip_translation(self, t):
        t_output = {}
        for k, v in t.items():
            #v['order'] = k
            t_output[v.pop('word')] = v 

        return t_output


    def plot_KG(self, translation_output):
        translation_output_temp = copy.deepcopy(translation_output)
        for k in translation_output_temp.keys():
            if 'subclassOf' in translation_output_temp[k].keys():
                if translation_output_temp[k]['subclassOf'] == 'cidsThing':
                    translation_output_temp[k].pop('subclassOf')
            
        m = set(translation_output_temp.keys())
        for t in translation_output_temp:
            for v in translation_output_temp[t]:
                if v!='subclassOf':
                    m.discard(translation_output_temp[t][v])

        prop_rel = []
        for t in translation_output_temp:
            for v in translation_output_temp[t]:
                if v != 'class':
                    prop_rel.append([[t,translation_output_temp[t][v]],v])
                
        G=nx.Graph()

        for e in prop_rel:
            G.add_edge(e[0][0], e[0][1], label=e[1], arrows=True)
        
        return G, prop_rel

