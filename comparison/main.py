import owlready2 as owl2
import datetime

class Comparison:
    def __init__(self, classes, individuals):
        self.classes = classes
        self.individuals = individuals
    
    # MAIN
    def compare_class_or_individual(self, item1, item2):
        
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
    
        beginning1 = item1.hasBeginning
        end1 = item1.hasEnd
        beginning2 = item2.hasBeginning
        end2 = item2.hasEnd

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

        beginning1 = item1.hasBeginning
        end1 = item1.hasEnd
        beginning2 = item2.hasBeginning
        end2 = item2.hasEnd

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
        
        beginning1 = item1.hasBeginning
        end1 = item1.hasEnd
        beginning2 = item2.hasBeginning
        end2 = item2.hasEnd
        
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

        beginning1 = item1.hasBeginning
        end1 = item1.hasEnd
        beginning2 = item2.hasBeginning
        end2 = item2.hasEnd

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
        
        if item1.located_in:
            location = item1.located_in
        elif item1.parentCountry:
            location = item1.parentCountry
        elif item1.hasCountry:
            location = item1.hasCountry
        elif item1.hasProvince:
            location = item1.hasProvince
        elif item1.hasState:
            location = item1.hasState
        elif item1.for_city: #city checked after Province/State so that most specific information can be compared
            location = item1.for_city
        elif item1.hasCity:
            location = item1.hasCity
        elif item1.hasCitySection:
            location = item1.hasCitySection

        if item2.located_in:
            location2 = item2.located_in
        elif item2.parentCountry:
            location2 = item2.parentCountry
        elif item2.hasCountry:
            location2 = item2.hasCountry
        elif item2.hasProvince:
            location2 = item2.hasProvince
        elif item2.hasState:
            location2 = item2.hasState
        elif item2.for_city: #city checked after Province/State so that most specific information can be compared
            location2 = item2.for_city
        elif item2.hasCity:
            location2 = item2.hasCity
        elif item2.hasCitySection:
            location2 = item2.hasCitySection
        
        if not(location) or not(location2):
            if not(location) and not(location2):
                print(f'{item1} and {item2} do not have a location property associated with them - place equality consistency check cannot be run.')
                return place_equality_consistent

            item = item1 if not(location) else item2
            print(item, " does not have a location property associated with it - place equality consistency check cannot be run.")
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
        if (item1.hasCitySection and item2.hasCitySection) and location2 == item1.hasCitySection:
            print(item1, " and ", item2, " refer to the same city section. Therefore they are place equality consistent.")
            place_equality_consistent = True
            #not returning here in case the city section name is the same but the country/province/state/city isnt
        elif (item1.hasCitySection and item2.hasCitySection) and location2 != item1.hasCitySection:
            print(item1, " and ", item2, " do not refer to the same city section. Therefore they are not place equality consistent.")
            return place_equality_consistent
        elif (item1.hasCity or item1.for_city) and (item2.hasCity or item2.for_city): 
            if (item2.hasCity or item2.for_city) and ((item1.hasCity == item2.hasCity) or (item1.for_city == item2.for_city) or (item1.hasCity == item2.for_city) or (item1.for_city == item2.hasCity)):
                print(item1, " and ", item2, " refer to the same city. Therefore they are place equality consistent.")
                place_equality_consistent = True
                #not returning here in case the city name is the same but the country/province/state isnt
            else:
                print(item1, " and ", item2, " do not refer to the same city. Therefore they are not place equality consistent.")
                return place_equality_consistent
        if (item1.hasProvince or item1.hasState) and (item2.hasProvince or item2.hasState):
            if  (item1.hasProvince == item2.hasProvince or item1.hasState == item2.hasState or item1.hasProvince == item2.hasState or item1.hasState == item2.hasProvince):
                print(item1, " and ", item2, " refer to the same province/state. Therefore they are place equality consistent.")
                place_equality_consistent = True
                #not returning here in case the state/province name is the same but the country isnt
            else:
                print(item1, " and ", item2, " do not refer to the same province/state. Therefore they are not place equality consistent.")
                return place_equality_consistent
        if (item1.hasCountry or item1.parentCountry) and (item2.hasCountry or item2.parentCountry):
            if item1.hasCountry == item2.hasCountry or item1.parentCountry == item2.parentCountry or item1.hasCountry == item2.parentCountry or item1.parentCountry == item2.hasCountry:
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
    
        if item2 in self.individuals and place_equality_consistent == False:
            #item1
            if not item1.hasCitySection and (not item1.hasCity or not item1.for_city) and (not item1.hasProvince or not item1.hasState) and (not item1.hasCountry or not item1.parentCountry):
                #no location information
                print("Subplace consistency check not run - location information not available for ", item1, ".") 
                return
            elif item1.hasCitySection and item1.hasCity and item2.hasCity and not item2.hasCitySection and item1.hasCity == item2.hasCity:
                #item1 is a city section, item2 is not a city section, and item1's city is item2's city
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and item1.for_city and item2.for_city and not item2.hasCitySection and item1.for_city == item2.for_city:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and item1.hasCity and item2.for_city and not item2.hasCitySection and item1.hasCity == item2.for_city:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and item1.for_city and item2.hasCity and not item2.hasCitySection and item1.for_city == item2.hasCity:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and item1.hasProvince and item2.hasProvince and not item2.hasCitySection and item1.hasProvince == item2.hasProvince:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and not item2.hasCitySection and item1.hasState and item2.hasState and item1.hasState == item2.hasState:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and not item2.hasCitySection and item1.hasState and item2.hasProvince and item1.hasState == item2.hasProvince:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and not item2.hasCitySection and item1.hasProvince and item2.hasState and item1.hasProvince == item2.hasState:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and not item2.hasCitySection and item1.hasCountry and item2.hasCountry and item1.hasCountry == item2.hasCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and not item2.hasCitySection  and item1.parentCountry and item2.parentCountry and item1.parentCountry == item2.parentCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and not item2.hasCitySection and item1.hasCountry and item2.parentCountry and item1.hasCountry == item2.parentCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif item1.hasCitySection and not item2.hasCitySection and item1.parentCountry and item2.hasCountry and item1.parentCountry == item2.hasCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return

            #   city vs province
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.hasProvince and item2.hasProvince and item1.hasProvince == item2.hasProvince:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.hasState and item2.hasState and item1.hasState == item2.hasState:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.hasState and item2.hasProvince and item1.hasState == item2.hasProvince:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.hasProvince and item2.hasState and item1.hasProvince == item2.hasState:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            
            #   city vs country
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.hasCountry and item2.hasCountry and item1.hasCountry == item2.hasCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.parentCountry and item2.parentCountry and item1.parentCountry == item2.parentCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.hasCountry and item2.parentCountry and item1.hasCountry == item2.parentCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif (item1.hasCity or item1.for_city) and (not item2.hasCity or not item2.for_city) and item1.parentCountry and item2.hasCountry and item1.parentCountry == item2.hasCountry:
                print (item1, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            else: #some missing location information
                print("some location information is not available. Therefore " ,item1, " and ", item2, " are potentially inconsistent.")

            #item2
            if not item2.hasCitySection and (not item2.hasCity or not item2.for_city) and (not item2.hasProvince or not item2.hasState) and (not item2.hasCountry or not item2.parentCountry):
                #no location information
                print("Subplace consistency check not run - location information not available for ", item2, ".") 
                return
            elif item2.hasCitySection and item2.hasCity and item1.hasCity and not item1.hasCitySection and item1.hasCity == item2.hasCity:
                #item1 is a city section, item2 is not a city section, and item1's city is item2's city
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and item2.for_city and item1.for_city and not item1.hasCitySection and item1.for_city == item2.for_city:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and item2.hasCity and item1.for_city and not item1.hasCitySection and item2.hasCity == item1.for_city:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and item2.for_city and item1.hasCity and not item1.hasCitySection and item2.for_city == item1.hasCity:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and item2.hasProvince and item1.hasProvince and not item1.hasCitySection and item1.hasProvince == item2.hasProvince:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and not item1.hasCitySection and item2.hasState and item1.hasState and item1.hasState == item2.hasState:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and not item1.hasCitySection and item2.hasState and item1.hasProvince and item2.hasState == item1.hasProvince:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and not item1.hasCitySection and item2.hasProvince and item1.hasState and item2.hasProvince == item1.hasState:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and not item1.hasCitySection and item2.hasCountry and item1.hasCountry and item1.hasCountry == item2.hasCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and not item1.hasCitySection  and item2.parentCountry and item1.parentCountry and item1.parentCountry == item2.parentCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and not item1.hasCitySection and item2.hasCountry and item1.parentCountry and item2.hasCountry == item1.parentCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif item2.hasCitySection and not item1.hasCitySection and item2.parentCountry and item1.hasCountry and item2.parentCountry == item1.hasCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return

            #   city vs province
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item2.hasProvince and item1.hasProvince and item1.hasProvince == item2.hasProvince:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item2.hasState and item1.hasState and item1.hasState == item2.hasState:
                print (item2, " is a subplace of ", item2, " therefore they are not subplace consistent.")
                return
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item2.hasState and item1.hasProvince and item2.hasState == item1.hasProvince:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item2.hasProvince and item1.hasState and item2.hasProvince == item1.hasState:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            
            #   city vs country
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item1.hasCountry and item2.hasCountry and item1.hasCountry == item2.hasCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item1.parentCountry and item2.parentCountry and item1.parentCountry == item2.parentCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item2.hasCountry and item1.parentCountry and item2.hasCountry == item1.parentCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            elif (item2.hasCity or item2.for_city) and (not item1.hasCity or not item1.for_city) and item2.parentCountry and item1.hasCountry and item2.parentCountry == item1.hasCountry:
                print (item2, " is a subplace of ", item1, " therefore they are not subplace consistent.")
                return
            else: #some missing location information
                print("some location information is not available. Therefore " ,item2, " and ", item1, " are potentially inconsistent.")

        else:
            if place_equality_consistent == True:
                print ("Subplace consistency check not run since the two items were already found to be place equality consistent.") 
            else:
                print("Subplace consistency check not run - it is only done when comparing an instance to another instance.") 
            return

    # intra check: done outside of the recursive loop
    def quantity_measure_consistency_check(self, item):
        '''
        Any two instances mij and mik ∊ Mi are measurement inconsistent if an instance of Quantity mij has a unit of measure uniti that is different from the Measure's unit of measure unit’i. 
        '''
        #TODO update this check to be based on item instead of item1 and item2 since its an internal check
        item1 = item
        item2 = item.valueOf

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

        elif item2 == item1.hasNumerator or item2 == item1.numerator or item2 == item1.hasDenominator or item2 == item1.denominator: #item2 has to be a component of item1 to run this check
            if item2.unit_of_measure[0] == item1.unit_of_measure[0]:
                print(item1, " has the same unit of measure as its component, ", item2, ". They are indicator unit component consistent.")
                return

        elif item1 == item2.hasNumerator or item1 == item2.numerator or item1 == item2.hasDenominator or item1 == item2.denominator: #item2 has to be a component of item1 to run this check
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
    def correspondence_consistency_check(self, item1, item2):
        '''
        Correspondence Inconsistency: where there are no correspondence detected between nodes in the indicator’s definition and published indicator data. 
        This means that not all components in the definition are covered by the published indicator data. 
        published indicator data Si is inconsistent in terms of correspondence if for any corresponding nodes mij  Mi and nik  Ni, 
        there exists a class niy that is linked to nik via property ait where there is no node mix linked to mij that corresponds to niy. 
        '''
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

            if len(class_nodes) > len(individual_nodes):
            #if set(class_nodes) != set(individual_nodes):
                print("Not all components in the definition are covered by the instance. Therefore they are correspondence inconsistent.")
            
            else:
                print("All components in the definition are covered by the instance. Therefore they are correspondence consistent.")

        else:
            print("An indicator definition and indicator data is required for correspondence consistency check, which the inputs ", item1, " and ", item2, " are not. Therefore, correspondence consistency check cannot be run.")    