from os.path import join

from cached_property import cached_property

from xsd2go.constants import XSD_NS
from xsd2go.xsd.util import parse_ref_value

from xsd2go.xsd_go_type import xsd2go_type

from .base import Node
from .attribute_container import AttributeContainerMixin
from .element_container import ElementContainerMixin


class ComplexType(Node, AttributeContainerMixin, ElementContainerMixin):
    def __init__(self, schema, node):
        super(ComplexType, self).__init__(schema, node)
        if 'name' in self.node.attrib:
            self.schema.add_type_instance(self)

    @cached_property
    def name(self):
        name_attr = self.node.xpath("@name")
        name_attr = (name_attr and name_attr[0]) or None
        return name_attr

    def _parse(self):
        self.content = None

        simple_content = self.node.xpath(
            "xsd:simpleContent",
            namespaces=self.schema.nsmap
        )
        if simple_content:
            simple_content = simple_content[0]
            self.content = SimpleContent(self.schema, simple_content)

        complex_content = self.node.xpath(
            "xsd:complexContent",
            namespaces=self.schema.nsmap
        )
        if complex_content:
            complex_content = complex_content[0]
            self.content = ComplexContent(self.schema, complex_content)

        if self.content is None:
            self._parse_attributes()
            self._parse_elements()

    def go_struct_name(self):
        return self.name

    def go_struct_attributes(self):
        lines = []
        added_attr = set()
        if self.content is not None:
            return self.content.go_struct_attributes()
        else:
            for attr in self.attributes:
                line = attr.export_go_def()
                if line is not None:
                    if attr.name in added_attr:
                        continue
                    added_attr.add(attr.name)
                    lines.append(line)
            for elem in self.elements:
                line = elem.export_go_def()
                if line is not None:
                    if elem.name in added_attr:
                        continue
                    added_attr.add(elem.name)
                    lines.append(line)
        return lines

    def go_struct_def(self):
        lines = []
        lines.append("struct {")
        lines.extend(self.go_struct_attributes())
        lines.append("}")
        return '\n'.join(lines)
    
    def export_go_struct(self, name=None):
        class_name = self.name or name
        if class_name is None:
            raise RuntimeError(
                "Cannot export class without name:\n%s",
                self.tostring()
            )
        if class_name in self.schema.exported_class:
            return
        else:
            self.schema.exported_class.add(class_name)

        file_name = class_name + '.go'
        lines = [
            "package %s" % self.schema.package,
            "",
            "type %s " % class_name + self.go_struct_def(),
            ""
        ]
        fout = open(join(self.schema.base_path, file_name), 'w')
        fout.write('\n'.join(lines))
        fout.close()


class Extension(Node, AttributeContainerMixin, ElementContainerMixin):
    @cached_property
    def base_type_instance(self):
        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            raise RuntimeError(
                'Cannot return base type instance for builtin type %s',
                self.node.attrib['type']
            )
        refered_type_instance = self.schema.get_type_instance(
            type_name, type_ns)

        if isinstance(refered_type_instance, ComplexType):
            refered_type_instance.export_go_struct()

        if refered_type_instance is None:
            raise RuntimeError(
                "Cannot find ref type for %s" % self.tostring())

        return refered_type_instance
    
    def _parse(self):
        self._parse_attributes()
        self._parse_elements()

    def go_struct_attributes(self):
        from .simple_type import SimpleType

        lines = []
        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            go_struct_name = xsd2go_type.get(type_name)
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find predefined go type for %s",
                    self.node.attrib['base']
                )
            lines.append(
                'Text %s `xml:",chardata"`;' % go_struct_name)
        elif isinstance(self.base_type_instance, SimpleType):
            lines.append(
                'Text %s `xml:",chardata"`;' % self.base_type_instance.go_struct_name())
        else:
            lines.append(self.base_type_instance.go_struct_name() + ";")

        for attr in self.attributes:
            line = attr.export_go_def()
            if line is not None:
                lines.append(line)
        for elem in self.elements:
            line = elem.export_go_def()
            if line is not None:
                lines.append(line)
        return lines


