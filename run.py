# TODO need main function?
import networkx as nx # TODO rb already imported this - how to avoid importing it again here? move all nx calls to within the rb function?
import matplotlib.pyplot as plt
import pandas as pd
import nltk
from transformers import BertTokenizer, BertModel
from nltk.corpus import stopwords

from rule_based.main import RuleBased
# from clustering.main import Clustering # TODO 
from wordnet.main import WordNet

file_path = 'files/'

# Initialize RuleBased model
rb_noun_grammar = r"""

    NP:
        {<NN.*|NNS.*>*<JJ><NN|NNS>+}
        {<NN.*|NNS.*>+}
        
    JJ:
        {<JJ>}
    
    VP:
        {<VB|VBG|VBN>+}
    

"""
treebankTagger = nltk.data.load('taggers/maxent_treebank_pos_tagger/english.pickle')
nltk.download('punkt')

rb_chunker = nltk.RegexpParser(rb_noun_grammar)
rb_lemmatizer = nltk.WordNetLemmatizer()
rb_stemmer = nltk.stem.porter.PorterStemmer()
rb_model = {'from': 'VB'}
rb_tagger = nltk.tag.UnigramTagger(model=rb_model, backoff=treebankTagger) 
rb_tagger = rb_tagger.tag 

rb = RuleBased(rb_noun_grammar, rb_chunker, rb_lemmatizer, rb_stemmer, rb_tagger)

# Initialize WordNet model
wn = WordNet()

### translation output
matched_indicators = pd.read_csv(file_path + 'glossarymatchedindicators.csv', index_col=0, header=None, squeeze=True).to_dict()
cids_classes = pd.read_csv(file_path + 'cidsclasses.csv', header=None, squeeze=True).to_list()
t1_text = 'Number of individuals residing in rural areas who sold goods or services to the organization during the reporting period.'
t1 = rb.get_key_pos_tag(t1_text)
ind_code = 'PI2566'
t1_output = rb.rb_translation(t1, ind_code, cids_classes, matched_indicators)

# networkx
G, prop_rel = rb.plot_KG(t1_output)
pos = nx.spring_layout(G, k=0.2)
plt.figure(figsize=(15,8))                                                    
nx.draw(G, pos, with_labels=True, arrows=True)                                                              
nx.draw_networkx_edge_labels(G,pos,edge_labels=nx.get_edge_attributes(G,'label'))

# plt.show() # TODO 

# ======= Clustering ========
# TODO move to module 

import torch
import pandas as pd
import nltk
import numpy as np
from sklearn.cluster import KMeans
import numpy as np
from sklearn.cluster import KMeans
import copy
import seaborn as sns
from collections import defaultdict
import matplotlib.pyplot as plt


# stop words 
nltk.download("stopwords")

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

# Training 
df = pd.read_csv(file_path + "iris.csv")
definitionsDF = df[["ID", "Definition"]]
definitionsDF.head()
# Load pre-trained model tokenizer (vocabulary)
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Load pre-trained model (weights)
model = BertModel.from_pretrained('bert-base-uncased',
                                  output_hidden_states = True, # Whether the model returns all hidden-states.
                                  )

# Put the model in "evaluation" mode, meaning feed-forward operation.

model.eval()

def get_word_embeddings(token_embeddings):
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

  print ('Shape is: %d x %d' % (len(token_vecs_sum), len(token_vecs_sum[0])))
  return token_vecs_sum


def remove_stop_words(tokenized_text, word_embeddings):
  new_text = []
  new_embeddings = []
  for i, word in enumerate(tokenized_text):
    if word in stop:
      continue
    else:
      new_text.append(tokenized_text[i])
      new_embeddings.append(word_embeddings[i])

  return new_text, new_embeddings


def create_word_tokens(): #creates tokens for all iris csv
    bert_embeddings = []
    word_list = []
    for index, row in definitionsDF.iterrows():
        text = row['Definition']
        marked_text = "[CLS] " + text + " [SEP]"

        # Tokenize our sentence with the BERT tokenizer.
        tokenized_text = tokenizer.tokenize(marked_text)

        #investigate removing punctuation

        # # Print out the tokens.
        # print(tokenized_text)
        # Map the token strings to their vocabulary indeces.
        indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)
        
        segments_ids = [1] * len(tokenized_text)
        # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor([indexed_tokens])
        segments_tensors = torch.tensor([segments_ids])

        with torch.no_grad():

            outputs = model(tokens_tensor, segments_tensors)

            # Evaluating the model will return a different number of objects based on 
            # how it's  configured in the `from_pretrained` call earlier. In this case, 
            # becase we set `output_hidden_states = True`, the third item will be the 
            # hidden states from all layers. See the documentation for more details:
            # https://huggingface.co/transformers/model_doc/bert.html#bertmodel
            hidden_states = outputs[2]

            token_embeddings = torch.stack(hidden_states, dim=0)
            token_embeddings = torch.squeeze(token_embeddings, dim=1)
            


            token_embeddings = token_embeddings.permute(1,0,2)

            word_embeddings = get_word_embeddings(token_embeddings) #outer length is embedding, inner is each word
            # bert_embeddings.extend(word_embeddings[1:-2])
            # word_list.extend(tokenized_text[1:-2])

            # Remove Stop Words First
            new_text, new_embeddings = remove_stop_words(tokenized_text, word_embeddings)
            bert_embeddings.extend(new_embeddings[1:-1])
            word_list.extend(new_text[1:-1])
    return bert_embeddings, word_list



