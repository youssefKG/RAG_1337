import ast
from pathlib import Path
from typing import override

project_path: Path = Path("vllm-0.10.1")
projects_asts: list[ast.Module] = list()


def hello_world() -> None:
    print("hello world")


chunks: list[str] = list()
CHUNK_SIZE: int = 200


class AstVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.__visited_functions: set[int] = set()
        self.functions: list[str] = list()
        self.imports: list[str] = list()
        self.classes: list[str] = list()

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if id(node) not in self.__visited_functions:
            self.functions.append(ast.unparse(node))
            self.generic_visit(node)

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for n in node.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.__visited_functions.add(id(n))
        self.classes.append(ast.unparse(node))
        self.generic_visit(node)

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if id(node) not in self.__visited_functions:
            self.functions.append(ast.unparse(node))
            self.generic_visit(node)

    @override
    def visit_Import(self, node: ast.Import) -> None:
        self.imports.append(ast.unparse(node))
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.append(ast.unparse(node))
        self.generic_visit(node)


with open("tests/ast_test.py") as file:
    file_content: str = file.read()
    tree = ast.parse(file_content)
    class_node: ast.AST | None = None
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.ClassDef)):
            class_node = node
            break
    if class_node:
        for child_node in ast.iter_child_nodes(class_node):
            print("_" * 10)
            print(ast.unparse(child_node))
