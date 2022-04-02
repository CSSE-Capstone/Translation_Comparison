import owlready2 as owl2
import datetime

class Comparison:
    def __init__(self, classes, individuals):
        self.classes = classes
        self.individuals = individuals
    
    # RECURSION MAIN 
    def recursion_check(self, node1, node2, check_type, count=0): # both roots are individuals
        '''
        Recursively performs consistency checks at every node in the owlready2 item. 
        Parameters:
            node1 - the current node being checked for item 1
            node2 - the current node being checked for item 2
            check_type - the type of check - individual check, class check, or mixed check (if item1 and item2 are a class-individual combination)
                options:
                    'individual'
                    'class'
                    'mixed'
        Outputs:
            consistency check print statements. For each check, it will determine if the two items are consistent, inconsistent, or potentially consistent at appropriate nodes. 
    '''
        # Validate check_type
        assert check_type in ['individual', 'class', 'mixed'], f"check_type of {check_type} undefined. Make sure that it is one of the following options: 'individual', 'class', 'mixed'"

        # run intra checks only once at the start node
        # works at the start node level
        if count == 0:
            if node1 in self.individuals:
                self.run_intra_checks(node1)
            if node2 in self.individuals:
                self.run_intra_checks(node2)
        
        # run inter checks
        if check_type == 'individual':
            self.run_individual_inter_checks(node1, node2)
        elif check_type == 'class':
            self.run_class_inter_checks(node1, node2)
        elif check_type == 'mixed':
            self.run_mixed_inter_checks(node1, node2)
        
        # Get all properties of node1 and node2
        node1_properties = node1.get_class_properties() if node1 in self.classes else node1.get_properties()
        node2_properties = node2.get_class_properties() if node2 in self.classes else node2.get_properties()

        # Remove duplicate properties in list, then sort node1_properties and node2_properties
        node1_properties = sorted(list(set(self.remove_annotation_properties(list(node1_properties)))))
        node2_properties = sorted(list(set(self.remove_annotation_properties(list(node2_properties)))))

        # Print inconsistent if a property from node1 is not found in node2, and vice versa
        ## If there are properties found in node1 but not in node2
        if set(node1_properties) - set(node2_properties):
            for p in list(set(node1_properties) - set(node2_properties)):
                print(f'Item 1 has the {node1} - {p} - {p[node1]} triple, but Item 2 does not.')
        ## If there are properties found in node2 but not in node1
        if set(node2_properties) - set(node1_properties):
            for p in list(set(node2_properties) - set(node1_properties)):
                print(f'Item 2 has the {node2} - {p} - {p[node2]} triple, but Item 1 does not.')

        # Get the list of common properties from node1 and node2
        common_properties = set(node1_properties).intersection(set(node2_properties))

        # Traverse both trees using their common properties
        for p in common_properties:
            # Get the child of this p for both trees
            node1_obj = p[node1]
            node2_obj = p[node2]
            
            # Determine if the child is a data value (ie a leaf node)
            node1_obj_is_data_value = isinstance(node1_obj, str) and isinstance(node1_obj, int) # TODO any more types?
            node2_obj_is_data_value = isinstance(node2_obj, str) and isinstance(node2_obj, int) # TODO any more types?

            # immediately inconsistent cases
            # TODO already in consistency checks? if so rm 
            if node1_obj_is_data_value and not node2_obj_is_data_value or not node1_obj_is_data_value and node2_obj_is_data_value:
                print('Inconsistent')
                print(f'node1 object is {node1_obj} but node2 object is {node2_obj}')
                return
            
            # Base case 1: if children are None 
            if node1_obj and node2_obj is None:
                return 
            # Base case 2: if children are data values
            if node1_obj_is_data_value and node2_obj_is_data_value:
                return
            
            # Recursion case 
            if not node1_obj_is_data_value and not node2_obj_is_data_value:
                return self.recursion_check(node1_obj, node2_obj, check_type, count+1) 

    def run_individual_inter_checks(self, item1, item2):
        place_equality_consistent = self.place_equality_consistency_check(item1, item2) #needed to run self.subplace_consistency_check
        self.subplace_consistency_check(place_equality_consistent, item1, item2)
        self.temporal_granularity_consistency_check(item1, item2) #run this before subinterval since subinterval needs them to be the same temporal unit, but actually, does it matter? No, but it does in the way that I implemented it using the datetime library
        self.subinterval_consistency_check(item1, item2)
        #property_consistency_check(item1, item2) #need to debug
        self.interval_equality_consistency_check(item1, item2)
        self.interval_non_overlap_consistency_check(item1, item2)

    # TODO add
    def run_intra_checks(self, item):
        self.quantity_measure_consistency_check(item)
        # if item is a ratio (individual), run the following checks
        item_property_names = [p.name for p in item.get_properties()]
        if all(p in item_property_names for p in ['hasNumerator', 'hasDenominator']) or all(p in item_property_names for p in ['numerator', 'hasDenominator']) or all(p in item_property_names for p in ['hasNumerator', 'denominator']) or all(p in item_property_names for p in ['numerator', 'denominator']):
            for p in item.get_properties():
                if p.name == 'hasNumerator' or p.name  == 'numerator':
                    numerator_obj = p[item]
                if p.name == 'hasDenominator' or p.name == 'denominator':
                    denominator_obj = p[item]
            self.indicator_unit_component_consistency_check(numerator_obj, denominator_obj)
            self.temporal_granularity_consistency_check(numerator_obj, denominator_obj)
            place_equality_consistent = self.place_equality_consistency_check(numerator_obj, denominator_obj) #needed to run self.subplace_consistency_check
            self.subplace_consistency_check(place_equality_consistent, numerator_obj, denominator_obj)

    def run_class_inter_checks(self, item1, item2):
        self.class_type_consistency_check(item1, item2)

    def run_mixed_inter_checks(self, item1, item2):
        self.instance_type_consistency_check(item1, item2)
        self.property_consistency_check(item1, item2)
        self.singular_unit_consistency_check(item1, item2)
        self.correspondence_consistency_check(item1, item2)

    
    def remove_annotation_properties(self, properties):
        return [p for p in properties if str(p) not in ['rdf-schema.commment', 'rdf-schema.label']]


    # MAIN
    def compare_class_or_individual(self, item1, item2):
        # TODO list of mix case checks
        # TODO list of class checks
        # TODO list of individuals checks
        if item1 in self.classes and item2 in self.individuals or item1 in self.individuals and item2 in self.classes:
            self.correspondence_consistency_check #for class and individual
            #TODO some checks may benefit from recognizing correspondence
            self.instance_type_consistency_check(item1, item2) #for class and individual
            self.singular_unit_consistency_check #for class and individual
        
        if item1 in self.classes:
            allprop = item1.get_class_properties()
            #remove annotation properties
            prop = [str(s) for s in allprop]
            if len(prop) > 0:
                for s in prop:
                #print (type(s))
                #print(s)
                    if s == 'rdf-schema.commment':
                        prop.remove('rdf-schema.commment')
                    if s == 'rdf-schema.label':
                        prop.remove('rdf-schema.label')
                    if s == 'rdf-schema.comment':
                        prop.remove('rdf-schema.comment')
          #print(prop)

            #class type inconsistency - type  inconsistent  if it is  not  the case that the two  self.classes are  equal, 
            #nor there exists a property  owl:equivalentClass or owl:subclassOf  between  the self.classes,  
            #or  one class  is  not  subsumed  by  another  class. 
            self.class_type_consistency_check(item1, item2)

        elif item1 in self.individuals:
            allprop = item1.get_properties()
            prop = [str(s) for s in allprop]
            #remove annotation properties 
            if len(prop) > 0:
                for s in prop:
                #print (type(s))
                #print(s)
                    if s == 'rdf-schema.commment':
                        prop.remove('rdf-schema.commment')
                    if s == 'rdf-schema.label':
                            prop.remove('rdf-schema.label')
                    if s == 'rdf-schema.comment':
                        prop.remove('rdf-schema.comment')
                #print(prop)
        
            place_equality_consistent = self.place_equality_consistency_check(item1, item2) #needed to run self.subplace_consistency_check
            self.subplace_consistency_check(place_equality_consistent, item1, item2)
            self.temporal_granularity_consistency_check(item1, item2) #run this before subinterval since subinterval needs them to be the same temporal unit, but actually, does it matter? No, but it does in the way that I implemented it using the datetime library
            self.subinterval_consistency_check(item1, item2)
            #self.property_consistency_check(item1, item2) #need to debug
            self.interval_equality_consistency_check(item1, item2)
            self.interval_non_overlap_consistency_check(item1, item2)
            self.indicator_unit_component_consistency_check(item1, item2)
            #self.quantity_measure_consistency_check(item1, item2)
    #inter
    def class_type_consistency_check(self, item1, item2): # item: KG of SPO or Indicator
        class_type_consistent = False

        if item2 not in self.classes:
            print("Class type consistency check not run - ", item2, " is not a class.")
            return

        prop1 = [p for p in item1.get_class_properties()]
        prop2 = [p for p in item2.get_class_properties()]
        # type(item) <- direct parent of item
        # prop1 <- names of properties, not the actual property values
        if ((type(item1) == type(item2)) and (item1.name and item2.name) and (item1.name == item2.name) and (set(prop1) == set(prop2))): 
            #check if properties the same (not checking property values to save computation time) and name and type
            class_type_consistent = True
            print("Class type consistent because self.classes are equal.")
            return class_type_consistent
        elif item2 in item1.INDIRECT_equivalent_to or item1 in item2.INDIRECT_equivalent_to:
            class_type_consistent = True
            print("Class type consistent due to equivalency.")
            return class_type_consistent
        elif item2 in list(item1.subclasses()) or item1 in list(item2.subclasses()):
            class_type_consistent = True
            print("Class type consistent because one is the subclass of the other.")
            return class_type_consistent
        #subsumption
        for x in list(item1.self.subclasses()):
            if x in list(item2.subclasses()) or x in item2.INDIRECT_equivalent_to or x == item2:
                class_type_consistent = True
                print("Class type consistent due to subsumption.")
                return class_type_consistent
        for y in list(item2.self.subclasses()):
            if y in list(item1.subclasses()) or y in item1.INDIRECT_equivalent_to or y == item1:
                class_type_consistent = True
                print("Class type consistent due to subsumption.")
                return class_type_consistent
        #final verdict
        if class_type_consistent == False:
            print("Class type inconsistent - neither of the two self.classes is equal, equivalent, or a subclass of the other class.")
            return class_type_consistent
        
    #inter
    def instance_type_consistency_check(self, item1, item2):
        '''
        Instance type inconsistency verifies that if the instances that make up a city's indicator are an instance of the same class, 
        #an equivalent class, a subclass of concepts defined in standard, 
        or have all necessary properties with values that satisfy the restrictions of those properties defined in the standard definition.
        
        There does  not  exist  a  direct  rdf:type  relation  between mij  and  nik,  mij is not an  instance  of  nik,  and mij is an  instance  of  civ, and  civ  is type inconsistent with  nik 

        For example, let mij be the 15.2 indicator value published by Toronto, nik be the class iso37120:’15.2’ where Cor(mij,nik). 
        Assuming there is a direct rdf:type such that Tri(mij, rdf:type, nik), or Tri(mij, rdf:type, civ) 
        and civ is the same class, equivalent class or a subclass of nik, i.e., iso37120:15.2, then mij is instance type consistent nik. 
        In Figure 22, given that Cor(mij,nik) and mij is an instance of civ. The class civ and nik are linked to c’iv and n’ik respectively via property ait. 


        There does not exist a direct rdf:type relation between mij and nik  (comparing instance m to class n)
        mij is not an instance of nik, and  
        mij is an instance of civ, and civ is type inconsistent with nik

        Given an individual and its corresponding class, the rules determine whether:
        • the individual contains all of the necessary properties as defined by the class it is a member of, and
        • the corresponding value for the individual’s property is consistent with the restrictions defined by the class for that property.

        '''
        if (item2 in self.classes and item1 in self.individuals):
            #item 2 = n, item1 = m
            #parent = item1.is_instance_of[0] #parent class of item1
            #if parent in str(item2.self.subclasses()))

            if item1 not in item2.instances(): 
                print(item1, " is not an instance of " , item2, " - therefore they are instance type inconsistent.")
                return
            
            else: #item1 is instance of item2
                if type(item1) == item2: #item1 has type item2
                    for c in item1.is_instance_of:
                        #The instance mij is type inconsistent with nik if the class civ is inconsistent with nik, i.e., Type InConsistency(civ,nik) is true. 
                        if self.class_type_consistency_check(c, item2) == False:
                            print(item1, " is an instance of " ,c, ", which is type inconsistent with " ,item2, " - therefore ", item1, "is instance type inconsistent with ", item2, ".")
                            break
                            return
                        #elif necessary properties satisfy restriction of properties
                        else:
                            print(item1, " is instance type consistent with ", item2, " because there is a direct rdf:type relation between them, ", item1, " is an instance of ", item2, ", and all self.classes that ", item1, " is an instance of are type consistent with ", item2, ".")
                            return
                else:
                    print(item1, " is instance type inconsistent with ", item2, " because there is not a direct rdf:type relation between them.")
                    return

        elif (item1 in self.classes and item2 in self.individuals):
            #item1 = n, item2 = m
            #parent = item2.is_instance_of[0] #parent class of item2
            #if parent in str(item1.self.subclasses()))

            if item2 not in item1.instances(): 
                print(item2, " is not an instance of " , item1, " - therefore they are instance type inconsistent.")
                return
            
            else: #item2 is instance of item1
                if type(item2) == item1: #item2 has type item1
                    for c in item2.is_instance_of:
                        #The instance mij is type inconsistent with nik if the class civ is inconsistent with nik, i.e., Type InConsistency(civ,nik) is true. 
                        if self.class_type_consistency_check(c, item1) == False:
                            print(item2, " is an instance of " ,c, ", which is type inconsistent with " ,item1, " - therefore ", item2, "is instance type inconsistent with ", item1, ".")
                            break
                            return
                        #elif necessary properties satisfy restriction of properties, can i use property consistency check?
                        else:
                            print(item2, " is instance type consistent with ", item1, " because there is a direct rdf:type relation between them, ", item2, " is an instance of ", item1, ", and all self.classes that ", item2, " is an instance of are type consistent with ", item1, ".")
                            return
                else:
                    print(item2, " is instance type inconsistent with ", item1, " because there is not a direct rdf:type relation between them.")
                    return

        else:
            print("Instance type consistency check not run - one of the items must be an instance and the other a class.")
            return      
    
    def get_date(self, beginning1, beginning2, end1, end2): 
        intervalBeginning1 = datetime.date(int(beginning1.year), int(beginning1.month), int(beginning1.day))
        intervalEnd1 = datetime.date(int(end1.year), int(end1.month), int(end1.day))
        #print(intervalBeginning1, intervalEnd1)

        intervalBeginning2 = datetime.date(int(beginning2.year), int(beginning2.month), int(beginning2.day))
        intervalEnd2 = datetime.date(int(end2.year), int(end2.month), int(end2.day))
        #print(intervalBeginning2, intervalEnd2)
        return intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2

    #might delete
    def get_date_when_none_values(self, beginning1, beginning2, end1, end2): 
        if type(beginning1.year) == None and (beginning1.month) and (beginning1.day) and type(beginning2.year) == None and (beginning2.month) and (beginning2.day):
            intervalBeginning1 = [int(beginning1.month), int(beginning1.day)]
            intervalEnd1 = [int(end1.month), int(end1.day)]
            #print(intervalBeginning1, intervalEnd1)
            intervalBeginning2 = [int(beginning2.month), int(beginning2.day)]
            intervalEnd2 = [int(end2.month), int(end2.day)]
            #print(intervalBeginning2, intervalEnd2)
        elif (beginning1.year) and (beginning1.month) and type(beginning1.day) == None and (beginning2.year) and type(beginning2.month) and type(beginning2.day) == None:
            intervalBeginning1 = [int(beginning1.year), int(beginning1.month)]
            intervalEnd1 = [int(end1.year), int(end1.month)]
            #print(intervalBeginning1, intervalEnd1)
            intervalBeginning2 = [int(beginning2.year), int(beginning2.month)]
            intervalEnd2 = [int(end2.year), int(end2.month)]
            #print(intervalBeginning2, intervalEnd2)
        return intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2
    
    #inter, if you want to check a ratio then you have to put item1 as the numerator and item2 as the denominator for example
    def subinterval_consistency_check(self, item1, item2): 
        '''
        #TODO NEED VERSION THAT WORKS WHEN YEAR MISSING! OR IN THIS CASE JUST PRINT - MISSING YEAR INFO. POTENTIALLY INCONSISTENT.
        #TODO Add docstring
        '''
        if item2 not in self.individuals: #cannot run this check unless both are instances
            print("Subinterval consistency check not run - it is only done when comparing 2 individuals.")
            return
        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = item1.hasBeginning 
            end1 = item1.hasEnd
            beginning2 = item2.hasBeginning
            end2 = item2.hasEnd
        else: 
            return

        if (beginning1.year) and (beginning1.month) and (beginning1.day) and (beginning2.year) and (beginning2.month) and (beginning2.day):
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date(beginning1, beginning2, end1, end2)

        #compare:

            #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
            if (intervalBeginning2 < intervalBeginning1 and intervalBeginning1< intervalEnd1 and intervalEnd1 < intervalEnd2):
                print(item1 , "'s time interval is during " , item2 , "'s. Therefore they are subinterval inconsistent.")
                return
            elif (intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                print(item2 , "'s time interval is during " , item1 , "'s. Therefore they are subinterval inconsistent.")
                return

            #overlaps: start(a) < start(b) < end(a) < end(b)
            elif (intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 < intervalEnd2):
                print(item1 , "'s time interval overlaps with " , item2 , "'s. Therefore they are subinterval inconsistent.")
                return
            elif (intervalBeginning2 < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                print(item2 , "'s time interval overlaps with " , item1 , "'s. Therefore they are subinterval inconsistent.")
                return
            
            #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
            elif intervalBeginning1 == intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 < intervalEnd2:
                print(item1 , "and " , item2 , "start together but " , item1 , " ends before " , item2 , ". Therefore they are subinterval inconsistent.")
                return
            elif intervalBeginning1 == intervalBeginning2 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1:
                print(item1 , "and " , item2 , "start together but " , item2 , " ends before " , item1 , ". Therefore they are subinterval inconsistent.")
                return

            #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
            elif intervalBeginning2 < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
                print(item1 , "and " , item2 , "end together but " , item1 , " starts after " , item2 , ". Therefore they are subinterval inconsistent.")
                return
            elif intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2 and intervalEnd2 == intervalEnd1:
                print(item1 , "and " , item2 , "end together but " , item2 , " starts after " , item1 , ". Therefore they are subinterval inconsistent.")
                return
            
            #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
            elif intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalBeginning2 and intervalBeginning2 < intervalEnd2:
                print(item1 , " ends when " , item2, " begins. Therefore they are subinterval inconsistent.")
                return
            elif intervalBeginning2 < intervalEnd2 and intervalEnd2 == intervalBeginning1 and intervalBeginning1 < intervalEnd1:
                print(item2 , " ends when " , item1, " begins. Therefore they are subinterval inconsistent.")
                return
            else:
                print(item1 , " and " , item2 , " are subinterval consistent.")
                return
        else:
        #check each item of list. List is always organized from [year, month, day]
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date_when_none_values(beginning1, beginning2, end1, end2)

        #compare all intervals on first element of list. then compare items on second element of list. 
        #TODO See if more efficient method
        #TODO make sure this works if month is higher but year is lower for something. it should though because I'm checking [0] before [1]

        #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
        if (intervalBeginning2[0] < intervalBeginning1[0]) and intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] < intervalEnd2[0]:
            print(item1 , "'s time interval is during " , item2 , "'s. Therefore they are subinterval inconsistent.")
            return
        elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0] < intervalEnd1[0]:
            print(item2 , "'s time interval is during " , item1 , "'s. Therefore they are subinterval inconsistent.")
            return
        #overlaps: start(a) < start(b) < end(a) < end(b)
        elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd1[0] and intervalEnd1[0] < intervalEnd2[0]:
            print(item1 , "'s time interval overlaps with " , item2 , "'s. Therefore they are subinterval inconsistent.")
            return
        elif (intervalBeginning2[0] < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
            print(item2 , "'s time interval overlaps with " , item1 , "'s. Therefore they are subinterval inconsistent.")
            return
        #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
        elif intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning2[0]< intervalEnd1[0]  and intervalEnd1[0]  < intervalEnd2[0]:
            print(item1 , "and " , item2 , "start together but " , item1 , " ends before " , item2 , ". Therefore they are subinterval inconsistent.")
            return
        elif intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning1[0] < intervalEnd2[0]  and intervalEnd2[0]  < intervalEnd1[0]:
            print(item1 , "and " , item2 , "start together but " , item2 , " ends before " , item1 , ". Therefore they are subinterval inconsistent.")
            return
        #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
        elif intervalBeginning2[0] < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
            print(item1 , "and " , item2 , "end together but " , item1 , " starts after " , item2 , ". Therefore they are subinterval inconsistent.")
            return
        elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0]  == intervalEnd1[0]:
            print(item1 , "and " , item2 , "end together but " , item2 , " starts after " , item1 , ". Therefore they are subinterval inconsistent.")
            return
        #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
        elif intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] == intervalBeginning2[0] and intervalBeginning2[0]< intervalEnd2[0]:
            print(item1 , " ends when " , item2, " begins. Therefore they are subinterval inconsistent.")
            return
        elif intervalBeginning2[0]< intervalEnd2[0] and intervalEnd2[0] == intervalBeginning1[0] and intervalBeginning1[0] < intervalEnd1[0]:
            print(item2 , " ends when " , item1, " begins. Therefore they are subinterval inconsistent.")
            return
        
        #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
        elif (intervalBeginning2[1] < intervalBeginning1[1] and intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] < intervalEnd2[1]):
            print(item1 , "'s time interval is during " , item2 , "'s. Therefore they are subinterval inconsistent.")
            return
        elif (intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1] < intervalEnd1[1]):
            print(item2 , "'s time interval is during " , item1 , "'s. Therefore they are subinterval inconsistent.")
            return
        #overlaps: start(a) < start(b) < end(a) < end(b)
        elif (intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd1[1] and intervalEnd1[1] < intervalEnd2[1]):
            print(item1 , "'s time interval overlaps with " , item2 , "'s. Therefore they are subinterval inconsistent.")
            return
        elif (intervalBeginning2[1] < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
            print(item2 , "'s time interval overlaps with " , item1 , "'s. Therefore they are subinterval inconsistent.")
            return
        #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
        elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning2[1]< intervalEnd1[1]  and intervalEnd1[1]  < intervalEnd2[1]:
            print(item1 , "and " , item2 , "start together but " , item1 , " ends before " , item2 , ". Therefore they are subinterval inconsistent.")
            return
        elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning1[1] < intervalEnd2[1]  and intervalEnd2[1]  < intervalEnd1[1]:
            print(item1 , "and " , item2 , "start together but " , item2 , " ends before " , item1 , ". Therefore they are subinterval inconsistent.")
            return
        #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
        elif intervalBeginning2[1] < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
            print(item1 , "and " , item2 , "end together but " , item1 , " starts after " , item2 , ". Therefore they are subinterval inconsistent.")
            return
        elif intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1]  == intervalEnd1[1]:
            print(item1 , "and " , item2 , "end together but " , item2 , " starts after " , item1 , ". Therefore they are subinterval inconsistent.")
            return
        #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
        elif intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] == intervalBeginning2[1] and intervalBeginning2[1]< intervalEnd2[1]:
            print(item1 , " ends when " , item2, " begins. Therefore they are subinterval inconsistent.")
            return
        elif intervalBeginning2[1]< intervalEnd2[1] and intervalEnd2[1] == intervalBeginning1[1] and intervalBeginning1[1] < intervalEnd1[1]:
            print(item2 , " ends when " , item1, " begins. Therefore they are subinterval inconsistent.")
            return
        else:
            print(item1 , " and " , item2 , " are subinterval consistent.")
            return

    #inter with an intra component (the beginning and end of the input's time interval is checked first), if you want to check a ratio then you have to put item1 as the numerator and item2 as the denominator for example
    def temporal_granularity_consistency_check(self, item1, item2):
        if item2 not in self.individuals: #cannot run this check unless both are instances
            print("Temporal granularity consistency check not run - it is only done when comparing 2 individuals.")
            return

        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = item1.hasBeginning 
            end1 = item1.hasEnd
            beginning2 = item2.hasBeginning
            end2 = item2.hasEnd
        else: 
            return

        #print(beginning1.year, type(beginning1.month), end1, beginning2, end2.day, type(end2.day))

        #checking the beginning vs end of each instance
        #consistency
        if (beginning1.year) and (beginning1.month) and (beginning1.day)  and (end1.year)  and (end1.month)  and (end1.day):
            print("Both the beginning and end of " , item1, "'s reporting period time interval have day, month, and year temporal units. Therefore they are temporal granular consistent.")
        elif (beginning2.year) and (beginning2.month) and (beginning2.day) and (end2.year) and (end2.month) and (end2.day):
            print("Both the beginning and end of " , item2, "'s reporting period time interval have day, month, and year temporal units. Therefore they are temporal granular consistent.")    
        
        #both start and end missing year
        elif type(beginning1.year) == None and (beginning1.month) and (beginning1.day) and type(end1.year) == None and (end1.month) and (end1.day):
            print("Both the beginning and end of " , item1, "'s reporting period time interval have day and month temporal units. Therefore they are temporal granular consistent.")
        elif type(beginning2.year) == None and (beginning1.month) and (beginning1.day) and type(end2.year) == None and (end1.month) and (end1.day):
            print("Both the beginning and end of " , item2, "'s reporting period time interval have day and month temporal units. Therefore they are temporal granular consistent.")
        
        #both start and end missing day
        elif (beginning1.year) and (beginning1.month) and type(beginning1.day) == None and (end1.year) and (end1.month) and type(end1.day) == None:
            print("Both the beginning and end of " , item1, "'s reporting period time interval have month and year temporal units. Therefore they are temporal granular consistent.") 
        elif (beginning2.year) and (beginning2.month) and type(beginning2.day) == None and (end2.year) and (end2.month) and type(end2.day) == None:
            print("Both the beginning and end of " , item2, "'s reporting period time interval have month and year temporal units. Therefore they are temporal granular consistent.") 

        #only start or only end missing year # TODO potentially inconsistent
        elif ((type(beginning1.year) == None and (beginning1.month) and (beginning1.day) and (end1.year) and (end1.month) and (end1.day)) or ((beginning1.year) and (beginning1.month) and (beginning1.day) and type(end1.year) == None and (end1.month) and (end1.day))):
            print("The beginning or end of " , item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            return
        elif ((type(beginning2.year) == None and (beginning2.month) and (beginning2.day) and (end2.year) and (end2.month) and (end2.day)) or ((beginning2.year) and (beginning2.month) and (beginning2.day) and type(end2.year) == None and (end2.month) and (end2.day))):
            print("The beginning or end of " , item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            return
        
        #only start or end missing day
        elif (((beginning1.year) and (beginning1.month) and type(beginning1.day) == None and (end1.year) and (end1.month) and (end1.day)) or ((beginning1.year) and (beginning1.month) and (beginning1.day) and (end1.year) and (end1.month) and type(end1.day) == None)):
            print("The beginning or end of " , item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            return
        elif (((beginning2.year) and (beginning2.month) and type(beginning2.day) == None and (end2.year) and (end2.month) and (end2.day)) or ((beginning2.year) and (beginning2.month) and (beginning2.day) and (end2.year) and (end2.month) and type(end2.day) == None)):
            print("The beginning or end of " , item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            return

        #checking both instances against each other. Only using beginning value since assumption is that beginning and end of each instance are already checked for temporal granularity
        #consistent cases
        # if type(beginning1.year) and type(beginning1.month) and type(beginning1.day) and type(beginning2.year) and type(beginning2.month) and type(beginning2.day):
        #     print("Both " , item1 , " and " , item2, " have day, month, and year temporal units to describe their reporting intervals. Therefore they are temporal granular consistent.")
        #     return
        if (beginning1.year) and (beginning1.month) and (beginning1.day) and (beginning2.year) and (beginning2.month) and (beginning2.day):
            print("Both " , item1 , " and " , item2, " have day, month, and year temporal units to describe their reporting intervals. Therefore they are temporal granular consistent.")
            return
        elif type(beginning1.day) == None and type(beginning2.day) == None:
            print("Both " , item1 , " and " , item2, " do not have day temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
            return
        elif type(beginning1.year) == None and type(beginning2.year) == None:
            print("Both " , item1 , " and " , item2, " do not have year temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
            return
        #inconsistent cases
        elif ((beginning1.year) and type(beginning2.year) == None):
            print(item2 , " does not have a year unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
            return
        elif ((beginning1.month) and type(beginning2.month) == None):
            print(item2 , " does not have a month unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
            return
        elif ((beginning1.day) and type(beginning2.year) == None):
            print(item2 , " does not have a day unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
            return
        elif ((beginning2.year) and type(beginning1.year) == None):
            print(item1 , " does not have a year unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
            return
        elif ((beginning2.month) and type(beginning1.month) == None):
            print(item1 , " does not have a month unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
            return
        elif ((beginning2.day) and type(beginning1.year) == None):
            print(item1 , " does not have a day unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
            return
    
    #inter (instance compared to its definition class)
    def property_consistency_check(self, item1, item2):
        '''
        #Property Inconsistency: An instance mij ∊ Mi is potentially inconsistent with its corresponding definition class nik ∊ Ni if there exist a necessary property ait 
        #defined in nik that satisfies one of the following conditions: ait does not exist in mij, 
        #or the cardinality of ait for mij does not satisfy the cardinality restriction defined in nik, 
        #or mij does not satisfy the value restriction of ait defined in nik
        '''
        if (item1 in self.classes and item2 in item1.ancestors()) or (item2 in item1.is_a):
        #instance_property_consistent = False

            properties_of_parent = []
            restrictions = [x for x in item2.is_a if (isinstance(x, owl2.entity.Restriction))]

            #cardinality of a for m does not satisfy cardinality restriction in n
            #it is not possible to do for loop over prop in proplist of item1 and then do item1.prop. 
            for r in restrictions:
                print(r)
                if r in item1.get_properties():
                    print("property: " , r.property , " value: " , r.value)

                # for prop in onto.drug_1.get_properties():
                #   for value in prop[onto.drug_1]:
                #      print(".%s == %s" % (prop.python_name, value))

            for prop in item2.get_class_properties():
                properties_of_parent.append(prop)
                if (len(prop.range) > 0) and (type(item1) not in prop.range):
                    print(item1 , " is property inconsistent with " , item2 , " because it does not satisfy the value restriction of property " , prop , " defined in " , item2 +".")
                    return
                elif prop not in item1.get_properties():
                    print(item1 , " is property inconsistent with " , item2 , " because  property " , prop , " defined in " , item2 , " does not exist for " , item1 , ".")
                    return
                    #at this point already checked if definition property not in instance
                elif (len(prop.range) == 0):
                    print(item1 , " is potentially property inconsistent with " , item2 , " because the value restriction (range) of property " , prop , " is not provided.")
                    return

        if (item2 in self.classes and item1 in item2.ancestors()) or (item1 in item2.is_a):
        #instance_property_consistent = False
            properties_of_parent = []
            restrictions = [x for x in item2.is_a if (isinstance(x, owl2.entity.Restriction))]

        #cardinality of a for m does not satisfy cardinality restriction in n
        #it is not possible to do for loop over prop in proplist of item1 and then do item1.prop. 
        #it needs the exact name of the prop to get the value. Therefore this isn't possible to do in owlready2, would have to be done manually.
            for r in restrictions:
                if r.property in item1.get_class_properties():
                    print("property: " , r.property , " value: " , r.value)
                else:
                    print(item1 , " is property inconsistent with " , item2 , " because it does not satisfy the value restriction of property " , prop , " defined in " , item2, ".")
            for prop in item1.get_class_properties():
                properties_of_parent.append(prop)
                if (len(prop.range) > 0) and (type(item1) not in prop.range):
                    print(item1 , " is property inconsistent with " , item2 , " because it does not satisfy the range restriction of property " , prop , " defined in " , item2 , ".")
                    return
                elif prop not in item1.get_class_properties():
                    print(item1 , " is property inconsistent with " , item2 , " because  property " , prop , " defined in " , item2 , " does not exist for " , item1 , ".")
                    return
                #at this point already checked if definition property not in instance
                elif (len(prop.range) == 0):
                    print(item1 , " is potentially property inconsistent with " , item2 , " because the value restriction (range) of property " , prop , " is not provided.")
                    return

        else: #TODO redo code to move this else to the top and reduce the if statements in this section. 
            print("Property consistency check not run - it is only done when comparing instance m with its definition class n.")
            return

    #inter, if you want to check a ratio then you have to put item1 as the numerator and item2 as the denominator for example
    def interval_equality_consistency_check(self, item1, item2):
        if item2 not in self.individuals:
            print("Interval equality consistency check not run - it is only done when comparing an instance to another instance.")
            return
        
        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = item1.hasBeginning 
            end1 = item1.hasEnd
            beginning2 = item2.hasBeginning
            end2 = item2.hasEnd
        else: 
            return
        
        if (beginning1.year) and (beginning1.month) and (beginning1.day) and (beginning2.year) and (beginning2.month) and (beginning2.day):
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date(beginning1, beginning2, end1, end2)

            #equals: start(a) = start(b) < end(a) = end(b) (a and b are identical)
            if (intervalBeginning1 == intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 == intervalEnd2):
                print(item1 , "'s time interval is identical to " , item2 , "'s. Therefore they are interval equality consistent.")
                return
            else:
                print(item1 , "'s time interval is not identical to " , item2 , "'s. Therefore they are interval equality inconsistent.")
                return
        else:
        #check each item of list. List is always organized from [year, month, day]
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date_when_none_values(beginning1, beginning2, end1, end2)
            if intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd1[0]  and intervalEnd1[0]  == intervalEnd2[0]:
                print(item1 , "and " , item2 , " have identical time intervals. Therefore they are interval equality consistent.")
                return
            elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd1[1]  and intervalEnd1[1]  == intervalEnd2[1]:
                print(item1 , "and " , item2 , " have identical time intervals. Therefore they are interval equality consistent.")
                return
            else:
                print(item1 , "'s time interval is not identical to " , item2 , "'s. Therefore they are interval equality inconsistent.")
                return
    
    #inter, if you want to check a ratio then you have to put item1 as the numerator and item2 as the denominator for example
    def interval_non_overlap_consistency_check(self, item1, item2):
        if item2 not in self.individuals:
            print("Non overlapping interval consistency check not run - it is only done when comparing an instance to another instance.")
            return

        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = item1.hasBeginning 
            end1 = item1.hasEnd
            beginning2 = item2.hasBeginning
            end2 = item2.hasEnd
        else: 
            return

        if (beginning1.year) and (beginning1.month) and (beginning1.day) and (beginning2.year) and (beginning2.month) and (beginning2.day):
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date(beginning1, beginning2, end1, end2)

            #only need to check before since after is an inverse of before. before: start(a) < end(a) < start(b) < end(b) (a ends before b starts)
            if (intervalBeginning1 < intervalEnd1 and intervalEnd1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2):
                print(item1 , "'s time interval is before " , item2 , "'s. Therefore their intervals do not overlap and they are not consistent.")
                return
            elif (intervalBeginning2 < intervalEnd2 and intervalEnd2 < intervalBeginning1 and intervalBeginning1 < intervalEnd1):
                print(item2 , "'s time interval is before " , item1 , "'s. Therefore their intervals do not overlap and they are not consistent.")
                return
            else:
                print(item1 , " and " , item2 , "'s time intervals are overlapping or equal. Therefore they are non overlapping interval consistent.")
                return
        else:
        #check each item of list. List is always organized from [year, month, day]
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date_when_none_values(beginning1, beginning2, end1, end2)
            if intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] < intervalBeginning2[0]  and intervalBeginning2[0]  < intervalEnd2[0]:
                print(item1 , "'s time interval is before " , item2 , "'s. Therefore their intervals do not overlap and they are not consistent.")
                return
            elif intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] < intervalBeginning2[1]  and intervalBeginning2[1]  < intervalEnd2[1]:
                print(item1 , "'s time interval is before " , item2 , "'s. Therefore their intervals do not overlap and they are not consistent.")
                return
            elif intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0] < intervalBeginning1[0]  and intervalBeginning1[0]  < intervalEnd1[0]:
                print(item2 , "'s time interval is before " , item1 , "'s. Therefore their intervals do not overlap and they are not consistent.")
                return
            elif intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1] < intervalBeginning1[1]  and intervalBeginning1[1]  < intervalEnd1[1]:
                print(item2 , "'s time interval is before " , item1 , "'s. Therefore their intervals do not overlap and they are not consistent.")
                return

            else:
                print(item1 , " and " , item2 , "'s time intervals are overlapping or equal. Therefore they are non overlapping interval consistent.")
                return
    
    #both. 
    #inter, if you want to check a ratio then you have to put item1 as the numerator and item2 as the denominator for example
    #intra, there is a case where you can compare the indicator's location to its population's location, so that would be intra? 
    def place_equality_consistency_check(self, item1, item2):
        '''
        #Place equality inconsistency where a population was drawn from a place different than the place specified by the indicator
        #if item1 or item2 = indicator and the other item is its population definition: should be all same location. 
        #forCitySection, forState, forProvince, for_city, parentCountry, located_in are common location properties. "reside_in" is used for area for IRIS indicators rather than actual geographical locations
        
        #not considering ratios
        '''
        place_equality_consistent = False #used in subplace consistency check

        if item2 not in self.individuals:
            print("Place equality consistency check not run - it is only done when comparing an instance to itself or another instance.")
            return place_equality_consistent
    
        parent = item1.is_instance_of[0] #parent class of item1
        parent2 = item2.is_instance_of[0] #parent class of item2
        location = None
        location2 = None
        
        item1_property_names = [p.name for p in item1.get_properties()]
        if 'located_in' in item1_property_names:
            location = item1.located_in
        elif 'parentCountry' :
            location = item1.parentCountry
        elif 'hasCountry' in item1_property_names:
            location = item1.hasCountry
        elif 'hasProvince' in item1_property_names:
            location = item1.hasProvince
        elif 'hasState' in item1_property_names:
            location = item1.hasState
        elif 'for_city' in item1_property_names: #city checked after Province/State so that most specific information can be compared
            location = item1.for_city
        elif 'hasCity' in item1_property_names:
            location = item1.hasCity
        elif 'hasCitySection' in item1_property_names:
            location = item1.hasCitySection

        item2_property_names = [p.name for p in item2.get_properties()]
        if 'located_in' in item2_property_names:
            location2 = item2.located_in
        elif 'parentCountry' :
            location2 = item2.parentCountry
        elif 'hasCountry' in item2_property_names:
            location2 = item2.hasCountry
        elif 'hasProvince' in item2_property_names:
            location2 = item2.hasProvince
        elif 'hasState' in item2_property_names:
            location2 = item2.hasState
        elif 'for_city' in item2_property_names: #city checked after Province/State so that most specific information can be compared
            location2 = item2.for_city
        elif 'hasCity' in item2_property_names:
            location2 = item2.hasCity
        elif 'hasCitySection' in item2_property_names:
            location2 = item2.hasCitySection
        
        
        if not(location) or not(location2):
            # if not(location) and not(location2):
                # print(f'{item1} and {item2} do not have a location property associated with them - place equality consistency check cannot be run.') # TODO neevi rm - silent return
                # return place_equality_consistent

            # item = item1 if not(location) else item2
            # print(item, " does not have a location property associated with it - place equality consistency check cannot be run.") # TODO neevi rm print statements - silent return
            return place_equality_consistent

    #   #considering case when checking consistency between indicator (item1) that has a location + its population/population definition (item2) has a location
    #     if ("iso21972.Indicator" in str(parent.ancestors())) or ("cids.Indicator" in str(parent.ancestors())): 
    #         population = item1.sumOf
    #         if population:
    #             definition = population[0].definedBy

    #             if item2 == item1.sumOf or item2 == definition: #if item2 is item1's population or if item2 is item1's population's definition             
    #                 #compare within indicator
    #                 if location and location2 and location == location2:
    #                     print(item1, " is place equality consistent with ", item2, " - they both refer to the same location.")
    #                     place_equality_consistent = True
    #                     return place_equality_consistent
    #                 elif location and location2 and location != location2:
    #                     print(item1, " is not place equality consistent with ", item2, " due to them referring to different locations.")
    #                     return place_equality_consistent 

    #     elif ("iso21972.Indicator" in str(parent2.ancestors())) or ("cids.Indicator" in str(parent2.ancestors())): 
    #         population = item2.sumOf
    #         if population:
    #             definition = population[0].definedBy

    #             if item1 == item2.sumOf or item1 == definition: #if item1 is item2's population or if item1 is item2's population's definition             
    #                 #compare within indicator
    #                 if location and location2 and location == location2:
    #                     print(item2, " is place equality consistent with ", item1, " - they both refer to the same location.")
    #                     place_equality_consistent = True
    #                     return place_equality_consistent
    #                 elif location and location2 and location != location2:
    #                     print(item2, " is not place equality consistent with ", item1, " due to them referring to different locations.")
    #                     return place_equality_consistent  

        #else: 
        #has location but does not fulfill above indicator relationship
        if ('hasCitySection' in item1_property_names and 'hasCitySection' in item2_property_names) and location2 == item1.hasCitySection:
            print(item1, " and ", item2, " refer to the same city section. Therefore they are place equality consistent.")
            place_equality_consistent = True
            #not returning here in case the city section name is the same but the country/province/state/city isnt
        elif ('hasCitySection' in item1_property_names and 'hasCitySection' in item2_property_names) and location2 != item1.hasCitySection:
            print(item1, " and ", item2, " do not refer to the same city section. Therefore they are not place equality consistent.")
            return place_equality_consistent
        elif ('hasCity' in item1_property_names or 'for_city' in item1_property_names) and ('hasCity' in item2_property_names or 'for_city' in item2_property_names): 
            item1_city_obj = item1.hasCity if 'hasCity' in item1_property_names else item1.for_city
            item2_city_obj = item2.hasCity if 'hasCity' in item2_property_names else item2.for_city
            if (item1_city_obj == item2_city_obj):
                print(item1, " and ", item2, " refer to the same city. Therefore they are place equality consistent.")
                place_equality_consistent = True
                #not returning here in case the city name is the same but the country/province/state isnt
            else:
                print(item1, " and ", item2, " do not refer to the same city. Therefore they are not place equality consistent.")
                return place_equality_consistent

        if ('hasProvince' in item1_property_names or 'hasState' in item1_property_names) and ('hasProvince' in item2_property_names or 'hasState' in item2_property_names):
            item1_province_obj = item1.hasProvince if 'hasProvince' in item1_property_names else item1.hasState
            item2_province_obj = item2.hasProvince if 'hasProvince' in item2_property_names else item2.hasState
            if (item1_province_obj == item2_province_obj):
                print(item1, " and ", item2, " refer to the same province/state. Therefore they are place equality consistent.")
                place_equality_consistent = True
                #not returning here in case the state/province name is the same but the country isnt
            else:
                print(item1, " and ", item2, " do not refer to the same province/state. Therefore they are not place equality consistent.")
                return place_equality_consistent

        if ('hasCountry' in item1_property_names or 'parentCountry' in item1_property_names) and ('hasCountry' in item2_property_names or 'parentCountry' in item2_property_names):
            item1_country_obj = item1.hasCountry if 'hasCountry' in item1_property_names else item1.parentCountry
            item2_country_obj = item2.hasCountry if 'hasCountry' in item2_property_names else item2.parentCountry

            if (item1_country_obj == item2_country_obj):
                print(item1, " and ", item2, " refer to the same country. Therefore they are place equality consistent.")
                place_equality_consistent = True
                return place_equality_consistent
            else:
                print(item1, " and ", item2, " do not refer to the same country. Therefore they are not place equality consistent.")
                return place_equality_consistent

    #inter
    #intra, there is a case where you can compare the indicator's location to its population's location. If the population is drawn from areas within the place specified by the indicator, subplace inconsistent  
    def subplace_consistency_check(self, place_equality_consistent, item1, item2):
        '''
        Any two instances mij and mik ∊ Mi are potentially subplace inconsistent if instance of placename referred by mik is an area within city referred by mij 
        Subplace inconsistency refers to the situation where the placename referred by an instance mik is an area within the instance of mij. 
        For example, the population measured by an indicator should be related to place instances city’i which include all areas within cityi which is referred by the indicator mij. 
        The measure may not be complete if city’i is only an area within cityi since not all populations in cityi have been considered. 

            city section vs city
            city section vs province
            city section vs country
        '''
        if item2 not in self.individuals and place_equality_consistent == True:
            # print ("Subplace consistency check not run since the two items were already found to be place equality consistent.") # TODO neevi rm silent return
                # print("Subplace consistency check not run - it is only done when comparing an instance to another instance.") # TODO neevi rm silent return
            return

        item1_property_names = [p.name for p in item1.get_properties()]
        item2_property_names = [p.name for p in item2.get_properties()]
        
        item1_city_section = item1.hasCitySection if 'hasCitySection' in item1_property_names else None
        item1_city = None
        item1_province = None
        item1_country = None
        if 'hasCity' in item1_property_names:
            item1_city = item1.hasCity
        elif 'for_city' in item1_property_names:
            item1_city = item1.for_city
        if 'hasProvince' in item1_property_names:
            item1_province = item1.hasProvince
        elif 'hasState' in item1_property_names:
            item1_province = item1.hasState
        if 'hasCountry' in item1_property_names:
            item1_country = item1.hasCountry
        elif 'parentCountry' in item1_property_names:
            item1_country = item1.parentCountry
        
        item2_city_section = item2.hasCitySection if 'hasCitySection' in item2_property_names else None
        item2_city = None
        item2_province = None
        item2_country = None
        if 'hasCity' in item2_property_names:
            item2_city = item2.hasCity
        elif 'for_city' in item2_property_names:
            item2_city = item2.for_city
        if 'hasProvince' in item2_property_names:
            item2_province = item2.hasProvince
        elif 'hasState' in item2_property_names:
            item2_province = item2.hasState
        if 'hasCountry' in item2_property_names:
            item2_country = item2.hasCountry
        elif 'parentCountry' in item2_property_names:
            item2_country = item2.parentCountry
            
        # If Item1 is a place node and has complete information
        if ('hasCitySection' in item1_property_names and ('hasCity' in item1_property_names or 'for_city' in item1_property_names) and ('hasProvince' in item1_property_names or 'hasState' in item1_property_names) and ('hasCountry' in item1_property_names or 'parentCountry' in item1_property_names)):
            # If item2 has at least one place property, item2 is a place node. Proceed with check. But if item2 does not have any place properties, item2 is not a place node. Therefore return. 
            if all([obj is None for obj in [item2_city_section, item2_city, item2_province, item2_country]]):
                return # Silent return
            # check item1 (place node, complete information) against item2 (place node, incomplete information)
            if not item2_city_section and item2_city and item1_city == item2_city:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif not item2_city_section and item2_province and item1_province == item2_province:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif not item2_city_section and item2_country and item1_country == item2_country:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif not item2_city and item2_province and item1_province == item2_province:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif not item2_city and item2_country and item1_country == item2_country:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
        # elif item2 is a place node with complete information
        elif ('hasCitySection' in item1_property_names and ('hasCity' in item1_property_names or 'for_city' in item1_property_names) and ('hasProvince' in item1_property_names or 'hasState' in item1_property_names) and ('hasCountry' in item1_property_names or 'parentCountry' in item2_property_names)):
            # If item1 has at least one place property, item1 is a place node. Proceed with check. But if item1 does not have any place properties, item1 is not a place node. Therefore return. 
            if all([obj is None for obj in [item1_city_section, item1_city, item1_province, item1_country]]):
                return # Silent return
            # check item2 (place node, complete information) against item1 (place node, incomplete information)
            if not item1_city_section and item1_city and item2_city == item1_city:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif not item1_city_section and item1_province and item2_province == item1_province:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif not item1_city_section and item1_country and item2_country == item1_country:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif not item1_city and item1_province and item2_province == item1_province:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif not item1_city and item1_country and item2_country == item1_country:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
        else:
            return


    # intra check: done outside of the recursive loop
    def quantity_measure_consistency_check(self, item):
        '''
        Any two instances mij and mik ∊ Mi are measurement inconsistent if an instance of Quantity mij has a unit of measure uniti that is different from the Measure's unit of measure unit’i. 
        '''
        item1 = item
        item2 = item.valueOf # TODO error. ppt does not exist

        if item2 not in self.individuals:
            print(item2, " is not an instance. Quantity Measurement Consistency Check cannot be run.")
            return
        
        elif "iso21972.Quantity" in str(item1.ancestors()) and "iso21972.Measure" in str(item2.ancestors()): #this check compares an instance of Quantity to a Measure. 
            if item1.unit_of_measure and item2.unit_of_measure:
                if item1.unit_of_measure[0] == item2.unit_of_measure[0]:
                    print(item1, " is measurement consistent with ", item2, " because they have the same unit of measure.")
                    return
                else:
                    print(item1, " is measurement inconsistent with ", item2, " because they do not have the same unit of measure.")
                    return
            else:
                print("Either ", item1, " or ", item2, " is missing a unit of measure. Quantity Measurement Consistency Check cannot be run.")
                return

        elif "iso21972.Quantity" in str(item2.ancestors()) and "iso21972.Measure" in str(item1.ancestors()): #this check compares an instance of Quantity to a Measure. 
            if item1.unit_of_measure and item2.unit_of_measure:
                if item1.unit_of_measure[0] == item2.unit_of_measure[0]:
                    print(item2, " is measurement consistent with ", item1, " because they have the same unit of measure.")
                    return
                else:
                    print(item2, " is measurement inconsistent with ", item1, " because they do not have the same unit of measure.")
                    return
            else:
                print("Either ", item1, " or ", item2, " is missing a unit of measure. Quantity Measurement Consistency Check cannot be run.")
                return
       
        else:
            print("Either ", item1, " is not an instance of Quantity or ", item2, " is not an instance of Measure. Quantity Measurement Consistency Check cannot be run.")
            return
    
    # intra
    #TODO update this check to be based on item instead of item1 and item2 since its an internal check
    def indicator_unit_component_consistency_check(self, item1, item2):
        '''
        Any two instances of om:Quantity mij and mik ∊ Mi where mij is connected to mik via a property ait(e.g., numerator, denominator), 
        mij and mik has a unit of measure uniti and unit’i respectively. 
        The instance mij is inconsistent with mik if definition of uniti and unit’i are not connected by ait. 
        The instance mij (indicator instance) will be inconsistent if one of mik and miv (its components) has a different unit than unit’i.
        
        only for ratios for now, not multiplication
        '''
        if item2 not in self.individuals:
            print(item2, " is not an instance. Indicator Unit Component Consistency Check cannot be run.")
            return
       
        for p in item1.get_properties():
            if p.name == 'hasNumerator' or p.name  == 'numerator':
                item1_numerator_obj = p[item1]
            if p.name == 'hasDenominator' or p.name == 'denominator':
                item1_denominator_obj = p[item1]
        for p in item2.get_properties():
            if p.name == 'hasNumerator' or p.name  == 'numerator':
                item2_numerator_obj = p[item2]
            if p.name == 'hasDenominator' or p.name == 'denominator':
                item2_denominator_obj = p[item2]

        if item2 == item1_numerator_obj or item2 == item1_denominator_obj: #item2 has to be a component of item1 to run this check
            if item2.unit_of_measure[0] == item1.unit_of_measure[0]:
                print(item1, " has the same unit of measure as its component, ", item2, ". They are indicator unit component consistent.")
                return

        elif item1 == item2_numerator_obj or item1 == item2_denominator_obj: #item2 has to be a component of item1 to run this check
            if item2.unit_of_measure[0] == item1.unit_of_measure[0]:
                print(item2, " has the same unit of measure as its component, ", item1, ". They are indicator unit component consistent.")
                return

        else:
            print(item1, "or ", item2, " is not a ratio (missing numerator or denominator property). Indicator Unit Component Consistency Check cannot be run.")
            return
    #this is inter since the instance is compared to its corresponding class
    def singular_unit_consistency_check(self, item1, item2):
        '''
        Singular Unit Inconsistency: when an instance mij has a unit of measure uniti that is a multiple or submultiple of the unit defined in its corresponding definition class nik. 
        It is therefore inconsistent with its corresponding class nik in terms of singular unit. 
        '''
        if item1 in item2.is_instance_of: #if item1 is the definition class, and item2 is the individual of that class
        #is_instance_of returns list
            if item2.unit_of_measure[0] and item1.unit_of_measure[0]:
                measure1 = item1.unit_of_measure[0] 
                measure2 = item2.unit_of_measure[0] 
                if "iso21972.Singular_unit" in str(measure1.is_instance_of): #if definition class had unit of measure of singular unit
                    if "iso21972.multiple_or_submultiple" in str(measure2.is_instance_of): #if instance had unit of measure of multiple unit
                        if measure2.singular_unit and measure2.singular_unit == measure1:
                        #I did it here but if multiple unit, not necessary to check if multiple unit's property of singular_unit leads back to measure1 since even knowing that the class is singular but the instance isn't is enough to prove inconsistency
                            print(item2, " is a multiple or submultiple of the unit defined in its definition class, ", item1, ".Therefore they are singular unit inconsistent.")
                            return
                    elif "iso21972.multiple_or_submultiple" not in str(measure2.is_instance_of) and "iso21972.Singular_unit" in str(measure2.is_instance_of): #if instance had unit of measure of singular unit
                        if measure2 == measure1:
                            print(item2, " is a singular unit of the type of unit defined in its definition class, ", item1, ".Therefore they are singular unit consistent.")
                            return
                    else:
                        print("Either ", item1, " or ", item2, " does not have a singular, multiple, or submultiple unit of measure property. Therefore Singular Unit Consistency Check cannot be run.")
                        return
            else:
                print("Either ", item1, " or ", item2, " does not have a unit of measure property. Therefore Singular Unit Consistency Check cannot be run.")
                return

        elif item2 in item1.is_instance_of: #if item2 is the definition class, and item1 is the individual of that class
            #is_instance_of returns list
            if item2.unit_of_measure[0] and item1.unit_of_measure[0]:
                measure1 = item1.unit_of_measure[0] 
                measure2 = item2.unit_of_measure[0] 
                if "iso21972.Singular_unit" in str(measure2.is_instance_of): #if definition class had unit of measure of singular unit
                    if "iso21972.multiple_or_submultiple" in str(measure1.is_instance_of): #if instance had unit of measure of multiple unit
                        if measure1.singular_unit and measure1.singular_unit == measure2:
                        #I did it here but if multiple unit, not necessary to check if multiple unit's property of singular_unit leads back to measure1 since even knowing that the class is singular but the instance isn't is enough to prove inconsistency
                            print(item1, " is a multiple or submultiple of the unit defined in its definition class, ", item2, ".Therefore they are singular unit inconsistent.")
                            return
                    elif "iso21972.multiple_or_submultiple" not in str(measure1.is_instance_of) and "iso21972.Singular_unit" in str(measure1.is_instance_of): #if instance had unit of measure of singular unit
                        if measure2 == measure1:
                            print(item2, " is a singular unit of the type of unit defined in its definition class, ", item1, ".Therefore they are singular unit consistent.")
                            return
                    else:
                        print("Either ", item1, " or ", item2, " does not have a singular, multiple, or submultiple unit of measure property. Therefore Singular Unit Consistency Check cannot be run.")
                        return
            else:
                print("Either ", item1, " or ", item2, " does not have a unit of measure property. Therefore Singular Unit Consistency Check cannot be run.")
                return
        else:
            print(item1, " or ", item2, "is not the definition class of the other. Singular Unit Consistency Check cannot be run.")

    #this one is comparing the instance to its definition class, but the way it does the proving is by looking at both internally. But I think it's still inter
    # put outside of recusion loop
    def correspondence_consistency_check(self, item1, item2):
        '''
        Correspondence Inconsistency: where there are no correspondence detected between nodes in the indicator’s definition and published indicator data. 
        This means that not all components in the definition are covered by the published indicator data. 
        published indicator data Si is inconsistent in terms of correspondence if for any corresponding nodes mij  Mi and nik  Ni, 
        there exists a class niy that is linked to nik via property ait where there is no node mix linked to mij that corresponds to niy. 
        '''
        # TODO call get prop based on if item1 /2is class or indvidual
        if item1 in self.classes and item2 in self.individuals:
            class_nodes = item1.get_class_properties()
            #remove annotation properties
            class_nodes = [str(s) for s in class_nodes]
            if len(class_nodes) > 0:
                for s in class_nodes:
                #print (type(s))
                #print(s)
                    if s == 'rdf-schema.commment':
                        class_nodes.remove('rdf-schema.commment')
                    if s == 'rdf-schema.label':
                        class_nodes.remove('rdf-schema.label')
                    if s == 'rdf-schema.comment':
                        class_nodes.remove('rdf-schema.comment')
            #print(prop)
            individual_nodes = item2.get_properties()
            individual_nodes = [str(s) for s in individual_nodes]
            #remove annotation properties 
            if len(individual_nodes) > 0:
                for s in individual_nodes:
                #print (type(s))
                #print(s)
                    if s == 'rdf-schema.commment':
                        individual_nodes.remove('rdf-schema.commment')
                    if s == 'rdf-schema.label':
                        individual_nodes.remove('rdf-schema.label')
                    if s == 'rdf-schema.comment':
                        individual_nodes.remove('rdf-schema.comment')
            #print(prop)

            if len(class_nodes) > len(individual_nodes):
            #if set(class_nodes) != set(individual_nodes):
                print("Not all components in the definition are covered by the instance. Therefore they are correspondence inconsistent.")
            
            else:
                print("All components in the definition are covered by the instance. Therefore they are correspondence consistent.")
        # TODO rm
        elif item1 in self.individuals and item2 in self.classes:
            class_nodes = item2.get_class_properties()
            #remove annotation properties
            class_nodes = [str(s) for s in class_nodes]
            if len(class_nodes) > 0:
                for s in class_nodes:
                #print (type(s))
                #print(s)
                    if s == 'rdf-schema.commment':
                        class_nodes.remove('rdf-schema.commment')
                    if s == 'rdf-schema.label':
                        class_nodes.remove('rdf-schema.label')
                    if s == 'rdf-schema.comment':
                        class_nodes.remove('rdf-schema.comment')
            #print(prop)
            individual_nodes = item1.get_properties()
            individual_nodes = [str(s) for s in individual_nodes]
            #remove annotation properties 
            if len(individual_nodes) > 0:
                for s in individual_nodes:
                #print (type(s))
                #print(s)
                    if s == 'rdf-schema.commment':
                        individual_nodes.remove('rdf-schema.commment')
                    if s == 'rdf-schema.label':
                        individual_nodes.remove('rdf-schema.label')
                    if s == 'rdf-schema.comment':
                        individual_nodes.remove('rdf-schema.comment')
            #print(prop)

            # if len(class_nodes) > len(individual_nodes):
            if set(class_nodes) != set(individual_nodes):
                print("Not all components in the definition are covered by the instance. Therefore they are correspondence inconsistent.")
            
            else:
                print("All components in the definition are covered by the instance. Therefore they are correspondence consistent.")

        else:
            print("An indicator definition and indicator data is required for correspondence consistency check, which the inputs ", item1, " and ", item2, " are not. Therefore, correspondence consistency check cannot be run.")    