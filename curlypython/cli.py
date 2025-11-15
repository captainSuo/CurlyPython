import argparse
import sys


def run_curly_code(code):
    # 创建新的全局命名空间
    global_namespace = {"__name__": "__main__", "__file__": None}
    exec(code, global_namespace)


def main():
    parser = argparse.ArgumentParser(description="CurlyPython - 用大括号写Python")
    parser.add_argument("input", help="input file (.curpy)")
    parser.add_argument("-o", "--output", help="output file")
    parser.add_argument(
        "-E", "--enhanced", help="enable enhanced mode", action="store_true"
    )

    args = parser.parse_args()

    if args.enhanced:
        from .parser_enhanced import CurlyParserEnhanced

        convertor = CurlyParserEnhanced()
    else:
        from .parser import CurlyParser

        convertor = CurlyParser()

    # 读取输入文件
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: '{args.input}'")
        return 1

    # 转换代码
    python_code = convertor.convert(code)

    # 输出或运行
    if not args.output:
        try:
            run_curly_code(python_code)
        except SyntaxError as e:
            print("Curpy Error: invalid or unsupported syntax")
            raise e
        except Exception as e:
            print("Runtime Error:")
            raise e
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(python_code)
        print(f"Parsed: {args.input} -> {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
