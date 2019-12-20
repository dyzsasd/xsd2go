class Element(object):
    def __init__(self, name, _type, is_attribute=False, ns=None,
                 is_array=False, min_occr=0, max_occr=1, docs=None):
        self.name = name
        self.type = _type
        self.is_attribute = is_attribute
        self.is_array = is_array
        self.min_occr = min_occr
        self.max_occr = max_occr
        self.ns = ns
        self.docs = docs
