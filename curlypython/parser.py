import re


class CurlyParser:

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

            if re.match(r"^\s*.+\s+def\s+\w+\s*\([^)]*\)\s*:", stripped):
                # 提取缩进和修饰符
                modifiers = re.findall(r"^\s*(.+)(?=\s+def)", stripped)[0].strip()
                # 构建装饰器和方法定义，将static替换为staticmethod
                decorators = [
                    f"{indent}@{'staticmethod' if modifier.strip() == 'static' else modifier.strip()}"
                    for modifier in modifiers.split()
                ]
                method_def = re.sub(r"^(\s*).+\s+def", f"{indent}def", stripped)
                # 添加装饰器和原方法定义
                new_lines.extend(decorators)
                new_lines.append(method_def)
            elif re.match(r"^\s*.+\s+class\s+\w+", stripped):
                # 提取缩进和修饰符
                modifiers = re.findall(r"^\s*(.+)(?=\s+class)", stripped)[0].strip()
                # 构建装饰器
                decorators = [
                    f"{indent}@{modifier.strip()}" for modifier in modifiers.split()
                ]
                # 移除修饰符，保留纯 class 定义
                class_def = re.sub(r"^(\s*).+\s+class", f"{indent}class", stripped)
                # 添加装饰器和原类定义
                new_lines.extend(decorators)
                new_lines.append(class_def)
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

    def convert(self, code):
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

        return code
