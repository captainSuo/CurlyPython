import re
from typing import Self
from xml.parsers.expat import model
from .parser import CurlyParser


class CurlyParserEnhanced(CurlyParser):

    decorator_alias: dict[str, str] = {
        "static": "staticmethod",
        "virtual": "abstractmethod",
        "struct": "dataclass",
    }

    auto_imports: dict[str, str] = {
        "virtual": "from abc import abstractmethod",
        "struct": "from dataclasses import dataclass",
    }

    def __init__(self) -> None:
        super().__init__()
        self.required_imports: set[str] = set()

    def parse_decorator(self) -> Self:
        lines = self.code.split("\n")
        new_lines = []

        for line in lines:
            # 计算当前行的缩进
            indent_match = re.match(r"^(\s*)", line)
            indent = indent_match.group(1) if indent_match else ""

            stripped = line.strip()

            pattern = r"^\s*(.+)\s+(def|class)\s+(\w+)(?:\s*\([^)]*\)\s*:)?\s*:?"
            match = re.match(pattern, stripped)

            if match:
                modifiers, keyword, name = match.groups()

                # 构建装饰器和处理导入
                mod_list = [
                    mod.strip()
                    for mod in modifiers.strip().split()
                    if mod.strip() != "async"
                ]

                if mod_list:
                    decorators = [
                        f"{indent}@{self.decorator_alias.get(mod, model)}"
                        for mod in mod_list
                    ]

                    # 处理自动导入
                    self.required_imports.update(
                        mod.strip()
                        for mod in mod_list
                        if mod.strip() in self.auto_imports
                    )

                    # 重构定义行，保留async关键字
                    # 重新构建定义行，保留原有的async（如果有的话）
                    has_async = "async" in modifiers
                    async_prefix = "async " if has_async else ""

                    # 使用原始行的内容来保留async
                    original_def = re.sub(
                        rf"^\s*.+\s+{keyword}",
                        f"{indent}{async_prefix}{keyword}",
                        stripped,
                    )

                    new_lines.extend(decorators)
                    new_lines.append(original_def)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        self.code = "\n".join(new_lines)
        return self

    def replace_double_colon(self) -> Self:
        # 使用单词边界\b来确保变量名的边界
        pattern = r"\b([a-zA-Z_][a-zA-Z0-9_]*)::([a-zA-Z_][a-zA-Z0-9_]*)\b"

        def replacer(match) -> str:
            return f"{match.group(1)}.{match.group(2)}"

        text = self.code

        # 需要多次应用来处理多重作用域
        old_text = ""
        while old_text != text:
            old_text = text
            text = re.sub(pattern, replacer, text)

        self.code = text
        return self

    def extra_imports(self) -> Self:
        ret: list[str] = []
        for import_str in self.required_imports:
            ret.append(f"{self.auto_imports[import_str]}")
        if ret:
            self.code = "\n".join(ret) + "\n\n" + self.code
        return self

    def convert(self, code) -> str:
        self.code = code
        (
            self.mark_comments()
            .mark_strings()
            .preprocess_code()
            .handle_indent()
            .replace_basic_syntax()
            .replace_double_colon()
            .parse_decorator()
            .extra_imports()
            .restore_strings()
            .restore_comments()
        )
        code = self.code
        self.code = ""
        return code
