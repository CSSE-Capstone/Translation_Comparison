import copy
import matplotlib.pyplot as plt
import pandas as pd
import nltk
from transformers import BertTokenizer, BertModel
from nltk.corpus import stopwords
import torch 
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict
from transformers import BertTokenizer, BertModel
nltk.download("stopwords")

# need to import RB lemmatizer
class Clustering: 
    def __init__(self, model, tokenizer, lemmatizer, df):
        self.model = model
        self.tokenizer = tokenizer
        self.lemmatizer = lemmatizer
        self.df = df
    
    
    def create_stopwords(self):
        # stop words 
        stop = set(stopwords.words('english'))
        stop.remove('during')
        stop.remove('between')
        stop.remove('has')
        stop.remove('had')
        stop.remove('have')
        stop.add('##r')
        stop.add('s')
        stop.add('(')
        stop.add(')')
        stop.add(',')
        stop.add('##de')
        stop.add('##ing')
        stop.add('##ation')
        stop.add("'")
        stop.add('.')
        stop.add('##i')
        stop.add('##vo')
        stop.add('##lun')
        stop.add('##de')
        stop.add('##tar')
        stop.add('##pr')
        stop.add('##ari')
        stop.add('##sb')
        stop.add('##s')
        stop.add('el')
        stop.add('etc')
        stop.add('ins')
        stop.add('g')
        stop.add('hg')
        stop.add('##hg')
        stop.add('-')
        return stop

    
    def get_word_embeddings(self, token_embeddings):
    # Stores the token vectors, with shape [22 x 768]
        token_vecs_sum = []

        # `token_embeddings` is a [22 x 12 x 768] tensor.

        # For each token in the sentence...
        for token in token_embeddings:

            # `token` is a [12 x 768] tensor

            # Sum the vectors from the last four layers.
            sum_vec = torch.sum(token[-4:], dim=0)
            
            # Use `sum_vec` to represent `token`.
            token_vecs_sum.append(sum_vec)

        # print ('Shape is: %d x %d' % (len(token_vecs_sum), len(token_vecs_sum[0])))
        return token_vecs_sum


    def remove_stop_words(self, tokenized_text, word_embeddings, stop):
        new_text = []
        new_embeddings = []
        for i, word in enumerate(tokenized_text):
            if word in stop:
                continue
            else:
                new_text.append(tokenized_text[i])
                new_embeddings.append(word_embeddings[i])

        return new_text, new_embeddings


    def create_word_tokens(self): #creates tokens for all iris csv
        # Training 
        definitionsDF = self.df[["ID", "Definition"]] # based on iris.csv
        definitionsDF.head()

        # Put the model in "evaluation" mode, meaning feed-forward operation.
        self.model.eval()
        bert_embeddings = []
        word_list = []
        for index, row in definitionsDF.iterrows():
            text = row['Definition']
            marked_text = "[CLS] " + text + " [SEP]"

            # Tokenize our sentence with the BERT self.tokenizer.
            tokenized_text = self.tokenizer.tokenize(marked_text)

            #investigate removing punctuation

            # # Print out the tokens.
            # print(tokenized_text)
            # Map the token strings to their vocabulary indeces.
            indexed_tokens = self.tokenizer.convert_tokens_to_ids(tokenized_text)
            
            segments_ids = [1] * len(tokenized_text)
            # Convert inputs to PyTorch tensors
            tokens_tensor = torch.tensor([indexed_tokens])
            segments_tensors = torch.tensor([segments_ids])

            with torch.no_grad():

                outputs = self.model(tokens_tensor, segments_tensors)

                # Evaluating the model will return a different number of objects based on 
                # how it's  configured in the `from_pretrained` call earlier. In this case, 
                # becase we set `output_hidden_states = True`, the third item will be the 
                # hidden states from all layers. See the documentation for more details:
                # https://huggingface.co/transformers/model_doc/bert.html#bertmodel
                hidden_states = outputs[2]

                token_embeddings = torch.stack(hidden_states, dim=0)
                token_embeddings = torch.squeeze(token_embeddings, dim=1)
                
                token_embeddings = token_embeddings.permute(1,0,2)

                word_embeddings = self.get_word_embeddings(token_embeddings) #outer length is embedding, inner is each word

                # Remove Stop Words First
                new_text, new_embeddings = self.remove_stop_words(tokenized_text, word_embeddings, self.create_stopwords())
                bert_embeddings.extend(new_embeddings[1:-1])
                word_list.extend(new_text[1:-1])
        return bert_embeddings, word_list


    def cluster(self):
        bert_embeddings, word_list = self.create_word_tokens()

        # how to cluster with labelled data
        X = []
        for embedding in bert_embeddings:
            X.append(embedding.cpu().detach().numpy()) 
        X = np.array(X)

        # Remove any statistical outliers prior to clustering
        mean, stdev = np.median(X, axis=0), np.std(X, axis=0)

        outliers = ((np.abs(X[:,0] - mean[0]) > stdev[0])
                * (np.abs(X[:,1] - mean[1]) > stdev[1])
                * (np.abs(X[:,2] - mean[2]) > stdev[2]))

        X_no_outliers = list(X)
        word_list_no_outliers = copy.deepcopy(word_list)
        for i in range(len(outliers)-1, -1, -1):
            if outliers[i] == True:
                X_no_outliers.pop(i)
                word_list_no_outliers.pop(i)

        # KMeans Clustering
        kmeans = KMeans(n_clusters=85, random_state=0, max_iter=600, algorithm="full")
        y_kmeans_token = kmeans.fit_predict(X_no_outliers)

        clusters = defaultdict(list)
        for i in range(len(word_list_no_outliers)):
            clusters[y_kmeans_token[i]].append(word_list_no_outliers[i])
        for k,v in clusters.items():
            clusters[k] = list(set(v))


        # Visualize Clusters Content
        cluster_text = ''
        for k,v in clusters.items():
            add = str(k)+ ':' + str(v) + "\n"
        cluster_text += add
        # Cluster Groups
        clusterGroups = []
        clusterGroups.append((20, "Quantity"))
        clusterGroups.append((55, "FinancialThing"))
        clusterGroups.append((46, "Farmer")) #
        clusterGroups.append((29, "Person"))
        clusterGroups.append((51, "Relation"))
        clusterGroups.append((84, "DateTimeInterval"))
        clusterGroups.append((45, "DateTimeInterval"))
        clusterGroups.append((19, "Supplier"))
        clusterGroups.append((26, "Organization"))
        clusterGroups.append((32, "Quantity"))
        clusterGroups.append((23, "Quantity"))
        clusterGroups.append((43, "FinancialThing"))
        clusterGroups.append((58, "FinancialThing"))
        clusterGroups.append((5, "Quantity"))
        clusterGroups.append((61, "Relation"))
        clusterGroups.append((47, "FinancialThing"))
        clusterGroups.append((40, "FinancialThing"))
        clusterGroups.append((3, "FinancialThing"))
        clusterGroups.append((2, "Organization"))
        clusterGroups.append((70, "FinancialThing"))
        clusterGroups.append((79, "FinancialThing"))
        clusterGroups.append((40, "FinancialThing"))
        clusterGroups.append((33, "FinancialThing"))
        clusterGroups.append((1, "DateTimeInterval"))
        clusterGroups.append((45, "DateTimeInterval"))
        clusterGroups.append((84, "DateTimeInterval"))
        clusterGroups.append((6, "DateTimeInterval"))
        clusterGroups.append((57, "DateTimeInterval"))
        clusterGroups.append((67, "DateTimeInterval"))
        clusterGroups.append((7, "Relation"))
        clusterGroups.append((24, "Quantity"))
        clusterGroups.append((9, "Relation"))
        clusterGroups.append((82, "ProductService"))
        clusterGroups.append((53, "ProductService"))
        clusterGroups.append((18, "ProductService"))
        clusterGroups.append((4, "Feature"))
        clusterGroups.append((34, "Feature"))
        clusterGroups.append((36, "EnvironmentThing"))
        clusterGroups.append((27, "EnvironmentThing"))
        clusterGroups.append((39, "Organization"))
        clusterGroups.append((73, "Organization"))
        clusterGroups.append((76, "Gender"))
        clusterGroups.append((31, "EnvironmentThing"))
        clusterGroups.append((74, "EnvironmentThing"))
        clusterGroups.append((81, "Employee"))
        clusterGroups.append((52, "Population"))
        clusterGroups.append((46, "Area"))
        clusterGroups.append((8, "Area"))
        clusterGroups.append((54, "Quantity"))
        clusterGroups.append((22, "DateTime"))
        clusterGroups.append((15, "Client"))
        clusterGroups.append((11, "ProductService"))
        clusterGroups.append((19, "ProductService"))

        clusterMap = dict(clusterGroups)

        for i in range(85):
            if i in clusterMap.keys():
                continue
            else:
                clusterMap[i] = None
        
        return clusterMap, y_kmeans_token, kmeans


    def create_triples(self, text, clusterMap, kmeans):
        marked_text = "[CLS] " + text + " [SEP]"

        # Tokenize our sentence with the BERT tokenizer.
        tokenized_text = self.tokenizer.tokenize(marked_text)

        #investigate removing punctuation

        # # Print out the tokens.
        print(tokenized_text)
        # Map the token strings to their vocabulary indeces.
        indexed_tokens = self.tokenizer.convert_tokens_to_ids(tokenized_text)

        segments_ids = [1] * len(tokenized_text)
        # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor([indexed_tokens])
        segments_tensors = torch.tensor([segments_ids])

        with torch.no_grad():
            outputs = self.model(tokens_tensor, segments_tensors)

            # Evaluating the model will return a different number of objects based on 
            # how it's  configured in the `from_pretrained` call earlier. In this case, 
            # becase we set `output_hidden_states = True`, the third item will be the 
            # hidden states from all layers. See the documentation for more details:
            # https://huggingface.co/transformers/model_doc/bert.html#bertmodel
            hidden_states = outputs[2]

            token_embeddings = torch.stack(hidden_states, dim=0)
            token_embeddings = torch.squeeze(token_embeddings, dim=1)
            


            token_embeddings = token_embeddings.permute(1,0,2)

            word_embeddings = self.get_word_embeddings(token_embeddings) #outer length is embedding, inner is each word
            # bert_embeddings.extend(word_embeddings[1:-2])
            # word_list.extend(tokenized_text[1:-2])

            # Remove Stop Words First
            new_text, new_embeddings = self.remove_stop_words(tokenized_text, word_embeddings, self.create_stopwords())
            bert = new_embeddings[1:-1]
            words = new_text[1:-1]
            # print(len(bert))
            # print(words)
            # print(len(words))

            ## Match to KMeans
            test = []
            for embedding in bert:
                test.append(embedding.cpu().detach().numpy())
            test = np.array(test)
            predictions = {}
            test= test.astype(float)
            y = kmeans.predict(test) # Cluster numbers, for clusterMap 

            Relations = [] #subject: [relation, object]

            #loop through and join noun-phrases together
            joinedTokens = []
            joinedClusters = []
            mapping_dict = {}
            i=0
            while i<len(words):
            # print(words[i], clusterMap[y[i]], y[i]) ##Need to join the words w ##
            #Apply Rules:

                if clusterMap[y[i]] is None: # Check if there's a cluster
                    joinedTokens.append(self.lemmatizer.lemmatize(words[i]))
                    joinedClusters.append("cidsThing")
                    mapping_dict[words[i]] = "cidsThing"
                    i+=1
                    continue
                else: #Check if it's a phrase ## USE POS TAGGING
                    j = i+1
                    wordphrase = self.lemmatizer.lemmatize(words[i])
                    while j<len(words):
                        if clusterMap[y[i]] == clusterMap[y[j]]:
                            wordphrase += self.lemmatizer.lemmatize(words[j].replace("#", ""))
                            j+=1
                        else:
                            break
                    joinedTokens.append(wordphrase.capitalize())
                    joinedClusters.append(clusterMap[y[i]])
                    mapping_dict[wordphrase] = clusterMap[y[i]]
                    diff = j-i-1
                    i+=(1+diff)
                    #Need to add cluster

            return mapping_dict


    def check_rb(self, rb_output):
        for key in rb_output.keys():
            if "subclassOf" in rb_output[key]:
                continue
            else:
                return False
        return True
    

    def rb_cluster_combined(self, rb_output, ind_text, clusterMap, kmeans):
        if not self.check_rb(rb_output):
            cids_mappings = self.create_triples(ind_text,clusterMap, kmeans)
            # print(cids_mappings)
            new_output = rb_output.copy()
            for key in rb_output.keys():
                if "subclassOf" in rb_output[key]:
                    if rb_output[key]["subclassOf"] == "cidsThing":
                        for k, v in cids_mappings.items():
                            new_key = [value for k, value in cids_mappings.items() if key.lower() in k.lower()]
                            if new_key:
                                new_output[key]["subclassOf"] = new_key[0]
                
            return new_output
        else:
            return rb_output




