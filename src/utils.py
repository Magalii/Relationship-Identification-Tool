import pandas as pd
import csv
import numpy as np

def parse_val(val):
    '''Parse string value and change it to appropriate type to be manipulated by RuleSet functions
        Accepted formats: "false" and "true" case insensitive, 'nan', '', "*", string representation of pandas.Interval
    '''
    #TODO Add more tests for this function (for 'nan' and, float)
    if val == '' or val == '*' or val.lower() == 'nan': return float('nan')
    elif val[0] == '(' or val[0] == '[' or val[0] == ']':
        return parse_interval(val)
    elif val.lower() == 'false': return False
    elif val.lower() == 'true': return True
    else:
        try:
            new_val = float(val)
            return new_val
        except ValueError:
            raise ValueError("Value given doesn't have appropriate format: " + str(val))

def parse_interval(val):
    #get characteristics of interval (closed on the left-side, right-side, both or neither)
    leftClosed = val[0] == '['
    if not leftClosed and not (val[0] == '(' or val[0] == ']'):
        raise ValueError("Value given doesn't have the proper format for a pandas.Interval: " + str(val))
    rightClosed = val[len(val)-1] == ']'
    if not rightClosed and not (val[len(val)-1] == ')' or val[len(val)-1] == '['):
        raise ValueError("Value given doesn't have the proper format for a pandas.Interval: " + str(val))
    if leftClosed and rightClosed: closed = 'both'
    elif leftClosed and not rightClosed: closed = 'left'
    elif not leftClosed and rightClosed: closed = 'right'
    else: closed = 'neither'
    #get left value
    left_str = ''
    i = 1
    while val[i] is not ',':
        left_str += val[i]
        i+=1
        if i==len(val):
            raise ValueError("Value given doesn't have the proper format for a pandas.Interval: " + str(val)+ ". A comma is missing.")
    try:
        left_val = float(left_str)
    except ValueError:
        raise ValueError("Value given doesn't have the proper format for a pandas.Interval: " + str(val))
    #get right value
    right_str = ''
    i += 1
    if val[i] == ' ': i+= 1 #skip the space that follows the comma if there is one
    for j in range(i,len(val)-1):
        right_str += val[j]
    try:
        right_val = float(right_str)
    except ValueError:
        raise ValueError("Value given doesn't have the proper format for pandas.Interval: " + str(val))
    return pd.Interval(left_val, right_val, closed)

def parse_csv(csv_name):
    #TODO Check that values in one column all have the same type
    ''' Parse csv and returns list of dictionnaries representing the rules'''
    rules = []
    with open(csv_name, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        #print(reader)
        for r in reader:
            #print(r)
            for key, val in r.items():
                if not key == "Rec" and not key == "Recommendation": #TODO Avoid parsing recommendation without hardcoding column name
                    #print("key: " + str(key) + " val: " + str(val))
                    if isinstance(val,str):
                        try:
                            r[key] = float(val)
                        except ValueError:
                            #print(" Error is being handled for value " + str(val))
                            r[key] = parse_val(val)
                    else:
                        print("value " + str(val) + " is not a string") #TODO This if string else is momentary for debug
            rules.append(r)
    return rules

def same_type(val1,val2):
    ''' Redefine same type relationships to ignore difference between numpy and regular types '''
    if type(val1) == type(val2):
        return True
    elif (isinstance(val1,np.bool_) and isinstance(val2,bool)) or (isinstance(val1,bool) and isinstance(val2,np.bool_)):
        return True
    elif (isinstance(val1,np.float64) and isinstance(val2,float)) or (isinstance(val1,float) and isinstance(val2,np.float64)):
        return True
    else:
        return False
'''
csv_name1 = "data/RuleSetSmall.csv"
csv_name2 = "data/saved_ruleset.csv"
csv_name3 = "data/RuleSetWeSmartAdapted.csv"

rules = parse_csv(csv_name3)

rule_set = pd.DataFrame(rules)
print("Rule set:")
print(rule_set)
'''

'''
print(rule_set.iloc[0,1])
print(type(rule_set.iloc[0,1]))
print(rule_set.iloc[0,3])
print(type(rule_set.iloc[0,3]))
'''


'''
setRead = pd.read_csv(csv_name2)
print(setRead)
print(type(setRead))
print(setRead.iloc[1,3])
print(type(setRead.iloc[1,3]))
print(setRead.iloc[0,2])
print(type(setRead.iloc[0,2]))

'''

