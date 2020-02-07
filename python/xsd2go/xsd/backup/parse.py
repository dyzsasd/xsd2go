from copy import deepcopy
import re

from lxml import etree

from .type import ComplexType, name2base_class, UnionSimpleType, ExtendedSimpleType
from .util import parse_tag, parse_value
from .element import Element, ElementCollection


def parse_type_node(schema, node, type_name):
    type_name = node.attrib.get('name') or type_name
    type_instance = None
    _, tag = parse_tag(node.tag)
    if tag == "simpleType":
        type_instance = parse_simple_type(schema, node, type_name)
    elif tag == "complexType":
        type_instance = parse_complex_type(schema, node, type_name)

    if type_instance is None:
        raise RuntimeError("cannot parse node\n%s" % etree.tostring(node).decode("utf8"))

    schema.name2type[type_name] = type_instance

    return type_instance


def parse_complex_type(schema, node, type_name):
    elements, base_name = [], None

    simple_content_node = node.xpath(
        "xsd:simpleContent", namespaces=schema.nsmap)
    complex_content_node = node.xpath(
        "xsd:complexContent", namespaces=schema.nsmap)

    if simple_content_node:
        elements, base_name = parse_simple_content(
            schema, simple_content_node[0])
    elif complex_content_node:
        elements, base_name = parse_complex_content(
            schema, complex_content_node[0])
    else:
        elements = parse_element_container(schema, node)

    # if (elements is None or len(elements) == 0) and (base_name is None or base_name == ""):
    #     raise RuntimeError(
    #         "Cannot parse complex type:\n%s" % etree.tostring(node).decode("utf8"))
    
    elements = elements or []

    type_instance = ComplexType(type_name, schema.target_ns, elements, base_name=base_name)

    docs = node.xpath(
        "xsd:annotation/xsd:documentation/text()",
        namespaces=schema.nsmap
    )
    if docs:
        type_instance.docs = docs
    return type_instance


def parse_element_container(schema, node):
    indicator = node.xpath(
        "*[self::xsd:all or self::xsd:sequence or self::xsd:choice]",
        namespaces=schema.nsmap
    )

    if len(indicator) > 0:
        container_node = indicator[0]
    else:
        container_node = node

    _, node_name = parse_tag(container_node.tag)
    
    elements = [
        parse_element_node(schema, element_node)
        for element_node in container_node.xpath(
            "xsd:element",
            namespaces=schema.nsmap
        )
    ]

    attribute_group_nodes = node.xpath(
        'xsd:attributeGroup', namespaces=schema.nsmap)
    attribute_group_refs = []
    for attribute_group_node in attribute_group_nodes:
        if 'ref' in attribute_group_node.attrib:
            # attribute_elements = schema.get_attribute_group(
            #     attribute_group_node.attrib['ref'])
            # elements.extend(attribute_elements)
            attribute_group_refs.append(attribute_group_node.attrib['ref'])
        elif 'name' in attribute_group_node.attrib:
            parse_attribute_group(schema, attribute_group_node)
        else:
            raise RuntimeError(
                "cannot parse attributeGroup node\n%s" % etree.tostring(attribute_group_node).decode('utf8'))

    for attribute_node in node.xpath("xsd:attribute", namespaces=schema.nsmap):
        element = parse_element_node(schema, attribute_node)
        elements.append(element)

    return ElementCollection(
        elements, attribute_group_refs=attribute_group_refs,
        indicator=node_name    
    )


def parse_complex_content(schema, node):
    extension_node = node.xpath("xsd:extension", namespaces=schema.nsmap)
    base_name = None
    elements = []
    if extension_node:
        extension_node = extension_node[0]
        base_name = extension_node.attrib['base']
        # base_type = schema.get_type_instance(base_type_name)
        elements = parse_element_container(schema, extension_node)
        
    if base_name is None:
        raise RuntimeError("base type is None in\n%s" % etree.tostring(node).decode('utf8'))

    return elements, base_name


