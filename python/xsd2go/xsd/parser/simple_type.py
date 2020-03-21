from xsd2go.xsd.node.simple_type import (
    SimpleType, SimpleTypeRestriction, List, Union)


def parse_simple_type(self, schema, node):
    content = None
    restriction_node = self.node.xpath(
        "xsd:restriction",
        namespaces=self.schema.nsmap
    )
    if restriction_node:
        restriction_node = restriction_node[0]
        content = parse_simple_type_restriction(
            schema, restriction_node)

    list_node = self.node.xpath(
        "xsd:restriction",
        namespaces=self.schema.nsmap
    )
    if list_node:
        self.content = List(self.schema, list_node[0])

    union_node = self.node.xpath(
        "xsd:union",
        namespaces=self.schema.nsmap
    )
    if union_node:
        self.content = Union(self.schema, union_node[0])

    simple_type = SimpleType(schema, node, content)
    if 'name' in self.node.attrib:
        if self.node.attrib['name'] in self.schema.name2type_instance:
            raise RuntimeError("Duplicate type definition in %s" % schema.path)
        self.schema.name2type_instance[self.node.attrib['name']] = self
    return simple_type


def parse_simple_type_restriction(schema, node):
    return SimpleTypeRestriction(schema, node)


def parse_list(schema, node):
    return List(schema, node)