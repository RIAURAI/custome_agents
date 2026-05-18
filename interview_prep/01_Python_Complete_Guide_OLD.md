# 🐍 Python Complete Interview Guide (10 Years Experience Level)

---

## 📌 Table of Contents
1. [Python Fundamentals (Advanced)](#1-python-fundamentals)
2. [OOP in Python](#2-oop-in-python)
3. [Data Structures & Algorithms](#3-data-structures--algorithms)
4. [Decorators, Generators & Context Managers](#4-decorators-generators--context-managers)
5. [Concurrency & Parallelism](#5-concurrency--parallelism)
6. [Memory Management & GC](#6-memory-management--garbage-collection)
7. [Design Patterns](#7-design-patterns-in-python)
8. [Testing & Debugging](#8-testing--debugging)
9. [Python Internals](#9-python-internals)
10. [Interview Questions & Answers](#10-interview-questions--answers)

---

## 1. Python Fundamentals

### 1.1 Python ka Introduction
- Python ek **high-level, interpreted, dynamically typed** language hai
- **Guido van Rossum** ne 1991 mein banaya
- Current stable version: **Python 3.12+**
- Use hota hai: Web Dev, Data Science, ML/AI, Automation, Scripting

### 1.2 Python 2 vs Python 3
| Feature | Python 2 | Python 3 |
|---------|----------|----------|
| Print | `print "hello"` | `print("hello")` |
| Division | `5/2 = 2` | `5/2 = 2.5` |
| Strings | ASCII by default | Unicode by default |
| Range | `range()` returns list | `range()` returns iterator |

### 1.3 Data Types
```python
# Immutable Types
int_val = 42              # Integer - unlimited precision
float_val = 3.14          # Float - 64-bit double precision
complex_val = 3 + 4j      # Complex number
str_val = "Hello"          # String - immutable sequence
tuple_val = (1, 2, 3)      # Tuple - immutable sequence
frozenset_val = frozenset({1, 2})  # Frozen Set

# Mutable Types
list_val = [1, 2, 3]      # List - mutable sequence
dict_val = {"a": 1}        # Dictionary - key-value pairs
set_val = {1, 2, 3}        # Set - unique elements
bytearray_val = bytearray(b"hello")  # Mutable bytes
```

### 1.4 Mutable vs Immutable - Deep Understanding
```python
# Immutable - naya object banta hai modification pe
a = "hello"
print(id(a))  # 140234866534960
a = a + " world"
print(id(a))  # 140234866535040 (different id = new object)

# Mutable - same object modify hota hai
lst = [1, 2, 3]
print(id(lst))  # 140234866123456
lst.append(4)
print(id(lst))  # 140234866123456 (same id = same object)
```

### 1.5 String Internals
```python
# String Interning - Python caches small strings
a = "hello"
b = "hello"
print(a is b)  # True - same object (interned)

a = "hello world!"
b = "hello world!"
print(a is b)  # False ya True - implementation dependent

# f-strings (Python 3.6+) - fastest string formatting
name = "Ritik"
print(f"Hello {name}")

# String methods important for interviews
s = "Hello World"
s.split()          # ['Hello', 'World']
s.strip()          # whitespace remove
s.replace("H","J") # "Jello World"
s.find("World")    # 6 (index return karta hai)
s.count("l")       # 3
s.startswith("He") # True
s.encode('utf-8')  # b'Hello World'
```

### 1.6 List Comprehension & Advanced
```python
# Basic List Comprehension
squares = [x**2 for x in range(10)]

# Nested Comprehension
matrix = [[1,2,3],[4,5,6],[7,8,9]]
flat = [num for row in matrix for num in row]
# [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Dict Comprehension
word_count = {word: len(word) for word in ["hello", "world"]}

# Set Comprehension
unique_lengths = {len(word) for word in ["hi", "hello", "hey"]}

# Generator Expression (memory efficient - lazy evaluation)
gen = (x**2 for x in range(1000000))  # No memory allocated yet
next(gen)  # 0 - computed on demand
```

### 1.7 *args aur **kwargs
```python
def flexible_func(*args, **kwargs):
    """
    *args   = tuple of positional arguments
    **kwargs = dictionary of keyword arguments
    """
    print(f"Args: {args}")      # (1, 2, 3)
    print(f"Kwargs: {kwargs}")  # {'name': 'Ritik', 'age': 30}

flexible_func(1, 2, 3, name="Ritik", age=30)

# Unpacking
def add(a, b, c):
    return a + b + c

nums = [1, 2, 3]
print(add(*nums))  # 6 - list unpack into positional args

config = {"a": 1, "b": 2, "c": 3}
print(add(**config))  # 6 - dict unpack into keyword args
```

### 1.8 Walrus Operator (:=) - Python 3.8+
```python
# Assignment expression
# Purana tarika
data = input("Enter: ")
while data != "quit":
    print(data)
    data = input("Enter: ")

# Walrus operator se
while (data := input("Enter: ")) != "quit":
    print(data)

# List mein use
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
results = [y for x in numbers if (y := x**2) > 25]
# [36, 49, 64, 81, 100]
```

### 1.9 Type Hints (Python 3.5+)
```python
from typing import List, Dict, Optional, Union, Tuple, Callable

def greet(name: str) -> str:
    return f"Hello {name}"

def process_items(items: List[int]) -> Dict[str, int]:
    return {"sum": sum(items), "count": len(items)}

def find_user(user_id: int) -> Optional[str]:
    """Optional means it can return str or None"""
    users = {1: "Ritik", 2: "Raj"}
    return users.get(user_id)

# Python 3.10+ - Union simplified
def process(data: int | str) -> str:
    return str(data)

# Callable type hint
def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)
```

---

## 2. OOP in Python

### 2.1 Classes & Objects - Complete
```python
class Employee:
    # Class variable (shared by all instances)
    company = "TechCorp"
    _employee_count = 0
    
    def __init__(self, name: str, salary: float):
        # Instance variables
        self.name = name           # Public
        self._salary = salary      # Protected (convention)
        self.__id = id(self)       # Private (name mangling)
        Employee._employee_count += 1
    
    # Instance method
    def get_details(self) -> str:
        return f"{self.name} - {self._salary}"
    
    # Class method - cls refers to class itself
    @classmethod
    def get_count(cls) -> int:
        return cls._employee_count
    
    # Alternative constructor using classmethod
    @classmethod
    def from_string(cls, emp_str: str):
        name, salary = emp_str.split("-")
        return cls(name.strip(), float(salary.strip()))
    
    # Static method - no access to cls or self
    @staticmethod
    def is_valid_salary(salary: float) -> bool:
        return salary > 0
    
    # Property (getter/setter)
    @property
    def salary(self) -> float:
        return self._salary
    
    @salary.setter
    def salary(self, value: float):
        if value < 0:
            raise ValueError("Salary cannot be negative")
        self._salary = value
    
    # Dunder/Magic methods
    def __repr__(self) -> str:
        return f"Employee('{self.name}', {self._salary})"
    
    def __str__(self) -> str:
        return f"{self.name} earns {self._salary}"
    
    def __eq__(self, other) -> bool:
        return self.name == other.name and self._salary == other._salary
    
    def __lt__(self, other) -> bool:
        return self._salary < other._salary
    
    def __len__(self) -> int:
        return len(self.name)
    
    def __del__(self):
        Employee._employee_count -= 1


# Usage
emp = Employee("Ritik", 100000)
emp2 = Employee.from_string("Raj - 90000")  # Alternative constructor
print(emp.salary)       # 100000 (property getter)
emp.salary = 120000     # Property setter
print(Employee.get_count())  # 2
```

### 2.2 Inheritance - Complete Types
```python
# 1. Single Inheritance
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        raise NotImplementedError("Subclass must implement")

class Dog(Animal):
    def speak(self):
        return f"{self.name} says Woof!"

# 2. Multiple Inheritance
class Flyable:
    def fly(self):
        return "I can fly"

class Swimmable:
    def swim(self):
        return "I can swim"

class Duck(Animal, Flyable, Swimmable):
    def speak(self):
        return f"{self.name} says Quack!"

duck = Duck("Donald")
print(duck.fly())    # I can fly
print(duck.swim())   # I can swim
print(duck.speak())  # Donald says Quack!

# 3. MRO (Method Resolution Order) - C3 Linearization
print(Duck.__mro__)
# (<class 'Duck'>, <class 'Animal'>, <class 'Flyable'>, <class 'Swimmable'>, <class 'object'>)

# 4. super() usage
class Manager(Employee):
    def __init__(self, name, salary, department):
        super().__init__(name, salary)  # Parent constructor call
        self.department = department
```

### 2.3 Abstract Classes & Interfaces
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        pass
    
    # Concrete method bhi ho sakta hai
    def description(self) -> str:
        return f"Shape with area {self.area()}"

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius
    
    def area(self) -> float:
        return 3.14159 * self.radius ** 2
    
    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius

# shape = Shape()  # TypeError! Can't instantiate abstract class
circle = Circle(5)
print(circle.area())  # 78.53975
```

### 2.4 Dataclasses (Python 3.7+)
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Product:
    name: str
    price: float
    quantity: int = 0
    tags: List[str] = field(default_factory=list)
    
    # Auto-generated: __init__, __repr__, __eq__
    
    @property
    def total_value(self) -> float:
        return self.price * self.quantity

@dataclass(frozen=True)  # Immutable dataclass
class Point:
    x: float
    y: float

@dataclass(order=True)   # Comparison operators auto-generated
class Student:
    sort_index: float = field(init=False, repr=False)
    name: str
    grade: float
    
    def __post_init__(self):
        self.sort_index = self.grade
```

### 2.5 Metaclasses
```python
# Metaclass = class ka class (class factory)
class SingletonMeta(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self):
        self.connection = "Connected"

db1 = Database()
db2 = Database()
print(db1 is db2)  # True - same instance (Singleton pattern)
```

### 2.6 Descriptors
```python
class Validator:
    """Descriptor protocol implementation"""
    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, f'_{self.name}', None)
    
    def __set__(self, obj, value):
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"{self.name} must be >= {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"{self.name} must be <= {self.max_val}")
        setattr(obj, f'_{self.name}', value)

class Product:
    price = Validator(min_val=0, max_val=10000)
    quantity = Validator(min_val=0)
    
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity
```

---

## 3. Data Structures & Algorithms

### 3.1 Built-in Data Structures - Time Complexity

| Operation | List | Dict | Set | Tuple |
|-----------|------|------|-----|-------|
| Access by index | O(1) | - | - | O(1) |
| Search | O(n) | O(1) avg | O(1) avg | O(n) |
| Insert/Append | O(1) amortized | O(1) avg | O(1) avg | - |
| Delete | O(n) | O(1) avg | O(1) avg | - |
| Sort | O(n log n) | - | - | - |

### 3.2 Collections Module
```python
from collections import (
    defaultdict, OrderedDict, Counter, 
    deque, namedtuple, ChainMap
)

# 1. defaultdict - missing key pe default value
word_count = defaultdict(int)
for word in "hello world hello python hello".split():
    word_count[word] += 1
# defaultdict(<class 'int'>, {'hello': 3, 'world': 1, 'python': 1})

# 2. Counter - counting made easy
counter = Counter("abracadabra")
print(counter.most_common(3))  # [('a', 5), ('b', 2), ('r', 2)]

# 3. deque - double-ended queue (O(1) both ends)
dq = deque([1, 2, 3])
dq.appendleft(0)   # [0, 1, 2, 3]
dq.rotate(1)        # [3, 0, 1, 2] - right rotation

# 4. namedtuple
Point = namedtuple('Point', ['x', 'y'])
p = Point(11, 22)
print(p.x, p.y)  # 11 22

# 5. ChainMap - multiple dicts ko ek mein merge
defaults = {"color": "red", "size": "medium"}
custom = {"color": "blue"}
combined = ChainMap(custom, defaults)
print(combined["color"])  # "blue" (custom gets priority)
print(combined["size"])   # "medium" (from defaults)
```

### 3.3 Sorting Algorithms - Python Implementation
```python
# Python uses Timsort (hybrid of merge sort + insertion sort)
# Time: O(n log n) average and worst
# Space: O(n)

# Custom sorting
students = [("Ritik", 90), ("Raj", 85), ("Priya", 95)]
students.sort(key=lambda x: x[1], reverse=True)
# [('Priya', 95), ('Ritik', 90), ('Raj', 85)]

# Multiple criteria sorting
from operator import itemgetter, attrgetter
students.sort(key=itemgetter(1, 0))

# functools.cmp_to_key for complex comparisons
from functools import cmp_to_key
def compare(a, b):
    if a[1] != b[1]:
        return b[1] - a[1]  # Descending by score
    return (a[0] > b[0]) - (a[0] < b[0])  # Ascending by name

students.sort(key=cmp_to_key(compare))
```

### 3.4 Common Algorithm Patterns
```python
# 1. Two Pointer
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        curr_sum = nums[left] + nums[right]
        if curr_sum == target:
            return [left, right]
        elif curr_sum < target:
            left += 1
        else:
            right -= 1
    return []

# 2. Sliding Window
def max_sum_subarray(arr, k):
    window_sum = sum(arr[:k])
    max_sum = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum

# 3. Binary Search
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# 4. BFS / DFS
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    result = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return result

def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    visited.add(start)
    result = [start]
    for neighbor in graph[start]:
        if neighbor not in visited:
            result.extend(dfs(graph, neighbor, visited))
    return result

# 5. Dynamic Programming
def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]

# Bottom-up DP
def fibonacci_bottom_up(n):
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

---

## 4. Decorators, Generators & Context Managers

### 4.1 Decorators - Complete Guide
```python
import functools
import time

# Basic Decorator
def timer(func):
    @functools.wraps(func)  # Preserve original function metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "Done"

# Decorator with Arguments
def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def greet(name):
    print(f"Hello {name}")

# Class-based Decorator
class CountCalls:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.num_calls = 0
    
    def __call__(self, *args, **kwargs):
        self.num_calls += 1
        print(f"Call {self.num_calls} of {self.func.__name__}")
        return self.func(*args, **kwargs)

@CountCalls
def say_hello():
    print("Hello!")

# Stacking Decorators
@timer
@repeat(times=2)
def complex_task():
    print("Running...")
# Execution order: timer(repeat(2)(complex_task))

# Real-world: Retry Decorator
def retry(max_attempts=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

# Real-world: Cache/Memoize
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(n):
    """Results cache ho jaate hain"""
    return sum(i * i for i in range(n))
```

### 4.2 Generators - Complete Guide
```python
# Generator Function
def fibonacci_gen(limit):
    a, b = 0, 1
    count = 0
    while count < limit:
        yield a
        a, b = b, a + b
        count += 1

# Usage
for num in fibonacci_gen(10):
    print(num, end=" ")  # 0 1 1 2 3 5 8 13 21 34

# Generator Expression
gen = (x**2 for x in range(1000000))
# Memory efficient - values computed lazily

# Generator with send()
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value

acc = accumulator()
next(acc)          # Initialize - returns 0
acc.send(10)       # Returns 10
acc.send(20)       # Returns 30
acc.send(30)       # Returns 60

# yield from (delegation)
def chain(*iterables):
    for it in iterables:
        yield from it

list(chain([1,2], [3,4], [5,6]))  # [1, 2, 3, 4, 5, 6]

# Generator for large file reading
def read_large_file(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

# Pipeline pattern with generators
def read_data(source):
    for item in source:
        yield item

def filter_data(data, condition):
    for item in data:
        if condition(item):
            yield item

def transform_data(data, func):
    for item in data:
        yield func(item)
```

### 4.3 Context Managers
```python
# Using __enter__ and __exit__
class DatabaseConnection:
    def __init__(self, db_url):
        self.db_url = db_url
        self.connection = None
    
    def __enter__(self):
        print(f"Connecting to {self.db_url}")
        self.connection = "active_connection"
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing connection")
        self.connection = None
        # Return True to suppress exceptions
        if exc_type is ValueError:
            print("Handled ValueError")
            return True
        return False

with DatabaseConnection("postgresql://localhost/db") as db:
    print(f"Using {db.connection}")

# Using contextlib
from contextlib import contextmanager

@contextmanager
def timer_context(label):
    start = time.perf_counter()
    try:
        yield  # Code inside 'with' block runs here
    finally:
        end = time.perf_counter()
        print(f"{label}: {end - start:.4f}s")

with timer_context("Heavy computation"):
    sum(range(1000000))

# contextlib.suppress
from contextlib import suppress
with suppress(FileNotFoundError):
    os.remove("nonexistent_file.txt")
```

---

## 5. Concurrency & Parallelism

### 5.1 GIL (Global Interpreter Lock)
```
GIL kya hai?
- CPython mein ek mutex lock hai
- Ek time pe sirf ek thread Python bytecode execute kar sakta hai
- CPU-bound tasks mein threading slow hota hai
- I/O-bound tasks mein threading useful hai (GIL release hota hai I/O pe)

GIL bypass kaise karein?
1. multiprocessing module use karein (separate processes)
2. C extensions use karein (numpy, etc.)
3. Alternative interpreters: PyPy, Jython
4. Python 3.13+ mein free-threaded mode (experimental)
```

### 5.2 Threading
```python
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Basic Threading
def download_file(url):
    print(f"Downloading {url}")
    time.sleep(2)  # Simulate I/O
    print(f"Finished {url}")

# Thread Pool (recommended)
urls = ["url1", "url2", "url3", "url4", "url5"]

with ThreadPoolExecutor(max_workers=3) as executor:
    # map - simple
    results = executor.map(download_file, urls)
    
    # submit - more control
    futures = [executor.submit(download_file, url) for url in urls]
    for future in futures:
        future.result()  # Wait for completion

# Thread Synchronization
lock = threading.Lock()
counter = 0

def increment():
    global counter
    with lock:  # Thread-safe
        temp = counter
        time.sleep(0.001)
        counter = temp + 1

# Semaphore - limit concurrent access
semaphore = threading.Semaphore(3)  # Max 3 concurrent

def limited_task(name):
    with semaphore:
        print(f"Task {name} running")
        time.sleep(1)
```

### 5.3 Multiprocessing
```python
from multiprocessing import Process, Pool, Queue, Manager
import os

# Process Pool
def cpu_heavy_task(n):
    return sum(i * i for i in range(n))

with Pool(processes=4) as pool:
    results = pool.map(cpu_heavy_task, [10**6, 10**6, 10**6, 10**6])
    print(results)

# Queue for inter-process communication
def producer(queue):
    for i in range(5):
        queue.put(i)
    queue.put(None)  # Sentinel

def consumer(queue):
    while True:
        item = queue.get()
        if item is None:
            break
        print(f"Consumed: {item}")

q = Queue()
p1 = Process(target=producer, args=(q,))
p2 = Process(target=consumer, args=(q,))
p1.start()
p2.start()
p1.join()
p2.join()
```

### 5.4 Asyncio
```python
import asyncio
import aiohttp

# Basic async/await
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Running multiple coroutines concurrently
async def main():
    urls = ["http://api1.com", "http://api2.com", "http://api3.com"]
    
    # gather - run all concurrently
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # TaskGroup (Python 3.11+)
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data(urls[0]))
        task2 = tg.create_task(fetch_data(urls[1]))

asyncio.run(main())

# Async Generator
async def async_counter(limit):
    for i in range(limit):
        await asyncio.sleep(0.1)
        yield i

# Async Context Manager
class AsyncDBConnection:
    async def __aenter__(self):
        await asyncio.sleep(0.1)  # Simulate connection
        return self
    
    async def __aexit__(self, *args):
        await asyncio.sleep(0.1)  # Simulate disconnect

# Semaphore for rate limiting
async def limited_fetch(url, semaphore):
    async with semaphore:
        return await fetch_data(url)

async def main():
    sem = asyncio.Semaphore(10)  # Max 10 concurrent
    tasks = [limited_fetch(url, sem) for url in urls]
    await asyncio.gather(*tasks)
```

### 5.5 Comparison Table
| Feature | Threading | Multiprocessing | Asyncio |
|---------|-----------|-----------------|---------|
| Best for | I/O-bound | CPU-bound | I/O-bound (high concurrency) |
| GIL issue | Yes | No (separate processes) | N/A (single thread) |
| Memory | Shared | Separate | Shared |
| Overhead | Low | High | Very Low |
| Debugging | Medium | Hard | Medium |

---

## 6. Memory Management & Garbage Collection

### 6.1 Memory Management
```python
import sys

# Reference Counting
a = [1, 2, 3]
print(sys.getrefcount(a))  # 2 (a + function argument)

b = a  # refcount = 3
del b  # refcount = 2

# Memory size
print(sys.getsizeof([]))      # 56 bytes
print(sys.getsizeof([1,2,3])) # 80 bytes
print(sys.getsizeof({}))      # 64 bytes

# __slots__ - memory optimization for classes
class WithoutSlots:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class WithSlots:
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

# WithSlots uses ~40% less memory per instance
```

### 6.2 Garbage Collection
```python
import gc

# Python uses:
# 1. Reference Counting (primary)
# 2. Generational Garbage Collection (for circular references)

# Circular Reference Example
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

a = Node(1)
b = Node(2)
a.next = b
b.next = a  # Circular reference!
# Reference counting alone can't clean this
# GC's generational collector handles it

# GC Control
gc.disable()   # Disable automatic GC
gc.enable()    # Enable automatic GC
gc.collect()   # Force collection
gc.get_count() # (gen0_count, gen1_count, gen2_count)

# Weak References (don't increase ref count)
import weakref
class Cache:
    pass

obj = Cache()
weak_ref = weakref.ref(obj)
print(weak_ref())  # <Cache object>
del obj
print(weak_ref())  # None (object was collected)
```

---

## 7. Design Patterns in Python

### 7.1 Creational Patterns
```python
# Singleton
class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Factory Method
class PaymentFactory:
    @staticmethod
    def create_payment(payment_type):
        payments = {
            "credit": CreditCardPayment,
            "paypal": PayPalPayment,
            "upi": UPIPayment,
        }
        return payments[payment_type]()

# Builder Pattern
class QueryBuilder:
    def __init__(self):
        self._table = None
        self._conditions = []
        self._limit = None
    
    def table(self, name):
        self._table = name
        return self
    
    def where(self, condition):
        self._conditions.append(condition)
        return self
    
    def limit(self, n):
        self._limit = n
        return self
    
    def build(self):
        query = f"SELECT * FROM {self._table}"
        if self._conditions:
            query += " WHERE " + " AND ".join(self._conditions)
        if self._limit:
            query += f" LIMIT {self._limit}"
        return query

query = (QueryBuilder()
    .table("users")
    .where("age > 18")
    .where("active = true")
    .limit(10)
    .build())
# SELECT * FROM users WHERE age > 18 AND active = true LIMIT 10
```

### 7.2 Structural Patterns
```python
# Decorator Pattern (different from Python decorators)
class Coffee:
    def cost(self):
        return 50
    def description(self):
        return "Plain Coffee"

class MilkDecorator:
    def __init__(self, coffee):
        self._coffee = coffee
    def cost(self):
        return self._coffee.cost() + 20
    def description(self):
        return self._coffee.description() + " + Milk"

coffee = MilkDecorator(Coffee())
print(coffee.description())  # Plain Coffee + Milk
print(coffee.cost())          # 70

# Adapter Pattern
class OldPaymentSystem:
    def make_payment(self, amount):
        return f"Paid {amount} via old system"

class NewPaymentInterface:
    def pay(self, amount, currency):
        pass

class PaymentAdapter(NewPaymentInterface):
    def __init__(self, old_system):
        self.old_system = old_system
    
    def pay(self, amount, currency="INR"):
        return self.old_system.make_payment(f"{amount} {currency}")
```

### 7.3 Behavioral Patterns
```python
# Observer Pattern
class EventManager:
    def __init__(self):
        self._subscribers = {}
    
    def subscribe(self, event_type, listener):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(listener)
    
    def notify(self, event_type, data):
        for listener in self._subscribers.get(event_type, []):
            listener(data)

# Strategy Pattern
class SortStrategy:
    def sort(self, data):
        raise NotImplementedError

class QuickSort(SortStrategy):
    def sort(self, data):
        return sorted(data)  # Simplified

class BubbleSort(SortStrategy):
    def sort(self, data):
        # Bubble sort implementation
        arr = data[:]
        for i in range(len(arr)):
            for j in range(len(arr) - 1 - i):
                if arr[j] > arr[j+1]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
        return arr

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy
    
    def sort(self, data):
        return self._strategy.sort(data)
```

---

## 8. Testing & Debugging

### 8.1 pytest
```python
# test_example.py
import pytest

# Basic Test
def test_addition():
    assert 1 + 1 == 2

# Parameterized Test
@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
])
def test_square(input, expected):
    assert input ** 2 == expected

# Fixtures
@pytest.fixture
def sample_list():
    return [1, 2, 3, 4, 5]

def test_list_sum(sample_list):
    assert sum(sample_list) == 15

# Mock
from unittest.mock import Mock, patch, MagicMock

def test_api_call():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"key": "value"}
        
        # Your function that calls requests.get
        # result = fetch_data("http://api.com")
        # assert result == {"key": "value"}

# Exception Testing
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

# Async Testing
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

### 8.2 Debugging Tools
```python
# 1. pdb - Python Debugger
import pdb
pdb.set_trace()  # Breakpoint set karo

# 2. breakpoint() - Python 3.7+ (recommended)
breakpoint()

# 3. logging (better than print for production)
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# 4. traceback
import traceback
try:
    1/0
except Exception:
    traceback.print_exc()

# 5. Profiling
import cProfile
cProfile.run('my_function()')

# Line profiling
# pip install line_profiler
# @profile
# def my_function():
#     ...
```

---

## 9. Python Internals

### 9.1 How Python Executes Code
```
Source Code (.py)
    ↓
Lexer/Tokenizer (tokens create karta hai)
    ↓
Parser (AST - Abstract Syntax Tree banata hai)
    ↓
Compiler (Bytecode generate karta hai - .pyc files)
    ↓
PVM (Python Virtual Machine - bytecode execute karta hai)
```

```python
# Bytecode dekhne ke liye
import dis
def add(a, b):
    return a + b

dis.dis(add)
# Output:
#   2           0 LOAD_FAST                0 (a)
#               2 LOAD_FAST                1 (b)
#               4 BINARY_ADD
#               6 RETURN_VALUE
```

### 9.2 Python Object Model
```python
# Everything is an object in Python
print(type(42))          # <class 'int'>
print(type(int))         # <class 'type'>
print(type(type))        # <class 'type'>

# isinstance vs type
print(isinstance(True, int))   # True (bool inherits from int)
print(type(True) is int)       # False (exact type check)

# id, type, value - three properties of every object
x = 42
print(id(x))    # Memory address
print(type(x))  # <class 'int'>
print(x)        # 42 (value)
```

### 9.3 Important Python 3.10+ Features
```python
# Structural Pattern Matching (Python 3.10+)
def process_command(command):
    match command:
        case "quit":
            return "Quitting..."
        case "help":
            return "Showing help..."
        case ["go", direction]:
            return f"Going {direction}"
        case {"action": action, "target": target}:
            return f"Doing {action} on {target}"
        case _:
            return "Unknown command"

# Exception Groups (Python 3.11+)
try:
    raise ExceptionGroup("errors", [
        ValueError("bad value"),
        TypeError("wrong type"),
    ])
except* ValueError as eg:
    print(f"Value errors: {eg.exceptions}")
except* TypeError as eg:
    print(f"Type errors: {eg.exceptions}")

# tomllib (Python 3.11+) - TOML parsing built-in
import tomllib
with open("config.toml", "rb") as f:
    config = tomllib.load(f)
```

---

## 10. Interview Questions & Answers

### Q1: Python mein `is` vs `==` ka kya difference hai?
```python
# == checks VALUE equality (calls __eq__)
# is checks IDENTITY (same object in memory)

a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)   # True  (same values)
print(a is b)   # False (different objects)

# Integer caching (-5 to 256)
x = 256
y = 256
print(x is y)   # True (cached)

x = 257
y = 257
print(x is y)   # False (not cached - may vary)
```

### Q2: Deep Copy vs Shallow Copy explain karein
```python
import copy

original = [[1, 2], [3, 4]]

# Shallow Copy - outer list naya, inner lists same reference
shallow = copy.copy(original)
shallow[0].append(99)
print(original)  # [[1, 2, 99], [3, 4]] - AFFECTED!

# Deep Copy - completely new object, nested bhi
original = [[1, 2], [3, 4]]
deep = copy.deepcopy(original)
deep[0].append(99)
print(original)  # [[1, 2], [3, 4]] - NOT affected
```

### Q3: Python mein closure kya hota hai?
```python
def outer(x):
    def inner(y):
        return x + y  # x is "closed over" - remembered
    return inner

add_5 = outer(5)
print(add_5(3))   # 8
print(add_5(10))  # 15

# nonlocal keyword
def counter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

c = counter()
print(c())  # 1
print(c())  # 2
print(c())  # 3
```

### Q4: Python mein Duck Typing kya hai?
```python
# "If it walks like a duck and quacks like a duck, it's a duck"
# Python type check nahi karta, behavior check karta hai

class Duck:
    def speak(self):
        return "Quack!"

class Person:
    def speak(self):
        return "Hello!"

def make_speak(thing):
    # No type check - just calls speak()
    return thing.speak()

print(make_speak(Duck()))    # Quack!
print(make_speak(Person()))  # Hello!
# Both work because both have speak() method
```

### Q5: `@staticmethod` vs `@classmethod` vs instance method?
```python
class MyClass:
    class_var = "I'm shared"
    
    # Instance method - has access to self (instance)
    def instance_method(self):
        return f"Instance: {self}"
    
    # Class method - has access to cls (class)
    @classmethod
    def class_method(cls):
        return f"Class: {cls.class_var}"
    
    # Static method - no access to self or cls
    @staticmethod
    def static_method():
        return "I'm just a function in the class namespace"

# classmethod ka main use: alternative constructors
# staticmethod ka main use: utility functions related to class
```

### Q6: What happens when you import a module in Python?
```
1. sys.modules mein check hota hai (already imported?)
2. Nahi mila toh sys.path mein file search hota hai
3. Module milne pe bytecode compile hota hai (.pyc)
4. Module ka code execute hota hai (top to bottom)
5. Module object sys.modules mein store hota hai
6. Name binding hota hai current namespace mein

Important: Module code sirf FIRST import pe execute hota hai
Subsequent imports cached version use karti hain
```

### Q7: Global Interpreter Lock (GIL) ko detail mein explain karein
```
GIL ek mutex hai jo Python objects ko concurrent access se protect karta hai.

Kyun hai?
- CPython ka memory management thread-safe nahi hai
- Reference counting ko protect karna zaroori hai

Impact:
- Multi-threaded CPU-bound code slow hota hai
- I/O-bound code pe effect kam hota hai (GIL release hota hai I/O operations pe)

Solutions:
1. multiprocessing - separate processes, separate GIL
2. C extensions - GIL release kar sakte hain
3. asyncio - cooperative multitasking
4. sub-interpreters (Python 3.12+)
5. free-threaded Python (3.13+ experimental, PEP 703)
```

### Q8: Python mein memory leak kaise detect aur fix karein?
```python
# Detection Tools:
# 1. tracemalloc
import tracemalloc
tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)

# 2. objgraph
import objgraph
objgraph.show_most_common_types(limit=10)
objgraph.show_growth()  # Show objects that increased

# 3. gc module
import gc
gc.set_debug(gc.DEBUG_LEAK)
gc.collect()

# Common Causes:
# - Circular references
# - Global variables holding large objects
# - Unclosed file handles / connections
# - Growing caches without eviction
# - Event listeners not being removed

# Fix: Use weak references, context managers, LRU cache with maxsize
```

### Q9: Explain LEGB Rule in Python
```python
# LEGB = Local → Enclosing → Global → Built-in

x = "global"  # Global scope

def outer():
    x = "enclosing"  # Enclosing scope
    
    def inner():
        x = "local"  # Local scope
        print(x)      # "local"
    
    inner()
    print(x)  # "enclosing"

outer()
print(x)  # "global"
print(len)  # <built-in function len> (Built-in scope)
```

### Q10: Python mein `__new__` vs `__init__` ka difference?
```python
class MyClass:
    def __new__(cls, *args, **kwargs):
        """
        Object CREATE karta hai (memory allocate)
        Called BEFORE __init__
        Returns the new instance
        """
        print("__new__ called")
        instance = super().__new__(cls)
        return instance
    
    def __init__(self, value):
        """
        Object INITIALIZE karta hai (attributes set)
        Called AFTER __new__
        Returns None
        """
        print("__init__ called")
        self.value = value

obj = MyClass(42)
# Output:
# __new__ called
# __init__ called

# __new__ ka main use: Singleton, immutable types (str, int, tuple) customize karna
```

### Q11: What are Python's dunder/magic methods? List important ones.
```python
# Object Lifecycle
__new__(cls)          # Object creation
__init__(self)        # Object initialization
__del__(self)         # Object destruction (destructor)

# String Representation
__repr__(self)        # Developer representation (unambiguous)
__str__(self)         # User representation (readable)
__format__(self)      # Custom format() behavior

# Comparison
__eq__(self, other)   # ==
__ne__(self, other)   # !=
__lt__(self, other)   # <
__le__(self, other)   # <=
__gt__(self, other)   # >
__ge__(self, other)   # >=

# Arithmetic
__add__(self, other)  # +
__sub__(self, other)  # -
__mul__(self, other)  # *
__truediv__(self, other)  # /

# Container
__len__(self)         # len()
__getitem__(self, key)    # obj[key]
__setitem__(self, key, value)  # obj[key] = value
__contains__(self, item)  # item in obj
__iter__(self)        # iter()
__next__(self)        # next()

# Context Manager
__enter__(self)       # with statement entry
__exit__(self, ...)   # with statement exit

# Callable
__call__(self, ...)   # obj() - object ko function ki tarah call karo

# Attribute Access
__getattr__(self, name)     # attribute not found pe call hota hai
__setattr__(self, name, value)  # attribute set pe call hota hai
__delattr__(self, name)     # del obj.attr pe call hota hai

# Hashing
__hash__(self)        # hash() - dict keys / set members
```

### Q12: What is monkey patching?
```python
# Monkey Patching = runtime pe class/module ko modify karna

class Calculator:
    def add(self, a, b):
        return a + b

# Original behavior
calc = Calculator()
print(calc.add(2, 3))  # 5

# Monkey patch
def new_add(self, a, b):
    print(f"Adding {a} + {b}")
    return a + b

Calculator.add = new_add
print(calc.add(2, 3))  # "Adding 2 + 3" then 5

# Use Cases: Testing mein mocks, third-party library fix
# Drawbacks: Code hard to understand, debugging mushkil
```

### Q13: Explain Python's `with` statement internally
```python
# with statement ye karta hai internally:

# 1. __enter__() call karta hai
# 2. return value ko 'as' variable mein assign karta hai
# 3. Block execute karta hai
# 4. __exit__() call karta hai (exception ho ya na ho)

# Equivalent code:
manager = ContextManager()
value = manager.__enter__()
try:
    # with block code
    pass
except Exception:
    if not manager.__exit__(*sys.exc_info()):
        raise
else:
    manager.__exit__(None, None, None)
```

### Q14: What are coroutines vs generators?
```python
# Generator - data PRODUCE karta hai (yield)
def number_generator():
    yield 1
    yield 2
    yield 3

# Coroutine - data CONSUME bhi karta hai (await)
async def fetch_user(user_id):
    response = await http_client.get(f"/users/{user_id}")
    return response.json()

# Key Differences:
# Generator: yield se values produce karta hai, lazy iteration
# Coroutine: await se async operations handle karta hai
# Generator: next() se advance hota hai
# Coroutine: event loop schedule karta hai
```

### Q15: Python Performance Optimization Tips
```python
# 1. Use built-in functions (C mein implemented hain)
# Bad
total = 0
for x in range(1000):
    total += x
# Good
total = sum(range(1000))

# 2. List comprehension > loop
# Bad
result = []
for x in range(1000):
    result.append(x * 2)
# Good
result = [x * 2 for x in range(1000)]

# 3. Local variables faster than global
def process():
    local_func = len  # Local reference
    for item in big_list:
        local_func(item)  # Faster lookup

# 4. Use generators for large datasets
# Bad - loads everything in memory
data = [process(x) for x in huge_list]
# Good - lazy evaluation
data = (process(x) for x in huge_list)

# 5. String concatenation
# Bad
result = ""
for s in strings:
    result += s  # Creates new string each time
# Good
result = "".join(strings)

# 6. Use __slots__ for memory
# 7. Use collections.deque for queue operations
# 8. Use numpy for numerical computations
# 9. Profile before optimizing (cProfile, line_profiler)
# 10. Use functools.lru_cache for expensive computations
```

---

## Quick Revision - One Liners

| Concept | Key Point |
|---------|-----------|
| GIL | One thread executes Python bytecode at a time |
| `is` vs `==` | `is` checks identity, `==` checks value |
| Mutable | list, dict, set (in-place modify ho sakte hain) |
| Immutable | int, str, tuple, frozenset (new object banta hai) |
| `*args` | Tuple of positional arguments |
| `**kwargs` | Dict of keyword arguments |
| Decorator | Function jo function ko modify kare |
| Generator | Lazy iterator using yield |
| Context Manager | `__enter__` + `__exit__` (with statement) |
| Metaclass | Class of a class (controls class creation) |
| Descriptor | `__get__`, `__set__`, `__delete__` protocol |
| MRO | Method Resolution Order (C3 Linearization) |
| LEGB | Local → Enclosing → Global → Built-in |
| Closure | Inner function remembering outer scope |
| Duck Typing | Check behavior, not type |
| Monkey Patching | Runtime modification of classes/modules |

---

*Document prepared for 10+ years experience level Python interview*