def parse_simple_content(schema, node):
    elements = []
    # base_type_instance = None
    base_name = None

    extensions = node.xpath(
        "xsd:extension", namespaces=schema.nsmap)
    if not extensions:
        return elements, base_name

    extension = extensions[0]
    base_name = extension.attrib["base"]

    # base_ns, base_tag = parse_tag(base_name)
    # if base_ns == schema.nsmap['xsd']:
    #     base_type_instance = name2base_class[base_tag]()
    # else:
    #     base_type_instance = schema.get_type_instance(base_name)

    if base_name:
        elements.append(
            Element("Text", base_name, is_attribute=False,
                    ns=schema.target_ns, min_occrs=0, max_occrs=1)
        )

    element_collection = parse_element_container(schema, extension)
    element_collection.elements.extend(elements)

    return element_collection, None


def parse_simple_type(schema, node, type_name):
    union_node = node.xpath("xsd:union", namespaces=schema.nsmap)
    restriction = node.xpath(
        "xsd:restriction", namespaces=schema.nsmap)
    if union_node:
        union_node = union_node[0]
        member_types = union_node.attrib.get('memberTypes')
        member_types = (member_types and member_types.split(" ")) or []
        for ix, simpleNode in enumerate(union_node.xpath("xsd:simpleType", namespaces=schema.nsmap)):
            sub_type_name = "%sUnionType%s" % (type_name, ix)
            parse_type_node(schema, simpleNode, sub_type_name)
            member_types.append(sub_type_name)
        if len(member_types) == 0:
            raise RuntimeError(
                "cannot parse union node\n%s" % etree.tostring(union_node).decode('utf8'))

        type_instance = UnionSimpleType(
            type_name, schema.target_ns, member_type_names=member_types)
    elif restriction:
        restriction = restriction[0]
        base = restriction.attrib["base"]

        kwargs = {}
        enum = []
        for item in restriction:
            ns, tag = parse_tag(item.tag)
            if ns != schema.nsmap['xsd']:
                raise RuntimeError("cannot parse restriction item %s", etree.tostring(item))
            if tag == "enumeration":
                enum.append(item.attrib["value"])
                continue
            kwargs[tag] = item.attrib["value"]
        if enum:
            kwargs['enumeration'] = enum

        kwargs['ns'] = schema.target_ns
        ns_tag, tag = parse_value(base)
        if ns_tag is not None and schema.nsmap[ns_tag] == schema.nsmap["xsd"]:
            type_instance = name2base_class[tag](**kwargs)
        else:
            type_instance = ExtendedSimpleType(
                type_name, schema.target_ns, base, kwargs)
            # base_type_instance = schema.get_type_instance(base)
            # if base_type_instance is None:
            #     raise RuntimeError(
            #         "simply type base type instance is None\n%s" % etree.tostring(node).decode("utf8"))
            # type_instance = deepcopy(base_type_instance)
            # for key, value in kwargs.items():
            #     setattr(type_instance, key, value)
        # if len(kwargs) == 0:
        #     raise RuntimeError("restriction is empty\n%s" % etree.tostring(node).decode('utf8'))
    else:
        raise RuntimeError(
            "cannot parse simple type:\n%s" % etree.tostring(node).decode("utf8"))
    
    return type_instance


def parse_attribute_group(schema, node):
    elements = parse_element_container(schema, node)
    schema.name2attribute_group[node.attrib['name']] = elements


def parse_element_node(schema, node):
    print(schema.xml_tree.getpath(node))
    is_attribute = node.tag == "%s:attribute"

    ref = node.attrib.get('ref')
    name = node.attrib.get('name')
    type_name = node.attrib.get('type', "Nested%sType" % name)
    max_occrs = node.attrib.get("maxOccurs")
    min_occrs = node.attrib.get("minOccurs")
    docs = node.xpath(
        "xsd:annotation/xsd:documentation/text()",
        namespaces=schema.nsmap
    )

    complexType = node.xpath('xsd:complexType', namespaces=schema.nsmap)

    if complexType:
        parse_type_node(schema, complexType[0], type_name)

    simpleType = node.xpath('xsd:simpleType', namespaces=schema.nsmap)
    if simpleType:
        parse_type_node(schema, simpleType[0], type_name)
    
    element = Element(
        name, type_name, ref=ref, is_attribute=is_attribute,
        ns=schema.target_ns, min_occrs=min_occrs, max_occrs=max_occrs, docs=docs)

    schema.name2element[name] = element

    return element
