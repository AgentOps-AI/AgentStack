"""
Tools for working with ASTs.

We include convenience functions here based on real needs inside the codebase,
such as finding a method definition in a class, or finding a method by its decorator.

It's not optimal to have a fully-featured set of functions as this would be
unwieldy, but since our use-cases are well-defined, we can provide a set of
functions that are useful for the specific tasks we need to accomplish.
"""

from typing import TypeVar, Optional, Union, Iterable, Pattern, Any
from pathlib import Path
import ast
import astor
import asttokens
from agentstack.exceptions import ValidationError


FileT = TypeVar('FileT', bound='File')
ASTT = TypeVar('ASTT', bound=ast.AST)


class File:
    """
    Parses and manipulates a Python source file with an AST.

    Use it as a context manager to make and save edits:
    ```python
    with File(filename) as f:
        f.edit_node_range(start, end, new_node)
    ```

    Lookups are done using the built-in `ast` module, which we only use to find
    and read nodes in the tree.

    Edits are done using string indexing on the source code, which preserves a
    majority of the original formatting and prevents comments from being lost.

    In cases where we are constructing new AST nodes, we use `astor` to render
    the node as source code.
    """

    filename: Path
    source: str
    atok: asttokens.ASTTokens
    tree: ast.Module

    def __init__(self, filename: Path):
        self.filename = filename
        self.read()

    def read(self):
        try:
            with open(self.filename, 'r') as f:
                self.source = f.read()
                self.atok = asttokens.ASTTokens(self.source, parse=True)
                self.tree = self.atok.tree
        except (FileNotFoundError, SyntaxError) as e:
            raise ValidationError(f"Failed to parse {self.filename}\n{e}")

    def write(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(self.source)

    def get_node_range(self, node: ast.AST) -> tuple[int, int]:
        """Get the string start and end indexes for a node in the source code."""
        return self.atok.get_text_range(node)

    def edit_node_range(self, start: int, end: int, node: Union[str, ast.AST]):
        """Splice a new node or string into the source code at the given range."""
        if isinstance(node, ast.expr):
            module = ast.Module(body=[ast.Expr(value=node)], type_ignores=[])
            _node = astor.to_source(module).strip()
        else:
            _node = node

        self.source = self.source[:start] + _node + self.source[end:]
        # In order to continue accurately modifying the AST, we need to re-parse the source.
        self.atok = asttokens.ASTTokens(self.source, parse=True)

        if self.atok.tree:
            self.tree = self.atok.tree
        else:
            raise ValidationError(f"Failed to parse {self.filename} after edit")

    def __enter__(self: FileT) -> FileT:
        return self

    def __exit__(self, *args):
        self.write()


def get_all_imports(tree: ast.Module) -> list[ast.ImportFrom]:
    """Find all import statements in an AST."""
    imports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom):  # NOTE must be in format `from x import y`
            imports.append(node)
    return imports


def find_method(tree: Union[Iterable[ASTT], ASTT], method_name: str) -> Optional[ast.FunctionDef]:
    """Find a method definition in an AST."""
    if isinstance(tree, ast.AST):
        _tree = list(ast.iter_child_nodes(tree))
    else:
        _tree = list(tree)

    for node in _tree:
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    return None


def find_kwarg_in_method_call(node: ast.Call, kwarg_name: str) -> Optional[ast.keyword]:
    """Find a keyword argument in a method call or class instantiation."""
    for arg in node.keywords:
        if isinstance(arg, ast.keyword) and arg.arg == kwarg_name:
            return arg
    return None


def find_class_instantiation(tree: Union[Iterable[ast.AST], ast.AST], class_name: str) -> Optional[ast.Call]:
    """
    Find a class instantiation statement in an AST by the class name.
    This can either be an assignment to a variable or a return statement.
    """
    if isinstance(tree, ast.AST):
        _tree = list(ast.iter_child_nodes(tree))
    else:
        _tree = list(tree)

    for node in _tree:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and isinstance(node.value, ast.Call)
                    and target.id == class_name
                ):
                    return node.value
        elif (
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == class_name
        ):
            return node.value
    return None


def find_class_with_decorator(tree: ast.Module, decorator_name: str) -> list[ast.ClassDef]:
    """Find a class definition that is marked by a decorator in an AST."""
    nodes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                    nodes.append(node)
    return nodes


def find_class_with_regex(tree: ast.Module, expr: Pattern) -> list[ast.ClassDef]:
    """Find a class definition with a name that matches the regex. """
    nodes = []
    pattern = re.compile(expr)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if pattern.match(node.name):
                nodes.append(node)
    return nodes


def find_method_in_class(classdef: ast.ClassDef, method_name: str) -> list[ast.FunctionDef]:
    """Find all methods named `method_name`."""
    nodes = []
    for node in ast.iter_child_nodes(classdef):
        if isinstance(node, ast.FunctionDef):
            if node.name == method_name:
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


def create_attribute(base_name: str, attr_name: str) -> ast.Attribute:
    """Create an AST node for an attribute"""
    return ast.Attribute(value=ast.Name(id=base_name, ctx=ast.Load()), attr=attr_name, ctx=ast.Load())


def get_node_value(node: Union[ast.expr, ast.Attribute, ast.Constant, ast.Str, ast.Num]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Attribute):
        prefix = get_node_value(node.value)
        if prefix:
            return '.'.join([prefix, node.attr])
        else:
            return node.attr
    else:
        return None
