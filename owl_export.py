import owlready2 as owl2
import datetime
from owlready2 import *

def create_ontology():

  world = owl2.World()
  cids_onto = world.get_ontology("cids.owl").load() #web protege download
  time_onto = world.get_ontology("Time.owl").load() #web protege download
  activity_onto = world.get_ontology("activity.owl").load() #web protege download
  # icontact_onto = world.get_ontology("/work/icontact.owl").load() #web protege download
  iso21972_onto = world.get_ontology("iso21972.owl").load() #web protege download
  organization_onto = world.get_ontology("organization.owl").load() #web protege download
  # genericProperties_onto = world.get_ontology("/work/GenericProperties.owl").load() #web protege download

  classes = list(cids_onto.classes())
  classes.extend(list(time_onto.classes()))
  # classes.extend(list(icontact_onto.classes()))
  classes.extend(list(activity_onto.classes()))
  classes.extend(list(iso21972_onto.classes()))
  classes.extend(list(organization_onto.classes()))
  # classes.extend(list(genericProperties_onto.classes()))

  individuals = list(cids_onto.individuals())
  individuals.extend(list(time_onto.individuals()))
  # individuals.extend(list(icontact_onto.individuals()))
  individuals.extend(list(activity_onto.individuals()))
  individuals.extend(list(iso21972_onto.individuals()))
  individuals.extend(list(organization_onto.individuals()))
  # individuals.extend(list(genericProperties_onto.individuals()))

  classes_string = []
  for c in classes:
    classes_string.append(str(c))
  return cids_onto, classes, classes_string, individuals

def create_cids_class(className, cids_onto, **kwargs):
  parent = kwargs.get('parent',None)
  properties = kwargs.get('properties',None)
  existing_class = kwargs.get('existing_class', None)

  with cids_onto:
    if existing_class:
      new_class = existing_class

    else:
      if parent:
        new_class = types.new_class(className, (parent,))
      else:
        new_class = types.new_class(className, (cids_onto.cidsThing,))
    
    # print("ancestors", new_class.ancestors())
    
    if properties:
      for prop in properties:
        # print("prop", prop)
        new_prop = types.new_class(prop[0], (ObjectProperty,))
        new_prop.domain = [new_class]
        new_prop.python_name = "new_property"
        new_class.new_property = prop[1] # what happens if prop[1] is None

        # print("properties",new_class.get_class_properties())
    
    return cids_onto

def init_classes(cids_onto, classes, classes_string):
  cids_onto = create_cids_class("ReportingPeriod", cids_onto, parent = classes[classes_string.index('time.DateTimeInterval')])
  cids_onto = create_cids_class("Farmer", cids_onto, parent = classes[classes_string.index('cids.Person')])
  cids_onto = create_cids_class("EnvironmentThing", cids_onto)
  cids_onto = create_cids_class("ProductService", cids_onto)
  cids_onto = create_cids_class("Land", cids_onto, parent = classes[classes_string.index('iso21972.Feature')])
  cids_onto = create_cids_class("Area", cids_onto, parent = classes[classes_string.index('iso21972.Quantity')], properties = [["hasPhenomenon", classes[classes_string.index('iso21972.Feature')]]])

  return cids_onto
  

def check_cids(word, classes, classes_string):
  ontologies = ["cids", "iso21972", "time", "organization", "activity"]
  for onto in ontologies:
    onto_word = onto + "."+word
    if onto_word in classes_string:
      ind = classes_string.index(onto_word)
      return classes[ind]
  
  return None

def convert_owl(tdict_list):
  cids_onto, classes, classes_string, individuals = create_ontology()

  cids_onto = init_classes(cids_onto, classes, classes_string)

  for tdict in tdict_list:
    for key in tdict.keys():
      parent = None
      properties = None
      # check cids which cids_class it's in
      class_val = check_cids(key, classes, classes_string)

      if "subclassOf" in tdict[key].keys():
        parent = check_cids(tdict[key]["subclassOf"], classes, classes_string)
      if tdict[key].keys():
        properties = []
        for subkey in tdict[key].keys():
          if subkey != "subclassOf":
            prop = check_cids(tdict[key][subkey], classes, classes_string)
            if prop is None:
              with cids_onto:
                prop = types.new_class(tdict[key][subkey], (cids_onto.cidsThing,))
            properties.append([subkey, prop])
        if len(properties)==0:
          properties = None
      
      # print(parent, properties, class_val)
      
      cids_onto = create_cids_class(key, cids_onto, parent = parent, properties = properties, existing_class = class_val)

      # Update classes
      classes.extend(list(cids_onto.classes()))
      classes = list(set(classes))
      classes_string = []
      for c in classes:
        classes_string.append(str(c))

  return cids_onto