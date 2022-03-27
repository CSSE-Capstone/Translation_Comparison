class Comparison:
    def __init__(self, classes, individuals, item1, item2):
        self.item1 = item1
        self.item2 = item2
        self.classes = self.classes
        self.individuals = self.individuals
    
    # MAIN
    def compare_class_or_individual(self):   
        self.instance_type_consistency_check(self.item1, self.item2) #for class and individual
        if self.item1 in self.classes:
            allprop = self.item1.get_class_properties()
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
            self.class_type_consistency_check(self.item1, self.item2)
          #print(prop)

        elif self.item1 in self.individuals:
            allprop = self.item1.get_properties()
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
        
            place_equality_consistent = self.place_equality_consistency_check(self.item1, self.item2) #needed to run self.subplace_consistency_check
            self.subplace_consistency_check(self.item1, self.item2, place_equality_consistent)
            self.temporal_granularity_consistency_check (self.item1, self.item2) #run this before subinterval since subinterval needs them to be the same temporal unit, but actually, does it matter? No, but it does in the way that I implemented it using the datetime library
            self.subinterval_consistency_check(self.item1, self.item2)
            #property_consistency_check(self.item1, self.item2) #need to debug
            self.interval_equality_consistency_check(self.item1, self.item2)
            self.interval_non_overlap_consistency_check(self.item1, self.item2)

    
    def class_type_consistency_check(self, item1, item2): # item: KG of SPO or Indicator
        class_type_consistent = False
        if self.item2 in self.classes:
            prop1 = [p for p in self.item1.get_class_properties()]
            prop2 = [p for p in self.item2.get_class_properties()]
            # type(item) <- direct parent of item
            # prop1 <- names of properties, not the actual property values
            if ((type(self.item1) == type(self.item2)) and (self.item1.label == self.item2.label) and (set(prop1) == set(prop2))): 
                #check if properties the same (not checking property values to save computation time) and label and type
                class_type_consistent = True
                print("Class type consistent because self.classes are equal.")
                return class_type_consistent
            elif self.item2 in self.item1.INDIRECT_equivalent_to or self.item1 in self.item2.INDIRECT_equivalent_to:
                class_type_consistent = True
                print("Class type consistent due to equivalency.")
                return class_type_consistent
            elif self.item2 in list(self.item1.self.subclasses()) or self.item1 in list(self.item2.self.subclasses()):
                class_type_consistent = True
                print("Class type consistent because one is the subclass of the other.")
                return class_type_consistent
            #subsumption
            for x in list(self.item1.self.subclasses()):
                if x in list(self.item2.self.subclasses()) or x in self.item2.INDIRECT_equivalent_to or x == self.item2:
                    class_type_consistent = True
                    print("Class type consistent due to subsumption.")
                    return class_type_consistent
            for y in list(self.item2.self.subclasses()):
                if y in list(self.item1.self.subclasses()) or y in self.item1.INDIRECT_equivalent_to or y == self.item1:
                    class_type_consistent = True
                    print("Class type consistent due to subsumption.")
                    return class_type_consistent
            #final verdict
            if class_type_consistent == False:
                print("Class type inconsistent - neither of the two self.classes is equal, equivalent, or a subclass of the other class.")
                return class_type_consistent
        else:
            print("Class type consistency check not run - ", self.item2, " is not a class.")
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
        if (self.item2 in self.classes and self.item1 in self.individuals):
            #item 2 = n, self.item1 = m
            #parent = self.item1.is_instance_of[0] #parent class of self.item1
            #if parent in str(self.item2.self.subclasses()))

            if self.item1 not in self.item2.instances(): 
                print(self.item1, " is not an instance of " , self.item2, " - therefore they are instance type inconsistent.")
                return
            
            else: #self.item1 is instance of self.item2
                if type(self.item1) == self.item2: #self.item1 has type self.item2
                    for c in self.item1.is_instance_of:
                        #The instance mij is type inconsistent with nik if the class civ is inconsistent with nik, i.e., Type InConsistency(civ,nik) is true. 
                        if self.class_type_consistency_check(c, self.item2) == False:
                            print(self.item1, " is an instance of " ,c, ", which is type inconsistent with " ,self.item2, " - therefore ", self.item1, "is instance type inconsistent with ", self.item2, ".")
                            break
                            return
                        #elif necessary properties satisfy restriction of properties
                        else:
                            print(self.item1, " is instance type consistent with ", self.item2, " because there is a direct rdf:type relation between them, ", self.item1, " is an instance of ", self.item2, ", and all self.classes that ", self.item1, " is an instance of are type consistent with ", self.item2, ".")
                            return
                else:
                    print(self.item1, " is instance type inconsistent with ", self.item2, " because there is not a direct rdf:type relation between them.")
                    return

        elif (self.item1 in self.classes and self.item2 in self.individuals):
            #self.item1 = n, self.item2 = m
            #parent = self.item2.is_instance_of[0] #parent class of self.item2
            #if parent in str(self.item1.self.subclasses()))

            if self.item2 not in self.item1.instances(): 
                print(self.item2, " is not an instance of " , self.item1, " - therefore they are instance type inconsistent.")
                return
            
            else: #self.item2 is instance of self.item1
                if type(self.item2) == self.item1: #self.item2 has type self.item1
                    for c in self.item2.is_instance_of:
                        #The instance mij is type inconsistent with nik if the class civ is inconsistent with nik, i.e., Type InConsistency(civ,nik) is true. 
                        if self.class_type_consistency_check(c, self.item1) == False:
                            print(self.item2, " is an instance of " ,c, ", which is type inconsistent with " ,self.item1, " - therefore ", self.item2, "is instance type inconsistent with ", self.item1, ".")
                            break
                            return
                        #elif necessary properties satisfy restriction of properties, can i use property consistency check?
                        else:
                            print(self.item2, " is instance type consistent with ", self.item1, " because there is a direct rdf:type relation between them, ", self.item2, " is an instance of ", self.item1, ", and all self.classes that ", self.item2, " is an instance of are type consistent with ", self.item1, ".")
                            return
                else:
                    print(self.item2, " is instance type inconsistent with ", self.item1, " because there is not a direct rdf:type relation between them.")
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
                if self.item2 in self.individuals: #cannot run this check unless both are instances
        '''
        indicatorSumOf1 = self.item1.sumOf
        indicatorSumOf2 = self.item2.sumOf

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
                    intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = get_date(beginning1, beginning2, end1, end2)

                #compare
                #self.item1 = January 1 2020 - December 31 2020
                #self.item2 = January 1 2020 - January 1 2021

                    #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
                    if (intervalBeginning2 < intervalBeginning1 and intervalBeginning1< intervalEnd1 and intervalEnd1 < intervalEnd2):
                        print(self.item1 , "'s time interval is during " , self.item2 , "'s. Therefore they are potentially inconsistent.")
                        return
                    elif (intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                        print(self.item2 , "'s time interval is during " , self.item1 , "'s. Therefore they are potentially inconsistent.")
                        return

                    #overlaps: start(a) < start(b) < end(a) < end(b)
                    elif (intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 < intervalEnd2):
                        print(self.item1 , "'s time interval overlaps with " , self.item2 , "'s. Therefore they are potentially inconsistent.")
                        return
                    elif (intervalBeginning2 < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                        print(self.item2 , "'s time interval overlaps with " , self.item1 , "'s. Therefore they are potentially inconsistent.")
                        return
                    
                    #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
                    elif intervalBeginning1 == intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 < intervalEnd2:
                        print(self.item1 , "and " , self.item2 , "start together but " , self.item1 , " ends before " , self.item2 , ". Therefore they are  inconsistent.")
                        return
                    elif intervalBeginning1 == intervalBeginning2 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1:
                        print(self.item1 , "and " , self.item2 , "start together but " , self.item2 , " ends before " , self.item1 , ". Therefore they are  inconsistent.")
                        return

                    #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
                    elif intervalBeginning2 < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
                        print(self.item1 , "and " , self.item2 , "end together but " , self.item1 , " starts after " , self.item2 , ". Therefore they are potentially inconsistent.")
                        return
                    elif intervalBeginning1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2 and intervalEnd2 == intervalEnd1:
                        print(self.item1 , "and " , self.item2 , "end together but " , self.item2 , " starts after " , self.item1 , ". Therefore they are potentially inconsistent.")
                        return
                    #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
                    elif intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalBeginning2 and intervalBeginning2 < intervalEnd2:
                        print(self.item1 , " ends when " , self.item2, " begins. Therefore they are potentially inconsistent.")
                        return
                    elif intervalBeginning2 < intervalEnd2 and intervalEnd2 == intervalBeginning1 and intervalBeginning1 < intervalEnd1:
                        print(self.item2 , " ends when " , self.item1, " begins. Therefore they are potentially inconsistent.")
                        return
                    else:
                        print(self.item1 , " and " , self.item2 , " are subinterval consistent.")
                        return
                else:
                #check each item of list. List is always organized from [year, month, day]
                    intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = self.get_date_when_none_values(beginning1, beginning2, end1, end2)

                #compare all intervals on first element of list. then compare items on second element of list. 
                #TODO See if more efficient method
                #TODO make sure this works if month is higher but year is lower for something. it should though because I'm checking [0] before [1]

                #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
                if (intervalBeginning2[0] < intervalBeginning1[0]) and intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] < intervalEnd2[0]:
                    print(self.item1 , "'s time interval is during " , self.item2 , "'s. Therefore they are  inconsistent.")
                    return
                elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0] < intervalEnd1[0]:
                    print(self.item2 , "'s time interval is during " , self.item1 , "'s. Therefore they are  inconsistent.")
                    return
                #overlaps: start(a) < start(b) < end(a) < end(b)
                elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd1[0] and intervalEnd1[0] < intervalEnd2[0]:
                    print(self.item1 , "'s time interval overlaps with " , self.item2 , "'s. Therefore they are  inconsistent.")
                    return
                elif (intervalBeginning2[0] < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                    print(self.item2 , "'s time interval overlaps with " , self.item1 , "'s. Therefore they are  inconsistent.")
                    return
                #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
                elif intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning2[0]< intervalEnd1[0]  and intervalEnd1[0]  < intervalEnd2[0]:
                    print(self.item1 , "and " , self.item2 , "start together but " , self.item1 , " ends before " , self.item2 , ". Therefore they are  inconsistent.")
                    return
                elif intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning1[0] < intervalEnd2[0]  and intervalEnd2[0]  < intervalEnd1[0]:
                    print(self.item1 , "and " , self.item2 , "start together but " , self.item2 , " ends before " , self.item1 , ". Therefore they are  inconsistent.")
                    return
                #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
                elif intervalBeginning2[0] < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
                    print(self.item1 , "and " , self.item2 , "end together but " , self.item1 , " starts after " , self.item2 , ". Therefore they are inconsistent.")
                    return
                elif intervalBeginning1[0] < intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0]  == intervalEnd1[0]:
                    print(self.item1 , "and " , self.item2 , "end together but " , self.item2 , " starts after " , self.item1 , ". Therefore they are inconsistent.")
                    return
                #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
                elif intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] == intervalBeginning2[0] and intervalBeginning2[0]< intervalEnd2[0]:
                    print(self.item1 , " ends when " , self.item2, " begins. Therefore they are inconsistent.")
                    return
                elif intervalBeginning2[0]< intervalEnd2[0] and intervalEnd2[0] == intervalBeginning1[0] and intervalBeginning1[0] < intervalEnd1[0]:
                    print(self.item2 , " ends when " , self.item1, " begins. Therefore they are inconsistent.")
                    return
                
                #during: start(b) < start(a) < end(a) < end(b) (a is contained by b)
                elif (intervalBeginning2[1] < intervalBeginning1[1] and intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] < intervalEnd2[1]):
                    print(self.item1 , "'s time interval is during " , self.item2 , "'s. Therefore they are inconsistent.")
                    return
                elif (intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1] < intervalEnd1[1]):
                    print(self.item2 , "'s time interval is during " , self.item1 , "'s. Therefore they are inconsistent.")
                    return
                #overlaps: start(a) < start(b) < end(a) < end(b)
                elif (intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd1[1] and intervalEnd1[1] < intervalEnd2[1]):
                    print(self.item1 , "'s time interval overlaps with " , self.item2 , "'s. Therefore they are inconsistent.")
                    return
                elif (intervalBeginning2[1] < intervalBeginning1 and intervalBeginning1 < intervalEnd2 and intervalEnd2 < intervalEnd1):
                    print(self.item2 , "'s time interval overlaps with " , self.item1 , "'s. Therefore they are inconsistent.")
                    return
                #starts: start(a) = start(b) < end(a) < end(b) (a and b start together but a ends before b)
                elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning2[1]< intervalEnd1[1]  and intervalEnd1[1]  < intervalEnd2[1]:
                    print(self.item1 , "and " , self.item2 , "start together but " , self.item1 , " ends before " , self.item2 , ". Therefore they are inconsistent.")
                    return
                elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning1[1] < intervalEnd2[1]  and intervalEnd2[1]  < intervalEnd1[1]:
                    print(self.item1 , "and " , self.item2 , "start together but " , self.item2 , " ends before " , self.item1 , ". Therefore they are  inconsistent.")
                    return
                #ends: start(b) < start(a) < end(a) = end(b) (a and b end together but a starts after b)
                elif intervalBeginning2[1] < intervalBeginning1 and intervalBeginning1 < intervalEnd1 and intervalEnd1 == intervalEnd2:
                    print(self.item1 , "and " , self.item2 , "end together but " , self.item1 , " starts after " , self.item2 , ". Therefore they are  inconsistent.")
                    return
                elif intervalBeginning1[1] < intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1]  == intervalEnd1[1]:
                    print(self.item1 , "and " , self.item2 , "end together but " , self.item2 , " starts after " , self.item1 , ". Therefore they are inconsistent.")
                    return
                #meets: start(a) < end(a) = start(b) < end(b) (a ends when b begins)
                elif intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] == intervalBeginning2[1] and intervalBeginning2[1]< intervalEnd2[1]:
                    print(self.item1 , " ends when " , self.item2, " begins. Therefore they are inconsistent.")
                    return
                elif intervalBeginning2[1]< intervalEnd2[1] and intervalEnd2[1] == intervalBeginning1[1] and intervalBeginning1[1] < intervalEnd1[1]:
                    print(self.item2 , " ends when " , self.item1, " begins. Therefore they are inconsistent.")
                    return
                else:
                    print(self.item1 , " and " , self.item2 , " are subinterval consistent.")
                    return
            else:
                print("Subinterval consistency check not run - either ", self.item1, " or ", self.item2, " does not have a time interval associated with it.")
        else:
            print("Subinterval consistency check not run - either ", self.item1, " or ", self.item2, " does not have a time interval associated with it.")
        else:
            print("Subinterval consistency check not run - it is only done when comparing 2 self.individuals.")
            return
    

    def temporal_granularity_consistency_check(self, item1, item2):
        if self.item2 in self.individuals: #cannot run this check unless both are instances
            indicatorSumOf1 = self.item1.sumOf
            indicatorSumOf2 = self.item2.sumOf

            if indicatorSumOf1 and indicatorSumOf2:
                if indicatorSumOf1[0].forTimeInterval and indicatorSumOf2[0].forTimeInterval:
                    timeInterval1 = indicatorSumOf1[0].forTimeInterval
                    timeInterval2 = indicatorSumOf2[0].forTimeInterval
                
                    beginning1 = timeInterval1[0].hasBeginning
                    end1 = timeInterval1[0].hasEnd
                    beginning2 = timeInterval2[0].hasBeginning
                    end2 = timeInterval2[0].hasEnd

                    print(beginning1.year, type(beginning1.month), end1, beginning2, end2.day, type(end2.day))

                    #checking the beginning vs end of each instance
                    #consistency
                    if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) != None and type(end1.month) != None and type(end1.day) != None:
                        print("Both the beginning and end of " , self.item1, "'s reporting period time interval have day, month, and year temporal units. Therefore they are temporal granular consistent.")
                    elif type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) != None and type(end2.month) != None and type(end2.day) != None:
                        print("Both the beginning and end of " , self.item2, "'s reporting period time interval have day, month, and year temporal units. Therefore they are temporal granular consistent.")    
                    
                    #both start and end missing year
                    elif type(beginning1.year) == None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) == None and type(end1.month) != None and type(end1.day) != None:
                        print("Both the beginning and end of " , self.item1, "'s reporting period time interval have day and month temporal units. Therefore they are temporal granular consistent.")
                    elif type(beginning2.year) == None and type(beginning1.month) != None and type(beginning1.day) != None and type(end2.year) == None and type(end1.month) != None and type(end1.day) != None:
                        print("Both the beginning and end of " , self.item2, "'s reporting period time interval have day and month temporal units. Therefore they are temporal granular consistent.")
                    
                    #both start and end missing day
                    elif type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) == None and type(end1.year) != None and type(end1.month) != None and type(end1.day) == None:
                        print("Both the beginning and end of " , self.item1, "'s reporting period time interval have month and year temporal units. Therefore they are temporal granular consistent.") 
                    elif type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) == None and type(end2.year) != None and type(end2.month) != None and type(end2.day) == None:
                        print("Both the beginning and end of " , self.item2, "'s reporting period time interval have month and year temporal units. Therefore they are temporal granular consistent.") 

                    #only start or only end missing year
                    elif ((type(beginning1.year) == None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) != None and type(end1.month) != None and type(end1.day) != None) or (type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) == None and type(end1.month) != None and type(end1.day) != None)):
                        print("The beginning or end of " , self.item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif ((type(beginning2.year) == None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) != None and type(end2.month) != None and type(end2.day) != None) or (type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) == None and type(end2.month) != None and type(end2.day) != None)):
                        print("The beginning or end of " , self.item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return
                    
                    #only start or end missing day
                    elif ((type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) == None and type(end1.year) != None and type(end1.month) != None and type(end1.day) != None) or (type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(end1.year) != None and type(end1.month) != None and type(end1.day) == None)):
                        print("The beginning or end of " , self.item1, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif ((type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) == None and type(end2.year) != None and type(end2.month) != None and type(end2.day) != None) or (type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None and type(end2.year) != None and type(end2.month) != None and type(end2.day) == None)):
                        print("The beginning or end of " , self.item2, "'s reporting period time interval have different temporal units (one of them is missing the year temporal unit). Therefore they have different temporal granularity and are inconsistent.")
                        return

                    #checking both instances against each other. Only using beginning value since assumption is that beginning and end of each instance are already checked for temporal granularity
                    #consistent cases
                    # if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None:
                    #     print("Both " , self.item1 , " and " , self.item2, " have day, month, and year temporal units to describe their reporting intervals. Therefore they are temporal granular consistent.")
                    #     return
                    if (beginning1.year) != None and (beginning1.month) != None and (beginning1.day) != None and (beginning2.year) != None and (beginning2.month) != None and (beginning2.day) != None:
                        print("Both " , self.item1 , " and " , self.item2, " have day, month, and year temporal units to describe their reporting intervals. Therefore they are temporal granular consistent.")
                        return
                    elif type(beginning1.day) == None and type(beginning2.day) == None:
                        print("Both " , self.item1 , " and " , self.item2, " do not have day temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
                        return
                    elif type(beginning1.year) == None and type(beginning2.year) == None:
                        print("Both " , self.item1 , " and " , self.item2, " do not have year temporal unit to describe their reporting intervals. Therefore they are temporal granular consistent.")
                        return
                    #inconsistent cases
                    elif (type(beginning1.year) != None and type(beginning2.year) == None):
                        print(self.item2 , " does not have a year unit whereas " , self.item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning1.month) != None and type(beginning2.month) == None):
                        print(self.item2 , " does not have a month unit whereas " , self.item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning1.day) != None and type(beginning2.year) == None):
                        print(self.item2 , " does not have a day unit whereas " , self.item1 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning2.year) != None and type(beginning1.year) == None):
                        print(self.item1 , " does not have a year unit whereas " , self.item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning2.month) != None and type(beginning1.month) == None):
                        print(self.item1 , " does not have a month unit whereas " , self.item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                    elif (type(beginning2.day) != None and type(beginning1.year) == None):
                        print(self.item1 , " does not have a day unit whereas " , self.item2 , " does. Therefore they have different temporal granularity and are inconsistent.")
                        return
                else:
                    print("Temporal granularity consistency check not run - either ", self.item1, " or ", self.item2, " does not have a time interval associated with it.")
            else:
                print("Temporal granularity consistency check not run - either ", self.item1, " or ", self.item2, " does not have a time interval associated with it.")
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
        if (self.item1 in self.classes and self.item2 in self.item1.ancestors()) or (self.item2 in self.item1.is_a):
        #instance_property_consistent = False

            properties_of_parent = []
            restrictions = [x for x in self.item2.is_a if (isinstance(x, o2.entity.Restriction))]

            #cardinality of a for m does not satisfy cardinality restriction in n
            #it is not possible to do for loop over prop in proplist of self.item1 and then do self.item1.prop. 
            for r in restrictions:
                print(r)
                if r in self.item1.get_properties():
                    print("property: " , r.property , " value: " , r.value)

                # for prop in onto.drug_1.get_properties():
                #   for value in prop[onto.drug_1]:
                #      print(".%s == %s" % (prop.python_name, value))

            for prop in self.item2.get_class_properties():
                properties_of_parent.append(prop)
                if (len(prop.range) > 0) and (type(self.item1) not in prop.range):
                    print(self.item1 , " is property inconsistent with " , self.item2 , " because it does not satisfy the value restriction of property " , prop , " defined in " , self.item2 +".")
                    return
                elif prop not in self.item1.get_properties():
                    print(self.item1 , " is property inconsistent with " , self.item2 , " because  property " , prop , " defined in " , self.item2 , " does not exist for " , self.item1 , ".")
                    return
                    #at this point already checked if definition property not in instance
                elif (len(prop.range) == 0):
                    print(self.item1 , " is potentially property inconsistent with " , self.item2 , " because the value restriction (range) of property " , prop , " is not provided.")
                    return

        if (self.item2 in self.classes and self.item1 in self.item2.ancestors()) or (self.item1 in self.item2.is_a):
        #instance_property_consistent = False
            properties_of_parent = []
            restrictions = [x for x in self.item2.is_a if (isinstance(x, o2.entity.Restriction))]

        #cardinality of a for m does not satisfy cardinality restriction in n
        #it is not possible to do for loop over prop in proplist of self.item1 and then do self.item1.prop. 
        #it needs the exact name of the prop to get the value. Therefore this isn't possible to do in owlready2, would have to be done manually.
        for r in restrictions:
            if r.property in allprop:
                print("property: " , r.property , " value: " , r.value)
            else:
                print(          print(self.item1 , " is property inconsistent with " , self.item2 , " because it does not satisfy the value restriction of property " , prop , " defined in " , self.item2 +".")

        for prop in self.item1.get_class_properties():
            properties_of_parent.append(prop)
            if (len(prop.range) > 0) and (type(self.item1) not in prop.range):
            print(self.item1 , " is property inconsistent with " , self.item2 , " because it does not satisfy the range restriction of property " , prop , " defined in " , self.item2 +".")
            return
            elif prop not in allprop:
            print(self.item1 , " is property inconsistent with " , self.item2 , " because  property " , prop , " defined in " , self.item2 , " does not exist for " , self.item1 , ".")
            return
            #at this point already checked if definition property not in instance
            elif (len(prop.range) == 0):
            print(self.item1 , " is potentially property inconsistent with " , self.item2 , " because the value restriction (range) of property " , prop , " is not provided.")
            return

        else:
        print("Property consistency check not run - it is only done when comparing instance m with its definition class n.")
        return

    def interval_equality_consistency_check(self):
        if self.item2 in self.individuals:
        indicatorSumOf1 = self.item1.sumOf
        timeInterval1 = indicatorSumOf1[0].forTimeInterval
        beginning1 = timeInterval1[0].hasBeginning
        end1 = timeInterval1[0].hasEnd
        indicatorSumOf2 = self.item2.sumOf
        timeInterval2 = indicatorSumOf2[0].forTimeInterval
        beginning2 = timeInterval2[0].hasBeginning
        end2 = timeInterval2[0].hasEnd
        if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None:
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = get_date(beginning1, beginning2, end1, end2)

            #equals: start(a) = start(b) < end(a) = end(b) (a and b are identical)
            if (intervalBeginning1 == intervalBeginning2 and intervalBeginning2 < intervalEnd1 and intervalEnd1 == intervalEnd2):
            print(self.item1 , "'s time interval is identical to " , self.item2 , "'s. Therefore they are interval equality consistent.")
            return
            else:
            print(self.item1 , "'s time interval is not identical to " , self.item2 , "'s. Therefore they are interval equality inconsistent.")
            return
        else:
        #check each item of list. List is always organized from [year, month, day]
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = get_date_when_none_values(beginning1, beginning2, end1, end2)
            if intervalBeginning1[0]  == intervalBeginning2[0] and intervalBeginning2[0] < intervalEnd1[0]  and intervalEnd1[0]  == intervalEnd2[0]:
            print(self.item1 , "and " , self.item2 , " have identical time intervals. Therefore they are interval equality consistent.")
            return
            elif intervalBeginning1[1]  == intervalBeginning2[1] and intervalBeginning2[1] < intervalEnd1[1]  and intervalEnd1[1]  == intervalEnd2[1]:
            print(self.item1 , "and " , self.item2 , " have identical time intervals. Therefore they are interval equality consistent.")
            return
            else:
            print(self.item1 , "'s time interval is not identical to " , self.item2 , "'s. Therefore they are interval equality inconsistent.")
            return
        else:
        print("Interval equality consistency check not run - it is only done when comparing an instance to another instance.")
        return

    
    def interval_non_overlap_consistency_check(self):
        if self.item2 in self.individuals:
        indicatorSumOf1 = self.item1.sumOf
        timeInterval1 = indicatorSumOf1[0].forTimeInterval
        beginning1 = timeInterval1[0].hasBeginning
        end1 = timeInterval1[0].hasEnd
        indicatorSumOf2 = self.item2.sumOf
        timeInterval2 = indicatorSumOf2[0].forTimeInterval
        beginning2 = timeInterval2[0].hasBeginning
        end2 = timeInterval2[0].hasEnd

        if type(beginning1.year) != None and type(beginning1.month) != None and type(beginning1.day) != None and type(beginning2.year) != None and type(beginning2.month) != None and type(beginning2.day) != None:
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = get_date(beginning1, beginning2, end1, end2)

            #only need to check before since after is an inverse of before. before: start(a) < end(a) < start(b) < end(b) (a ends before b starts)
            if (intervalBeginning1 < intervalEnd1 and intervalEnd1 < intervalBeginning2 and intervalBeginning2 < intervalEnd2):
            print(self.item1 , "'s time interval is before " , self.item2 , "'s. Therefore their intervals do not overlap and they are not consistent.")
            return
            elif (intervalBeginning2 < intervalEnd2 and intervalEnd2 < intervalBeginning1 and intervalBeginning1 < intervalEnd1):
            print(self.item2 , "'s time interval is before " , self.item1 , "'s. Therefore their intervals do not overlap and they are not consistent.")
            return
            else:
            print(self.item1 , " and " , self.item2 , "'s time intervals are overlapping or equal. Therefore they are non overlapping interval consistent.")
            return
        else:
        #check each item of list. List is always organized from [year, month, day]
            intervalBeginning1, intervalEnd1, intervalBeginning2, intervalEnd2 = get_date_when_none_values(beginning1, beginning2, end1, end2)
            if intervalBeginning1[0] < intervalEnd1[0] and intervalEnd1[0] < intervalBeginning2[0]  and intervalBeginning2[0]  < intervalEnd2[0]:
            print(self.item1 , "'s time interval is before " , self.item2 , "'s. Therefore their intervals do not overlap and they are not consistent.")
            return
            elif intervalBeginning1[1] < intervalEnd1[1] and intervalEnd1[1] < intervalBeginning2[1]  and intervalBeginning2[1]  < intervalEnd2[1]:
            print(self.item1 , "'s time interval is before " , self.item2 , "'s. Therefore their intervals do not overlap and they are not consistent.")
            return
            elif intervalBeginning2[0] < intervalEnd2[0] and intervalEnd2[0] < intervalBeginning1[0]  and intervalBeginning1[0]  < intervalEnd1[0]:
            print(self.item2 , "'s time interval is before " , self.item1 , "'s. Therefore their intervals do not overlap and they are not consistent.")
            return
            elif intervalBeginning2[1] < intervalEnd2[1] and intervalEnd2[1] < intervalBeginning1[1]  and intervalBeginning1[1]  < intervalEnd1[1]:
            print(self.item2 , "'s time interval is before " , self.item1 , "'s. Therefore their intervals do not overlap and they are not consistent.")
            return

            else:
            print(self.item1 , " and " , self.item2 , "'s time intervals are overlapping or equal. Therefore they are non overlapping interval consistent.")
            return
        else:
        print("Non overlapping interval consistency check not run - it is only done when comparing an instance to another instance.")
        return
    
    def place_equality_consistency_check(self):
        '''
        #if self.item1 or self.item2 = indicator and the other item is its population definition: should be all same location. 
        #forCitySection, forState, forProvince, for_city, parentCountry, located_in are common location properties. "reside_in" is used for area for IRIS indicators rather than actual geographical locations
        '''
        place_equality_consistent = False #used in subplace consistency check

        if self.item2 in self.individuals: #self.item1 and self.item2 both need to be self.individuals
            parent = self.item1.is_instance_of[0] #parent class of self.item1
            parent2 = self.item2.is_instance_of[0] #parent class of self.item2
            location = None
            location2 = None
            
            if self.item1.located_in:
                    location = self.item1.located_in
            elif self.item1.parentCountry:
                location = self.item1.parentCountry
            elif self.item1.hasCountry:
                location = self.item1.hasCountry
            elif self.item1.hasProvince:
                location = self.item1.hasProvince
            elif self.item1.hasState:
                location = self.item1.hasState
            elif self.item1.for_city: #city checked after Province/State so that most specific information can be compared
                location = self.item1.for_city
            elif self.item1.hasCity:
                location = self.item1.hasCity
            elif self.item1.hasCitySection:
                location = self.item1.hasCitySection

            if self.item2.located_in:
                location2 = self.item2.located_in
            elif self.item2.parentCountry:
                location2 = self.item2.parentCountry
            elif self.item2.hasCountry:
                location2 = self.item2.hasCountry
            elif self.item2.hasProvince:
                location2 = self.item2.hasProvince
            elif self.item2.hasState:
                location2 = self.item2.hasState
            elif self.item2.for_city: #city checked after Province/State so that most specific information can be compared
                location2 = self.item2.for_city
            elif self.item2.hasCity:
                location2 = self.item2.hasCity
            elif self.item2.hasCitySection:
                location2 = self.item2.hasCitySection

            if location and location2: #both have locations
                #considering case when checking consistency between indicator (self.item1) that has a location + its population/population definition (self.item2) has a location
                if ("iso21972.Indicator" in str(parent.ancestors())) or ("cids.Indicator" in str(parent.ancestors())): 
                    population = self.item1.sumOf
                    if population:
                        definition = population[0].definedBy

                        if self.item2 == self.item1.sumOf or self.item2 == definition: #if self.item2 is self.item1's population or if self.item2 is self.item1's population's definition             
                            #compare within indicator
                            if location and location2 and location == location2:
                                print(self.item1, " is place equality consistent with ", self.item2, " - they both refer to the same location.")
                                place_equality_consistent = True
                                return place_equality_consistent
                            elif location and location2 and location != location2:
                                print(self.item1, " is not place equality consistent with ", self.item2, " due to them referring to different locations.")
                                return place_equality_consistent 

                elif ("iso21972.Indicator" in str(parent2.ancestors())) or ("cids.Indicator" in str(parent2.ancestors())): 
                    population = self.item2.sumOf
                    if population:
                        definition = population[0].definedBy

                        if self.item1 == self.item2.sumOf or self.item1 == definition: #if self.item1 is self.item2's population or if self.item1 is self.item2's population's definition             
                            #compare within indicator
                            if location and location2 and location == location2:
                                print(self.item2, " is place equality consistent with ", self.item1, " - they both refer to the same location.")
                                place_equality_consistent = True
                                return place_equality_consistent
                            elif location and location2 and location != location2:
                                print(self.item2, " is not place equality consistent with ", self.item1, " due to them referring to different locations.")
                                return place_equality_consistent  

                else: #has location but does not fulfill above indicator relationship
                    if (self.item1.hasCitySection and self.item2.hasCitySection) and location2 == self.item1.hasCitySection:
                        print(self.item1, " and ", self.item2, " refer to the same city section. Therefore they are place equality consistent.")
                        place_equality_consistent = True
                        #not returning here in case the city section name is the same but the country/province/state/city isnt
                    elif (self.item1.hasCitySection and self.item2.hasCitySection) and location2 != self.item1.hasCitySection:
                        print(self.item1, " and ", self.item2, " do not refer to the same city section. Therefore they are not place equality consistent.")
                        return place_equality_consistent
                    elif (self.item1.hasCity or self.item1.for_city) and (self.item2.hasCity or self.item2.for_city): 
                        if (self.item2.hasCity or self.item2.for_city) and ((self.item1.hasCity == self.item2.hasCity) or (self.item1.for_city == self.item2.for_city) or (self.item1.hasCity == self.item2.for_city) or (self.item1.for_city == self.item2.hasCity)):
                            print(self.item1, " and ", self.item2, " refer to the same city. Therefore they are place equality consistent.")
                            place_equality_consistent = True
                            #not returning here in case the city name is the same but the country/province/state isnt
                        else:
                            print(self.item1, " and ", self.item2, " do not refer to the same city. Therefore they are not place equality consistent.")
                            return place_equality_consistent
                    if (self.item1.hasProvince or self.item1.hasState) and (self.item2.hasProvince or self.item2.hasState):
                        if  (self.item1.hasProvince == self.item2.hasProvince or self.item1.hasState == self.item2.hasState or self.item1.hasProvince == self.item2.hasState or self.item1.hasState == self.item2.hasProvince):
                            print(self.item1, " and ", self.item2, " refer to the same province/state. Therefore they are place equality consistent.")
                            place_equality_consistent = True
                            #not returning here in case the state/province name is the same but the country isnt
                        else:
                            print(self.item1, " and ", self.item2, " do not refer to the same province/state. Therefore they are not place equality consistent.")
                            return place_equality_consistent
                    if (self.item1.hasCountry or self.item1.parentCountry) and (self.item2.hasCountry or self.item2.parentCountry):
                        if self.item1.hasCountry == self.item2.hasCountry or self.item1.parentCountry == self.item2.parentCountry or self.item1.hasCountry == self.item2.parentCountry or self.item1.parentCountry == self.item2.hasCountry:
                            print(self.item1, " and ", self.item2, " refer to the same country. Therefore they are place equality consistent.")
                            place_equality_consistent = True
                            return place_equality_consistent
                        else:
                            print(self.item1, " and ", self.item2, " do not refer to the same country. Therefore they are not place equality consistent.")
                            return place_equality_consistent

            elif not location: #self.item1 does not have a location 
                print(self.item1, " does not have a location property associated with it - place equality consistency check cannot be run.")
                return place_equality_consistent

            elif not location2: #self.item2 does not have a location 
                print(self.item2, " does not have a location property associated with it - place equality consistency check cannot be run.")
                return place_equality_consistent

            #not considering ratios
        else:
        print("Place equality consistency check not run - it is only done when comparing an instance to itself or another instance.")
        return place_equality_consistent
        

    def subplace_consistency_check(self, place_equality_consistent):
        '''
        #Any two instances mij and mik ∊ Mi are potentially subplace inconsistent if instance of placename referred by mik is an area within city referred by mij 
        #Subplace inconsistency refers to the situation where the placename referred by an instance mik is an area within the instance of mij. 
        #For example, the population measured by an indicator should be related to place instances city’i which include all areas within cityi which is referred by the indicator mij. 
        #The measure may not be complete if city’i is only an area within cityi since not all populations in cityi have been considered. 

            # city section vs city
        #   city section vs province
        #   city section vs country
        '''

        if self.item2 in self.individuals and place_equality_consistent == False:
            #self.item1
            if not self.item1.hasCitySection and (not self.item1.hasCity or not self.item1.for_city) and (not self.item1.hasProvince or not self.item1.hasState) and (not self.item1.hasCountry or not self.item1.parentCountry):
                #no location information
                print("Subplace consistency check not run - location information not available for ", self.item1, ".") 
                return
            elif self.item1.hasCitySection and self.item1.hasCity and self.item2.hasCity and not self.item2.hasCitySection and self.item1.hasCity == self.item2.hasCity:
                #self.item1 is a city section, self.item2 is not a city section, and self.item1's city is self.item2's city
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and self.item1.for_city and self.item2.for_city and not self.item2.hasCitySection and self.item1.for_city == self.item2.for_city:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and self.item1.hasCity and self.item2.for_city and not self.item2.hasCitySection and self.item1.hasCity == self.item2.for_city:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and self.item1.for_city and self.item2.hasCity and not self.item2.hasCitySection and self.item1.for_city == self.item2.hasCity:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and self.item1.hasProvince and self.item2.hasProvince and not self.item2.hasCitySection and self.item1.hasProvince == self.item2.hasProvince:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and not self.item2.hasCitySection and self.item1.hasState and self.item2.hasState and self.item1.hasState == self.item2.hasState:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and not self.item2.hasCitySection and self.item1.hasState and self.item2.hasProvince and self.item1.hasState == self.item2.hasProvince:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and not self.item2.hasCitySection and self.item1.hasProvince and self.item2.hasState and self.item1.hasProvince == self.item2.hasState:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and not self.item2.hasCitySection and self.item1.hasCountry and self.item2.hasCountry and self.item1.hasCountry == self.item2.hasCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and not self.item2.hasCitySection  and self.item1.parentCountry and self.item2.parentCountry and self.item1.parentCountry == self.item2.parentCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and not self.item2.hasCitySection and self.item1.hasCountry and self.item2.parentCountry and self.item1.hasCountry == self.item2.parentCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif self.item1.hasCitySection and not self.item2.hasCitySection and self.item1.parentCountry and self.item2.hasCountry and self.item1.parentCountry == self.item2.hasCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return

            #   city vs province
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.hasProvince and self.item2.hasProvince and self.item1.hasProvince == self.item2.hasProvince:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.hasState and self.item2.hasState and self.item1.hasState == self.item2.hasState:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.hasState and self.item2.hasProvince and self.item1.hasState == self.item2.hasProvince:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.hasProvince and self.item2.hasState and self.item1.hasProvince == self.item2.hasState:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            
            #   city vs country
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.hasCountry and self.item2.hasCountry and self.item1.hasCountry == self.item2.hasCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.parentCountry and self.item2.parentCountry and self.item1.parentCountry == self.item2.parentCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.hasCountry and self.item2.parentCountry and self.item1.hasCountry == self.item2.parentCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif (self.item1.hasCity or self.item1.for_city) and (not self.item2.hasCity or not self.item2.for_city) and self.item1.parentCountry and self.item2.hasCountry and self.item1.parentCountry == self.item2.hasCountry:
                print (self.item1, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            else: #some missing location information
                print("some location information is not available. Therefore " ,self.item1, " and ", self.item2, " are potentially inconsistent.")

            #self.item2
            if not self.item2.hasCitySection and (not self.item2.hasCity or not self.item2.for_city) and (not self.item2.hasProvince or not self.item2.hasState) and (not self.item2.hasCountry or not self.item2.parentCountry):
                #no location information
                print("Subplace consistency check not run - location information not available for ", self.item1, ".") 
                return
            elif self.item2.hasCitySection and self.item2.hasCity and self.item1.hasCity and not self.item1.hasCitySection and self.item1.hasCity == self.item2.hasCity:
                #self.item1 is a city section, self.item2 is not a city section, and self.item1's city is self.item2's city
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and self.item2.for_city and self.item1.for_city and not self.item1.hasCitySection and self.item1.for_city == self.item2.for_city:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and self.item2.hasCity and self.item1.for_city and not self.item1.hasCitySection and self.item2.hasCity == self.item1.for_city:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and self.item2.for_city and self.item1.hasCity and not self.item1.hasCitySection and self.item2.for_city == self.item1.hasCity:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and self.item2.hasProvince and self.item1.hasProvince and not self.item1.hasCitySection and self.item1.hasProvince == self.item2.hasProvince:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and not self.item1.hasCitySection and self.item2.hasState and self.item1.hasState and self.item1.hasState == self.item2.hasState:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and not self.item1.hasCitySection and self.item2.hasState and self.item1.hasProvince and self.item2.hasState == self.item1.hasProvince:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and not self.item1.hasCitySection and self.item2.hasProvince and self.item1.hasState and self.item2.hasProvince == self.item1.hasState:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and not self.item1.hasCitySection and self.item2.hasCountry and self.item1.hasCountry and self.item1.hasCountry == self.item2.hasCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and not self.item1.hasCitySection  and self.item2.parentCountry and self.item1.parentCountry and self.item1.parentCountry == self.item2.parentCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and not self.item1.hasCitySection and self.item2.hasCountry and self.item1.parentCountry and self.item2.hasCountry == self.item1.parentCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif self.item2.hasCitySection and not self.item1.hasCitySection and self.item2.parentCountry and self.item1.hasCountry and self.item2.parentCountry == self.item1.hasCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return

            #   city vs province
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item2.hasProvince and self.item1.hasProvince and self.item1.hasProvince == self.item2.hasProvince:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item2.hasState and self.item1.hasState and self.item1.hasState == self.item2.hasState:
                print (self.item2, " is a subplace of ", self.item2, " therefore they are not subplace consistent.")
                return
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item2.hasState and self.item1.hasProvince and self.item2.hasState == self.item1.hasProvince:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item2.hasProvince and self.item1.hasState and self.item2.hasProvince == self.item1.hasState:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            
            #   city vs country
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item1.hasCountry and self.item2.hasCountry and self.item1.hasCountry == self.item2.hasCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item1.parentCountry and self.item2.parentCountry and self.item1.parentCountry == self.item2.parentCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item2.hasCountry and self.item1.parentCountry and self.item2.hasCountry == self.item1.parentCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            elif (self.item2.hasCity or self.item2.for_city) and (not self.item1.hasCity or not self.item1.for_city) and self.item2.parentCountry and self.item1.hasCountry and self.item2.parentCountry == self.item1.hasCountry:
                print (self.item2, " is a subplace of ", self.item1, " therefore they are not subplace consistent.")
                return
            else: #some missing location information
                print("some location information is not available. Therefore " ,self.item2, " and ", self.item1, " are potentially inconsistent.")

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
