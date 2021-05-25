from enum import Enum

class Relation(Enum):
    DIFFERENCE = 0
    EQUALITY = 1
    INCLUSION_IJ = 2 #val1 is included in val2 #must be prime number
    INCLUSION_JI = 3 #val2 is included in val1 #must be prime number
    OVERLAP = 6 #Overlap must equal INCLUSION_IJ*INCLUSION_JI
    SAME_REC = 1
    DIFF_REC = -1
    #SAME_REC and DIFF_REC must have opposite signe and have absolute value of 1