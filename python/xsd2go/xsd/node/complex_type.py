from os.path import join
from pathlib import Path

from cached_property import cached_property

from xsd2go.constants import XSD_NS
from xsd2go.xsd.util import parse_ref_value

from xsd2go.xsd_go_type import xsd2go_type

from .base import Node
from .attribute_container import AttributeContainerMixin
from .element_container import ElementContainerMixin


class ComplexType(Node, AttributeContainerMixin, ElementContainerMixin):
    def __init__(self, schema, node, parent):
        super(ComplexType, self).__init__(schema, node, parent)
        if 'name' in self.node.attrib:
            self.schema.add_type_instance(self)

    @cached_property
    def name(self):
        name_attr = self.node.xpath("@name")
        name_attr = (name_attr and name_attr[0]) or None
        return name_attr

    @cached_property
    def prefix(self):
        if self.name is not None:
            return self.name
        elif self.name is None and self.parent is not None:
            return self.parent.prefix
        else:
            raise RuntimeError(
                "Cannot generate prefix for isolate complextype\n%s",
                self.tostring()
            )

    def _parse(self):
        self.content = None

        simple_content = self.node.xpath(
            "xsd:simpleContent",
            namespaces=self.schema.nsmap
        )
        if simple_content:
            simple_content = simple_content[0]
            self.content = SimpleContent(self.schema, simple_content, self)

        complex_content = self.node.xpath(
            "xsd:complexContent",
            namespaces=self.schema.nsmap
        )
        if complex_content:
            complex_content = complex_content[0]
            self.content = ComplexContent(self.schema, complex_content, self)

        if self.content is None:
            self._parse_attributes()
            self._parse_elements()

    def go_type_name(self):
        return self.name or self.prefix + 'BuiltinType'

    def go_base_class(self):
        if self.content is not None:
            return self.content.go_base_class()
        return None

    def go_struct_attributes(self):
        attrs = []
        added_attr = set()
        if self.content is not None:
            return self.content.go_struct_attributes()
        else:
            for attribute in self.attributes:
                go_attr = attribute.export_go_def()
                if go_attr is not None:
                    if go_attr['field_name'] in added_attr:
                        continue
                    added_attr.add(go_attr['field_name'])
                    attrs.append(go_attr)
            for elem in self.elements:
                go_attr = elem.export_go_def()
                if go_attr is not None:
                    if go_attr['field_name'] in added_attr:
                        continue
                    added_attr.add(go_attr['field_name'])
                    attrs.append(go_attr)
        return attrs

    def go_struct_def(self):
        lines = []
        lines.append("struct {")

        base_class = self.go_base_class()
        if base_class is not None:
            lines.append(base_class + ";")

        for attribute in self.go_struct_attributes():
            line = attribute['field_name'] + ' '
            if attribute['is_array']:
                line += '[]'
            if attribute['is_pointer']:
                line += '*'
            line += attribute['type_name']
            line += ' '
            if attribute['xml_field_suffix']:
                line += '`xml:"{xml_field_name},{xml_field_suffix},omitempty"`;'.format(**attribute)
            else:
                line += '`xml:"{xml_field_name},omitempty"`;'.format(**attribute)
            lines.append(line)
        lines.append("}")
        return '\n'.join(lines)
    
    def export_go_struct(self, base_path, base_module):
        class_name = self.go_type_name()
        if class_name is None:
            raise RuntimeError(
                "Cannot export class without name:\n%s",
                self.tostring()
            )
        if class_name in self.schema.exported_class:
            return
        else:
            self.schema.exported_class.add(class_name)

        packages = set()
        for attr in self.go_struct_attributes():
            if attr['type_instance'] is not None and isinstance(attr['type_instance'], ComplexType):
                if attr['type_instance'].go_package_name() != self.go_package_name():
                    packages.add('"' + join(base_module, base_path, attr['type_instance'].go_package_name()) + '"')

        items = (self.go_base_class() or '').split('.')
        if len(items) == 2:
            packages.add('"' + join(base_module, base_path, items[0]) + '"')

        dir_name = join(base_path, self.go_package_name())
        Path(dir_name).mkdir(parents=True, exist_ok=True)

        file_path = join(dir_name, class_name + '.go')
        lines = [
            "package %s" % self.schema.go_package_name(),
        ]

        if packages:
            lines.append('import (')
            lines.extend(list(packages))
            lines.append(')')
        lines.extend([
            "",
            "type %s " % class_name + self.go_struct_def(),
            ""
        ])
        fout = open(file_path, 'w')
        fout.write('\n'.join(lines))
        fout.close()
        for attr in self.go_struct_attributes():
            if attr['type_instance'] is not None:
                attr['type_instance'].export_go_struct(base_path, base_module)


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

        if refered_type_instance is None:
            raise RuntimeError(
                "Cannot find ref type for %s" % self.tostring())

        return refered_type_instance
    
    def _parse(self):
        self._parse_attributes()
        self._parse_elements()

    def go_base_class(self):
        from .simple_type import SimpleType
        
        _, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            return None
        elif isinstance(self.base_type_instance, SimpleType):
            return None
        elif self.base_type_instance is None:
            raise RuntimeError(
                "Base class cannot be None\n%s", self.tostring())
        
        base_class_name = self.base_type_instance.go_type_name()
        if self.go_package_name() != self.base_type_instance.go_package_name():
            base_class_name = self.base_type_instance.go_package_name() + '.' + base_class_name

        return base_class_name

    def go_struct_attributes(self):
        from .simple_type import SimpleType

        attrs = []
        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            go_struct_name = xsd2go_type.get(type_name)
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find predefined go type for %s",
                    self.node.attrib['base']
                )
            attrs.append({
                "field_name": 'Text',
                "type_name": go_struct_name,
                "is_array": False,
                "is_pointer": False,
                "type_instance": None,
                "xml_field_name": "",
                "xml_field_suffix": "chardata",
            })
        elif isinstance(self.base_type_instance, SimpleType):
            attrs.append({
                "field_name": 'Text',
                "type_name": self.base_type_instance.go_type_name(),
                "is_array": False,
                "is_pointer": False,
                "type_instance": None,
                "xml_field_name": "",
                "xml_field_suffix": "chardata",
            })
        elif self.base_type_instance is None:
            raise RuntimeError(
                "Base class cannot be None\n%s", self.tostring())
        # else:
        #     lines.append(self.base_type_instance.go_type_name() + ";")

        added_attr = set()
        for attr in self.attributes:
            go_attr = attr.export_go_def()
            if go_attr is not None:
                if go_attr['field_name'] in added_attr:
                    continue
                added_attr.add(go_attr['field_name'])
                attrs.append(go_attr)
        for elem in self.elements:
            go_attr = elem.export_go_def()
            if go_attr is not None:
                if go_attr['field_name'] in added_attr:
                    continue
                added_attr.add(go_attr['field_name'])
                attrs.append(go_attr)
        return attrs