bert_embeddings, word_list = create_word_tokens()

# how to cluster with labelled data
X = []
for embedding in bert_embeddings:
  X.append(embedding.cpu().detach().numpy())
X = np.array(X)

mean, stdev = np.median(X, axis=0), np.std(X, axis=0)

outliers = ((np.abs(X[:,0] - mean[0]) > stdev[0])
        * (np.abs(X[:,1] - mean[1]) > stdev[1])
        * (np.abs(X[:,2] - mean[2]) > stdev[2]))
# print(len(outliers))
# print(X.shape)
# print(np.count_nonzero(outliers))
X_no_outliers = list(X)
word_list_no_outliers = copy.deepcopy(word_list)
for i in range(len(outliers)-1, -1, -1):
  if outliers[i] == True:
    X_no_outliers.pop(i)
    word_list_no_outliers.pop(i)

# how to cluster with labelled data
kmeans = KMeans(n_clusters=85, random_state=0, max_iter=600, algorithm="full")
# kmeans = KMedoids(n_clusters=85, random_state=0, max_iter=600)

y_kmeans_token = kmeans.fit_predict(X_no_outliers)


# plot clusters
# TODO make a function 
sns.set()  # for plot styling
# plt.scatter(X, c=y_kmeans, s=50, cmap='viridis')

centers = kmeans.cluster_centers_
plt.scatter(centers[:, 0], centers[:, 1], c='black', s=200, alpha=0.5);

plt.figure(figsize=(10,11))
X_no_outliers = np.array(X_no_outliers)
plt.scatter(X_no_outliers[:, 0], X_no_outliers[:, 1])
plt.subplot()

plt.scatter(centers[:, 0], centers[:, 1], c='black', s=200, alpha=0.5)
# plt.show() # TODO 


# Groups words to clusters in a dictionary:
# TODO make a function
# print(len(set(word_list_no_outliers)))
clusters = defaultdict(list)
for i in range(len(word_list_no_outliers)):
    clusters[y_kmeans_token[i]].append(word_list_no_outliers[i])
for k,v in clusters.items():
    clusters[k] = list(set(v))


# Visualize Clusters Content
# TODO make a function
cluster_text = ''
for k,v in clusters.items():
    add = str(k)+ ':' + str(v) + "\n"
cluster_text += add

# print(cluster_text)


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
clusterGroups.append((46, "Area")) # Q: should these be features or areas or geography or.. ?
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
# print(clusterMap)


def create_triples(text, clusterMap, kmeans):
  marked_text = "[CLS] " + text + " [SEP]"

  # Tokenize our sentence with the BERT tokenizer.
  tokenized_text = tokenizer.tokenize(marked_text)

  #investigate removing punctuation

  # # Print out the tokens.
  print(tokenized_text)
  # Map the token strings to their vocabulary indeces.
  indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)

  segments_ids = [1] * len(tokenized_text)
  # Convert inputs to PyTorch tensors
  tokens_tensor = torch.tensor([indexed_tokens])
  segments_tensors = torch.tensor([segments_ids])

  with torch.no_grad():
    outputs = model(tokens_tensor, segments_tensors)

    # Evaluating the model will return a different number of objects based on 
    # how it's  configured in the `from_pretrained` call earlier. In this case, 
    # becase we set `output_hidden_states = True`, the third item will be the 
    # hidden states from all layers. See the documentation for more details:
    # https://huggingface.co/transformers/model_doc/bert.html#bertmodel
    hidden_states = outputs[2]

    token_embeddings = torch.stack(hidden_states, dim=0)
    token_embeddings = torch.squeeze(token_embeddings, dim=1)
    


    token_embeddings = token_embeddings.permute(1,0,2)

    word_embeddings = get_word_embeddings(token_embeddings) #outer length is embedding, inner is each word
    # bert_embeddings.extend(word_embeddings[1:-2])
    # word_list.extend(tokenized_text[1:-2])

    # Remove Stop Words First
    new_text, new_embeddings = remove_stop_words(tokenized_text, word_embeddings)
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
        joinedTokens.append(rb_lemmatizer.lemmatize(words[i]))
        joinedClusters.append("cidsThing")
        mapping_dict[words[i]] = "cidsThing"
        i+=1
        continue
      else: #Check if it's a phrase ## USE POS TAGGING
        j = i+1
        wordphrase = rb_lemmatizer.lemmatize(words[i])
        while j<len(words):
        # TODO add lemmatizer here (wordnet lemmatizer)
          if clusterMap[y[i]] == clusterMap[y[j]]:
            wordphrase += rb_lemmatizer.lemmatize(words[j].replace("#", ""))
            j+=1
          else:
            break
        joinedTokens.append(wordphrase.capitalize())
        joinedClusters.append(clusterMap[y[i]])
        mapping_dict[wordphrase] = clusterMap[y[i]]
        diff = j-i-1
        i+=(1+diff)
        #Need to add cluster
    # print(joinedTokens)
    # print(joinedClusters)
    # print(mapping_dict)
    # print(y)
    return mapping_dict



