class ElementContainerMixin(object):
    def _parse_elements(self):
        from .element_collection import Sequence, create_collection

        self.element_collection = None

        collection_nodes = self.node.xpath(
            "*[self::xsd:group or self::xsd:all or self::xsd:choice or self::xsd:sequence]",
            namespaces=self.schema.nsmap
        )
        if collection_nodes:
            self.element_collection = create_collection(self.schema, collection_nodes[0])

        if self.element_collection is None:
            # By default, the indicator is Sequence
            self.indicator = Sequence(self.schema, self.node)
