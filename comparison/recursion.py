#imports
from main import *
import owlready2 as owl2
import datetime

#Edit file path 
#file_path = '../files/'
file_path = '/Users/neevi/OneDrive - University of Toronto/Fourth Year 2T1-2T2/Capstone/Translation_Comparison/files/'

world = owl2.World()
cids_onto = world.get_ontology(file_path + "cids.owl").load() #web protege download
time_onto = world.get_ontology(file_path + "Time.owl").load() #web protege download
activity_onto = world.get_ontology(file_path + "activity.owl").load() #web protege download
icontact_onto = world.get_ontology(file_path + "icontact.owl").load() #web protege download
iso21972_onto = world.get_ontology(file_path + "iso21972.owl").load() #web protege download
organization_onto = world.get_ontology(file_path + "organization.owl").load() #web protege download
genericProperties_onto = world.get_ontology(file_path + "GenericProperties.owl").load() #web protege download

# get all classes - cids and all other imported ontologies
classes = list(cids_onto.classes())
classes.extend(list(time_onto.classes()))
classes.extend(list(icontact_onto.classes()))
classes.extend(list(activity_onto.classes()))
classes.extend(list(iso21972_onto.classes()))
classes.extend(list(organization_onto.classes()))
classes.extend(list(genericProperties_onto.classes()))

# get all individuals - cids and all other imported ontologies
individuals = list(cids_onto.individuals())
individuals.extend(list(time_onto.individuals()))
individuals.extend(list(icontact_onto.individuals()))
individuals.extend(list(activity_onto.individuals()))
individuals.extend(list(iso21972_onto.individuals()))
individuals.extend(list(organization_onto.individuals()))
individuals.extend(list(genericProperties_onto.individuals()))

#input
indicator_standard_selection = input("Which indicator standards, if any, have been included? The options are “none”, “UN SDG”, “IRIS”, or both.")
text = input("Input the label of the first thing you wish to compare: ")
text2 = input("Input the label of the second thing you wish to compare: ")

item1 = cids_onto.search_one(label = "*" + text + "*", _use_str_as_loc_str=True, _case_sensitive=False) 
item2 = cids_onto.search_one(label = "*" + text + "*", _use_str_as_loc_str=True, _case_sensitive=False) 

#run recursion check
#recursion_check(self, node1, node2, check_type, count=0)
recursion_check(item1, item2, "class", count=0)
