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
        if count == 0 and check_type == 'individual':
            self.run_intra_checks(node1)
            self.run_intra_checks(node2) #TODO added
        
        # run inter checks
        if check_type == 'individual':
            self.run_individual_inter_checks(node1, node2)
        elif check_type == 'class':
            self.run_class_inter_checks(node1, node2)
        elif check_type == 'mixed':
            self.run_mixed_inter_checks(node1, node2)
        
        #leaving print statements here for future debugging purposes:
        # print("node1: ", node1)
        # print("node2: ", node2)
        
        # Get all properties of node1 and node2
        if node1 in self.classes:
            node1_properties = self.get_object(node1).get_class_properties()
        elif node1 in self.individuals: 
            node1_properties = self.get_object(node1).get_properties()
        
        if node2 in self.classes:
            node2_properties = self.get_object(node2).get_class_properties()
        elif node2 in self.individuals: 
            node2_properties = self.get_object(node2).get_properties()

        if node1_properties and node2_properties and len(node1_properties) > 0 and len(node2_properties) > 0:
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
                node1_obj = p[node1][0]
                node2_obj = p[node2][0]
                
                # Determine if the child is a data value (ie a leaf node)
                node1_obj_is_data_value = isinstance(node1_obj, str) and isinstance(node1_obj, int) 
                node2_obj_is_data_value = isinstance(node2_obj, str) and isinstance(node2_obj, int) 

                # immediately inconsistent cases
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
        self.subplace_consistency_check(item1, item2, place_equality_consistent)
        temporal_granular_consistent = self.temporal_granularity_consistency_check(item1, item2) #needed to run self.subinterval_consistency_check
        self.subinterval_consistency_check(item1, item2, temporal_granular_consistent) 
        self.interval_equality_consistency_check(item1, item2)
        self.interval_non_overlap_consistency_check(item1, item2)

    def run_intra_checks(self, item):
        self.quantity_measure_consistency_check(item)
        # if item is a ratio (individual), run the following checks
        item = self.get_object(item).get_properties()

        if item and len(item) > 0:
            item_property_names = [p.name for p in item]

            if all(p in item_property_names for p in ['hasNumerator', 'hasDenominator']) or all(p in item_property_names for p in ['numerator', 'hasDenominator']) or all(p in item_property_names for p in ['hasNumerator', 'denominator']) or all(p in item_property_names for p in ['numerator', 'denominator']):
                self.indicator_unit_component_consistency_check(self.get_object(item)) #running after the if all ensures it's a ratio
                
                for p in self.get_object(item).get_properties():
                    if p.name == 'hasNumerator' or p.name  == 'numerator':
                        numerator_obj = p[item]
                    if p.name == 'hasDenominator' or p.name == 'denominator':
                        denominator_obj = p[item]
                self.temporal_granularity_consistency_check(numerator_obj, denominator_obj) #no need to return temporal_granular_consistent boolean here because it will be done in the inter check
                place_equality_consistent = self.place_equality_consistency_check(numerator_obj, denominator_obj) #needed to run self.subplace_consistency_check
                self.subplace_consistency_check(numerator_obj, denominator_obj, place_equality_consistent)

    def run_class_inter_checks(self, item1, item2):
        self.class_type_consistency_check(item1, item2)

    def run_mixed_inter_checks(self, item1, item2):
        self.instance_type_consistency_check(item1, item2)
        self.property_consistency_check(item1, item2)
        self.singular_unit_consistency_check(item1, item2)
        self.correspondence_consistency_check(item1, item2)

    def remove_annotation_properties(self, properties):
        return [p for p in properties if str(p) not in ['rdf-schema.commment', 'rdf-schema.comment', 'rdf-schema.label']]
    
    def get_object(self, obj):
        '''
        When accessing the object via <item>.<property>, sometimes OwlReady2 returns a list containing the object, other times it returns the object.

        Handles both cases and just returns the object. 
        '''
        if isinstance(obj, list) and len(obj) > 0:
            return obj[0]
        else:
            return obj

    # ======= consistency checks =======

    #class inter
    def class_type_consistency_check(self, item1, item2): # item: Knowledge Graph (KG) of SPO or Indicator
        '''
        From Wang's Thesis: 
        a class X is type inconsistent with class Y if 
        X is not the same, 
        an equivalent class, 
        nor a subclass of Y, 
        or X is not subsumed by Y.
        '''

        class_type_consistent = False #used in instance type consistency check

        if item1 not in self.classes or item2 not in self.classes:
            #print("Class type consistency check not run - ", item1, " and/or ", item2, " is not a class.")
            return

        prop1 = [p for p in item1.get_class_properties()]
        prop2 = [p for p in item2.get_class_properties()]
        # type(item) <- direct parent of item
        # prop1 <- names of properties, not the actual property values

        #for equality: checking if same type, same name, and same properties (not checking property values to save computation time, this is potential improvement)
        if ((type(item1) == type(item2)) and (item1.name and item2.name) and (item1.name == item2.name) and (set(prop1) == set(prop2))): 
            class_type_consistent = True
            print("Class type consistent because classes ", item1, " and ", item2, " are equal.")
            return class_type_consistent
        
        #checking equivalency, even if indirect
        elif item2 in item1.INDIRECT_equivalent_to or item1 in item2.INDIRECT_equivalent_to:
            class_type_consistent = True
            print("Class type consistent due to equivalency.")
            return class_type_consistent
        
        #checking subclass relationship
        elif item2 in list(item1.subclasses()) or item1 in list(item2.subclasses()):
            class_type_consistent = True
            print("Class type consistent because one is the subclass of the other.")
            return class_type_consistent
        
        #subsumption - from Professor Fox's Notes: Class A is subsumed by Class B if all individuals in A are also individuals in B, but not vice versa.
        if not (set(item1.instances()) == set(item2.instances())): #extra check to ensure they are not the same set of instances for both classes
            for i in item1.instances():
                if i in item2.instances():
                    continue
                elif i not in item2.instances():
                    break #all individuals in A should be individuals in B
                
                class_type_consistent = True
                print("Class type consistent due to subsumption - ", item1, " is subsumed by ", item2, ".")
                return class_type_consistent

            for i in item2.instances():
                if i in item1.instances():
                    continue
                elif i not in item1.instances():
                    break #all individuals in A should be individuals in B
                
                class_type_consistent = True
                print("Class type consistent due to subsumption - ", item2, " is subsumed by ", item1, ".")
                return class_type_consistent
        
        #final verdict
        if class_type_consistent == False:
            print("Class type inconsistent - neither of the two classes is equal, equivalent, or a subclass of the other class.")
            return class_type_consistent
        
    #mixed inter
    def instance_type_consistency_check(self, item1, item2):
        '''
        From Wang's thesis: Instance type inconsistency verifies that if the instances that make up an indicator are an instance of the same class, 
        an equivalent class, a subclass of concepts defined in standard, 
        or have all necessary properties with values that satisfy the restrictions of those properties defined in the standard definition.
        
        Inconsistent if there does not exist a direct rdf:type relation between instance m and class n
        m is not an instance of n, and 
        m is an instance of class c, and c is type inconsistent with n
        '''
        if (item2 in self.classes and item1 in self.individuals):
            #item 2 = n, item1 = m

            if item1 not in item2.instances(): 
                print(item1, " is not an instance of " , item2, " - therefore they are instance type inconsistent.")
                return
            
            else: #item1 is instance of item2
                if type(item1) == item2: #item1 has type item2
                    for c in item1.is_instance_of:
                        #The instance m is type inconsistent with n if the class c is inconsistent with n - class_type_consistency is false.  
                        if self.class_type_consistency_check(c, item2) == False:
                            print(item1, " is an instance of " ,c, ", which is type inconsistent with " ,item2, " - therefore ", item1, " is instance type inconsistent with ", item2, ".")
                            break
                            return
                        else:
                            print(item1, " is instance type consistent with ", item2, " because there is a direct rdf:type relation between them, ", item1, " is an instance of ", item2, ", and all classes that ", item1, " is an instance of are type consistent with ", item2, ".")
                            return
                else:
                    print(item1, " is instance type inconsistent with ", item2, " because there is not a direct rdf:type relation between them.")
                    return

        elif (item1 in self.classes and item2 in self.individuals):
            #item1 = n, item2 = m

            if item2 not in item1.instances(): 
                print(item2, " is not an instance of " , item1, " - therefore they are instance type inconsistent.")
                return
            
            else: #item2 is instance of item1
                if type(item2) == item1: #item2 has type item1
                    for c in item2.is_instance_of:
                        #The instance m is type inconsistent with n if the class c is inconsistent with n - class_type_consistency is false.  
                        if self.class_type_consistency_check(c, item1) == False:
                            print(item2, " is an instance of " ,c, ", which is type inconsistent with " ,item1, " - therefore ", item2, " is instance type inconsistent with ", item1, ".")
                            break
                            return
                        else:
                            print(item2, " is instance type consistent with ", item1, " because there is a direct rdf:type relation between them, ", item2, " is an instance of ", item1, ", and all classes that ", item2, " is an instance of are type consistent with ", item1, ".")
                            return
                else:
                    print(item2, " is instance type inconsistent with ", item1, " because there is not a direct rdf:type relation between them.")
                    return

        else:
            #print("Instance type consistency check not run - one of the items must be an instance and the other a class.")
            return      

    def get_date(self, beginning1, beginning2, end1, end2): 
        '''
        This function gets the interval date values into 1 list in the order of year, month, day. 
        '''
        intervalBeginning1 = datetime.date(int(beginning1.year), int(beginning1.month), int(beginning1.day))
        intervalEnd1 = datetime.date(int(end1.year), int(end1.month), int(end1.day))
        #print(intervalBeginning1, intervalEnd1)

        intervalBeginning2 = datetime.date(int(beginning2.year), int(beginning2.month), int(beginning2.day))
        intervalEnd2 = datetime.date(int(end2.year), int(end2.month), int(end2.day))
        #print(intervalBeginning2, intervalEnd2)
        return intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2

    def get_date_when_none_values(self, beginning1, beginning2, end1, end2): 
        '''
        This function gets the interval date values into 1 list in the order of year, month, day when either the year or the day is missing.
        '''
        #didn't account for missing month value because didn't think there would realistically be a case where year and day are provided but not month
        #missing year value
        if not (beginning1.year) and (beginning1.month) and (beginning1.day) and not (beginning2.year) and (beginning2.month) and (beginning2.day):
            intervalBeginning1 = [int(beginning1.month), int(beginning1.day)]
            intervalEnd1 = [int(end1.month), int(end1.day)]
            #print(intervalBeginning1, intervalEnd1)
            intervalBeginning2 = [int(beginning2.month), int(beginning2.day)]
            intervalEnd2 = [int(end2.month), int(end2.day)]
            #print(intervalBeginning2, intervalEnd2)
        
        #missing day value
        elif (beginning1.year) and (beginning1.month) and not(beginning1.day) and (beginning2.year) and (beginning2.month) and not(beginning2.day):
            intervalBeginning1 = [int(beginning1.year), int(beginning1.month)]
            intervalEnd1 = [int(end1.year), int(end1.month)]
            #print(intervalBeginning1, intervalEnd1)
            intervalBeginning2 = [int(beginning2.year), int(beginning2.month)]
            intervalEnd2 = [int(end2.year), int(end2.month)]
            #print(intervalBeginning2, intervalEnd2)
        return intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2
    
    #individual inter
    def subinterval_consistency_check(self, item1, item2, temporal_granular_consistent): 
        '''
        An instance x is potentially subinterval inconsistent with y if it is related to a time interval i that 
        - is during the interval i??? for y, or 
        - overlaps with i', or 
        - starts interval i???, or 
        - ends interval i???, or 
        - meets interval i??? 
        '''
        if item1 not in self.individuals or item2 not in self.individuals: #cannot run this check unless both are instances
            #print("Subinterval consistency check not run - it is only done when comparing 2 individuals.")
            return
        elif temporal_granular_consistent == False:
            #print("Subinterval consistency check not run - it is only done when comparing 2 temporal granular consistent individuals.")
            return
        
        #if both inputs have beginning and end time interval values
        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = self.get_object(item1.hasBeginning) 
            end1 = self.get_object(item1.hasEnd)
            beginning2 = self.get_object(item2.hasBeginning)
            end2 = self.get_object(item2.hasEnd)
        else: 
            #print("Subinterval consistency check not run - missing time interval properties.")
            return

        #if year, month, and day values exist for both inputs, then call get_date function to convert to interval to datetime library
        if (beginning1.year) and (beginning1.month) and (beginning1.day) and (beginning2.year) and (beginning2.month) and (beginning2.day):
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date(beginning1, beginning2, end1, end2)

        #compare (this is facilitated by the datetime library):

            #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
            if (intervalBeginning2 < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 < intervalEnd2):
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
        
        else: #an interval is missing some date values
        #check each item of interval list. List is always organized from [year, month, day]
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date_when_none_values(beginning1, beginning2, end1, end2)

            #compare all intervals on first element of list that is available. then compare items on second element of list that is available. 
            if not (beginning1.year) and not (beginning2.year):
                print("Both inputs are missing year values. Therefore they are potentially subinterval inconsistent.")
            #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
            elif (intervalBeginning2[0] < intervalBeginning1[0]) and intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] < intervalEnd2[0]:
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
        
            #then compare items on second element of list that is available. 
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
            elif intervalBeginning2[1] < intervalBeginning1[1] and intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] == intervalEnd2[1]:
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

    #indvidual inter, however, the beginning and end of the input's time interval is checked first
    def temporal_granularity_consistency_check(self, item1, item2):
        '''
        Two instances x and y (that are instances of the same indicator) are potentially inconsistent in terms of temporal granularity if their time intervals a and b respectively have different temporal units.
        An instance would be temporal granularity inconsistent if the beginning and end of its interval have different temporal units as well.
        '''

        if item1 not in self.individuals or item2 not in self.individuals: #cannot run this check unless both are instances
            #print("Temporal granularity consistency check not run - it is only done when comparing 2 individuals.")
            return

        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = self.get_object(item1.hasBeginning) 
            end1 = self.get_object(item1.hasEnd)
            beginning2 = self.get_object(item2.hasBeginning)
            end2 = self.get_object(item2.hasEnd)
        else: 
            #print("Subinterval consistency check not run - missing time interval properties.")
            return
       
        temporal_granular_consistent = False
        #TODO remove print statement after testing:
        #print(beginning1.year, type(beginning1.month), end1, beginning2, end2.day, type(end2.day))

        #checking the beginning vs end of each instance for year and day inconsistencies. Assumption here is that an interval won't be missing a month if it has a year and day so missing month case is not accounted for.
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

        #only start or only end missing year 
        elif ((not(beginning1.year) and (beginning1.month) and (beginning1.day) and (end1.year) and (end1.month) and (end1.day)) or ((beginning1.year) and (beginning1.month) and (beginning1.day) and not(end1.year) and (end1.month) and (end1.day))):
            print("The beginning or end of " , item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        elif ((not(beginning2.year) and (beginning2.month) and (beginning2.day) and (end2.year) and (end2.month) and (end2.day)) or ((beginning2.year) and (beginning2.month) and (beginning2.day) and not(end2.year) and (end2.month) and (end2.day))):
            print("The beginning or end of " , item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        
        #only start or end missing day
        elif (((beginning1.year) and (beginning1.month) and type(beginning1.day) == None and (end1.year) and (end1.month) and (end1.day)) or ((beginning1.year) and (beginning1.month) and (beginning1.day) and (end1.year) and (end1.month) and type(end1.day) == None)):
            print("The beginning or end of " , item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        elif (((beginning2.year) and (beginning2.month) and type(beginning2.day) == None and (end2.year) and (end2.month) and (end2.day)) or ((beginning2.year) and (beginning2.month) and (beginning2.day) and (end2.year) and (end2.month) and type(end2.day) == None)):
            print("The beginning or end of " , item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent

        #checking both instances against each other. Only using beginning value since assumption is that beginning and end of each instance are already checked for temporal granularity
        #consistent cases
        if (beginning1.year) and (beginning1.month) and (beginning1.day) and (beginning2.year) and (beginning2.month) and (beginning2.day):
            print("Both " , item1 , " and " , item2, " have day, month, and year temporal units to describe their reporting intervals. Therefore they are temporal granular consistent.")
            temporal_granular_consistent = True
            return temporal_granular_consistent
        elif type(beginning1.day) == None and type(beginning2.day) == None:
            print("Both " , item1 , " and " , item2, " do not have day temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
            temporal_granular_consistent = True
            return temporal_granular_consistent
        elif type(beginning1.year) == None and type(beginning2.year) == None:
            print("Both " , item1 , " and " , item2, " do not have year temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
            temporal_granular_consistent = True
            return temporal_granular_consistent
        
        #inconsistent cases
        elif ((beginning1.year) and type(beginning2.year) == None):
            print(item2 , " does not have a year unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        elif ((beginning1.month) and type(beginning2.month) == None):
            print(item2 , " does not have a month unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        elif ((beginning1.day) and type(beginning2.year) == None):
            print(item2 , " does not have a day unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        elif ((beginning2.year) and type(beginning1.year) == None):
            print(item1 , " does not have a year unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        elif ((beginning2.month) and type(beginning1.month) == None):
            print(item1 , " does not have a month unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
        elif ((beginning2.day) and type(beginning1.year) == None):
            print(item1 , " does not have a day unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
            temporal_granular_consistent = False
            return temporal_granular_consistent
    
    #mixed inter (instance compared to its definition class)
    def property_consistency_check(self, item1, item2):
        '''
        An instance m is inconsistent with its corresponding definition class n if there exist necessary property a
        defined in n that satisfies one of the following conditions: a does not exist in m, 
        or the cardinality of a for m does not satisfy the cardinality restriction defined in n, 
        or m does not satisfy the value restriction of a defined in n
        '''

        #item1 is a class n, item2 is an instance m. item1 is the definition class of item2 (item2 is instance of item1)
        if (item1 not in self.classes or item2 not in item1.instances()):
            #print("Property consistency check not run - it is only done when comparing instance m with its definition class n.")
            return

        elif (item1 in self.classes and item2 in item1.instances()):
            #check if they have the same properties (a that is defined in n also exists in m)
            class_prop = item1.get_class_properties()
            indiv_prop = item2.get_properties()
            
            for p in class_prop:
                if p not in indiv_prop:
                    print(item2 , " is property inconsistent with " , item1 , " because  property " , p , " defined in " , item1 , " does not exist for " , item2 , ".")
                    return
                else:
                    #next check value restriction
                    if (len(p.range) > 0) and (type(item2) not in p.range):
                        print(item2 , " is property inconsistent with " , item1 , " because it does not satisfy the value restriction of property " , p , " defined in " , item1, ".")
                        return
                    elif (len(p.range) == 0):
                        print(item2, " is potentially property inconsistent with " , item1 , " - the value restriction (range) of property " , p , " is not provided.")
                        return
                    else:
                    #cardinality of a for m does not satisfy the cardinality restriction defined in n
                        restrictions = [x for x in item1.is_a if (isinstance(x, owl2.entity.Restriction))]
                        for r in restrictions: #r is of the form cids.forOutcome.only(cids.Outcome)
                            p = r.property #r.property is of the form cids.forOutcome
                            c = r.cardinality
                            cardinalityType = None #only restriction
                            if r.type == 24: #some
                                cardinalityType = "some"
                            elif r.type == 26: #exactly
                                cardinalityType = "exactly"
                            elif r.type == 27: #min
                                cardinalityType = "min"
                            elif r.type == 28: #max
                                cardinalityType = "max"

                            if p in item2.get_properties():
                                count = 0

                                for v in p[item2]: #for value in property p of item2
                                    #print(".%s == %s" % (p.name, v))
                                    if r.value not in v.is_instance_of:
                                        print(item2 , " is property inconsistent with " , item1 , " because it does not satisfy the value restriction of property " , p , " defined in " , item1, ".")
                                        return
                                    for vi in v.is_instance_of: #if the value in the instance item2 is of the same type as the value of r in the class
                                        if "|" in str(r.value) or "OneOf" in str(r.value): #or symbol for multiple options
                                            if str(r.value) in str(vi): #even if substring match since there are multiple options possible
                                                count +=1
                                            elif str(r.value) not in str(vi): #accounts for "only" restriction
                                                print(item2 , " is property inconsistent with " , item1 , " because it does not satisfy the cardinality restriction of property " , p , " defined in " , item1, ".")
                                                return
                                        else:
                                            if r.value == vi: 
                                                count +=1
                                            elif r.value != vi: #accounts for "only" restriction
                                                print(item2 , " is property inconsistent with " , item1 , " because it does not satisfy the cardinality restriction of property " , p , " defined in " , item1, ".")
                                                return
                                        
                                    #evaluate:
                                    if cardinalityType == "exactly" and count == c:
                                        continue
                                    elif cardinalityType == "min" and count >= c:
                                        continue
                                    elif cardinalityType == "max" and count <= c:
                                        continue
                                    elif cardinalityType == "some" and count >= 1:
                                        continue
                                    else:
                                        print(item2 , " is property inconsistent with " , item1 , " because it does not satisfy the cardinality restriction of property " , p , " defined in " , item1, ".")
                                        return
                                                 
                        #if not returned yet
                        print(item2 , " is property consistent with " , item1 , " because it satisfies the cardinality restriction of the properties defined in " , item1, ".")
                        return
                                
        elif (item2 in self.classes and item1 in item2.instances()):
            #check if they have the same properties (a that is defined in n also exists in m)
            class_prop = item2.get_class_properties()
            indiv_prop = item1.get_properties()
            
            for p in class_prop:
                if p not in indiv_prop:
                    print(item1 , " is property inconsistent with " , item2 , " because  property " , p , " defined in " , item2 , " does not exist for " , item1 , ".")
                    return
                else:
                    #next check value restriction
                    if (len(p.range) > 0) and (type(item2) not in p.range):
                        print(item1 , " is property inconsistent with " , item2 , " because it does not satisfy the value restriction of property " , p , " defined in " , item2, ".")
                        return
                    elif (len(p.range) == 0):
                        print(item1, " is potentially property inconsistent with " , item2 , " - the value restriction (range) of property " , p , " is not provided.")
                        return
                    else:
                    #cardinality of a for m does not satisfy the cardinality restriction defined in n
                        restrictions = [x for x in item2.is_a if (isinstance(x, owl2.entity.Restriction))]
                        for r in restrictions: #r is of the form cids.forOutcome.only(cids.Outcome)
                            p = r.property #r.property is of the form cids.forOutcome
                            c = r.cardinality
                            cardinalityType = None #only restriction
                            if r.type == 24: #some
                                cardinalityType = "some"
                            elif r.type == 26: #some
                                cardinalityType = "exactly"
                            elif r.type == 27: #min
                                cardinalityType = "min"
                            elif r.type == 28: #max
                                cardinalityType = "max"

                            if p in item1.get_properties():
                                count = 0

                                for v in p[item1]: #for value in property p of item1
                                    #print(".%s == %s" % (p.name, v))
                                    if r.value not in v.is_instance_of:
                                        print(item1, " is property inconsistent with " , item2, " because it does not satisfy the value restriction of property " , p , " defined in " , item2, ".")
                                        return

                                    for vi in v.is_instance_of: #if the value in the instance item1 is of the same type as the value of r in the class
                                        if "|" in str(r.value) or "OneOf" in str(r.value): #or symbol for multiple options
                                            if str(r.value) in str(vi): #even if substring match since there are multiple options possible
                                                count +=1
                                            elif str(r.value) not in str(vi): #accounts for "only" restriction
                                                print(item1 , " is property inconsistent with " , item2 , " because it does not satisfy the cardinality restriction of property " , p , " defined in " , item2, ".")
                                                return
                                        else:
                                            if r.value == vi: 
                                                count +=1
                                            elif r.value != vi: #accounts for "only" restriction
                                                print(item1 , " is property inconsistent with " , item2, " because it does not satisfy the cardinality restriction of property " , p , " defined in " , item2, ".")
                                                return
                                        
                                    #evaluate:
                                    if cardinalityType == "exactly" and count == c:
                                        continue
                                    elif cardinalityType == "min" and count >= c:
                                        continue
                                    elif cardinalityType == "max" and count <= c:
                                        continue
                                    elif cardinalityType == "some" and count >= 1:
                                        continue
                                    else:
                                        print(item1 , " is property inconsistent with " , item2, " because it does not satisfy the cardinality restriction of property " , p , " defined in " , item2, ".")
                                        return
                                        
                        #if not returned yet
                        print(item1, " is property consistent with " , item2, " because it satisfies the cardinality restriction of the properties defined in " , item2, ".")
                        return

    #individual inter
    def interval_equality_consistency_check(self, item1, item2):
        '''
        For two instances of Quantity or Measure for the same indicator, for the instance x to be temporally consistent with instance y, 
        the time intervals for x and y should be equal.
        '''
        if item1 not in self.individuals or item2 not in self.individuals:
            #print("Interval equality consistency check not run - it is only done when comparing an instance to another instance.")
            return

        elif (("iso21972.Quantity" not in str(item1.is_a) or "iso21972.Measure" not in str(item1.is_a)) and ("iso21972.Quantity" not in str(item2.is_a) or "iso21972.Measure" not in str(item2.is_a))):
            #print("Interval equality consistency check not run - it is only done when comparing instances of Quantity or Measure.")
            return
        
        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = self.get_object(item1.hasBeginning) 
            end1 = self.get_object(item1.hasEnd)
            beginning2 = self.get_object(item2.hasBeginning)
            end2 = self.get_object(item2.hasEnd)
        else: 
            #print("Interval equality consistency check not run - either or both inputs are missing one or more time interval properties.")
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
                print(item1 , "'s time interval is identical to " , item2 , "'s. Therefore they are interval equality consistent.")
                return
            elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd1[1]  and intervalEnd1[1]  == intervalEnd2[1]:
                print(item1 , "and " , item2 , " have identical time intervals. Therefore they are interval equality consistent.")
                return
            else:
                print(item1 , "'s time interval is not identical to " , item2 , "'s. Therefore they are interval equality inconsistent.")
                return
    
    #inter, if you want to check a ratio then you can put item1 as the numerator and item2 as the denominator for example
    def interval_non_overlap_consistency_check(self, item1, item2):
        '''
        For two instances of Quantity or Measure for the same indicator, for the instance x to be temporally consistent with instance y, 
        the time intervals for x and y should be equal. 
        Instance x and y are inconsistent if their data do not overlap for any time point within their time intervals. 
        Thus, instance x and y are interval non overlap inconsistent if instance x's time interval is before or after instance y's. 
        '''
        if item1 not in self.individuals or item2 not in self.individuals:
            #print("Non overlapping interval consistency check not run - it is only done when comparing an instance to another instance.")
            return
        
        elif (("iso21972.Quantity" not in str(item1.is_a) or "iso21972.Measure" not in str(item1.is_a)) and ("iso21972.Quantity" not in str(item2.is_a) or "iso21972.Measure" not in str(item2.is_a))):
            #print("Non overlapping interval consistency check not run - it is only done when comparing instances of Quantity or Measure.")
            return
        
        if all(p in [p.name for p in item1.get_properties()] for p in ['hasBeginning', 'hasEnd']) and all(p in [p.name for p in item2.get_properties()] for p in ['hasBeginning', 'hasEnd']):
            beginning1 = self.get_object(item1.hasBeginning) 
            end1 = self.get_object(item1.hasEnd)
            beginning2 = self.get_object(item2.hasBeginning)
            end2 = self.get_object(item2.hasEnd)
        
        else: 
            #print("Non overlapping interval consistency check not run - either or both inputs are missing one or more time interval properties.")
            return

        #all time information (year, month, and day)
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
    
    #inter
    #intra, there is a case where you can compare the indicator's location to its population's location.
    def place_equality_consistency_check(self, item1, item2):
        '''
        For two instances of the same indicator, for the instance x to be place equality consistent with instance y, 
        the locations of x and y should be equal. Within the same indicator as well, everything should be referring to the same place. 
        forCitySection, forState, forProvince, for_city, parentCountry, located_in are common location properties. "reside_in" is used for area for IRIS indicators rather than actual geographical locations
        '''
        place_equality_consistent = False #used in subplace consistency check

        if item1 not in self.individuals or item2 not in self.individuals:
            #print("Place equality consistency check not run - it is only done when comparing an instance to itself or another instance.")
            return place_equality_consistent

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
                # print(f'{item1} and {item2} do not have a location property associated with them - place equality consistency check cannot be run.') 
                # return place_equality_consistent

            # item = item1 if not(location) else item2
            # print(item, " does not have a location property associated with it - place equality consistency check cannot be run.") 
            return place_equality_consistent

        #has location
        if ('hasCitySection' in item1_property_names and 'hasCitySection' in item2_property_names) and location2 == location:
            print(item1, " and ", item2, " refer to the same city section. Therefore they are place equality consistent.")
            place_equality_consistent = True
            #not returning here in case the city section name is the same but the country/province/state/city isnt
        elif ('hasCitySection' in item1_property_names and 'hasCitySection' in item2_property_names) and location2 != location:
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
    def subplace_consistency_check(self, item1, item2, place_equality_consistent):
        '''
        For two instances of the same indicator, instance x is subplace inconsistent with instance y if the location of x is within the location of y. 
        forCitySection, forState, forProvince, for_city, parentCountry, located_in are common location properties. "reside_in" is used for area for IRIS indicators rather than actual geographical locations. 
        '''
        if item1 not in self.individuals or item2 not in self.individuals:
            # print("Subplace consistency check not run - it is only done when comparing an instance to another instance.")
            return
        elif place_equality_consistent == True:
            # print ("Subplace consistency check not run since the two items were already found to be place equality consistent.")   
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

        #item1
        if not item1_city_section and not item1_city and not item1_province and not item1_country:
            #no location information
            print("Subplace consistency check not run - location information not available for ", item1, ".") 
            return
        elif item1_city_section and item1_city and item2_city and not item2_city_section and item1_city == item2_city:
            #item1 is a city section, item2 is not a city section, and item1's city is item2's city
            print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
            return
        elif item1_city_section and item1_province and item2_province and not item2_city_section and item1_province == item2_province:
            print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
            return
        elif item1_city_section and not item2_city_section and item1_country and item2_country and item1_country == item2_country:
            print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
            return

        #   city vs province
        elif item1_city and not item2_city and item1_province and item2_province and item1_province == item2_province:
            print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
            return
        
        #   city vs country
        elif item1_city and not item2_city and item1_country and item2_country and item1_country == item2_country:
            print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
            return
        else: #some missing location information
            print("Some location information is not available. Therefore " ,item1, " and ", item2, " are potentially inconsistent.")

        #item2
        if not item2_city_section and not item2_city and not item2_province and not item2_country:
            #no location information
            print("Subplace consistency check not run - location information not available for ", item2, ".") 
            return
        elif item2_city_section and item2_city and item1_city and not item1_city_section and item1_city == item2_city:
            #item1 is a city section, item2 is not a city section, and item1's city is item2's city
            print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
            return
        elif item2_city_section and item2_province and item1_province and not item1_city_section and item1_province == item2_province:
            print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
            return
        elif item2_city_section and not item1_city_section and item2_country and item1_country and item1_country == item2_country:
            print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
            return

        #   city vs province
        elif item2_city and not item1_city and item2_province and item1_province and item1_province == item2_province:
            print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
            return
        
        #   city vs country
        elif item2_city and not item1_city and item1_country and item2_country and item1_country == item2_country:
            print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
            return
        
        else: #some missing location information
            print("Some location information is not available. Therefore " , item2, " and ", item1, " are potentially inconsistent.")
            return

    # done outside of the recursive loop
    def quantity_measure_consistency_check(self, item):
        '''
        Any two instances x (instance of Quantity) and y (instance of Measure) of the same indicator are quantity measurement inconsistent if x has a unit of measure that is different from y's unit of measure. 
        '''
        if item not in self.individuals:
            #print(item, " is not an instance. Quantity Measurement Consistency Check cannot be run.")
            return
       
        #quantity = item, measure = item.value
        if item.value:
            item2 = self.get_object(item.value) #item2 is always Measure of item, which is a Quantity
            parentItem = self.get_object(item.is_instance_of)
            parentItem2 = self.get_object(item2.is_instance_of)
        
            if "iso21972.Quantity" in str(parentItem.ancestors()) and "iso21972.Measure" in str(parentItem2.ancestors()): #this check compares an instance of Quantity to a Measure. 
                if item.unit_of_measure and item2.unit_of_measure:
                    if self.get_object(item.unit_of_measure) == self.get_object(item2.unit_of_measure):
                        print(item, " is measurement consistent with ", item2, " because they have the same unit of measure.")
                        return
                    else:
                        print(item, " is measurement inconsistent with ", item2, " because they do not have the same unit of measure.")
                        return
                else:
                    #print("Either ", item, " or ", item2, " is missing a unit of measure. Quantity Measurement Consistency Check cannot be run.")
                    return
            else:
                #print("Either ", item, " is not an instance of Quantity or ", item2, " is not an instance of Measure. Quantity Measurement Consistency Check cannot be run.")
                return
    
    # done outside of the recursive loop
    def indicator_unit_component_consistency_check(self, item):
        '''
        Given two instances of Quantity x and y of the same indicator, where x is connected to y via property a (like numerator or denominator), 
        x and y has a unit of measure a and b respectively. x and y are inconsistent if a and b are not connected by property a. 
        An indicator instance x is inconsistent if its components y and z have a different unit than it. 
        '''
        if item not in self.individuals:
            #print(item, " is not an instance. Indicator Unit Component Consistency Check cannot be run.")
            return
       
        for p in item.get_properties():
            if p.name == 'hasNumerator' or p.name  == 'numerator':
                item1_numerator_obj = p[item]
                item1_numerator_obj = self.get_object(item1_numerator_obj)
            if p.name == 'hasDenominator' or p.name == 'denominator':
                item1_denominator_obj = p[item]
                item1_denominator_obj = self.get_object(item1_denominator_obj)
            if p.name == 'unit_of_measure':
                unit_of_measure = p[item]
                unit_of_measure = self.get_object(unit_of_measure)
        
        if  item1_numerator_obj and unit_of_measure: #numerator has to be a component of item to run this check
            if self.get_object(item1_numerator_obj.unit_of_measure) == self.get_object(unit_of_measure):
                print(item, " has the same unit of measure as its component, ", item1_numerator_obj, ". They are indicator unit component consistent.")
                return
            elif self.get_object(item1_numerator_obj.unit_of_measure) ==  self.get_object(unit_of_measure.numerator):
                print(item, "'s unit of measure is connected to its component, ", item1_numerator_obj, "'s unit of measure by the numerator property. They are indicator unit component consistent.")
                return
            
        elif item1_denominator_obj and unit_of_measure: #denominator has to be a component of item to run this check
            if self.get_object(item1_denominator_obj.unit_of_measure) == self.get_object(unit_of_measure):
                print(item, " has the same unit of measure as its component, ", item1_denominator_obj, ". They are indicator unit component consistent.")
                return
            elif self.get_object(item1_denominator_obj.unit_of_measure) ==  self.get_object(unit_of_measure.numerator):
                print(item, "'s unit of measure is connected to its component, ", item1_denominator_obj, "'s unit of measure by the denominator property. They are indicator unit component consistent.")
                return 
        else:
            #print(item1, "or ", item2, " is not a ratio (missing numerator or denominator property). Indicator Unit Component Consistency Check cannot be run.")
            return
    
    #this is inter since the instance is compared to its class
    def singular_unit_consistency_check(self, item1, item2):
        '''
        Instance m has a unit of measure a that is multiple or submultiple of the unit defined in its definition class n. 
        Instance m is then singular unit inconsistent with its definition class n. 
        '''
        if item1 in self.classes and item1 in item2.is_instance_of: #if item1 is the definition class, and item2 is the individual of that class
        #is_instance_of returns list
            if item2.unit_of_measure and item1.unit_of_measure: #if both items have unit of measure values
                measure1 = self.get_object(item1.unit_of_measure)
                measure2 = self.get_object(item2.unit_of_measure)

                if "iso21972.Singular_unit" in str(measure1.ancestors()): #if definition class has unit of measure of singular unit
                    if "iso21972.Unit_multiple_or_submultiple" in str(measure2.is_instance_of): #if instance had unit of measure of multiple unit
                        if measure2.singular_unit and type(self.get_object(measure2.singular_unit)) == measure1:
                            #Did it here but if multiple unit, not necessary to check if multiple unit's property of singular_unit leads back to measure1 since even knowing that the class is singular but the instance isn't shows inconsistency
                            print(item2, " is a multiple or submultiple of the unit defined in its definition class, ", item1, ". Therefore they are singular unit inconsistent.")
                            return
                    
                    elif "iso21972.Unit_multiple_or_submultiple" not in str(measure2.is_instance_of):
                        # and "iso21972.Singular_unit" in str(measure2.is_instance_of): 
                        #if instance had unit of measure of singular unit
                        if measure1 == self.get_object(measure2.is_instance_of) or measure1 == measure2:
                            print(item2, " is a singular unit of the type of unit defined in its definition class, ", item1, ". Therefore they are singular unit consistent.")
                            return
                    else:
                        #print("Either ", item1, " or ", item2, " does not have a singular, multiple, or submultiple unit of measure property. Therefore Singular Unit Consistency Check cannot be run.")
                        return
            else:
                #print("Either ", item1, " or ", item2, " does not have a unit of measure property. Therefore Singular Unit Consistency Check cannot be run.")
                return

        elif item2 in self.classes and item2 in item1.is_instance_of: #if item2 is the definition class, and item1 is the individual of that class
            #is_instance_of returns list
            if item1.unit_of_measure and item2.unit_of_measure:
                measure1 = self.get_object(item1.unit_of_measure)
                measure2 = self.get_object(item2.unit_of_measure)
                
                if "iso21972.Singular_unit" in str(measure2.ancestors()): #if definition class had unit of measure of singular unit
                    if "iso21972.Unit_multiple_or_submultiple" in str(measure1.is_instance_of): #if instance had unit of measure of multiple unit
                        if measure1.singular_unit and type(self.get_object(measure1.singular_unit)) == measure2:
                            print(item1, " is a multiple or submultiple of the unit defined in its definition class, ", item2, ". Therefore they are singular unit inconsistent.")
                            return
                    
                    elif "iso21972.Unit_multiple_or_submultiple" not in str(measure1.is_instance_of):
                         #and "iso21972.Singular_unit" in str(measure1.is_a): 
                         #if instance had unit of measure of singular unit
                            if measure2 == measure1.is_instance_of[0] or measure2 == measure1:
                                print(item1, " is a singular unit of the type of unit defined in its definition class, ", item2, ". Therefore they are singular unit consistent.")
                                return
                else:
                    # print("Either ", item1, " or ", item2, " does not have a singular, multiple, or submultiple unit of measure property. Therefore Singular Unit Consistency Check cannot be run.")
                    return
            
        else:
            # print(item1, " or ", item2, "is not the definition class of the other. Singular Unit Consistency Check cannot be run.")
            return

    #this one is comparing the instance to its definition class
    def correspondence_consistency_check(self, item1, item2):
        ''' 
        Correspondence Inconsistency is when there is no correspondence detected between nodes in the indicator???s definition and the instance. 
        This means that not all components in the definition are covered by the instance. 
        '''
        item1  = self.get_object(item1)
        item2 = self.get_object(item2)

        if item1 in self.classes and item2 in self.individuals:
            class_properties = item1.get_class_properties()
            self.remove_annotation_properties(class_properties) #remove annotation properties

            individual_properties = item2.get_properties()
            self.remove_annotation_properties(individual_properties)

            if set(class_properties) != set(individual_properties):
                print("Not all components in the definition are covered by the instance. Therefore they are correspondence inconsistent.")
                return
            
            elif set(class_properties) == set(individual_properties):
                print("All components in the definition are covered by the instance. Therefore they are correspondence consistent.")
                return
        
        elif item1 in self.individuals and item2 in self.classes:
            class_properties = item2.get_class_properties()
            individual_properties = item1.get_properties()
            class_properties = self.remove_annotation_properties(class_properties) #remove annotation properties
            individual_properties = self.remove_annotation_properties(individual_properties)

            if set(class_properties) != set(individual_properties):
                print("Not all components in the definition are covered by the instance. Therefore they are correspondence inconsistent.")
                return
            
            elif set(class_properties) == set(individual_properties):
                print("All components in the definition are covered by the instance. Therefore they are correspondence consistent.")
                return

        else:
            #print("An indicator definition and indicator data is required for correspondence consistency check, which the inputs ", item1, " and ", item2, " are not. Therefore, correspondence consistency check cannot be run.") 
            return   