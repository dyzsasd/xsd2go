from .node.attribute import Attribute, AttributeGroup


def _parse_attributes(schema, node):
    attribute_nodes = node.xpath(
        "xsd:attribute",
        namespaces=schema.nsmap
    )
    nested_attributes = [
        Attribute(schema, node)
        for node in attribute_nodes
    ]

    attribute_group_nodes = node.xpath(
        "xsd:attributeGroup",
        namespaces=schema.nsmap
    )
    nested_attribute_groups = [
        AttributeGroup(schema, node)
        for node in attribute_group_nodes
    ]

    return nested_attributes, nested_attribute_groups