import re


def parse_ref_value(value, nsmap):
    if not value:
        return None, None
    name, ns_tag = parse_attrib_value(value)
    if ns_tag is not None:
        return name, nsmap.get(ns_tag)
    return name, None


def parse_tag(tag_name):
    extract = [
        m.groupdict()
        for m in re.finditer(
            r'(\{(?P<ns>.+)\})?(?P<tag>.+)', tag_name)
    ][0]
    return extract.get("tag"), extract.get("ns")


def parse_attrib_value(value):
    extract = [
        m.groupdict()
        for m in re.finditer(
            r'((?P<ns_tag>.+)\:)?(?P<tag>.+)', value)
    ][0]
    return extract.get("tag"), extract.get("ns_tag")