class SimpleContentRestriction(Node, AttributeContainerMixin):
    def _parse(self):
        from .simple_type import SimpleType

        self.nested_type = None
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_nodes:
            self.nested_type = SimpleType(
                self.schema, simple_type_nodes[0], self)
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
        return []
    
    def go_base_class(self):
        from .simple_type import SimpleType

        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            go_struct_name = xsd2go_type.get(type_name)
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find predefined go type for %s",
                    self.node.attrib['base']
                )
            return go_struct_name
        elif isinstance(self.base_type_instance, SimpleType):
            return self.base_type_instance.go_type_name()

        base_class_name = self.base_type_instance.go_type_name()
        if self.go_package_name() != self.base_type_instance.go_package_name():
            base_class_name = self.base_type_instance.go_package_name() + '.' + base_class_name

        return base_class_name


class ComplexContentRestriction(Node, AttributeContainerMixin, ElementContainerMixin):
    def _parse(self):
        from .simple_type import SimpleType

        self.nested_type = None
        simple_type_nodes = self.node.xpath(
            "xsd:simpleType",
            namespaces=self.schema.nsmap
        )

        if simple_type_nodes:
            self.nested_type = SimpleType(
                self.schema, simple_type_nodes[0], self)
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
        return []

    def go_base_class(self):
        from .simple_type import SimpleType

        type_name, type_ns = self.parse_ref_value(
            self.node.attrib['base'])
        if type_ns == self.schema.nsmap[XSD_NS]:
            go_struct_name = xsd2go_type.get(type_name)
            if go_struct_name is None:
                raise RuntimeError(
                    "Cannot find predefined go type for %s",
                    self.node.attrib['base']
                )
            return go_struct_name
        elif isinstance(self.base_type_instance, SimpleType):
            return self.base_type_instance.go_type_name()
        
        base_class_name = self.base_type_instance.go_type_name()
        if self.go_package_name() != self.base_type_instance.go_package_name():
            base_class_name = self.base_type_instance.go_package_name() + '.' + base_class_name

        return base_class_name


class Content(Node):
    pass


class SimpleContent(Content):
    def _parse(self):
        self.decorator = None

        extensions = self.node.xpath(
            "xsd:extension", namespaces=self.schema.nsmap)
        if extensions:
            self.decorator = Extension(self.schema, extensions[0], self)

        restrictions = self.node.xpath(
            "xsd:restriction", namespaces=self.schema.nsmap)
        if restrictions:
            self.decorator = SimpleContentRestriction(
                self.schema, restrictions[0], self)

    def go_base_class(self):
        if self.decorator is None:
            raise RuntimeError("decorator is empty")
        return self.decorator.go_base_class()

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
            self.decorator = Extension(self.schema, extensions[0], self)

        restrictions = self.node.xpath(
            "xsd:restriction", namespaces=self.schema.nsmap)
        if restrictions:
            self.decorator = ComplexContentRestriction(
                self.schema, restrictions[0], self)

    def go_base_class(self):
        if self.decorator is None:
            raise RuntimeError("decorator is empty")
        return self.decorator.go_base_class()

    def go_struct_attributes(self):
        if self.decorator is None:
            raise RuntimeError("decorator is empty")
        return self.decorator.go_struct_attributes()
