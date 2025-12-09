class IncompleteData(Exception):
    """Raised when trying to deserialise a data value with less bytes than needed"""