class SimpleContentRestriction(Node, AttributeContainerMixin):
    def _parse(self):
        from .simple_type import SimpleType

        self.nested_type = None
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_nodes:
            self.nested_type = SimpleType(self.schema, simple_type_nodes[0])
        self._parse_attributes()

    @cached_property
    def base_type_instance(self):
        if self.nested_type is not None:
            return self.nested_type

        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            raise RuntimeError(
                'Cannot return base type instance for builtin type %s',
                self.node.attrib['type']
            )
        refered_type_instance = self.schema.get_type_instance(
            type_name, type_ns)
        if refered_type_instance is None:
            raise RuntimeError(
                "Cannot find ref type for %s" % self.tostring())

        return refered_type_instance
    
    def go_struct_attributes(self):
        from .simple_type import SimpleType

        lines = []
        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            go_struct_name = xsd2go_type.get(type_name)
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find predefined go type for %s",
                    self.node.attrib['base']
                )
            lines.append(go_struct_name + ";")
        elif isinstance(self.base_type_instance, SimpleType):
            lines.append(self.base_type_instance.go_struct_name() + ";")
        else:
            lines.append(self.base_type_instance.go_struct_name() + ";")
        return lines


class ComplexContentRestriction(Node, AttributeContainerMixin, ElementContainerMixin):
    def _parse(self):
        from .simple_type import SimpleType

        self.nested_type = None
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_nodes:
            self.nested_type = SimpleType(self.schema, simple_type_nodes[0])
        self._parse_attributes()
        self._parse_elements()

    @cached_property
    def base_type_instance(self):
        if self.nested_type is not None:
            return self.nested_type

        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            raise RuntimeError(
                'Cannot return base type instance for builtin type %s',
                self.node.attrib['type']
            )
        refered_type_instance = self.schema.get_type_instance(
            type_name, type_ns)
        if refered_type_instance is None:
            raise RuntimeError(
                "Cannot find ref type for %s" % self.tostring())

        return refered_type_instance

    def go_struct_attributes(self):
        from .simple_type import SimpleType

        lines = []
        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            go_struct_name = xsd2go_type.get(type_name)
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find predefined go type for %s",
                    self.node.attrib['base']
                )
            lines.append(go_struct_name + ";")
        elif isinstance(self.base_type_instance, SimpleType):
            lines.append(self.base_type_instance.go_struct_name() + ";")
        else:
            lines.append(self.base_type_instance.go_struct_name() + ";")
        return lines


class Content(Node):
    pass


class SimpleContent(Content):
    def _parse(self):
        self.decorator = None

        extensions = self.node.xpath(
            "xsd:extension", namespaces=self.schema.nsmap)
        if extensions:
            self.decorator = Extension(self.schema, extensions[0])

        restrictions = self.node.xpath(
            "xsd:restriction", namespaces=self.schema.nsmap)
        if restrictions:
            self.decorator = SimpleContentRestriction(
                self.schema, restrictions[0])

    def go_struct_attributes(self):
        if self.decorator is None:
            raise RuntimeError("decorator is empty")
        return self.decorator.go_struct_attributes()


class ComplexContent(Content):
    def _parse(self):
        self.decorator = None

        extensions = self.node.xpath(
            "xsd:extension", namespaces=self.schema.nsmap)
        if extensions:
            self.decorator = Extension(self.schema, extensions[0])

        restrictions = self.node.xpath(
            "xsd:restriction", namespaces=self.schema.nsmap)
        if restrictions:
            self.decorator = ComplexContentRestriction(
                self.schema, restrictions[0])

    def go_struct_attributes(self):
        if self.decorator is None:
            raise RuntimeError("decorator is empty")
        return self.decorator.go_struct_attributes()
