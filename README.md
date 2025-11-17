# CurlyPython

用大括号风格写 Python 的奇妙小工具

## 这是什么？

一个让 Python 支持大括号语法的转换工具：
#### 这样写 Python
```javascript
def main() {
    for i in range(5) {
        if (i % 2 == 0) {
            print(f"{i} is even");
        } else {
            print(f"{i} is odd");
        }
    }
}

class Calculator {
    def __init__(self, value = 0) {
        self._value = value;
    }
    
    def add(self, x) {
        self._value += x;
        return self;
    }
    
    staticmethod def helper() {
        return "I'm a static method";
    }

    property def value(self) {
        return self._value;
    }
}
```

#### 甚至这样
```javascript
def main() {for i in range(5) {if (i % 2 == 0) {print(f"{i} is even");} else {print(f"{i} is odd");}}}class Calculator {def __init__(self, value = 0) {self.value = value or 0}def add(self, x) {self.value += x;return self;}staticmethod def helper() {return "I'm a static method";}}

```

## 特色功能

- ✅ 大括号自动转缩进
- ✅ 静态方法支持
- ✅ 装饰器支持
- ✅ 增量赋值支持
- 🚧 更多语法糖陆续添加...

### 注意

这只是一个趣味项目：
- 不是真正的编译器
- 不追求完整语法兼容  
- 核心是让 Python 支持大括号写法

适合：
- 喜欢大括号的程序员
- 想换个风格写 Python



## 安装使用

```bash
# 运行文件
curpy my_script.curpy

# 解析为 python
curpy my_script.curpy -o my_script.py
```

## 语法对照

| CurlyPython | Python |
|-------------|--------|
| `def foo() { ... }` | `def foo(): ...` |
| `if (x) { ... }` | `if x: ...` |
| `class Bar { ... }` | `class Bar: ...` |
| `decorator class/def` | `@decorator` + `class/def` |
| `i++` / `i--`| `i += 1` / `i -= 1` |
| `else if` / `elif`| `elif`|

* 注意 ： 所有`def`和`class`前的内容都会被解析为装饰器，支持多重装饰器
* 注意 ： 语法不支持**列表推导式**及**字典推导式**

## 扩展功能
如果在使用时加上`-E`参数，则开启扩展功能
```bash
curpy my_script.curpy -E
```

### 扩展功能语法
| CurlyPython | Python |
|-------------|--------|
| `static def` | `@staticmethod` |
| `virtual def` | `@abstractmethod` |
| `struct class`| `@dataclass` |
| `MyClass::method()`| `MyClass.method()` |

* 注意 ： 解析器会自动处理导入

#### 示例
```javascript
class MyClass() {
    virtual static def hello() {
        print("Hello, world!");
    }
}
```

#### 转换后
```python
from abc import abstractmethod

class MyClass() :
    @abstractmethod
    @staticmethod
    def hello() :
        print("Hello, world!")
```
