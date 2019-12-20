import re


def parse_tag(tag_name):
    extract = [
        m.groupdict()
        for m in re.finditer(
            r'(\{(?P<ns>.+)\})?(?P<tag>.+)', tag_name)
    ][0]
    return extract.get("ns"), extract.get("tag")


def parse_value(value):
    extract = [
        m.groupdict()
        for m in re.finditer(
            r'(?P<ns_tag>.+)\:(?P<tag>.+)', value)
    ][0]
    return extract.get("ns_tag"), extract.get("tag")
