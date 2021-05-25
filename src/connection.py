from enum import Enum

class Connection(Enum):
    DISCONNECTED = "disconnected"
    EQUAL_DIFF = "cover equality"
    EQUAL_SAME = "rule equality"
    INCLUSION_DIFF = "cover inclusion"
    INCLUSION_SAME = "rule inclusion"
    OVERLAP_DIFF = "cover overlap"
    OVERLAP_SAME = "rule overlap"
    ERROR = "must build pm matrix"
    REFERENCE = "reference"