import argparse
import os

from xsd2go.xsd.project import Project


parser = argparse.ArgumentParser()
parser.add_argument("path", type=str, help="XSD file repo path")

parser.add_argument(
    "--base-path", type=str, default="ndc",
    help="base path of go scripts"
)

parser.add_argument(
    "--base-module", type=str, required=True,
    help="base path of go scripts"
)

parser.add_argument(
    "--recursive", default=False, action="store_true",
    help="Register all classes even it is not directly attached to root node"
)


if __name__ == "__main__":
    args = parser.parse_args()

    p = Project(args.path)
    p.load_schema(recursive=args.recursive)

    for name, s in p.schemas.items():
        if s is None:
            raise RuntimeError("Cannot find xsd file of %s", name)
        for name, type_instance in s.name2type_instance.items():
            type_instance.export_go_struct(args.base_path, args.base_module)
        for element in s.element_collection:
            if element.nested_type is not None:
                element.nested_type.export_go_struct(args.base_path,  args.base_module)
