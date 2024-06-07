import argparse
import ast
import os


class Boto3IAMParser(ast.NodeVisitor):
    def __init__(self, directory):
        self.directory = directory
        self.client_methods = {}
        self.client_vars = {}

    def visit_Assign(self, node):
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr in {"client", "resource"}
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "boto3"
            and isinstance(node.value.args[0], ast.Constant)
        ):
            client_name = node.value.args[0].value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.client_vars[target.id] = client_name
                    if client_name not in self.client_methods:
                        self.client_methods[client_name] = set()
        self.generic_visit(node)

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"client", "resource"}
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "boto3"
            and isinstance(node.args[0], ast.Constant)
        ):
            client_name = node.args[0].value
            if client_name not in self.client_methods:
                self.client_methods[client_name] = set()
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Attribute)
            and isinstance(node.func.value.func.value, ast.Name)
            and node.func.value.func.value.id == "boto3"
            and node.func.value.func.attr in {"client", "resource"}
            and isinstance(node.func.value.args[0], ast.Constant)
        ):
            client_name = node.func.value.args[0].value
            method_name = node.func.attr
            self.client_methods.setdefault(client_name, set()).add(method_name)
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.client_vars
        ):
            client_name = self.client_vars[node.func.value.id]
            method_name = node.func.attr
            self.client_methods.setdefault(client_name, set()).add(method_name)

        self.generic_visit(node)

    def walk(self):
        for root, _, files in os.walk(self.directory):
            if root == os.path.join(self.directory, "tests"):
                continue
            for file in files:
                if not file.endswith(".py"):
                    continue
                with open(os.path.join(root, file), "r") as f:
                    tree = ast.parse(f.read(), filename=file)
                    self.visit(tree)
        return self

    def print_results(self):
        for client, methods in self.client_methods.items():
            for method in sorted(methods):
                print(f"{client}:{method}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    args = parser.parse_args()
    Boto3IAMParser(args.directory).walk().print_results()


if __name__ == "__main__":
    main()
