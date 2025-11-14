import argparse
import sys
from .parser import CurlyParser


def main():
    parser = argparse.ArgumentParser(description="CurlyPython - 用大括号写Python")
    parser.add_argument("input", help="输入文件 (.curpy)")
    parser.add_argument("-o", "--output", help="输出文件")

    convertor = CurlyParser()

    args = parser.parse_args()

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
            exec(python_code)
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
