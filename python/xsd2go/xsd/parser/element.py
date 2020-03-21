from xsd2go.xsd.node.element import Element
from xsd2go.xsd.node.simple_type import SimpleType
from xsd2go.xsd.node.complex_type import ComplexType

import xsd2go.xsd.parser.simple_type as st


def parse_element(schema, node):
    nested_type = None

    simple_type_node = node.xpath(
        "xsd:simpleType",
        namespaces=schema.nsmap
    )

    if simple_type_node:
        nested_type = st.parse_simple_type(schema, simple_type_node[0])

    complex_type_node = node.xpath(
        "xsd:complexType",
        namespaces=schema.nsmap
    )

    if complex_type_node:
        nested_type = parse_complex_type(schema, complex_type_node[0])

    element = Element(schema, node, nested_type)

    if 'name' in node.attrib:
        schema.add_element(element)
    
    return element


def parse_complex_type(schema, node):
    return ComplexType(schema, node)