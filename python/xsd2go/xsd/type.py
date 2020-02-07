from copy import deepcopy

from .util import parse_attrib_value, parse_tag, parse_ref_value


class BaseType(object):
    def __init__(self, name, ns, docs=None):
        self.name = name
        self.ns = ns
        self.doc = None

    def parse(self, schema):
        raise NotImplementedError(
            "parse method not implemented in %s" % self.__class__)

        
class Extension(object):
    def __init__(self, base, element_collection, attribute_collection):
        self.base = base
        self.base_type_instance = None
        self.element_collection = element_collection
        self.attribute_collection = attribute_collection

    def parse(self, schema):
        if self.base_type_instance is None:
            ns_tag, type_tag = parse_attrib_value(self.base)
            if ns_tag is not None and schema.nsmap[ns_tag] == schema.nsmap['xsd']:
                self.base_type_instance = name2base_class[type_tag]()
            else:
                self.base_type_instance = schema.get_type_instance(self.base)
                self.base_type_instance.parse(schema)
        if self.element_collection:
            self.element_collection.parse()
        if self.attribute_collection:
            self.attribute_collection.parse()


class Restriction(object):
    def __init__(self, base, element_collection, attribute_collection, kwargs):
        self.base = base
        self.base_type_instance = None
        self.element_collection = element_collection
        self.attribute_collection = attribute_collection
        self.kwargs = kwargs

    def parse(self, schema):
        if self.base_type_instance is None:
            ns_tag, type_tag = parse_attrib_value(self.base)
            if ns_tag is not None and schema.nsmap[ns_tag] == schema.nsmap['xsd']:
                self.base_type_instance = name2base_class[type_tag]()
            else:
                self.base_type_instance = schema.get_type_instance(self.base)
                self.base_type_instance.parse(schema)


class ComplexTypeContent(object):
    def __init__(self, content_type, restriction, extension):
        self.content_type = content_type

        self.restriction = restriction
        self.extension = extension
        if (self.restriction is None) == (self.extension is None):
            raise RuntimeError(
                "Invalid value of restriction and extension in simple content",
                self.restriction, self.extension
            )

    def parse(self, schema):
        if self.restriction:
            self.restriction.parse(schema)
        if self.extension:
            self.extension.parse(schema)


class ComplexType(BaseType):
    def __init__(self, name, ns, element_collection, attribute_collection,
                 complex_type_content=None):
        super(ComplexType, self).__init__(name, ns)
        self.element_collection = element_collection
        self.attribute_collection = attribute_collection

        self.complex_type_content = complex_type_content

    def parse(self, schema):
        if self.element_collection:
            self.element_collection.parse(schema)
        if self.attribute_collection:
            self.attribute_collection.parse(schema)
        if self.complex_type_content:
            self.complex_type_content.parse(schema)
    


class UnionSimpleType(BaseType):
    def __init__(self, name, ns, member_type_names):
        super(UnionSimpleType, self).__init__(name, ns)
        self.member_type_names = member_type_names
        self.member_types = None

    def parse(self, schema):
        if self.member_types:
            return
        
        self.member_types = []
        for type_name in self.member_type_names:
            type_instance = schema.get_type_instance(type_name)
            type_instance.parse(schema)
            self.member_types.append(type_instance)

    
class ExtendedSimpleType(BaseType):
    def __init__(self, name, ns, base_type_name, kwargs):
        super(ExtendedSimpleType, self).__init__(name, ns)
        self.base_type_name = base_type_name
        self.kwargs = kwargs
        self.type_instance = None

    def parse(self, schema):
        self.type_instance = deepcopy(
            schema.get_type_instance(self.base_type_name))
        for k, v in self.kwargs.items():
            setattr(self.type_instance, k, v)



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
    
    def parse(self, schema):
        pass


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
    
    def parse(self, schema):
        pass


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

    def parse(self, schema):
        pass


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

    def parse(self, schema):
        pass

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

    def parse(self, schema):
        pass


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