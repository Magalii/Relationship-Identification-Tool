# Relationship Identification Tool
This tool was created as part of my master thesis to manage a set of rules so it can later be used in a rule-based expert system.
It allows for the management of the rule set by modification, addition or deletion of rules. The main feature is to allow to visualize the potential connections between the different rules so the user can see which different rules could apply to the same situation.

## Rules format
The rules have to correspond to a set of attributes and values. The first attribute has to be 'Recommendation' or 'Rec' and its value is a string that formulates the recommendation associated to that rule. Other attributes can be any string and their values has to be an interval, a float or a boolean. Attribute values can also be left empty or be given the wild card '\*' and are then considered as 'Any value possible'.

Rules can be encoded directly into the tool through the GUI or they can be stored in a csv file then loaded into the tool. In the latter case, rules are encoded in rows and attributes in columns. The first row is reserved for the attributes names. Examples of ruleset stored in csv files with proper format can be found the file 'data'.

### Boolean
Must be encoded with "false" or "true", cases are ignored

### Numbers
Units and decimals must be seperated with a dot

### Unspecified value
An unspecied value can be considered to be the set of all possible values or the absence of constraint  
Can be encoded as en empty field, the character '\*' or the string "nan" with cases ignored

### Intervals
The left number must be lower or equal than the right number  
The left brace must be '\[' if it is closed and can be '(' or '\]' if it is open  
The right brace must be '\]' if it is closed and can be ')' or '\[' if it is open  
Number must be seperated by a comma, which be followed by one optional space

## Run the program
To run the visual interface, you have to run the program "src/gui.py"  
To run the tests, you have to run the program "src/tests.py"
Python packages required: numpy, pysimplegui  
PySimpleGui can be install with one of the following commands:  
$ pip install pysimplegui  
$ conda install -c conda-forge pysimplegui  
$ conda install -c conda-forge/label/cf202003 pysimplegui  
### *WARNING*  
This program was written in Python 3.7. It doesn't provide guarantee to work properly with other Python version. In particular, errors have been detected with Python 3.9 for some Numpy functions. No errors have been detected with Python 3.8.
