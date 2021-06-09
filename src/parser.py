import pandas as pd
import csv
import numpy as np

def parse_val(val):
    '''Parse string value and change it to appropriate type to be manipulated by RuleSet functions
        Accepted formats: "false" and "true" case insensitive, 'nan', '', "*", string representation of pandas.Interval
    '''
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
    #Possible to improve this function by checking that values in one column all have the same type
    ''' Parse csv and returns list of dictionnaries representing the rules'''
    rules = []
    with open(csv_name, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for r in reader:
            for key, val in r.items():
                if not key == "Rec" and not key == "Recommendation":
                    if isinstance(val,str):
                        try:
                            r[key] = float(val)
                        except ValueError:
                            r[key] = parse_val(val)
            rules.append(r)
    return rules


