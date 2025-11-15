import re


class CurlyParserEnhanced:

    decorator_alias: dict[str, str] = {
        "static": "staticmethod",
        "virtual": "abstractmethod",
        "struct": "dataclasses",
    }

    auto_imports: dict[str, str] = {
        "virtual": "from abc import abstractmethod",
        "struct": "from dataclasses import dataclass",
    }

    def __init__(self) -> None:
        self.required_imports: set[str] = set()

    def mark_comment_ends(self, code):
        """在每行注释结束位置做标记"""
        lines = code.split("\n")
        marked_lines = []

        for line in lines:
            if "#" in line:
                # 在注释开始位置插入特殊标记
                parts = line.split("#", 1)
                marked_line = parts[0] + "#" + parts[1] + "¶"  # 标记注释结束
                marked_lines.append(marked_line)
            else:
                marked_lines.append(line)

        return "\n".join(marked_lines)

    def restore_comment_ends(self, code):
        """将注释结束标记替换为换行+当前缩进"""
        lines = code.split("\n")
        restored_lines = []

        for line in lines:
            if "¶" in line:
                # 计算当前行的缩进
                indent_match = re.match(r"^(\s*)", line)
                indent = indent_match.group(1) if indent_match else ""
                # 替换标记为换行+相同缩进
                line = indent + line.strip().replace("¶", "\n" + indent[:-1])
            restored_lines.append(line)

        return "\n".join(restored_lines)

    def preprocess_code(self, code) -> str:
        """将所有连续空白（空格、tab、换行）替换为单个空格"""
        code = self.mark_comment_ends(code)
        code = re.sub(r"\s+", " ", code)
        return code.strip()

    def final_syntax_cleanup(self, code):
        lines = code.split("\n")
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
                mod_list = modifiers.strip().split()
                decorators = [
                    f"{indent}@{self.decorator_alias.get(mod.strip(), mod.strip())}"
                    for mod in mod_list
                ]

                # 处理自动导入（def 和 class 都需要）
                self.required_imports.update(
                    mod.strip()
                    for mod in mod_list
                    if mod.strip() in self.auto_imports
                )

                # 重构定义行
                new_def = re.sub(
                    rf"^\s*.+\s+{keyword}", f"{indent}{keyword}", stripped
                )

                new_lines.extend(decorators)
                new_lines.append(new_def)
            else:
                new_lines.append(line)

        return "\n".join(new_lines)

    def replace_double_colon(self, text) -> str:
        # 使用单词边界\b来确保变量名的边界
        pattern = r"\b([a-zA-Z_][a-zA-Z0-9_]*)::([a-zA-Z_][a-zA-Z0-9_]*)\b"

        def replacer(match) -> str:
            return f"{match.group(1)}.{match.group(2)}"

        # 需要多次应用来处理多重作用域
        old_text = ""
        while old_text != text:
            old_text = text
            text = re.sub(pattern, replacer, text)

        return text

    def extra_imports(self) -> str:
        ret: list[str] = []
        for import_str in self.required_imports:
            ret.append(f"{self.auto_imports[import_str]}")
        if ret:
            return "\n".join(ret) + "\n\n"
        else:
            return ""

    def convert(self, code) -> str:
        # 预处理
        code = self.preprocess_code(code)

        # 缩进匹配大括号
        no_more_spaces: bool = False
        in_string = False
        string_char = None  # 记录字符串引号类型 ' 或 "
        in_comment = False
        output = []
        indent_level = 0
        i = 0
        length = len(code)

        while i < length:
            char = code[i]

            # 处理字符串状态
            if in_string:
                output.append(char)
                # 检查字符串结束（匹配相同的引号）
                if char == string_char:
                    # 检查转义字符，如果是转义的引号则不结束字符串
                    if i > 0 and code[i - 1] == "\\":
                        pass  # 转义引号，继续字符串
                    else:
                        in_string = False
                        string_char = None
                i += 1
                continue

            # 处理注释状态
            if in_comment:
                output.append(char)
                # 注释在换行时结束
                if char == "\n":
                    in_comment = False
                i += 1
                continue

            # 检查字符串开始（非转义的引号）
            if char in ['"', "'"]:
                # 检查是否是转义的引号
                if i > 0 and code[i - 1] == "\\":
                    output.append(char)
                else:
                    in_string = True
                    string_char = char
                    output.append(char)
                i += 1
                continue

            # 大括号处理
            if char == "{":
                output.append(":")
                indent_level += 1
                output.append("\n" + " " * (indent_level * 4))
                no_more_spaces = True

            elif char == "}":
                indent_level -= 1
                output.append("\n" + " " * (indent_level * 4))
                in_else = False
                no_more_spaces = True

            elif char == ";":
                output.append("\n" + " " * (indent_level * 4))
                no_more_spaces = True

            elif char == " " and no_more_spaces:
                no_more_spaces = False

            else:
                output.append(char)
                no_more_spaces = False

            if output[-7:] == list("else if"):
                for _ in range(7):
                    output.pop()
                output.append("elif")
            elif output[-2:] == ["+", "+"]:
                output.pop()
                output.pop()
                output.append("+= 1")

            elif output[-2:] == ["-", "-"]:
                output.pop()
                output.pop()
                output.append("-= 1")

            i += 1

        code = "".join(output).strip()
        code = self.final_syntax_cleanup(code)
        code = self.replace_double_colon(code)
        code = self.restore_comment_ends(code)
        code = self.extra_imports() + code

        return code
