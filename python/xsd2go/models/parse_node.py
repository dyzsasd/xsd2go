from copy import deepcopy
import re

from lxml import etree

from .type import ComplexType, name2base_class
from .util import parse_tag, parse_value
from .element import Element


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
    elements, base = [], None

    simple_content_node = node.xpath(
        "xsd:simpleContent", namespaces=schema.nsmap)
    complex_content_node = node.xpath(
        "xsd:complexContent", namespaces=schema.nsmap)

    if simple_content_node:
        elements, base = parse_simple_content(
            schema, simple_content_node[0])
    elif complex_content_node:
        elements, base = parse_complex_content(
            schema, complex_content_node[0])
    else:
        elements = parse_element_container(schema, node)

    if (elements is None or len(elements) == 0) and base is None:
        raise RuntimeError(
            "Cannot parse complex type:\n%s" % etree.tostring(node).decode("utf8"))
    
    type_instance = ComplexType(type_name, schema.target_ns, elements, base=base)

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

    container_node = (indicator and indicator[0]) or node

    node_name = container_node.tag.replace("{%s}" % schema.nsmap['xsd'], "")
    is_indicator = node_name in set(["all", "choice", "sequence"]   )
    
    elements = [
        parse_element_node(schema, element_node)
        for element_node in container_node.xpath(
            "xsd:element",
            namespaces=schema.nsmap
        )
    ]

    attribute_group_nodes = node.xpath(
        'xsd:attributeGroup', namespaces=schema.nsmap)
    for attribute_group_node in attribute_group_nodes:
        attribute_elements = schema.get_attribute_group(
            attribute_group_node.attrib['ref'])
        elements.extend(attribute_elements)
    
    for attribute_node in node.xpath("xsd:attribute", namespaces=schema.nsmap):
        element = parse_element_node(schema, attribute_node)
        elements.append(element)

    return elements


def parse_complex_content(schema, node):
    extension_node = node.xpath("xsd:extention")
    base_type = None
    elements = []
    if extension_node:
        extension_node = extension_node[0]
        base_type_name = extension_node.attrib['base']
        base_type = schema.get_type_instance(base_type_name)
        elements = parse_element_container(schema, extension_node)
        
    if base_type is None:
        raise RuntimeError("base type is None in \n%s", etree.tostring(node))

    return elements, base_type


def parse_simple_content(schema, node):
    elements = []
    base_type_instance = None

    extensions = node.xpath(
        "xsd:extension", namespaces=schema.nsmap)
    if not extensions:
        return elements, base_type_instance

    extension = extensions[0]
    base_name = extension.attrib["base"]

    base_ns, base_tag = parse_tag(base_name)
    if base_ns == schema.nsmap['xsd']:
        base_type_instance = name2base_class[base_tag]()
    else:
        base_type_instance = schema.get_type_instance(base_name)

    elements.append(
        Element("Text", base_type_instance, ns=schema.target_ns)
    )

    elements.extend(parse_element_container(schema, extension))

    return elements, None



def parse_simple_type(schema, node, type_name):
    restriction = node.xpath(
        "xsd:restriction", namespaces=schema.nsmap)[0]
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
    if schema.nsmap[ns_tag] == schema.nsmap["xsd"]:
        type_instance = name2base_class[tag](**kwargs)
    else:
        base_type_instance = schema.get_type_instance(base)
        if base_type_instance is None:
            raise RuntimeError(
                "simply type base type instance is None\n%s" % etree.tostring(node).decode("utf8"))
        type_instance = deepcopy(base_type_instance)
        for key, value in kwargs.items():
            setattr(type_instance, key, value)
    # if len(kwargs) == 0:
    #     raise RuntimeError("restriction is empty\n%s" % etree.tostring(node).decode('utf8'))
    
    return type_instance


def parse_attribute_group(schema, node):
    elements = parse_element_container(schema, node)
    schema.name2attribute_group[node.attrib['name']] = elements


def parse_element_node(schema, node):
    _type_instance = None
    is_attribute = node.tag == "%s:attribute"

    if 'ref' in node.attrib:
        ref_element = schema.get_type_instance(node.attrib['ref'])
        _type_instance = ref_element._type

        name = node.attrib.get('name') or ref_element.name
        max_occurs = node.attrib.get("maxOccurs") or ref_element.max_occr
        min_occurs = node.attrib.get("minOccurs", "0") or ref_element.min_occr
    else:
        name = node.attrib['name']
        max_occurs = node.attrib.get("maxOccurs", "1")
        min_occurs = node.attrib.get("minOccurs", "0")

        _type = node.attrib.get('type')
        complexType = node.xpath('xsd:complexType', namespaces=schema.nsmap)

        ns_tag, type_tag = parse_value(_type)

        if _type is None and complexType:
            type_name = "Nested%sType" % name
            _type_instance = parse_type_node(schema, complexType[0], type_name)
        elif schema.nsmap[ns_tag] == schema.nsmap['xsd']:
            _type_instance = name2base_class[type_tag]()
        else:
            _type_instance = schema.get_type_instance(_type)

    if _type_instance is None:
        raise RuntimeError(
            "Type instance is None when parsing \n%s" % etree.tostring(node).decode('utf8'))

    is_array = max_occurs != "1"
    
    docs = node.xpath(
        "xsd:annotation/xsd:documentation/text()",
        namespaces=schema.nsmap
    )
    
    element = Element(
        name, _type_instance, is_attribute=is_attribute, ns=schema.target_ns,
        is_array=is_array, min_occr=min_occurs, max_occr=max_occurs, docs=docs)
    
    return element