def check_rb(rb_output):
    for key in rb_output.keys():
        if "subclassOf" in rb_output[key]:
            continue
        else:
            return False
    return True

# MAIN
def rb_cluster_combined(rb_output, ind_text, clusterMap, kmeans):
    if not check_rb(rb_output):
        cids_mappings = create_triples(ind_text,clusterMap,  kmeans)
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



# ======= Merge =======
'''
# for each [IRIS or UNSDG] indicator text,
## POS the indicator text.
## Perform Rule based (NER,RE). Returns a dictionary-form KG.
## Perform clustering. Returns an updated dictionary-form KG.
### (Extract cidsThing noun phrases from the dictionary)
## Perform wn. Returns an updated dictionary-form KG.
### (Extract xxxThing noun phrases from the dictionary)
'''
# TODO uncomment
# rb_output_test = {'PI2566': {'subclassOf': 'Cardinality', 'cardinalityOf': 'PI2566Population'},
#  'PI2566Population': {'subclassOf': 'Population',
#   'forTimeInterval': 'ReportingPeriod',
#   'definedBy': 'Individual'},
#  'ReportingPeriod': {'subclassOf': 'DateTimeInterval'},
#  'Cardinality': {},
#  'Individual': {'subclassOf': 'Person', 'residing': 'RuralArea'},
#  'RuralArea': {'subclassOf': 'Area', 'sold': 'GoodService'},
#  'GoodService': {'subclassOf': 'cidsThing'},
#  'Organization': {}}

# # Clustering 
# clustering_kg_dict = rb_cluster_combined(rb_output_test, t1_text, clusterMap, kmeans)
# print(f'clustering_kg_dict:{clustering_kg_dict}')

# # wn
# # wn_kg_dict = wordnet(t1_text, clustering_kg_dict) # TODO uncomment
# print(f't1_output: {t1_output}')
# wn_kg_dict = wn.wordnet(t1_text, t1_output) # TODO rm
# print(f'wn_kg_dict: {wn_kg_dict}')

# ===== Demo =====
indtestset = pd.read_csv(file_path + 'indicatortestset.csv', encoding = "ISO-8859-1", engine='python')

for index, row in indtestset.iterrows():
  ind_code = row['Indicator Code']
  ind_def = row['Indicator Definition']
  print(ind_code)
  print(ind_def)
  #output_kg(ind_code, ind_def)

  pos_tagged = rb.get_key_pos_tag(ind_def)
  rb_output = rb.rb_translation(pos_tagged, ind_code, cids_classes, matched_indicators)
  print('rb_output')
  print(rb_output)
  cluster_output = rb_cluster_combined(rb_output, ind_def, clusterMap, kmeans)
  print('cluster_output')
  print(cluster_output)
  wordnet_output = wn.wordnet(ind_def, rb_output)
  print('wordnet_output')
  print(wordnet_output)
  if cluster_output != wordnet_output: import pdb;pdb.set_trace() # TODO rm

  G, prop_rel = rb.plot_KG(cluster_output)
  pos = nx.spring_layout(G, k=0.2)
  plt.figure(figsize=(15,8))                                                    
  nx.draw(G, pos, with_labels=True, arrows=True)                                                              
  nx.draw_networkx_edge_labels(G,pos,edge_labels=nx.get_edge_attributes(G,'label'))

#   plt.show()
  print('\n')