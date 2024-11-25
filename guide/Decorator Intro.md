# Python 裝飾器（Decorator）完整指南

## 1. 基本概念

裝飾器是 Python 中的一種語法糖（Syntactic Sugar），它允許我們修改或增強函式的行為而不改變其原始程式碼。本質上，裝飾器是一個接受函式作為參數並回傳函式的函式。

### 1.1 最簡單的裝飾器

```python
def simple_decorator(func):
    def wrapper():
        print("在函式執行前")
        func()
        print("在函式執行後")
    return wrapper

# 使用裝飾器
@simple_decorator
def hello():
    print("Hello, World!")

# 執行
hello()

# 輸出：
# 在函式執行前
# Hello, World!
# 在函式執行後
```

### 1.2 裝飾器的本質

上面的 `@simple_decorator` 語法實際上等同於：

```python
def hello():
    print("Hello, World!")
hello = simple_decorator(hello)
```

## 2. 進階用法

### 2.1 帶參數的函式裝飾器

```python
def logging_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"呼叫 {func.__name__} 函式")
        print(f"參數：args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"返回值：{result}")
        return result
    return wrapper

@logging_decorator
def add(a, b):
    return a + b

# 執行
result = add(3, 5)

# 輸出：
# 呼叫 add 函式
# 參數：args=(3, 5), kwargs={}
# 返回值：8
```

### 2.2 帶參數的裝飾器

```python
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def greet(name):
    print(f"Hello, {name}!")

# 執行
greet("Alice")

# 輸出：
# Hello, Alice!
# Hello, Alice!
# Hello, Alice!
```

## 3. 實用技巧

### 3.1 保留函式資訊

使用 `functools.wraps` 保留原始函式的資訊：

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)  # 保留原始函式的資訊
    def wrapper(*args, **kwargs):
        """wrapper 函式的文件字串"""
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def example():
    """example 函式的文件字串"""
    pass

# 不使用 @wraps 時：print(example.__doc__) 會顯示 "wrapper 函式的文件字串"
# 使用 @wraps 後：print(example.__doc__) 會顯示 "example 函式的文件字串"
```

### 3.2 類別方法的裝飾器

```python
def method_decorator(method):
    def wrapper(self, *args, **kwargs):
        print(f"正在呼叫 {self.__class__.__name__} 的 {method.__name__} 方法")
        return method(self, *args, **kwargs)
    return wrapper

class MyClass:
    @method_decorator
    def my_method(self, x):
        return x * 2

# 執行
obj = MyClass()
result = obj.my_method(5)

# 輸出：
# 正在呼叫 MyClass 的 my_method 方法
```

## 4. 實際應用範例

### 4.1 計時裝飾器

```python
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 執行時間：{end_time - start_time:.4f} 秒")
        return result
    return wrapper

@timing_decorator
def slow_function():
    time.sleep(1)
    return "完成"

# 執行
slow_function()
# 輸出：slow_function 執行時間：1.0012 秒
```

### 4.2 錯誤處理裝飾器

```python
def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"錯誤：在執行 {func.__name__} 時發生 {str(e)}")
            return None
    return wrapper

@error_handler
def divide(a, b):
    return a / b

# 執行
result = divide(10, 0)
# 輸出：錯誤：在執行 divide 時發生 division by zero
```

### 4.3 快取裝飾器

```python
def memoize(func):
    cache = {}
    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 執行
print(fibonacci(10))  # 第一次計算
print(fibonacci(10))  # 從快取中取得結果
```

## 5. 注意事項

1. **順序問題**：多個裝飾器的執行順序是從下到上的：
```python
@decorator1
@decorator2
def function():
    pass

# 等同於：
function = decorator1(decorator2(function))
```

2. **參數傳遞**：確保正確處理所有可能的參數形式：
```python
def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):  # 使用 *args 和 **kwargs 處理任意參數
        return func(*args, **kwargs)
    return wrapper
```

3. **副作用**：注意裝飾器可能帶來的副作用，特別是在處理類別方法時。

4. **效能影響**：裝飾器會增加函式呼叫的開銷，在效能關鍵的場景需要謹慎使用。

## 6. 最佳實踐

1. 總是使用 `@wraps` 裝飾器來保留原始函式的元資料。
2. 確保裝飾器是可重用的，避免過度耦合。
3. 適當使用文件字串說明裝飾器的功能。
4. 考慮裝飾器的錯誤處理機制。

Author: Zi-Liang Yang