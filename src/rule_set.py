import numpy as np
import pandas as pd

from relation import *
from connection import *

class RuleSet:
    #############################
    # Methods to build rule set #
    #############################
    def __init__(self,rules_list):
        ''' @rules_list: list of ordered dictionnaries each representing a rule with their attributes as keys'''
        self.set = pd.DataFrame(rules_list)
        if len(rules_list) > 0:
            self.m = len(rules_list[0]) #number of attributes (considering the recommendation)
        else:
             self.m = 0
        self.n = len(rules_list) #number of rules
        self.idm = np.empty(0) #Inter-Difference Matrix
        self.pm = np.empty(0) #Product Matrix (holds products of IDC for each pair of rules)
        self.attr_names = self.set.columns.tolist()

    def build_IDM(self):
        if self.n > 1: #needs at least two rules to compare them
            self.idm = np.zeros((self.m, self.n, self.n))
            #fill in IDC's for all attributes relationships
            for k in range(1,self.m):
                for i in range(self.n):
                    for j in range(i+1,self.n):
                        self.idm[k,i,j] = self._val_IDC(self.set.iloc[i,k],self.set.iloc[j,k])
            #fill in IDC's for recommendation relationships
            for i in range(self.n):
                for j in range(i+1,self.n):
                    self.idm[0,i,j] = self._rec_IDC(self.set.iloc[i,0],self.set.iloc[j,0])
    
    def build_PM(self):
        if(len(self.idm) > 0):
            self.pm = np.prod(self.idm,axis=0)
            return True
        else:
            return False

    # Helper methods to build rule set
    def _val_IDC(self, val1, val2):
        #Check for nan values
        if pd.isna(val1) and pd.isna(val2):
            return Relation.EQUALITY.value  #val1 and val2 are both nan
        elif pd.isna(val1): # and not pd.isna(val2):
            return Relation.INCLUSION_JI.value #val1 is nan and val2 is included in it
        elif pd.isna(val2):
            return Relation.INCLUSION_IJ.value #val2 is nan and val1 is included in it
        #check for type mismatch
        elif not self.same_type(val1,val2):  
            raise TypeError("val1 and val2 should have the same type when neither of them are NaN. val1: "+str(type(val1))+str(val1) + " val2: "+str(type(val2))+str(val2))
        #Both values are valid (not nan) and have the same type
        elif isinstance(val1,pd.Interval):
            return self._intervals_IDC_(val1,val2)
        else:
            if val1 == val2:
                return Relation.EQUALITY.value
            else:
                return Relation.DIFFERENCE.value

    def _intervals_IDC_(self,val1,val2):
        INCL_IJ = Relation.INCLUSION_IJ.value
        INCL_JI = Relation.INCLUSION_JI.value
        if val1.left > val2.left:
            val = val1; val1 = val2; val2 = val
            INCL_IJ = Relation.INCLUSION_JI.value
            INCL_JI = Relation.INCLUSION_IJ.value
        #val1.left <= val2.left
        if not val1.overlaps(val2):
            return Relation.DIFFERENCE.value
        else:
            if val1.left == val2.left:
                if val1.right == val2.right:
                    if val1.closed == val2.closed:
                        #print('c')
                        return Relation.EQUALITY.value # a,b a,b
                    elif self._isclosed(val1,'left') and self._isclosed(val1,'right'):
                        #print('d')
                        return INCL_JI #val1 = [a,b], val2 included
                    elif self._isclosed(val2,'left') and self._isclosed(val2,'right'):
                        #print('e')
                        return INCL_IJ #val2 = [a,b], val1 included
                    elif not self._isclosed(val1,'left') and not self._isclosed(val1,'right'):
                        #print('f')
                        return INCL_IJ #val1 = (a,b), val1 included
                    elif not self._isclosed(val2,'left') and not self._isclosed(val2,'right'):
                        #print('g')
                        return INCL_JI #val2 = (a,b), val2 included
                    else:
                        #print('h')
                        return Relation.OVERLAP.value # (a,b] [a,b)                        
                else:
                    if not (self._isclosed(val1,'left') == self._isclosed(val2,'left')):
                            #print('m')
                            return Relation.OVERLAP.value # (a,b [a,c with c > b
                    else:
                        if val1.right < val2.right:
                            #print('i')
                            return INCL_IJ #a,b a,c with b < c
                        else:
                            #print('j')
                            return INCL_JI #a,b a,c with b > c
            #val1.left < val2.left                
            elif val1.right >= val2.right:
                #print('k')
                return INCL_JI
            else:
                #print('l')
                return Relation.OVERLAP.value

    def _isclosed(self,inter,side):
        ''' Return true if interval 'inter' is closed on side 'side', False if it is open on that side
            @inter: an interval pandas.Interval
            @side: 'left', 'right', 'both' or 'neither'
        '''
        if inter.closed == side or inter.closed == 'both':
            return True
        else:
            return False   

    def _rec_IDC(self, rec1, rec2):
        if(rec1 == rec2):
            return Relation.SAME_REC.value
        else:
            return Relation.DIFF_REC.value

    #############################################
    # Methods to get information about rule set #
    #############################################

    def get_val(self,rule,attr):
        ''' returns the value that 'rule' has for attribute 'attr'
            @rule: index of the rule (int)
            @attr: either index (int) or name (str) of the attribute 
        '''
        if type(rule) is not int or rule < 0 or rule >= self.n:
            raise ValueError("'rule' must be an integer in [0,"+str(self.n-1)+"]")
        if type(attr) is str:
            if attr not in self.attr_names:
                raise ValueError("Attribute given doesn't exist. attr="+attr)
            return self.set[attr][rule]
        elif type(attr) is int and attr >= 0 and attr < self.m:
            #print("set before set.iloc:")
            #print(self.set)
            return self.set.iloc[rule,attr]
        else:
            raise ValueError("'attr' must be either an integer in [0,"+str(self.m-1)+"] or an existing attribute name")

    def connection(self, r1, r2):
        ''' Returns the Relation enum that corresponds to the relation between rules with indexes 'r1' and 'r2'
            or the enum ERROR if the PM matrix hasn't been built yet
            rules indexes start at 0; r1 and r2 may be given in any order
        '''
        if len(self.pm) == 0: #build_PM needs to be called to create PM matrix
            return Connection.ERROR
        elif r1 >= self.n or r2 >= self.n:
            raise ValueError("indexes given for connections are too high r1:"+str(r1)+" r2:"+str(r1)+" maxVal:"+str(self.n-1))
        else:
            if r1 == r2:
                return Connection.REFERENCE
            if r1 > r2:
                r = r1; r1 = r2; r2 = r
            p = self.pm[r1][r2]
            #print("r1: "+str(r1)+" r2: "+str(r2)+" p: "+str(p))
            if p == Relation.DIFFERENCE.value: return Connection.DISCONNECTED
            elif p == Relation.EQUALITY.value : return Connection.EQUAL_SAME
            elif p == -Relation.EQUALITY.value : return Connection.EQUAL_DIFF
            elif p % Relation.OVERLAP.value == 0 and p > 0: return Connection.OVERLAP_SAME
            elif p % Relation.OVERLAP.value == 0 and p < 0 : return Connection.OVERLAP_DIFF
            elif (p % Relation.INCLUSION_IJ.value == 0 or p % Relation.INCLUSION_JI.value == 0) and p*Relation.SAME_REC.value > 0 : return Connection.INCLUSION_SAME
            elif (p % Relation.INCLUSION_IJ.value == 0 or p % Relation.INCLUSION_JI.value == 0) and p*Relation.DIFF_REC.value > 0 : return Connection.INCLUSION_DIFF
            else:
                raise ValueError("pm has illegal value at indices ["+str(r1)+","+str(r2)+']')

    def same_type(self,val1,val2):
        ''' Redefine same type relationships to ignore difference between numpy and regular types '''
        if type(val1) == type(val2):
            return True
        elif (isinstance(val1,np.bool_) and isinstance(val2,bool)) or (isinstance(val1,bool) and isinstance(val2,np.bool_)):
            return True
        elif (isinstance(val1,np.float64) and isinstance(val2,float)) or (isinstance(val1,float) and isinstance(val2,np.float64)):
            return True
        else:
            return False
    
    def has_type(self,val,checked_type):
        if isinstance(val,checked_type):
            return True
        elif ((checked_type == bool) and isinstance(val,np.bool_)) or ((checked_type == np.bool_) and isinstance(val,bool)):
            return True
        elif ((checked_type == float) and isinstance(val,np.float64)) or ((checked_type == np.float64) and isinstance(val,float)):
            return True
        else:
            return False

    def __str__(self):
        header = "Rules in set:\n"
        size = "AttributeNbr: " + str(self.m) + "RulesNbr: " + str(self.n) + "\n"
        return header + str(self.set)

    ###############################
    # Methods to modifiy rule set #
    ###############################

    def recompute_m(self):
        ''' recompute the matrix idm and pm if they already exist'''
        if len(self.idm) > 0:
                self.build_IDM()
                if len(self.pm) > 0:
                    self.build_PM()

    def update_idm(self,rule,attr):
        if len(self.idm) > 0:
            #update idm
            for i in range(self.n):
                #update of regular value
                if attr > 0 and i < rule:
                    self.idm[attr,i,rule] = self._val_IDC(self.set.iloc[i,attr],self.set.iloc[rule,attr])
                elif attr > 0 and i > rule:
                    self.idm[attr,rule,i] = self._val_IDC(self.set.iloc[rule,attr],self.set.iloc[i,attr])
                #update of recommendation
                if attr == 0 and i < rule:
                    self.idm[attr,i,rule] = self._rec_IDC(self.set.iloc[i,attr],self.set.iloc[rule,attr])
                elif attr == 0 and i > rule:
                    #print("update_idm : i="+str(i)+" attr="+str(attr)+"rule="+str(rule)+str(self.n))
                    #print("-- set in update_idm --")
                    #print(self.set)
                    #print("-- ism in update_idm --")
                    #print(self.idm)
                    self.idm[attr,rule,i] = self._rec_IDC(self.set.iloc[i,attr],self.set.iloc[rule,attr])
    
    def update_pm(self,rule):
        if len(self.pm) > 0:
            #update pm
            self.pm[rule,:] = np.prod(self.idm[:,rule,:],axis=0)
            self.pm[:,rule] = np.prod(self.idm[:,:,rule],axis=0)

    def update_val(self, rule, attr, val, update=True):
        ''' Update value of an attribute by setting value in position [rule,attr] in de DataFrame rules to value val
            if update = True, recompute self.idm and self.pm, leave them unchanged otherwise
            rule and attr must be int with rule < n and 0 <attr < m
            val must either be nan or have the same type as the rest of the values in the column
            (No checks are performed on val for performance reasons)
            (Method designed for attributes and not for the recommendation)
        '''
        if attr >= self.m or rule >= self.n:
            raise ValueError("Index condition not respected: rule ("+str(rule)+") must be lower than "+str(self.n)+" and attr ("+str(attr)+") must be lower than "+str(self.m))
        self.set.iloc[rule,attr] = val
        if update:
            self.update_idm(rule,attr)
            self.update_pm(rule)
            
    def update_attr(self,attr_list):
        ''' update attr by giving a new attr list
         '''
        for i in range(len(attr_list)):
            if attr_list[i] == '':
                raise ValueError("Attribute name cannot be an empty string.")
            for j in range(i+1,len(attr_list)):
                if attr_list[i] == attr_list[j]:
                    raise ValueError("Two attributes can't have the same name.")
        if attr_list[0] != 'Rec' and attr_list[0] != 'Recommendation':
            raise ValueError("First column must have name 'Rec' or 'Recommendation")
        self.set.columns = attr_list
        self.attr_names = attr_list
    
    '''
    def update_attr(self,new_attr,position):
        if new_attr in self.attr_names and new_attr!=self.attr_names[position]:
            raise ValueError("New attribute name can't be the same as an already existing one.")
        if position == 0 and (new_attr == 'Rec' or new_attr == 'Recommendation'):
            raise ValueError("First column must have name 'Rec' or 'Recommendation")
        self.attr_names[position] = new_attr
        self.set.columns = self.attr_names
    '''
   
    def add_attr(self,attr_name,val_list=None):
        ''' @val_list: list containing the value of that attribute for each rule
            verification of correct type is not guaranteed because is only done if idm > 0
        '''
        if self.n == 0:
            raise ValueError("Cannot add attribute to empty ruleset. Add a rule first.")
        if attr_name == '':
                raise ValueError("Attribute name cannot be an empty string.")
        if attr_name in self.attr_names:
            raise ValueError("The new attribute name must not already be used. Error with attr_name="+str(attr_name))
        if val_list is None:
            self.set[attr_name] = pd.Series(float('nan'),index=range(self.n))
            #new idm layer for this attr has 1's for all rules since all values are the same
            if len(self.idm) > 0:
                new_idm_layer = np.zeros((1,self.n,self.n))
                for i in range(1,self.n):
                    for j in range(i+1,self.n):
                        new_idm_layer[0,i,j] = 1
                self.idm = np.concatenate((self.idm,new_idm_layer))
            #No changes to pm needed since all new values are one's
        else:
            if len(val_list) != self.n:
                raise ValueError("Length of list value ("+str(len(val_list))+") must be equal to number of rules ("+str(self.n)+")")
            self.set[attr_name] = pd.Series(val_list)
            #build new idm layer and add it to idm
            if len(self.idm) > 0:
                new_idm_layer = np.zeros((1,self.n,self.n))
                for i in range(0,self.n):
                    for j in range(i+1,self.n):
                        try:
                            new_idm_layer[0,i,j] = self._val_IDC(self.set[attr_name][i],self.set[attr_name][j])
                        except TypeError:
                            raise TypeError("New attribute contains values with different types.")
                self.idm = np.concatenate((self.idm,new_idm_layer))
                #recompute pm
                if len(self.pm) > 0:
                    self.build_PM()        
        self.m += 1
        self.attr_names = self.set.columns.tolist()
    
    def add_rule(self,rec,val_list=None):
        ''' @val_list: list containing the values for all attributes of this rule (recommendation excluded)
            verification of correct type is not guaranteed because is only done if idm > 0
        '''
        if self.n == 0:
            names = ['Recommendation']
            values = [rec]
            if val_list is not None:
                for i in range(len(val_list)):
                    names += ['Attr '+str(i+1)]
                values = [rec] + val_list
            rule_dict = {k:v for k,v in zip(names,values)}
            self.set = pd.DataFrame([rule_dict])[names]
            self.m = len(names)
            self.n = 1
            self.attr_names = names
        else:
            old_n = self.n
            new_n = self.n+1
            self.n += 1 #update needs to be done before call to update_idm()
            if val_list == None:
                rule = pd.DataFrame(None,index=[old_n])
                self.set = pd.concat([self.set,rule],sort=False)
                self.set.iloc[old_n,0] = rec
            else:
                if len(val_list) != self.m-1:
                    self.n = old_n
                    raise ValueError("The number of values given ("+str(len(val_list))+") is not the same as the number of attributes ("+str(self.m-1)+").")
                keys = self.attr_names
                values = [rec] + val_list
                val_dict = {k:v for k,v in zip(keys,values)}
                rule = pd.DataFrame(val_dict,index=[old_n])
                self.set = pd.concat([self.set,rule],sort=False)
            #add new rows and columns to idm
            if len(self.idm) > 0:
                rows = np.zeros((self.m,1,old_n))
                self.idm = np.concatenate((self.idm,rows),axis=1)
                cols = np.zeros((self.m,old_n+1,1))
                self.idm = np.concatenate((self.idm,cols),axis=2)
                for attr in range(self.m):
                    try:
                        #print("-- ruleset--")
                        #print(self.set)
                        #print("i: "+str(old_n)+" attr: "+str(attr))
                        #print("-- idm --")
                        #print(self.idm)
                        #print()
                        self.update_idm(old_n,attr)
                    except TypeError:
                        self.n = old_n
                        raise TypeError("New rule contains value with inadequate type.")
                #add new rows and columns in pm
                if len(self.pm) > 0:
                    rows = np.zeros((old_n,1))
                    self.pm = np.concatenate((self.pm,rows),axis=1)
                    cols = np.zeros((1,old_n+1))
                    self.pm = np.concatenate((self.pm,cols),axis=0)
                    self.pm[:,old_n] = np.prod(self.idm[:,:,old_n],axis=0)

    def delete_attr(self,attr):
        if attr == 0 or attr == 'Rec' or attr == 'Recommendation':
            raise ValueError("Recommendation cannot be deleted from ruleset")
        if isinstance(attr,int):
            if attr < 0 or attr >= self.m:
                raise ValueError("The recommendation index for deletion has to be in [1,"+str(self.m-1)+"]. attr="+str(attr))
            else:
                index = attr
                name = self.attr_names[attr]
        else:
            if attr not in self.attr_names:
                raise ValueError("The recommendation given for deletion ("+str(attr)+"is not found in the ruleset.")
            else:
                index = self.attr_names.index(attr)
                name = attr
        del self.set[name]
        self.attr_names = self.set.columns.tolist()
        self.m -= 1 #has to be before update of idm
        if len(self.idm) > 0:
            self.idm = np.delete(self.idm,index,axis=0)
            if len(self.pm) > 0:
                self.build_PM()

    def delete_rule(self,rule):
        '''  '''
        if rule < 0 or rule >= self.n:
            raise ValueError("The rule index for deletion has to be in [0,"+str(self.m-1)+"]. rule="+str(rule))
        self.n -= 1 #has to be before update of set indexes
        new_set = self.set.drop(rule)
        self.set = new_set
        new_set.index = range(self.n)
        if len(self.idm) > 0:
            if self.n > 1: #needs at least two rules to compare them in idm and pm
                temp_idm = np.delete(self.idm,rule,axis=1)
                self.idm = np.delete(temp_idm,rule,axis=2)
                if len(self.pm) > 0:
                    temp_pm = np.delete(self.pm,rule,axis=0)
                    self.pm = np.delete(temp_pm,rule,axis=1)
            else:
                self.idm = np.empty(0)
                self.pm = np.empty(0)
                
    
    def to_csv(self,file_name):
        self.set.to_csv(file_name,index=False)

    
    