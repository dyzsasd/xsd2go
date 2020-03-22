from cached_property import cached_property

from xsd2go.constants import XSD_NS
from xsd2go.xsd.util import parse_ref_value, parse_tag

from .base import Node
from xsd2go.xsd_go_type import xsd2go_type



# class TypeDecorator(Node):
#     def wrapped_type(self):
#         raise NotImplementedError(
#             "Method `wrapped_type` isn't implemented in class %s" % self.__class__)

#     def _parse(self):
#         from .simple_type import SimpleType

#         self.nested_type = None
#         simple_type_nodes = self.node.xpath(
#             "xsd:simpleType",
#             namespaces=self.schema.nsmap
#         )

#         if simple_type_nodes:
#             self.nested_type = SimpleType(self.schema, simple_type_nodes[0])


# class Restriction(TypeDecorator):
#     @cached_property
#     def wrapped_type(self):
#         if hasattr(self, "nested_type") is not None:
#             return self.nested_type

#         base_type_name, base_type_ns = parse_ref_value(
#             self.node.attrib['base'], self.schema.nsmap)
#         if base_type_ns == self.schema.nsmap[XSD_NS]:
#             return name2base_class[base_type_name]()
#         else:
#             refered_type_instance = self.schema.get_type_instance(
#                 base_type_name, base_type_ns)
#             if refered_type_instance is None:
#                 raise RuntimeError(
#                     "Cannot find ref type for %s" % self.tostring())
#             else:
#                 return refered_type_instance
        

class SimpleTypeRestriction(Node):
    "Restriction element nested in simple type"
    # TODO: ADD restriction parsing for msg validation
    def type_name(self):
        base_type_name, base_type_ns = parse_ref_value(
            self.node.attrib['base'], self.schema.nsmap)
        if base_type_ns == self.schema.nsmap[XSD_NS]:
            return xsd2go_type[base_type_name]
        else:
            refered_type_instance = self.schema.get_type_instance(
                base_type_name, base_type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance.type_name()

    def type_def(self):
        return None


class List(Node):
    # TODO: ADD list parsing for msg validation
    def type_name(self):
        return "string"

    def type_def(self):
        return None


class Union(Node):
    # TODO: ADD Union parsing for msg validation
    def type_name(self):
        return "string"

    def type_def(self):
        return None
