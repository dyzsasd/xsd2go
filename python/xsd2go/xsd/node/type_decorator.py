from cached_property import cached_property

from xsd2go.constants import XSD_NS
from xsd2go.xsd.util import parse_ref_value, parse_tag

from .base import Node
from xsd2go.xsd_go_type import xsd2go_type


class SimpleTypeRestriction(Node):
    def _parse(self):
        pass

    "Restriction element nested in simple type"
    # TODO: ADD restriction parsing for msg validation
    def go_type_name(self):
        base_type_name, base_type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if base_type_ns == self.schema.nsmap[XSD_NS]:
            return xsd2go_type[base_type_name]
        else:
            refered_type_instance = self.schema.get_type_instance(
                base_type_name, base_type_ns)
            if refered_type_instance is None:
                raise RuntimeError(
                    "Cannot find ref type for %s" % self.tostring())
            else:
                return refered_type_instance.go_type_name()

    def go_struct_attributes(self):
        return []


class List(Node):
    def _parse(self):
        pass

    # TODO: ADD list parsing for msg validation
    def go_type_name(self):
        return "string"

    def go_struct_attributes(self):
        return []


class Union(Node):
    def _parse(self):
        pass

    # TODO: ADD Union parsing for msg validation
    def go_type_name(self):
        return "string"

    def go_struct_attributes(self):
        return []
