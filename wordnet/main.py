
from operator import ge
import string
from string import punctuation
from nltk.corpus import stopwords, wordnet as wn, wordnet_ic
from nltk.corpus.reader.wordnet import Synset
from typing import *
import re
import owlready2 as owl2
from nltk.probability import FreqDist


class WordNet: 
    def __init__(self, similarity_threshold=0.8, t_ss_method='mfs', c_ss_method='mfs', last_word_weight=0.6):
        self.similarity_threshold = similarity_threshold
        self.t_ss_method = t_ss_method
        self.c_ss_method = c_ss_method
        self.last_word_weight = last_word_weight


    # MAIN FUNCTION
    def wordnet(self, sentence, clustering_kg_dict):
        # Load CIDS ontology
        owl2.onto_path.append('.')
        onto = owl2.get_ontology('http://ontology.eil.utoronto.ca/cids/cids.owl') 
        onto.load() 

        # Get list of CIDS class names
        cids_classes = [c.name for c in list(onto.classes())] # Get all classes from CIDS as well as dependency ontologies
        
        res_dict = clustering_kg_dict.copy()
        tw_c = self.get_Thing_classes(clustering_kg_dict)
        # if empty, just return 
        if not tw_c:
            print(f'No classes to work with. No wordnet output.')
            return

        for target_phrase, c in tw_c.items():
            res_class = None
            ranked_sim_classes = self.get_ranked_similar_cids_class(sentence,target_phrase, cids_classes)
            # Get the most similar class (first item in ranked list)
            if len(ranked_sim_classes) > 0:
                res_class = list(ranked_sim_classes.keys())[0]
            
            # Fitler ranked_sim_classes by cluster_class
            filtered = self.filter_by_genre(ranked_sim_classes, c)

            if len(filtered) > 0:
                res_class = list(filtered.keys())[0]
            else:
                res_class = None         
            
            # Update res_dict with res_class
            for key in clustering_kg_dict.keys():
                if "subclassOf" in clustering_kg_dict[key]:
                    if clustering_kg_dict[key]["subclassOf"] == c:
                        if res_class:
                            res_dict[key]['subclassOf'] = res_class
                        
        return res_dict
    

    def get_Thing_classes(self, clustering_kg_dict):
        '''
        Returns a dictionary where the key is the target phrase and the value is the Thing-suffixed cluster output class
        '''
        res = {}
        for key in clustering_kg_dict.keys():
            if bool(clustering_kg_dict[key]) and "subclassOf" in clustering_kg_dict[key]:
                if "Thing" in clustering_kg_dict[key]["subclassOf"]:
                    res[key] = clustering_kg_dict[key]["subclassOf"]
        return res


    def get_ranked_similar_cids_class(self, sentence: str, target_phrase, list_of_class_names):
        '''
        Returns a CIDS class that is most semantically related to the target (noun) phrase. The target phrase will become a new CIDS class, and it will become the child of the returned CIDS class.
        
        The Wu-Palmer similarity measure is used to derive similarity score between the target phrase and a CIDS class. It is a ratio and therefore yields a score between 0 and 1.

        Assumes that the words that make up target_phrase (one or more), as well as the CIDS class, are in PascalCase.
        '''
        
        # If the target phrase matches exactly with one of the CIDS classes, 
        if target_phrase in list_of_class_names:
            for c in list_of_class_names:
                if target_phrase.lower() == c.lower(): 
                    return c # return the CIDS class
        # If there is no exact match
        else:
            most_similar_classes = dict()
            # Compare similarity of target phrase to every CIDS class
            for idx, c in enumerate(list_of_class_names):
                # If target phrase has no synset matches, it is a phrase composed of multiple words. Only keep the last word (assume it is a noun, and preceding words are adjectives)
                if len(wn.synsets(target_phrase)) == 0:
                    # Split it into its constituent words
                    target_phrase = re.findall('[A-Z][^A-Z]*', target_phrase)[-1] # Only keep the last word
                # Get target phrase sense
                if self.t_ss_method == 'mfs':
                    target_phrase_ss = self.mfs(target_phrase)
                elif self.t_ss_method == 'lesk':
                    target_phrase_ss = self.lesk(sentence, target_phrase)
                
                # If the CIDS class is a phrase with more than one word, it will not be in WordNet and have no synsets
                if len(wn.synsets(c)) == 0:
                    term_similarity = []
                    # Split the CIDS class phrase into its constituent words
                    words = re.findall('[A-Z][^A-Z]*', c)
                    # For each word, get its sense. Then do similarity comp w the single-word target 
                    for w in words:
                        w_ss = None
                        if len(wn.synsets(w)) > 0:
                            if self.c_ss_method == 'mfs':
                                w_ss = self.mfs(w) 
                            elif self.c_ss_method == 'lesk':
                                w_ss = self.lesk(sentence, w)
                            # Run Wu-Palmer similarity on target phrase synset to the CIDS class synset
                            term_similarity.append(target_phrase_ss.wup_similarity(w_ss)) 
                    # Derive the score of this CIDS class against the target phrase, by a weighted score of all words against the target phrase.
                    similarity = 0
                    for idx, t in enumerate(term_similarity):
                        if idx < len(term_similarity) - 1:
                            weight = (1.0 - self.last_word_weight) / float(len(term_similarity) - 1) # Weight for each word that is not the last word
                            similarity += t * weight
                        else:
                            similarity += t * self.last_word_weight # Multiple the last word's score by last_word_weight
                            
                # If class is a single word, it should be in WordNet and therefore have synsets
                else: 
                    if self.c_ss_method == 'mfs':
                        c_ss = self.mfs(c) 
                    elif self.c_ss_method == 'lesk':
                        c_ss = self.lesk(sentence, c)
                    similarity = target_phrase_ss.wup_similarity(c_ss)          
                if similarity >= self.similarity_threshold:
                    most_similar_classes[c] = similarity
        
            most_similar_classes =  self.sort_classes_desc(most_similar_classes)
            return most_similar_classes


    def filter_by_genre(self, similar_classes: Dict[str, float], genre: str) -> Dict[str, float]:
        '''
        Takes the upstream clustering output class, which is a higher level ancestor, as the filter for the output. 
        For example, 
        target noun - 'pupil'
        clustering output - 'EducationThing'
        'EducationThing' acts as a filter. It goes through the list of similar classes to the target noun, and only retains classes that are related to education. 
        
        Assumes that the muiltiwords are in PascalCase.

        Returns a filtered list of similar CIDS classes. 
        '''
        # Take the first word out of genre
        genre = re.findall('[A-Z][^A-Z]*', genre)[0]
        # Get genre's sense
        g_ss = self.mfs(genre)
        # Get a list of scores for c with most simialr scores based on filter threshold  
        res = dict()
        for c in similar_classes:
            if len(wn.synsets(c)) == 0:
                target_word_similarity = []
                # Split it into its constituent words
                words = re.findall('[A-Z][^A-Z]*', c)
                for w in words:
                    if len(wn.synsets(w)) > 0:
                        w_ss = self.mfs(w) 
                        target_word_similarity.append(g_ss.wup_similarity(w_ss)) 
                score = 0
                for idx, t in enumerate(target_word_similarity):
                    if idx < len(target_word_similarity) - 1:
                        weight = (1.0 - self.last_word_weight) / float(len(target_word_similarity) - 1) # Weight for each word that is not the last word
                        score += t * weight
                    else:
                        score += t * self.last_word_weight
                # if does not exceed filter threshold, store to res for filtering later
                if score < self.similarity_threshold:
                    res[c] = score
            else: 
                c_ss = self.mfs(c)
                score = c_ss.wup_similarity(g_ss)
                # if does not exceed filter threshold, store to res for filtering later
                if score < self.similarity_threshold:
                    res[c] = score
        for res_c in res:
            # If c does not have high similarity with the genre (ie does not exceed threshold), remove c from similar class
            if res_c in similar_classes:
                del similar_classes[res_c]
        # Re-sort the filtered dict and return
        res = self.sort_classes_desc(similar_classes)
        return res


    def sort_classes_desc(self, class_dict: Dict[str, float]) -> Dict[str, float]:
        return dict(sorted(class_dict.items(), key=lambda item: item[1], reverse=True))
        

    def mfs(self, word: str) -> Synset:
        """Returns the most frequently occuring noun sense of a word in the sense-tagged corpora that WordNet is built upon.

        Returns:
            Synset: The most frequent sense for the given word.
        """    
        return wn.synsets(word, pos=wn.NOUN)[0] if len(wn.synsets(word)) > 0 else None


    def lesk(self, sentence: str, word: str) -> Synset:
        """Simplified Lesk algorithm.
        Args:
            sentence (list of str): The sentence containing the word to be
                disambiguated1
            word_index (int): The index of the target phrase in the sentence.

        Returns:
            Synset: The prediction of the correct sense for the given word.
        """
        best_sense = self.mfs(word)
        best_score = 0 
    
        context = self.get_context(sentence) 
        # Remove common words found in indicators that are (in most cases) not contributing to the word's context
        context = [t for t in context if t not in ['reporting', 'period', 'organization']]

        # Only get noun synsets of the word 
        synsets = wn.synsets(word, pos=wn.NOUN)

        for ss in synsets:
            signature = self.get_signature(ss)
            score = self.overlap(signature, context)
            if score > best_score:
                best_score = score
                best_sense = ss

        return best_sense

    #======= HELPER FUNCTIONS ========
    def get_context(self, sentence: str) -> List[str]: 
        context = self.stop_tokenize(sentence)
        return context

    def get_signature(self, synset: Synset) -> List[str]:
        # Get synset definition
        definition = self.stop_tokenize(synset.definition())
        # Get synset example
        examples = self.flatten([self.stop_tokenize(example) for example in synset.examples()])
        signature = definition + examples

        return signature

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

    def stop_tokenize(self, sentence: str) -> List[str]:
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
        s = [w for w in re.findall(r"[\w]+|['/.,!?;]", sentence) if w.lower() not in stopwords.words('english') and w not in punctuation]

        return s