import enum
from operator import ge
import string
from string import punctuation
from nltk.corpus import stopwords, wordnet as wn, wordnet_ic
from nltk.tokenize import word_tokenize
from nltk.corpus.reader.wordnet import Synset
from typing import *
import re
import owlready2 as owl2
from nltk.probability import FreqDist

THRESHOLD = 0.3
T_SS_METHOD = 'mfs' # Target word synset selection method
C_SS_METHOD = 'mfs' # Class word synset selection method 
LAST_SUBWORD_WEIGHT = 0.6 # Percentage
SIMILARITY_METHOD = 'wup'

class WordNet: 
    def __init__(self):
        pass

    # TODO handle what if cant find thing in dict
    def get_Thing_classes(self, clustering_kg_dict):
        '''
        Returns a dictionary where the key is the target word and the value is the Thing-suffixed cluster output class
        '''
        res = {}
        for key in clustering_kg_dict.keys():
            if bool(clustering_kg_dict[key]) and "subclassOf" in clustering_kg_dict[key]:
                if "Thing" in clustering_kg_dict[key]["subclassOf"]:
                    res[key] = clustering_kg_dict[key]["subclassOf"]
        print(res)
        return res


    # MAIN FUNCTION
    def wordnet(self, sentence, clustering_kg_dict):
        # Load CIDS ontology
        owl2.onto_path.append('.')
        onto = owl2.get_ontology('http://ontology.eil.utoronto.ca/cids/cids.owl') 
        onto.load() 
        # Get list of CIDS class names
        cids_classes = [c.name for c in list(onto.classes())] # Get all classes from CIDS as well as dependency ontologies

        res_dict = clustering_kg_dict.copy()
        tw_c = self.get_Thing_classes(clustering_kg_dict) # TODO if emtpy dont run 
        for target_word, c in tw_c.items():
            res_class = None
            ranked_sim_classes = self.get_parent_cids_class(sentence,target_word, cids_classes)
            if len(ranked_sim_classes) > 0:
                res_class = list(ranked_sim_classes.keys())[0]
            else:
                break # TODO Get the most similar class (first item in ranked list)
            print(target_word) # Target class
            print(f'{ranked_sim_classes}') # Results before clustering output filtering
            print(len(ranked_sim_classes)) # Length of results

            # Fitler ranked_sim_classes by cluster_class
            if ranked_sim_classes[res_class] < 0.8:
                filtered = self.filter_by_genre(ranked_sim_classes, c)
                if len(filtered) > 0:
                    res_class = list(filtered.keys())[0]
                else:
                    break # Update result class # TODO Get the most similar class (first item in ranked list)
                print(f'Filter by {c}') 
                print(filtered) # TODO replace w cluster_label
                print(len(filtered)) # Length of results after filtering
                print('\n') 
                
            
            # Update res_dict with res_class # TODO handle if fallback
            if res_class: 
                for key in clustering_kg_dict.keys():
                    if "subclassOf" in clustering_kg_dict[key]:
                        if clustering_kg_dict[key]["subclassOf"] == c:
                            res_dict[key]['subclassOf'] = res_class
                # TODO if below sim threshold, fallback to cluster_output (xxxThing)
                return res_dict
            else:
                return clustering_kg_dict

    def get_parent_cids_class(self, sentence: List[str], target_word, list_of_class_names):
        '''
        Returns a CIDS class that is most semantically related to the target word. The target word will become a new CIDS class, and it will become the child of the returned CIDS class.

        We will be using the Wu-Palmer similarity formula. It is a ratio and therefore yields a score between 0 and 1.
        '''
        
        # If target word (noun) matches exactly with one of the CIDS classes
        # TODO what if the dependency ontology has the same class name as CIDS? Priority should be given to CIDS.
        if target_word in list_of_class_names:
            for c in list_of_class_names:
                if target_word.lower() == c.lower(): 
                    return c # return the CIDS class
        # If there is no exact match
        else:
            most_similar_classes = dict()
            for idx, c in enumerate(list_of_class_names):
                # If target word is a multi-word, only keep the last subword (assume it is the noun, and preceding subwords are adjectives)
                if len(wn.synsets(target_word)) == 0:
                    # Split it into its constituent terms
                    target_word = re.findall('[A-Z][^A-Z]*', target_word)[-1] # Only keep the last subword
                else:
                    # Get target word sense
                    if T_SS_METHOD == 'mfs':
                        target_word_ss = self.mfs(target_word)
                    elif T_SS_METHOD == 'lesk':
                        target_word_ss = self.lesk(sentence, sentence.index(target_word.lower())) # TODO make work for multiword # lower doesnt work if word is actually first word (hence capitalized)
                    # If class is a multiword, it will not be in WordNet and have no synsets
                    if len(wn.synsets(c)) == 0:
                        term_similarity = []
                        # Split it into its constituent terms
                        subwords = re.findall('[A-Z][^A-Z]*', c)
                        # For each subword, get its sense. Then do similarity comp w the single-word target 
                        for sw in subwords:
                            if len(wn.synsets(sw)) > 0:
                                if C_SS_METHOD == 'mfs':
                                    w_ss = self.mfs(sw) 
                                # elif SS_SELECTION_METHOD == 'lesk': # TODO
                                #     w_ss = self.lesk(sw)
                                if SIMILARITY_METHOD == 'wup':
                                    term_similarity.append(target_word_ss.wup_similarity(w_ss)) 
                                elif SIMILARITY_METHOD == 'resnik':
                                    if not '.n.' in w_ss.name(): # If w_ss is not a noun ss, skip 
                                        continue
                                    brown_ic = wordnet_ic.ic('ic-brown.dat') # Set an Information Content source to use
                                    term_similarity.append(target_word_ss.res_similarity(w_ss, brown_ic))
                        # Derive the score via the weighted average of all subwords.
                        # 1 - 0.6 = 0.4 / subwords
                        similarity = 0
                        # TODO: the weights should be a percentage; this isnt!
                        for idx, t in enumerate(term_similarity):
                            if idx < len(term_similarity) - 1:
                                weight = (1.0 - LAST_SUBWORD_WEIGHT) / float(len(term_similarity) - 1) # Weight for each word that is not the last subword
                                similarity += t * weight
                            else:
                                similarity += t * LAST_SUBWORD_WEIGHT
                        # similarity = sum(term_similarity)/len(term_similarity) if len(term_similarity) > 0 else 0  # TODO rm 
                    # If class is a single word, it should be in WordNet and therefore have synsets
                    else: 
                        c_ss = self.mfs(c)
                        if SIMILARITY_METHOD == 'wup':
                            similarity = target_word_ss.wup_similarity(c_ss)    
                        elif SIMILARITY_METHOD == 'resnik':
                            similarity = target_word_ss.res_similarity(w_ss, brown_ic)
                    if similarity >= THRESHOLD:
                        most_similar_classes[c] = similarity
            
            most_similar_classes =  self.sort_classes_desc(most_similar_classes)
            return most_similar_classes


    def filter_by_genre(self, similar_classes: Dict[str, float], genre: str, filter_threshold=0.7) -> Dict[str, float]:
        '''
        Takes the upstream clustering output class, which is a higher level ancestor, as the filter for the output. 
        For example, 
        target noun - 'pupil'
        clustering output - 'EducationThing'
        'EducationThing' acts as a filter. It goes through the list of similar classes to the target noun, and only retains classes that are related to education. 
        Returns a filtered list of similar CIDS classes. 
        '''
        # Take the first word out of genre. # TODO correct to assume that follows the format xxThing for multiword genre?
        ## Assumes that the muiltiwords are like CIDS, in PascalCase, even for single words TODO cfm
        genre = re.findall('[A-Z][^A-Z]*', genre)[0]
        # Get genre's sense
        g_ss = self.mfs(genre)
        # Get a list of scores for c with most simialr scores based on filter threshold  
        res = dict()
        for c in similar_classes:
            if len(wn.synsets(c)) == 0:
                term_similarity = []
                # Split it into its constituent terms
                subwords = re.findall('[A-Z][^A-Z]*', c)
                for sw in subwords:
                    if len(wn.synsets(sw)) > 0:
                        sw_ss = self.mfs(sw) 
                        term_similarity.append(g_ss.wup_similarity(sw_ss)) 
                similarity = 0
                for idx, t in enumerate(term_similarity):
                    if idx < len(term_similarity) - 1:
                        weight = (1.0 - LAST_SUBWORD_WEIGHT) / float(len(term_similarity) - 1) # Weight for each word that is not the last subword
                        similarity += t * weight
                    else:
                        similarity += t * LAST_SUBWORD_WEIGHT
            else: 
                c_ss = self.mfs(c)
                score = c_ss.wup_similarity(g_ss)
                # if does not exceed filter threshold, store to res for filtering later
                if score < filter_threshold:
                    res[c] = score
        for res_c in res:
            # If c does not have high similarity with the genre (ie does not exceed threshold), remove c from similar class
            if res_c in similar_classes:
                del similar_classes[res_c]
        # Re-sort the filtered dict and return
        return self.sort_classes_desc(similar_classes)


    def sort_classes_desc(self, class_dict: Dict[str, float]) -> Dict[str, float]:
        return dict(sorted(class_dict.items(), key=lambda item: item[1], reverse=True))
        

    def mfs(self, word: str) -> Synset:
        """Most frequent sense of a word.
        Word is a noun.
        Returns:
            Synset: The most frequent sense for the given word.
        """    
        return wn.synsets(word)[0] if len(wn.synsets(word)) > 0 else None

    def lesk(self, sentence: List[str], word_index: int) -> Synset:
        """Simplified Lesk algorithm.
        Args:
            sentence (list of str): The sentence containing the word to be
                disambiguated1
            word_index (int): The index of the target word in the sentence.

        Returns:
            Synset: The prediction of the correct sense for the given word.
        """
        best_sense = self.mfs(sentence[word_index])
        best_score = 0 
    
        context = self.get_context(sentence) 
        synsets = wn.synsets(sentence[word_index])
        for ss in synsets:
            signature = self.get_signature(ss)
            score = self.overlap(signature, context)
            if score > best_score:
                best_score = score
                best_sense = ss

        return best_sense

    #======= HELPER FUNCTIONS ========
    def get_context(self, sentence: List[str]) -> List[str]: 
        context = self.token_filtering(sentence) 
        return context

    def get_signature(self, synset: Synset) -> List[str]:
        # Get synset definition
        definition = self.stop_tokenize(synset.definition())
        # Get synset example
        examples = self.flatten([self.stop_tokenize(example) for example in synset.examples()])
        signature = definition + examples

        return signature


    def token_filtering(self, tokens: List[str]) -> List[str]:
        """
        Removes stop words and punctuation tokens from the token list. 
        """
        filtered_tokens = []
        for token in tokens:
            if token not in punctuation and token.lower() not in stopwords.words('english'):
                filtered_tokens.append(token)
        return filtered_tokens

    def flatten(self, list: List) -> List:
        return [item for sublist in list for item in sublist] 

    def overlap(self, signature: List[str], context: List[str]) -> List[str]:
        """
        Returns the cardinality of the intersection of the bags signature and context, i.e., the number of words tokens that the signature and context have in common. NOT WORD TYPE!
        """

        _signature = dict(FreqDist(signature))
        _context = dict(FreqDist(context))
        cardinality = 0

        for c in _context.keys():
            if c in _signature.keys():
                cardinality += 2 * min(_context[c], _signature[c])

        return cardinality

    def stop_tokenize(self, s: str) -> List[str]: # TODO may not need this if it is already handled upstream
        """Word-tokenize and remove stop words and punctuation-only tokens.

        Args:
            s (str): String to tokenize

        Returns:
            list[str]: The non-stopword, non-punctuation tokens in s

        Examples:
            >>> stop_tokenize('The Dance of Eternity, sir!')
            ['Dance', 'Eternity', 'sir']
        """
        # Remove stop words and punctuation
        s = [w for w in word_tokenize(s) if w.lower() not in stopwords.words('english') and w not in punctuation]

        return s

    def split_sentence(self, sentence: str) -> List[str]: # TODO move to a different file # TODO may not need this if alrady handled upstream
        '''
        Punctuations found in a sentence are individual elements in the returned list.
        '''
        # Split sentence by whitespaces and punctuation
        return re.findall(r"[\w]+|['/.,!?;]", sentence) # TODO <word>/<word> - include / in separation
        