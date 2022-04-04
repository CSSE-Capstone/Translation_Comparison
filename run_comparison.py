import owlready2 as owl2
import datetime
from comparison.main import Comparison

file_path = 'files/'

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

# Initialize Comparison 
c = Comparison(classes, individuals)

indicator_standard_selection = input("Which indicator standards, if any, have been included? The options are “none”, “UN SDG”, “IRIS”, or both.")
text1 = input("Input the first thing (an individual or a class) from CIDS that you wish to compare: ")
text2 = input("Input the second thing (an individual or a class) from CIDS that you wish to compare: ")

#exact label
item1 = cids_onto.search_one(label = text1, _use_str_as_loc_str=True, _case_sensitive=False) 
item2 = cids_onto.search_one(label = text2, _use_str_as_loc_str=True, _case_sensitive=False) 


if item1 in classes and item2 in classes:
    c.recursion_check(item1, item2, check_type='class', count=0)
elif item1 in individuals and item2 in individuals:
    c.recursion_check(item1, item2, check_type='individual', count=0)
else:
    c.recursion_check(item1, item2, check_type='mixed', count=0)
