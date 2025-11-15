import re
from typing import Self


class CurlyParser:

    def __init__(self) -> None:
        self.comments: list[str] = []
        self.strings: list[str] = []
        self.code: str = ""

    def mark_comments(self) -> Self:
        """提取注释并用索引标记替换"""
        lines = self.code.split("\n")
        marked_lines = []

        for line in lines:
            if "#" in line:
                # 分割代码和注释
                code_part, comment_part = line.split("#", 1)
                comment_content = comment_part.rstrip()

                # 保存注释内容
                self.comments.append(comment_content)

                # 用索引标记替换整个注释
                comment_index = len(self.comments) - 1
                marked_line = f"{code_part.rstrip()} #__COMMENT_{comment_index}__;"
                marked_lines.append(marked_line)
            else:
                marked_lines.append(line)

        self.code = "\n".join(marked_lines)
        return self

    def restore_comments(self) -> Self:
        """恢复注释内容"""
        import re

        def replace_comment(match):
            index = int(match.group(1))
            if index < len(self.comments):
                return f"#{self.comments[index]}"
            return match.group(0)

        # 替换所有注释标记
        self.code = re.sub(r"#__COMMENT_(\d+)__", replace_comment, self.code)
        return self

    def mark_strings(self) -> Self:
        """提取字符串并用索引标记替换"""
        import re

        # 存储字符串内容
        self.strings = []

        # 处理双引号字符串
        double_pattern = r'"(?:\\.|[^"\\])*"'
        double_matches = list(re.finditer(double_pattern, self.code))
        for i, match in enumerate(reversed(double_matches)):
            string_content = match.group(0)
            self.strings.append(string_content)
            placeholder = f"__$STRING_{len(self.strings)-1}__"
            start, end = match.span()
            self.code = self.code[:start] + placeholder + self.code[end:]

        # 处理单引号字符串
        single_pattern = r"'(?:\\.|[^'\\])*'"
        single_matches = list(re.finditer(single_pattern, self.code))
        for i, match in enumerate(reversed(single_matches)):
            string_content = match.group(0)
            self.strings.append(string_content)
            placeholder = f"__$STRING_{len(self.strings)-1}__"
            start, end = match.span()
            self.code = self.code[:start] + placeholder + self.code[end:]

        return self

    def restore_strings(self) -> Self:
        """恢复字符串内容"""
        import re

        def replace_string(match):
            index = int(match.group(1))
            if index < len(self.strings):
                return self.strings[index]
            return match.group(0)

        # 替换所有字符串标记
        self.code = re.sub(r"__\$STRING_(\d+)__", replace_string, self.code)
        return self

    def preprocess_code(self) -> Self:
        """将所有连续空白（空格、tab、换行）替换为单个空格"""
        self.code = re.sub(r"\s+", " ", self.code).strip()
        return self

    def handle_indent(self) -> Self:
        # 缩进匹配大括号
        no_more_spaces: bool = False
        in_string = False
        string_char = None  # 记录字符串引号类型 ' 或 "
        in_comment = False
        output = []
        indent_level = 0
        i = 0
        length = len(self.code)

        while i < length:
            char = self.code[i]

            # 处理字符串状态
            if in_string:
                output.append(char)
                # 检查字符串结束（匹配相同的引号）
                if char == string_char:
                    # 检查转义字符，如果是转义的引号则不结束字符串
                    if i > 0 and self.code[i - 1] == "\\":
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
                if i > 0 and self.code[i - 1] == "\\":
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

            i += 1

        self.code = "".join(output).strip()
        return self

    def replace_basic_syntax(self) -> Self:

        self.code = re.sub(r"\belse\s+if\b", "elif", self.code)
        self.code = re.sub(r"(\w+)\+\+", r"(\1 := \1 + 1) - 1", self.code)
        self.code = re.sub(r"\+\+(\w+)", r"(\1 := \1 + 1)", self.code)
        self.code = re.sub(r"(\w+)\-\-", r"(\1 := \1 - 1) + 1", self.code)
        self.code = re.sub(r"\-\-(\w+)", r"(\1 := \1 - 1)", self.code)

        return self

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
                mod_list = modifiers.strip().split()
                decorators = [f"{indent}@{mod.strip()}" for mod in mod_list]

                # 重构定义行
                new_def = re.sub(
                    rf"^\s*.+\s+{keyword}", f"{indent}{keyword}", stripped
                )

                new_lines.extend(decorators)
                new_lines.append(new_def)
            else:
                new_lines.append(line)

        self.code = "\n".join(new_lines)

        return self

    def convert(self, code) -> str:
        self.code = code
        (
            self.mark_comments()
            .mark_strings()
            .preprocess_code()
            .handle_indent()
            .replace_basic_syntax()
            .parse_decorator()
            .restore_strings()
            .restore_comments()
        )
        code = self.code
        self.code = ""
        return code
