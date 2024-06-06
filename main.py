import argparse
import ast
import os


class Boto3IAMParser(ast.NodeVisitor):
    def __init__(self):
        self.boto3_clients = set()

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"client", "resource"}
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "boto3"
            and isinstance(node.args[0], ast.Constant)
        ):
            self.boto3_clients.add(node.args[0].value)

        self.generic_visit(node)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    args = parser.parse_args()
    parser = Boto3IAMParser()
    for root, _, files in os.walk(args.directory):
        for file in files:
            if not file.endswith(".py"):
                continue
            with open(os.path.join(root, file), "r") as f:
                tree = ast.parse(f.read(), filename=file)
                parser.visit(tree)
    print(f"Required IAM Permissions: {sorted(parser.boto3_clients)}")


if __name__ == "__main__":
    main()
