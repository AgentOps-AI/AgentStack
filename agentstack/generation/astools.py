"""
Shotcuts for working with ASTs.
"""
import ast


def find_class_with_decorator(tree: ast.AST, decorator_name: str) -> list[ast.ClassDef]:
    """Find a class definition that is marked by a decorator in an AST."""
    nodes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                    nodes.append(node)
    return nodes

def find_decorated_method_in_class(classdef: ast.ClassDef, decorator_name: str) -> list[ast.FunctionDef]:
    """Find all method definitions in a class definition which are decorated with a specific decorator."""
    nodes = []
    for node in ast.iter_child_nodes(classdef):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                    nodes.append(node)
    return nodes

def create_attribute(attr_name: str, base_name: str) -> ast.Attribute:
    """Create an AST node for an attribute"""
    return ast.Attribute(
        value=ast.Name(id=base_name, ctx=ast.Load()),
        attr=attr_name,
        ctx=ast.Load()
    )

