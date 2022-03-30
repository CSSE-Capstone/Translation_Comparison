import pandas as pd
import string
import re
import networkx as nx
import matplotlib.pyplot as plt
import copy
import nltk
import nltk.tag, nltk.data

from nltk import tokenize
from nltk.corpus import stopwords
from nltk.tag import UnigramTagger
from nltk.tokenize import word_tokenize

nltk.download("stopwords")
nltk.download('wordnet')
nltk.download('treebank')
nltk.download('maxent_treebank_pos_tagger')
nltk.download('punkt')

class RuleBased:
    def __init__(self, rb_grammar, chunker, lemmatizer, tagger):
        self.rb_grammar = rb_grammar
        self.chunker = chunker
        self.lemmatizer = lemmatizer
        self.tagger = tagger

    def POS_tagger(self, phrase, chunker, lemmatizer):
        """
        POS tag words in input text according to noun/verb, chunk into key phrases according to a set grammar, lemmatize key phrases

        Parameters:
        phrase (str): input text
        chunker: selected chunker (ex: nltk.RegexpParser)
        lemmatizer: selected lemmatizer (ex: nltk.WordnetLemmatizer)

        Returns:
        terms (dict): key phrases and their POS tag (N for noun, V for verb)
        """
        #split input text into words
        words = re.findall(r'\w+', phrase)

        #tag words according to tagged POS
        tagged_words = self.tagger(words)
        #chunk tagged words into key phrases
        chunked_phrases = chunker.parse(tagged_words)
        subtrees = chunked_phrases.subtrees()

        terms = {}   #term dictionary of tagged noun/verb keyphrases
        lvl = 0

        for s in subtrees:
            phrase = s.label()
            #add noun key phrases
            if phrase == 'NP':
                p = {}
                for w in range(len(s.leaves())):
                    p[w] = lemmatizer.lemmatize(s.leaves()[w][0])
                terms[lvl] = {'pos':'N', 'phrase':p}
                lvl+=1

            elif phrase == 'VP':
                #add verb key phrases
                p = {}
                for w in range(len(s.leaves())):
                    p[w] = lemmatizer.lemmatize(s.leaves()[w][0])
                terms[lvl] = {'pos':'V', 'phrase':p}
                lvl+=1

        return terms

    def acceptable_word(word):
        """
        Checks conditions for acceptable word to be considered in a key phrase: 
            word length, not a stopword (the, and, or)

        Parameters:
        word (str): word to check for validity

        Returns:
        accepted (bool): True if word is checks pass
        """
        accepted = bool(1 < len(word) <= 40 and word.lower() not in ['the','and','or'])
        return accepted

    def get_key_pos_tag(self, phrase):
        """
        Clean up raw input text before preprocessing, run POS tag

        Parameters:
        phrase (str): raw input text

        Returns:
        keyphrases (dict): nested dictionary of key phrases and POS tag, in order of appearance in input phrase
        """
        #input text clean up
        phrase = re.split(r'. [A-Z]', phrase)[0] #get first sentence of input text
        phrase = re.sub(r'\([^)]*\)', '', phrase) #remove words inside parentheses
        phrase = re.sub(r'[^\w\s]','', phrase) #remove non word phrases
        phrase = re.sub(r'end of the reporting period','', phrase) #date time interval is added by default, remove as a keyphrases
        phrase = re.sub(r'during the reporting period','', phrase)
        #phrase = predictor.coref_resolved(phrase) #run coreference resolution if desired

        phrases = [i.lower() for i in word_tokenize(phrase) if self.acceptable_word(i)]
        #run POS tagging
        terms = self.POS_tagger(' '.join(phrases), self.chunker, self.lemmatizer)

        #format key phrases into camelcase
        keyphrases = {}
        for t in terms:
            keyphrases[t] = terms[t]
            keyphrases[t]['phrase'] = {k:v.title() for k,v in keyphrases[t]['phrase'].items()}
        
        return keyphrases

    def flip_POS_tag(POS_tag):
        """
        Reformat POS tag output dictionary from using key phrase position as keys, to word phrase as key
        """
        flipped_POS_tag = {}
        for k, v in POS_tag.items():
            flipped_POS_tag[v.pop('word')] = v 

        return flipped_POS_tag
    
    def joinPhrase(input):
        """
        Join a list of terms into a single string

        Parameters:
        input (list): list of strings

        Returns:
        joined (str): concatenated string, with no separator
        """
        joined = ''.join(str(word) for word in input['phrase'].values())
        return joined

    def rb_translation(self, pos_breakdown, ind_code, cids_classes, matched_indicators):
        """
        Set up framework of translation using rules

        Parameters:
        pos_breakdown (dict): output from get_key_pos_tag
        ind_code (str): indicator code number

        Returns:
        translation (dict): 
            Keys: text keyphrases and CIDS indicator key classes
            Values: parameters and associated keys
        """

        #default translation components
        translation = {90:{'word':ind_code,'subclassOf':'Indicator'},
                        91:{'subclassOf':'Population', 'forTimeInterval':'ReportingPeriod','word':ind_code+'Population'},
                        92:{'subclassOf':'DateTimeInterval','word':'ReportingPeriod'}}

        word_indices = list(pos_breakdown.keys())
        phenom_key = word_indices[1] #phenomenon of the quantity

        # run through noun keyphrases
        for word_index in pos_breakdown:
            phrase = pos_breakdown[word_index]['phrase']
            word = ''.join(str(word) for word in pos_breakdown[word_index]['phrase'].values())
            pos = pos_breakdown[word_index]['pos']
            
            if ((word not in translation) and (pos == 'N') and word_index==0):
                #identify type of quantity measurement
                if (word in ['Value','Sum','Amount']):
                    translation[word_index] = {'word':'Sum'}
                elif (word in ['Number','Count']):
                    translation[word_index] = {'word':'Cardinality'}
                elif (word in ['Percentage','Ratio']):
                    translation[word_index] = {'word':'RatioIndicator'}
                else: #use sum as the default quantity measurement
                    translation[word_index] = {'word':'Sum'}
                
                #sets quantity to be a measurement of the indicator population
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

                # check if a cids class can be assigned according to the manual/cluster mapping dictionary
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
                
        # run through verb keyphrases, use as properties to relate noun keyphrases
        translation = self.flip_POS_tag(translation)
        for word_index in pos_breakdown:  
            phrase = pos_breakdown[word_index]['phrase']
            word = ' '.join(str(word) for word in pos_breakdown[word_index]['phrase'].values())
            pos = pos_breakdown[word_index]['pos']

            if pos == 'V' and word_index+1 in pos_breakdown.keys(): #check if verb key phrases is in a triple
                if pos_breakdown[word_index+1]['pos'] != 'V': #if two verbs one after another, use the last verb before a noun phrase
                    i=1
                    while pos_breakdown[word_index-i]['pos'] != 'N': #identify closest noun phrase before the verb phrase
                        i+=1
                    if self.joinPhrase(pos_breakdown[word_index-i]) in translation.keys():
                        original_verb_phrase = self.joinPhrase(pos_breakdown[word_index])
                        verb_phrase = original_verb_phrase[0].lower() + original_verb_phrase[1:] #set verb phrase into camelcase
                        translation[self.joinPhrase(pos_breakdown[word_index-i])][verb_phrase]=self.joinPhrase(pos_breakdown[word_index+1]) #add noun-verb-noun triple to dictionary

        return translation


    def plot_KG(self, translation_output):
        """
        Rearrange translation dictionary into triples and plot KG using networkX

        Parameters:
        translation_output (dict): translation in a dictionary format

        Returns:
        G (networkX graph): visualized KG, excluding "cidsThing" subclasses
        triples (list): list of triples of keyphrase-property-keyphrase in the KG
        """
        #reformat translation dictionary
        translation_output_temp = copy.deepcopy(translation_output)
        for k in translation_output_temp.keys():
            if 'subclassOf' in translation_output_temp[k].keys():
                #remove cidsThing subclass to avoid cluttering visualization
                if translation_output_temp[k]['subclassOf'] == 'cidsThing':
                    translation_output_temp[k].pop('subclassOf')

        triples = []
        for t in translation_output_temp:
            for v in translation_output_temp[t]:
                if v != 'class':
                    triples.append([[t,translation_output_temp[t][v]],v])
            
        #add triples to networkX graph
        G=nx.Graph()
        for e in triples:
            G.add_edge(e[0][0], e[0][1], label=e[1], arrows=True)
        
        return G, triples

