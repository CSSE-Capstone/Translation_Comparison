import owlready2 as o2
import datetime

class Comparison:
    def __init__(self, classes, individuals):
        self.classes = classes
        self.individuals = individuals
    
    # MAIN
    def compare_class_or_individual(self, item1, item2):
        self.instance_type_consistency_check(item1, item2) #for class and individual
        
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
            #class type inconsistency - type  inconsistent  if it is  not  the case that the two  self.classes are  equal, 
            #nor there exists a property  owl:equivalentClass or owl:subclassOf  between  the self.classes,  
            #or  one class  is  not  subsumed  by  another  class. 
            self.class_type_consistency_check(item1, item2)
          #print(prop)

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
            #property_consistency_check(item1, item2) #need to debug
            self.interval_equality_consistency_check(item1, item2)
            self.interval_non_overlap_consistency_check(item1, item2)

    
    def class_type_consistency_check(self, item1, item2): # item: KG of SPO or Indicator
        class_type_consistent = False
        if item2 in self.classes:
            prop1 = [p for p in item1.get_class_properties()]
            prop2 = [p for p in item2.get_class_properties()]
            # type(item) <- direct parent of item
            # prop1 <- names of properties, not the actual property values
            if ((type(item1) == type(item2)) and (item1.label == item2.label) and (set(prop1) == set(prop2))): 
                #check if properties the same (not checking property values to save computation time) and label and type
                class_type_consistent = True
                print("Class type consistent because self.classes are equal.")
                return class_type_consistent
            elif item2 in item1.INDIRECT_equivalent_to or item1 in item2.INDIRECT_equivalent_to:
                class_type_consistent = True
                print("Class type consistent due to equivalency.")
                return class_type_consistent
            elif item2 in list(item1.self.subclasses()) or item1 in list(item2.self.subclasses()):
                class_type_consistent = True
                print("Class type consistent because one is the subclass of the other.")
                return class_type_consistent
            #subsumption
            for x in list(item1.self.subclasses()):
                if x in list(item2.self.subclasses()) or x in item2.INDIRECT_equivalent_to or x == item2:
                    class_type_consistent = True
                    print("Class type consistent due to subsumption.")
                    return class_type_consistent
            for y in list(item2.self.subclasses()):
                if y in list(item1.self.subclasses()) or y in item1.INDIRECT_equivalent_to or y == item1:
                    class_type_consistent = True
                    print("Class type consistent due to subsumption.")
                    return class_type_consistent
            #final verdict
            if class_type_consistent == False:
                print("Class type inconsistent - neither of the two self.classes is equal, equivalent, or a subclass of the other class.")
                return class_type_consistent
        else:
            print("Class type consistency check not run - ", item2, " is not a class.")
            return
    

    def instance_type_consistency_check(self, item1, item2):
        '''

                #Instance type inconsistency verifies that if the instances that make up a city's indicator are an instance of the same class, 
                # #an equivalent class, a subclass of concepts defined in standard, 
                #or have all necessary properties with values that satisfy the restrictions of those properties defined in the standard definition.
            
            #There does  not  exist  a  direct  rdf:type  relation  between mij  and  nik,  mij is not an  instance  of  nik,  and mij is an  instance  of  civ, and  civ  is type inconsistent with  nik 

            #For example, let mij be the 15.2 indicator value published by Toronto, nik be the class iso37120:’15.2’ where Cor(mij,nik). 
            #Assuming there is a direct rdf:type such that Tri(mij, rdf:type, nik), or Tri(mij, rdf:type, civ) 
            #and civ is the same class, equivalent class or a subclass of nik, i.e., iso37120:15.2, then mij is instance type consistent nik. 
            #In Figure 22, given that Cor(mij,nik) and mij is an instance of civ. The class civ and nik are linked to c’iv and n’ik respectively via property ait. 


            # There does not exist a direct rdf:type relation between mij and nik  (comparing instance m to class n)
            # mij is not an instance of nik, and  
            # mij is an instance of civ, and civ is type inconsistent with nik

            # Given an individual and its corresponding class, the rules determine whether:
            # • the individual contains all of the necessary properties as defined by the class it is a member of, and
            # • the corresponding value for the individual’s property is consistent with the restrictions defined by the class for that property.

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
        if type(beginning1.year) == None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) == None and type(beginning2.month) != None and type(beginning2.day) != None:
            intervalBeginning1 = [int(beginning1.month), int(beginning1.day)]
            intervalEnd1 = [int(end1.month), int(end1.day)]
            #print(intervalBeginning1, intervalEnd1)
            intervalBeginning2 = [int(beginning2.month), int(beginning2.day)]
            intervalEnd2 = [int(end2.month), int(end2.day)]
            #print(intervalBeginning2, intervalEnd2)
        elif type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) == None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) == None:
            intervalBeginning1 = [int(beginning1.year), int(beginning1.month)]
            intervalEnd1 = [int(end1.year), int(end1.month)]
            #print(intervalBeginning1, intervalEnd1)
            intervalBeginning2 = [int(beginning2.year), int(beginning2.month)]
            intervalEnd2 = [int(end2.year), int(end2.month)]
            #print(intervalBeginning2, intervalEnd2)
        return intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2
    
    def subinterval_consistency_check(self, item1, item2): 
        '''
        #NEED VERSION THAT WORKS WHEN YEAR MISSING!
        #subinterval consistency check ALWAYS results in potentially inconsistent. It's only if the time intervals don't overlap at all that it would be inconsistent
        #no, im using potentially inconsistent when there isn't enough info. so these would all be inconsistent.
        '''
        if item2 in self.individuals: #cannot run this check unless both are instances
            indicatorSumOf1 = item1.sumOf
            indicatorSumOf2 = item2.sumOf

            if indicatorSumOf1 and indicatorSumOf2:
                if indicatorSumOf1[0].forTimeInterval and indicatorSumOf2[0].forTimeInterval:
                    timeInterval1 = indicatorSumOf1[0].forTimeInterval
                    timeInterval2 = indicatorSumOf2[0].forTimeInterval
                
                    beginning1 = timeInterval1[0].hasBeginning
                    end1 = timeInterval1[0].hasEnd
                    beginning2 = timeInterval2[0].hasBeginning
                    end2 = timeInterval2[0].hasEnd
        
                    #^^ I did it this way to guarantee label names dont matter
                    if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None:
                        intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date(beginning1, beginning2, end1, end2)

                    #compare
                    #item1 = January 1 2020 - December 31 2020
                    #item2 = January 1 2020 - January 1 2021

                        #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
                        if (intervalBeginning2 < intervalBeginning1 and intervalBeginning1< intervalEnd1 and intervalEnd1 < intervalEnd2):
                            print(item1 , "'s time interval is during " , item2 , "'s. Therefore they are potentially inconsistent.")
                            return
                        elif (intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                            print(item2 , "'s time interval is during " , item1 , "'s. Therefore they are potentially inconsistent.")
                            return

                        #overlaps: start(a) < start(b) < end(a) < end(b)
                        elif (intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 < intervalEnd2):
                            print(item1 , "'s time interval overlaps with " , item2 , "'s. Therefore they are potentially inconsistent.")
                            return
                        elif (intervalBeginning2 < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                            print(item2 , "'s time interval overlaps with " , item1 , "'s. Therefore they are potentially inconsistent.")
                            return
                        
                        #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
                        elif intervalBeginning1 == intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 < intervalEnd2:
                            print(item1 , "and " , item2 , "start together but " , item1 , " ends before " , item2 , ". Therefore they are  inconsistent.")
                            return
                        elif intervalBeginning1 == intervalBeginning2 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1:
                            print(item1 , "and " , item2 , "start together but " , item2 , " ends before " , item1 , ". Therefore they are  inconsistent.")
                            return

                        #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
                        elif intervalBeginning2 < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
                            print(item1 , "and " , item2 , "end together but " , item1 , " starts after " , item2 , ". Therefore they are potentially inconsistent.")
                            return
                        elif intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2 and intervalEnd2 == intervalEnd1:
                            print(item1 , "and " , item2 , "end together but " , item2 , " starts after " , item1 , ". Therefore they are potentially inconsistent.")
                            return
                        #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
                        elif intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalBeginning2 and intervalBeginning2 < intervalEnd2:
                            print(item1 , " ends when " , item2, " begins. Therefore they are potentially inconsistent.")
                            return
                        elif intervalBeginning2 < intervalEnd2 and intervalEnd2 == intervalBeginning1 and intervalBeginning1 < intervalEnd1:
                            print(item2 , " ends when " , item1, " begins. Therefore they are potentially inconsistent.")
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
                        print(item1 , "'s time interval is during " , item2 , "'s. Therefore they are  inconsistent.")
                        return
                    elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0] < intervalEnd1[0]:
                        print(item2 , "'s time interval is during " , item1 , "'s. Therefore they are  inconsistent.")
                        return
                    #overlaps: start(a) < start(b) < end(a) < end(b)
                    elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd1[0] and intervalEnd1[0] < intervalEnd2[0]:
                        print(item1 , "'s time interval overlaps with " , item2 , "'s. Therefore they are  inconsistent.")
                        return
                    elif (intervalBeginning2[0] < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                        print(item2 , "'s time interval overlaps with " , item1 , "'s. Therefore they are  inconsistent.")
                        return
                    #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
                    elif intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning2[0]< intervalEnd1[0]  and intervalEnd1[0]  < intervalEnd2[0]:
                        print(item1 , "and " , item2 , "start together but " , item1 , " ends before " , item2 , ". Therefore they are  inconsistent.")
                        return
                    elif intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning1[0] < intervalEnd2[0]  and intervalEnd2[0]  < intervalEnd1[0]:
                        print(item1 , "and " , item2 , "start together but " , item2 , " ends before " , item1 , ". Therefore they are  inconsistent.")
                        return
                    #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
                    elif intervalBeginning2[0] < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
                        print(item1 , "and " , item2 , "end together but " , item1 , " starts after " , item2 , ". Therefore they are inconsistent.")
                        return
                    elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0]  == intervalEnd1[0]:
                        print(item1 , "and " , item2 , "end together but " , item2 , " starts after " , item1 , ". Therefore they are inconsistent.")
                        return
                    #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
                    elif intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] == intervalBeginning2[0] and intervalBeginning2[0]< intervalEnd2[0]:
                        print(item1 , " ends when " , item2, " begins. Therefore they are inconsistent.")
                        return
                    elif intervalBeginning2[0]< intervalEnd2[0] and intervalEnd2[0] == intervalBeginning1[0] and intervalBeginning1[0] < intervalEnd1[0]:
                        print(item2 , " ends when " , item1, " begins. Therefore they are inconsistent.")
                        return
                    
                    #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
                    elif (intervalBeginning2[1] < intervalBeginning1[1] and intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] < intervalEnd2[1]):
                        print(item1 , "'s time interval is during " , item2 , "'s. Therefore they are inconsistent.")
                        return
                    elif (intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1] < intervalEnd1[1]):
                        print(item2 , "'s time interval is during " , item1 , "'s. Therefore they are inconsistent.")
                        return
                    #overlaps: start(a) < start(b) < end(a) < end(b)
                    elif (intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd1[1] and intervalEnd1[1] < intervalEnd2[1]):
                        print(item1 , "'s time interval overlaps with " , item2 , "'s. Therefore they are inconsistent.")
                        return
                    elif (intervalBeginning2[1] < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                        print(item2 , "'s time interval overlaps with " , item1 , "'s. Therefore they are inconsistent.")
                        return
                    #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
                    elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning2[1]< intervalEnd1[1]  and intervalEnd1[1]  < intervalEnd2[1]:
                        print(item1 , "and " , item2 , "start together but " , item1 , " ends before " , item2 , ". Therefore they are inconsistent.")
                        return
                    elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning1[1] < intervalEnd2[1]  and intervalEnd2[1]  < intervalEnd1[1]:
                        print(item1 , "and " , item2 , "start together but " , item2 , " ends before " , item1 , ". Therefore they are  inconsistent.")
                        return
                    #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
                    elif intervalBeginning2[1] < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
                        print(item1 , "and " , item2 , "end together but " , item1 , " starts after " , item2 , ". Therefore they are  inconsistent.")
                        return
                    elif intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1]  == intervalEnd1[1]:
                        print(item1 , "and " , item2 , "end together but " , item2 , " starts after " , item1 , ". Therefore they are inconsistent.")
                        return
                    #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
                    elif intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] == intervalBeginning2[1] and intervalBeginning2[1]< intervalEnd2[1]:
                        print(item1 , " ends when " , item2, " begins. Therefore they are inconsistent.")
                        return
                    elif intervalBeginning2[1]< intervalEnd2[1] and intervalEnd2[1] == intervalBeginning1[1] and intervalBeginning1[1] < intervalEnd1[1]:
                        print(item2 , " ends when " , item1, " begins. Therefore they are inconsistent.")
                        return
                    else:
                        print(item1 , " and " , item2 , " are subinterval consistent.")
                        return
                else:
                    print("Subinterval consistency check not run - either ", item1, " or ", item2, " does not have a time interval associated with it.")
            else:
                print("Subinterval consistency check not run - either ", item1, " or ", item2, " does not have a time interval associated with it.")
        else:
            print("Subinterval consistency check not run - it is only done when comparing 2 self.individuals.")
            return
    

    def temporal_granularity_consistency_check(self, item1, item2):
        if item2 in self.individuals: #cannot run this check unless both are instances
            indicatorSumOf1 = item1.sumOf
            indicatorSumOf2 = item2.sumOf

            if indicatorSumOf1 and indicatorSumOf2:
                if indicatorSumOf1[0].forTimeInterval and indicatorSumOf2[0].forTimeInterval:
                    timeInterval1 = indicatorSumOf1[0].forTimeInterval
                    timeInterval2 = indicatorSumOf2[0].forTimeInterval
                
                    beginning1 = timeInterval1[0].hasBeginning
                    end1 = timeInterval1[0].hasEnd
                    beginning2 = timeInterval2[0].hasBeginning
                    end2 = timeInterval2[0].hasEnd

                    print(beginning1.year, type(beginning1.month), end1, beginning2, end2.day, type(end2.day)) # TODO do we need to print this?

                    #checking the beginning vs end of each instance
                    #consistency
                    if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) != None and type(end1.month) != None and type(end1.day) != None:
                        print("Both the beginning and end of " , item1, "'s reporting period time interval have day, month, and year temporal units. Therefore they are temporal granular consistent.")
                    elif type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) != None and type(end2.month) != None and type(end2.day) != None:
                        print("Both the beginning and end of " , item2, "'s reporting period time interval have day, month, and year temporal units. Therefore they are temporal granular consistent.")    
                    
                    #both start and end missing year
                    elif type(beginning1.year) == None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) == None and type(end1.month) != None and type(end1.day) != None:
                        print("Both the beginning and end of " , item1, "'s reporting period time interval have day and month temporal units. Therefore they are temporal granular consistent.")
                    elif type(beginning2.year) == None and type(beginning1.month) != None and type(beginning1.day) != None and type(end2.year) == None and type(end1.month) != None and type(end1.day) != None:
                        print("Both the beginning and end of " , item2, "'s reporting period time interval have day and month temporal units. Therefore they are temporal granular consistent.")
                    
                    #both start and end missing day
                    elif type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) == None and type(end1.year) != None and type(end1.month) != None and type(end1.day) == None:
                        print("Both the beginning and end of " , item1, "'s reporting period time interval have month and year temporal units. Therefore they are temporal granular consistent.") 
                    elif type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) == None and type(end2.year) != None and type(end2.month) != None and type(end2.day) == None:
                        print("Both the beginning and end of " , item2, "'s reporting period time interval have month and year temporal units. Therefore they are temporal granular consistent.") 

                    #only start or only end missing year
                    elif ((type(beginning1.year) == None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) != None and type(end1.month) != None and type(end1.day) != None) or (type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) == None and type(end1.month) != None and type(end1.day) != None)):
                        print("The beginning or end of " , item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif ((type(beginning2.year) == None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) != None and type(end2.month) != None and type(end2.day) != None) or (type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) == None and type(end2.month) != None and type(end2.day) != None)):
                        print("The beginning or end of " , item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return
                    
                    #only start or end missing day
                    elif ((type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) == None and type(end1.year) != None and type(end1.month) != None and type(end1.day) != None) or (type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) != None and type(end1.month) != None and type(end1.day) == None)):
                        print("The beginning or end of " , item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif ((type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) == None and type(end2.year) != None and type(end2.month) != None and type(end2.day) != None) or (type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) != None and type(end2.month) != None and type(end2.day) == None)):
                        print("The beginning or end of " , item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return

                    #checking both instances against each other. Only using beginning value since assumption is that beginning and end of each instance are already checked for temporal granularity
                    #consistent cases
                    # if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None:
                    #     print("Both " , item1 , " and " , item2, " have day, month, and year temporal units to describe their reporting intervals. Therefore they are temporal granular consistent.")
                    #     return
                    if (beginning1.year) != None and (beginning1.month) != None and (beginning1.day) != None and (beginning2.year) != None and (beginning2.month) != None and (beginning2.day) != None:
                        print("Both " , item1 , " and " , item2, " have day, month, and year temporal units to describe their reporting intervals. Therefore they are temporal granular consistent.")
                        return
                    elif type(beginning1.day) == None and type(beginning2.day) == None:
                        print("Both " , item1 , " and " , item2, " do not have day temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
                        return
                    elif type(beginning1.year) == None and type(beginning2.year) == None:
                        print("Both " , item1 , " and " , item2, " do not have year temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
                        return
                    #inconsistent cases
                    elif (type(beginning1.year) != None and type(beginning2.year) == None):
                        print(item2 , " does not have a year unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning1.month) != None and type(beginning2.month) == None):
                        print(item2 , " does not have a month unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning1.day) != None and type(beginning2.year) == None):
                        print(item2 , " does not have a day unit whereas " , item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning2.year) != None and type(beginning1.year) == None):
                        print(item1 , " does not have a year unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning2.month) != None and type(beginning1.month) == None):
                        print(item1 , " does not have a month unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning2.day) != None and type(beginning1.year) == None):
                        print(item1 , " does not have a day unit whereas " , item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                else:
                    print("Temporal granularity consistency check not run - either ", item1, " or ", item2, " does not have a time interval associated with it.")
            else:
                print("Temporal granularity consistency check not run - either ", item1, " or ", item2, " does not have a time interval associated with it.")
        else:
            print("Temporal granularity consistency check not run - it is only done when comparing 2 self.individuals.")
            return
    

      
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
            restrictions = [x for x in item2.is_a if (isinstance(x, o2.entity.Restriction))]

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
            restrictions = [x for x in item2.is_a if (isinstance(x, o2.entity.Restriction))]

        #cardinality of a for m does not satisfy cardinality restriction in n
        #it is not possible to do for loop over prop in proplist of item1 and then do item1.prop. 
        #it needs the exact name of the prop to get the value. Therefore this isn't possible to do in owlready2, would have to be done manually.
            allprop = item1.get_properties()
            for r in restrictions:
                if r.property in allprop:
                    print("property: " , r.property , " value: " , r.value)
                else:
                    print(item1 , " is property inconsistent with " , item2 , " because it does not satisfy the value restriction of property " , prop , " defined in " , item2 +".")

            for prop in item1.get_class_properties():
                properties_of_parent.append(prop)
                if (len(prop.range) > 0) and (type(item1) not in prop.range):
                    print(item1 , " is property inconsistent with " , item2 , " because it does not satisfy the range restriction of property " , prop , " defined in " , item2 +".")
                    return
                elif prop not in allprop:
                    print(item1 , " is property inconsistent with " , item2 , " because  property " , prop , " defined in " , item2 , " does not exist for " , item1 , ".")
                    return
                #at this point already checked if definition property not in instance
                elif (len(prop.range) == 0):
                    print(item1 , " is potentially property inconsistent with " , item2 , " because the value restriction (range) of property " , prop , " is not provided.")
                    return

        else:
            print("Property consistency check not run - it is only done when comparing instance m with its definition class n.")
            return

    def interval_equality_consistency_check(self, item1, item2):
        if item2 in self.individuals:
            indicatorSumOf1 = item1.sumOf
            timeInterval1 = indicatorSumOf1[0].forTimeInterval
            beginning1 = timeInterval1[0].hasBeginning
            end1 = timeInterval1[0].hasEnd
            indicatorSumOf2 = item2.sumOf
            timeInterval2 = indicatorSumOf2[0].forTimeInterval
            beginning2 = timeInterval2[0].hasBeginning
            end2 = timeInterval2[0].hasEnd
            if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None:
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
        else:
            print("Interval equality consistency check not run - it is only done when comparing an instance to another instance.")
            return

    
    def interval_non_overlap_consistency_check(self, item1, item2):
        if item2 in self.individuals:
            indicatorSumOf1 = item1.sumOf
            timeInterval1 = indicatorSumOf1[0].forTimeInterval
            beginning1 = timeInterval1[0].hasBeginning
            end1 = timeInterval1[0].hasEnd
            indicatorSumOf2 = item2.sumOf
            timeInterval2 = indicatorSumOf2[0].forTimeInterval
            beginning2 = timeInterval2[0].hasBeginning
            end2 = timeInterval2[0].hasEnd

            if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None:
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
        else:
            print("Non overlapping interval consistency check not run - it is only done when comparing an instance to another instance.")
            return
    
    def place_equality_consistency_check(self, item1, item2):
        '''
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
                print(f'{item1} and {item2} do not have a location property associated with it - place equality consistency check cannot be run.')
                return place_equality_consistent

            item = item1 if not(location) else item2
            print(item, " does not have a location property associated with it - place equality consistency check cannot be run.")
            return place_equality_consistent


        #considering case when checking consistency between indicator (item1) that has a location + its population/population definition (item2) has a location
        if ("iso21972.Indicator" in str(parent.ancestors())) or ("cids.Indicator" in str(parent.ancestors())): 
            population = item1.sumOf
            if population:
                definition = population[0].definedBy

                if item2 == item1.sumOf or item2 == definition: #if item2 is item1's population or if item2 is item1's population's definition             
                    #compare within indicator
                    if location and location2 and location == location2:
                        print(item1, " is place equality consistent with ", item2, " - they both refer to the same location.")
                        place_equality_consistent = True
                        return place_equality_consistent
                    elif location and location2 and location != location2:
                        print(item1, " is not place equality consistent with ", item2, " due to them referring to different locations.")
                        return place_equality_consistent 

        elif ("iso21972.Indicator" in str(parent2.ancestors())) or ("cids.Indicator" in str(parent2.ancestors())): 
            population = item2.sumOf
            if population:
                definition = population[0].definedBy

                if item1 == item2.sumOf or item1 == definition: #if item1 is item2's population or if item1 is item2's population's definition             
                    #compare within indicator
                    if location and location2 and location == location2:
                        print(item2, " is place equality consistent with ", item1, " - they both refer to the same location.")
                        place_equality_consistent = True
                        return place_equality_consistent
                    elif location and location2 and location != location2:
                        print(item2, " is not place equality consistent with ", item1, " due to them referring to different locations.")
                        return place_equality_consistent  

        else: #has location but does not fulfill above indicator relationship
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
        

    def subplace_consistency_check(self, place_equality_consistent, item1, item2):
        '''
        #Any two instances mij and mik ∊ Mi are potentially subplace inconsistent if instance of placename referred by mik is an area within city referred by mij 
        #Subplace inconsistency refers to the situation where the placename referred by an instance mik is an area within the instance of mij. 
        #For example, the population measured by an indicator should be related to place instances city’i which include all areas within cityi which is referred by the indicator mij. 
        #The measure may not be complete if city’i is only an area within cityi since not all populations in cityi have been considered. 

            # city section vs city
        #   city section vs province
        #   city section vs country
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
                print("Subplace consistency check not run - location information not available for ", item1, ".") 
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

    # TODO Quantity Measure Inconsistency 
    # TODO Indicator Unit Component Inconsistency 
    # TODO Singular Unit Inconsistency 
    # TODO Correspondence Inconsistency: where there are no correspondence detected between nodes in the indicator’s definition and city published indicator data. This means that not all components in the definition are covered by the published indicator data. 
