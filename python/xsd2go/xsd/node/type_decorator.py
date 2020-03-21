from cached_property import cached_property

from xsd2go.constants import XSD_NS
from xsd2go.xsd.util import parse_ref_value, parse_tag

from .base import Node
from .base_type import name2base_class



class TypeDecorator(Node):
    def wrapped_type(self):
        raise NotImplementedError(
            "Method `wrapped_type` isn't implemented in class %s" % self.__class__)

    def _parse(self):
        from .simple_type import SimpleType

        self.nested_type = None
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_nodes:
            self.nested_type = SimpleType(self.schema, simple_type_nodes[0])


class Restriction(TypeDecorator):
    @cached_property
    def wrapped_type(self):
        if hasattr(self, "nested_type") is not None:
            return self.nested_type

        base_type_name, base_type_ns = parse_ref_value(
            self.node.attrib['base'], self.schema.nsmap)
        if base_type_ns == self.schema.nsmap[XSD_NS]:
            return name2base_class[base_type_name]()
        else:
            refered_type_instance = self.schema.get_type_instance(
                base_type_name, base_type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance
        

class SimpleTypeRestriction(Restriction):
    "Restriction element nested in simple type"
    
    @cached_property
    def restrictions(self):
        kwargs = {}
        enum = []
        for item in self.node:
            ns, tag = parse_tag(item.tag)
            if ns != self.schema.nsmap['xsd']:
                raise RuntimeError(
                    "cannot parse restriction item %s", self.tostring())
            if tag == "enumeration":
                enum.append(item.attrib["value"])
                continue
            kwargs[tag] = item.attrib["value"]

        if enum:
            kwargs['enumeration'] = enum

        return kwargs


class List(TypeDecorator):
    @cached_property
    def wrapped_type(self):
        if self.nested_type is not None:
            return self.nested_type
        else:
            type_name, type_ns = parse_ref_value(
                self.node.attrib['itemType'], self.schema.nsmap)
            refered_type_instance = self.schema.get_type_instance(
                type_name, type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance


class Union(Node):
    @cached_property
    def member_types(self):
        if self.nested_types:
            return self.nested_types
        else:
            member_type_names = self.node.attrib['memberTypes'].split(" ")
            _member_type_instances = []
            for _name in member_type_names:
                type_name, type_ns = parse_ref_value(
                    self.node.attrib['itemType'], self.schema.nsmap)
                refered_type_instance = self.schema.get_type_instance(
                    type_name, type_ns)
                if refered_type_instance is None:
                    raise RuntimeError(
                        "Cannot find ref type for %s" % self.tostring())
                else:
                    _member_type_instances.append(refered_type_instance)
            return _member_type_instances

    def _parse(self):
        from .simple_type import SimpleType

        self.nested_types = []
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        for type_node in simple_type_nodes:
            self.nested_types.append(
                SimpleType(self.schema, type_node))
