import networkx as nx 
import matplotlib.pyplot as plt
import pandas as pd
import nltk
from transformers import BertTokenizer, BertModel
from nltk.corpus import stopwords
import argparse

from rule_based.main import RuleBased
from clustering.main import Clustering 
from wordnet.main import WordNet

# Command line options 
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--plot', action='store_true', default=False, help='if True, generates NetworkX graphs.')
parser.add_argument('-d', '--dataset', action='store', default='indicatortestset.csv', help="Specify name of the indicator definition text csv file, e.g. 'indicatortestset.csv'")
args = parser.parse_args()
plot_graph = bool(args.plot)
dataset_name = args.dataset

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
wn = WordNet(similarity_threshold=0.8, 
			t_ss_method='lesk',
			c_ss_method='lesk',
			last_subword_weight=0.6)


# Run test set 
indtestset = pd.read_csv(file_path + dataset_name, encoding = "ISO-8859-1", engine='python')
cids_classes = pd.read_csv(file_path + 'cidsclasses.csv', header=None, squeeze=True).to_list()
matched_indicators = pd.read_csv(file_path + 'glossarymatchedindicators.csv', index_col=0, header=None, squeeze=True).to_dict()

# Peform translation on each sentence in indicatortestset.csv
for index, row in indtestset.iterrows():
	ind_code = row['Indicator Code']
	ind_def = row['Indicator Definition']
	print(ind_code)
	print(ind_def)
	
	# Step 1: POS tag sentence
	pos_tagged = rb.get_key_pos_tag(ind_def)
	rb_output = rb.rb_translation(pos_tagged, ind_code, cids_classes, matched_indicators)
	print('rb_output')
	print(rb_output)

	clusterMap, kmeans = clustering.cluster()
	cluster_output = clustering.rb_cluster_combined(rb_output, ind_def, clusterMap, kmeans)
	print('cluster_output')
	print(cluster_output)

	wordnet_output = wn.wordnet(ind_def, cluster_output)
	print('wordnet_output')
	print(wordnet_output)

	# Plot networkx graph
	G, prop_rel = rb.plot_KG(wordnet_output)
	pos = nx.spring_layout(G, k=0.2)
	plt.figure(figsize=(15,8))                                                    
	nx.draw(G, pos, with_labels=True, arrows=True)                                                              
	nx.draw_networkx_edge_labels(G,pos,edge_labels=nx.get_edge_attributes(G,'label'))

	if plot_graph:
		plt.show() 
	print('\n')

# TODO @sandy: Add translated indicators to CIDS .owl file 