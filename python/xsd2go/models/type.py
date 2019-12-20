class BaseType(object):
    def __init__(self, name, ns, docs=None):
        self.name = name
        self.ns = ns
        self.doc = None


class ComplexType(BaseType):
    def __init__(self, name, ns, elements, base=None):
        super(ComplexType, self).__init__(name, ns)
        self.elements = elements or []
        self.base = base
        self.indicator = None


class String(BaseType):
    def __init__(self, ns=None, enumeration=None, length=None, maxLength=None,
                 minLength=None, pattern=None, whiteSpace=None):
        super(String, self).__init__("string", ns)
        self.enumeration = enumeration
        self.length = length
        self.maxLength = maxLength
        self.minLength = minLength
        self.pattern = pattern
        self.whiteSpace = whiteSpace


class Decimal(BaseType):
    def __init__(self, ns=None, enumeration=None, fractionDigits=None,
                 maxExclusive=None, maxInclusive=None, minExclusive=None,
                 minInclusive=None, pattern=None, totalDigits=None,
                 whiteSpace=None):
        super(Decimal, self).__init__("float32", ns)
        self.enumeration = enumeration
        self.fractionDigits = fractionDigits
        self.maxExclusive = maxExclusive
        self.maxInclusive = maxInclusive
        self.minExclusive = minExclusive
        self.minInclusive = minInclusive
        self.pattern = pattern
        self.totalDigits = totalDigits
        self.whiteSpace = whiteSpace


class Integer(BaseType):
    def __init__(self, ns=None, enumeration=None, fractionDigits=None,
                 maxExclusive=None, maxInclusive=None, minExclusive=None,
                 minInclusive=None, pattern=None, totalDigits=None,
                 whiteSpace=None):
        super(Integer, self).__init__("int", ns)
        self.enumeration = enumeration
        self.fractionDigits = fractionDigits
        self.maxExclusive = maxExclusive
        self.maxInclusive = maxInclusive
        self.minExclusive = minExclusive
        self.minInclusive = minInclusive
        self.pattern = pattern
        self.totalDigits = totalDigits
        self.whiteSpace = whiteSpace


class Boolean(BaseType):
    def __init__(self, ns=None):
        super(Boolean, self).__init__("boolean", ns)


class DateTime(BaseType):
    def __init__(self, ns=None, enumeration=None, maxExclusive=None,
                 maxInclusive=None, minExclusive=None, minInclusive=None, 
                 pattern=None, whiteSpace=None):
        super(DateTime, self).__init__("string", ns)
        self.enumeration = enumeration
        self.maxExclusive = maxExclusive
        self.maxInclusive = maxInclusive
        self.minExclusive = minExclusive
        self.minInclusive = minInclusive
        self.pattern = pattern
        self.whiteSpace = whiteSpace

class Duration(BaseType):
    def __init__(self, ns=None, enumeration=None, maxExclusive=None,
                 maxInclusive=None, minExclusive=None, minInclusive=None, 
                 pattern=None, whiteSpace=None):
        super(Duration, self).__init__("string", ns)
        self.enumeration = enumeration
        self.maxExclusive = maxExclusive
        self.maxInclusive = maxInclusive
        self.minExclusive = minExclusive
        self.minInclusive = minInclusive
        self.pattern = pattern
        self.whiteSpace = whiteSpace


name2base_class = {
    "ENTITIES": String,
    "ENTITY": String,
    "ID": String,
    "IDREF": String,
    "IDREFS": String,
    "Name": String,
    "NCName": String,
    "NMTOKEN": String,
    "NMTOKENS": String,
    "normalizedString": String,
    "QName": String,
    "string": String,
    "token": String,

    "date": DateTime,
    "dateTime": DateTime,
    "duration": DateTime,
    "gDay": DateTime,
    "gMonth": DateTime,
    "gMonthDay": DateTime,
    "gYear": DateTime,
    "gYearMonth": DateTime,
    "time": DateTime,

    "byte": Integer,
    "decimal": Decimal,
    "int": Integer,
    "integer": Integer,
    "long": Integer,
    "negativeInteger": Integer,
    "nonNegativeInteger": Integer,
    "nonPositiveInteger": Integer,
    "positiveInteger": Integer,
    "short": Integer,
    "unsignedLong": Integer,
    "unsignedInt": Integer,
    "unsignedShort": Integer,
    "unsignedByte": Integer,

    "boolean": Boolean,
    "base64Binary": String,
    "hexBinary": String,
    "anyURI": String,
    "double": Decimal,
    "float": Decimal,
}