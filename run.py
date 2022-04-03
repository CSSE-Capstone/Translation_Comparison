# TODO need main function?
import networkx as nx # TODO rb already imported this - how to avoid importing it again here? move all nx calls to within the rb function?
import matplotlib.pyplot as plt
import pandas as pd
import nltk
from transformers import BertTokenizer, BertModel
from nltk.corpus import stopwords

from rule_based.main import RuleBased
from clustering.main import Clustering 
from wordnet.main import WordNet

file_path = 'files/'

# Initialize RuleBased model
rb_grammar = r"""

    NP:
        {<NN.*|NNS.*>*<JJ><NN|NNS>+}
        {<NN.*|NNS.*>+}
    
    VP:
        {<VB|VBG|VBN>+}
    

"""
treebankTagger = nltk.data.load('taggers/maxent_treebank_pos_tagger/english.pickle')
nltk.download('punkt')

rb_chunker = nltk.RegexpParser(rb_grammar)
rb_lemmatizer = nltk.WordNetLemmatizer()
rb_model = {'from': 'VB'}
rb_tagger = nltk.tag.UnigramTagger(model=rb_model, backoff=treebankTagger) 
rb_tagger = rb_tagger.tag 

rb = RuleBased(rb_grammar, rb_chunker, rb_lemmatizer, rb_tagger)

# Initialize Clustering model
df = pd.read_csv(file_path + "iris.csv")
## Load pre-trained model (weights)
model = BertModel.from_pretrained('bert-base-uncased',
                                  output_hidden_states = True, # Whether the model returns all hidden-states.
                                  )
## Load pre-trained model tokenizer (vocabulary)
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
clustering = Clustering(model, tokenizer, rb_lemmatizer, df)

# Initialize WordNet model
wn = WordNet()

### translation output
matched_indicators = pd.read_csv(file_path + 'glossarymatchedindicators.csv', index_col=0, header=None, squeeze=True).to_dict()
cids_classes = pd.read_csv(file_path + 'cidsclasses.csv', header=None, squeeze=True).to_list()
t1_text = 'Number of individuals residing in rural areas who sold goods or services to the organization during the reporting period.'
pos_breakdown = rb.get_key_pos_tag(t1_text)
ind_code = 'PI2566'
pos_breakdown_output = rb.rb_translation(pos_breakdown, ind_code, cids_classes, matched_indicators)

# networkx
G, prop_rel = rb.plot_KG(pos_breakdown_output)
pos = nx.spring_layout(G, k=0.2)
plt.figure(figsize=(15,8))                                                    
nx.draw(G, pos, with_labels=True, arrows=True)                                                              
nx.draw_networkx_edge_labels(G,pos,edge_labels=nx.get_edge_attributes(G,'label'))

# plt.show() # TODO 


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
	clusterMap, kmeans = clustering.cluster()
	cluster_output = clustering.rb_cluster_combined(rb_output, ind_def, clusterMap, kmeans)
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