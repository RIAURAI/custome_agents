# 🐍 Python Complete Theory Guide (10 Years Experience Level)

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
- Python **interpreted** hai — source code pehle bytecode mein compile hota hai (.pyc), phir Python Virtual Machine (PVM) pe execute hota hai
- **Dynamically typed:** Variable ka type runtime pe decide hota hai, declaration mein type specify nahi karna
- **Strongly typed:** Implicit type conversion nahi hota (e.g., string + int directly nahi kar sakte)
- **Multi-paradigm:** OOP, Functional, Procedural — teeno support karta hai

### 1.2 Python 2 vs Python 3

| Feature | Python 2 | Python 3 |
|---------|----------|----------|
| Print | Statement (print "hello") | Function (print("hello")) |
| Division | Integer division (5/2 = 2) | True division (5/2 = 2.5) |
| Strings | ASCII by default | Unicode by default |
| Range | range() returns list | range() returns iterator (memory efficient) |
| Exception | except Exception, e | except Exception as e |
| Input | raw_input() | input() |
| End of Life | January 2020 | Active development |

### 1.3 Data Types

**Immutable Types (modify nahi ho sakte — naya object banta hai):**
- **int:** Integer — unlimited precision (Python 3 mein no overflow)
- **float:** 64-bit double precision floating point
- **complex:** Complex number (real + imaginary part, e.g., 3+4j)
- **str:** String — Unicode characters ka immutable sequence
- **tuple:** Ordered, immutable sequence — hashable, dictionary key ban sakta hai
- **frozenset:** Immutable version of set — hashable
- **bytes:** Immutable byte sequence

**Mutable Types (in-place modify ho sakte hain):**
- **list:** Ordered, mutable sequence — dynamic array internally
- **dict:** Key-value pairs — hash table based (Python 3.7+ insertion order preserved)
- **set:** Unordered unique elements — hash table based
- **bytearray:** Mutable byte sequence

**None Type:** Singleton object — absence of value represent karta hai. `None` ek object hai, null nahi.

### 1.4 Mutable vs Immutable - Deep Understanding
- **Immutable:** Jab aap immutable object modify karte ho, ek naya object banta hai naye memory address pe. Purana object wahi rehta hai (if referenced).
- **Mutable:** Same object in-place update hota hai — memory address same rehta hai.
- **Why it matters:** Function arguments pass-by-object-reference hote hain. Agar mutable object pass kiya aur function mein modify kiya, toh original bhi change hoga. Immutable mein aisa nahi hota.
- **Default argument trap:** Function ke default argument mein mutable object (list, dict) use karna dangerous — sharing hota hai across function calls.
- **id() function:** Object ka memory address return karta hai — same id matlab same object.

### 1.5 String Internals
- **String Interning:** Python chhote strings ("hello") ko cache karta hai — same content ke liye same object reuse hota hai. Yeh optimization hai.
- **`is` vs `==`:** `is` checks identity (same object), `==` checks equality (same value). Strings ke liye `==` use karo, `is` nahi.
- **f-strings (Python 3.6+):** Sabse fast string formatting method. format() aur % se faster hai.
- **String methods:** Strings immutable hain, toh har method naya string return karta hai (replace, upper, strip, etc.)
- **String concatenation:** Loop mein + se concatenate karna O(n²) hai — join() method use karo (O(n))

### 1.6 List Comprehension & Advanced
- **List Comprehension:** Concise way to create lists — regular loop se faster (C level optimization)
- **Dict Comprehension:** Dictionary create karna concisely
- **Set Comprehension:** Unique elements ka set create karna
- **Generator Expression:** Parentheses mein — memory efficient, lazy evaluation
- **Nested Comprehension:** Matrix operations, flattening ke liye
- **Comprehension vs map/filter:** Readability ke liye comprehension better, but complex cases mein map/filter bhi useful
- **When NOT to use:** Jab logic complex ho jaye — readability > cleverness

### 1.7 *args aur **kwargs
- ***args:** Variable number of positional arguments accept karta hai — tuple ke form mein milte hain
- ****kwargs:** Variable number of keyword arguments accept karta hai — dictionary ke form mein milte hain
- **Order in function signature:** normal args → *args → keyword-only args → **kwargs
- **Unpacking:** * se list/tuple unpack, ** se dict unpack kar sakte hain function call mein
- **Use cases:** Decorators, inheritance (super().__init__(*args, **kwargs)), flexible APIs

### 1.8 Walrus Operator (:=) - Python 3.8+
- **Assignment expression:** Variable assign karo aur simultaneously use karo ek expression mein
- **Use cases:** While loops mein (read + check), list comprehension mein (compute once + filter), if conditions mein (assign + check)
- **Tradeoff:** Convenient but overuse se readability kam hoti hai
- Controversial feature — PEP 572 ki bahut debate hui thi

### 1.9 Type Hints (Python 3.5+)
- **Static type annotations:** Runtime pe enforce nahi hote — documentation aur tool support ke liye
- **Basic types:** int, str, float, bool
- **typing module:** List, Dict, Tuple, Optional, Union, Any, Callable
- **Optional[X]:** X ya None — same as Union[X, None]
- **Type checking tools:** mypy, pyright, pytype — static analysis karte hain
- **Python 3.10+:** Union X | Y syntax, built-in types as generics (list[int] instead of List[int])
- **Protocol (Python 3.8+):** Structural subtyping — duck typing ko type hints ke saath
- **TypeVar:** Generic types ke liye
- **Benefits:** Better IDE support, early bug detection, self-documenting code

---

## 2. OOP in Python

### 2.1 Classes & Objects - Complete

**Core Concepts:**
- **Class:** Blueprint/template — attributes aur methods define karta hai
- **Object/Instance:** Class ka actual instance — memory mein exist karta hai
- **self:** Current instance ka reference — har instance method mein first parameter
- **__init__:** Constructor — object creation pe automatically call hota hai
- **__new__:** Object creation (memory allocate) — __init__ se pehle call hota hai

**Four Pillars of OOP:**
1. **Encapsulation:** Data aur methods ko ek unit mein bundle karna. Access control through naming conventions:
   - `public` — normal name
   - `_protected` — single underscore (convention, not enforced)
   - `__private` — double underscore (name mangling: _ClassName__attr)
2. **Abstraction:** Complex implementation hide karo, simple interface dikaho
3. **Inheritance:** Parent class ke features child class mein reuse
4. **Polymorphism:** Same interface, different implementation

**Instance vs Class vs Static:**
- **Instance variables:** Har object ke apne — self.name
- **Class variables:** Sabhi objects share karein — class level pe define
- **Instance method:** self milta hai — instance pe kaam karta hai
- **@classmethod:** cls milta hai — class pe kaam karta hai. Factory methods ke liye useful
- **@staticmethod:** Na self na cls — utility function jo class se logically related hai

**Property Decorator:**
- Getter/Setter/Deleter ko Pythonic way mein implement karo
- @property: Getter. @name.setter: Setter. @name.deleter: Deleter
- Direct attribute access jaisa dikhta hai but method call hota hai internally
- Validation, computed properties ke liye use hota hai

**Magic/Dunder Methods (Important ones):**
- `__init__`: Constructor
- `__repr__`: Developer-friendly string (unambiguous)
- `__str__`: User-friendly string (readable)
- `__len__`: len() support
- `__getitem__`, `__setitem__`: Indexing/subscript support
- `__iter__`, `__next__`: Iterator protocol
- `__eq__`, `__lt__`, `__gt__`: Comparison operators
- `__add__`, `__mul__`: Arithmetic operators
- `__enter__`, `__exit__`: Context manager support
- `__call__`: Object ko function jaisa call karo
- `__hash__`: Set/dict mein use ke liye
- `__slots__`: Memory optimization (dynamic __dict__ band)

### 2.2 Inheritance - Complete Types
- **Single Inheritance:** Ek parent, ek child
- **Multiple Inheritance:** Ek child, multiple parents — Python supports, Java nahi
- **Multilevel Inheritance:** A → B → C chain
- **Hierarchical:** Ek parent, multiple children
- **Hybrid:** Multiple types ka combination

**MRO (Method Resolution Order):**
- Python C3 Linearization algorithm use karta hai
- Multiple inheritance mein method kaunsa call hoga — MRO decide karta hai
- Left to right, depth first, but C3 ensures no class repeated before its parent
- ClassName.__mro__ ya ClassName.mro() se dekh sakte hain
- **Diamond Problem:** A inherited by B & C, D inherits both B & C — MRO se solve hota hai

**super() function:**
- Parent class ke methods access karne ke liye
- MRO follow karta hai — direct parent nahi, next in MRO
- Multiple inheritance mein cooperative inheritance enable karta hai

### 2.3 Abstract Classes & Interfaces
- **ABC (Abstract Base Class):** abc module se — abstractmethod decorator
- Abstract class ka object nahi ban sakta
- Child class ko sabhi abstract methods implement karne padte hain
- **Interface in Python:** Formal interface nahi hai — ABC use karo ya Protocol (structural subtyping)
- **Protocol (Python 3.8+):** Duck typing + type checking. Class ko explicitly inherit nahi karna padta — bas required methods implement karo

### 2.4 Dataclasses (Python 3.7+)
- `@dataclass` decorator: __init__, __repr__, __eq__ automatically generate hota hai
- Less boilerplate — pure data container classes ke liye
- `field()` function: Default factory, repr/compare control
- `frozen=True`: Immutable dataclass
- `__post_init__`: __init__ ke baad extra initialization
- NamedTuple se similar but mutable (by default) aur zyada features
- **Pydantic vs Dataclass:** Pydantic adds validation, JSON serialization, settings management — dataclass sirf data container

### 2.5 Metaclasses
- **Class ki class — class kaise banta hai woh control karta hai**
- `type` sabhi classes ka metaclass hai
- Class creation flow: Metaclass.__new__ → Metaclass.__init__
- **Use cases:** ORM (Django models), API frameworks, validation, singleton pattern
- **__init_subclass__:** Simpler alternative to metaclasses (Python 3.6+)
- Rule: "If you're wondering whether you need metaclasses, you don't"
- Django ORM internally metaclasses use karta hai models ke liye

### 2.6 Descriptors
- **Object that defines __get__, __set__, __delete__ methods**
- Python ka property, classmethod, staticmethod sab descriptors hain
- **Data descriptor:** __get__ + __set__/__delete__ define — instance __dict__ se priority zyada
- **Non-data descriptor:** Sirf __get__ define — instance __dict__ se priority kam
- **Descriptor Protocol:** Python attribute access internally descriptors use karta hai
- **Use cases:** Lazy loading, validation, caching, type checking

---

## 3. Data Structures & Algorithms

### 3.1 Built-in Data Structures - Time Complexity

| Operation | List | Dict | Set |
|-----------|------|------|-----|
| Access by index | O(1) | N/A | N/A |
| Search | O(n) | O(1) avg | O(1) avg |
| Insert at end | O(1) amortized | O(1) avg | O(1) avg |
| Insert at beginning | O(n) | N/A | N/A |
| Delete | O(n) | O(1) avg | O(1) avg |
| Sort | O(n log n) | N/A | N/A |

- **List internally:** Dynamic array — jab capacity full ho, ~1.125x resize hota hai + copy
- **Dict internally:** Hash table — Python 3.6+ compact dict (insertion order + less memory)
- **Set internally:** Hash table (dict jaisa but only keys, no values)
- **Tuple vs List:** Tuple immutable + hashable, slightly faster, less memory

### 3.2 Collections Module (Important ones)
- **defaultdict:** Missing key pe default value return karta hai (KeyError nahi)
- **Counter:** Elements count karta hai — most_common() useful
- **OrderedDict:** Insertion order remember (Python 3.7+ mein regular dict bhi, but OrderedDict has move_to_end(), equality check order-sensitive)
- **deque (Double-Ended Queue):** O(1) append/pop dono sides pe. list mein left insert O(n) hota hai
- **namedtuple:** Tuple with named fields — lightweight, immutable
- **ChainMap:** Multiple dicts ko ek jaisa access karo

### 3.3 Sorting in Python
- **sorted():** Naya sorted list return karta hai (any iterable pe)
- **list.sort():** In-place sort (sirf list pe)
- **Algorithm:** TimSort — Merge Sort + Insertion Sort ka hybrid. O(n log n) worst case, O(n) best (already sorted)
- **Stable sort:** Equal elements ka original order preserve hota hai
- **key parameter:** Custom sorting — lambda ya function pass karo
- **reverse parameter:** Descending order

### 3.4 Common Algorithm Patterns
- **Two Pointers:** Sorted array mein pair find karna, palindrome check
- **Sliding Window:** Subarray/substring problems, maximum sum subarray
- **Hash Map:** Frequency count, two sum, anagram check
- **Binary Search:** Sorted data mein O(log n) search. bisect module Python mein
- **Stack:** Valid parentheses, next greater element, DFS
- **Queue:** BFS, sliding window maximum
- **Recursion + Memoization:** Fibonacci, dynamic programming problems
- **DFS/BFS:** Tree/Graph traversal

**Big O Complexity Order:** O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2ⁿ) < O(n!)

### 3.5 Hashability in Python
- Hashable objects: __hash__ + __eq__ defined — dictionary key aur set member ban sakte hain
- Immutable built-ins hashable: int, str, tuple (if elements hashable), frozenset
- Mutable objects (list, dict, set) hashable nahi
- Custom classes: By default hashable (id-based hash). __eq__ define karne pe __hash__ None ho jata hai — manually define karo

---

## 4. Decorators, Generators & Context Managers

### 4.1 Decorators - Complete Guide

**Decorator kya hai?**
- Ek function jo dusre function ko modify/enhance kare bina uska code change kiye
- @decorator syntax sugar hai: `func = decorator(func)` ka shorthand
- Higher-order function concept — function as argument, function as return

**Types of Decorators:**
- **Function decorator:** Function ko wrap karta hai
- **Class decorator:** Class ko modify karta hai
- **Method decorators:** @staticmethod, @classmethod, @property
- **Decorator with arguments:** Ek extra outer function layer — decorator factory pattern
- **Stacked decorators:** Multiple decorators ek function pe — bottom to top apply hote hain

**functools.wraps:**
- Decorator lagane pe original function ka __name__, __doc__ lose hota hai
- @wraps(func) se original metadata preserve hota hai
- Best practice: Hamesha use karo

**Common Use Cases:**
- Logging, timing, caching (@functools.lru_cache)
- Authentication/Authorization (Django/Flask mein @login_required)
- Rate limiting, retry logic
- Input validation
- Singleton pattern

**functools.lru_cache:**
- Memoization decorator — function result cache karta hai
- LRU (Least Recently Used) eviction
- maxsize parameter: Cache size limit
- Pure functions ke liye best (same input → same output)
- Python 3.9+: @functools.cache (unlimited cache)

### 4.2 Generators - Complete Guide

**Generator kya hai?**
- Function jo yield statement use karta hai — lazy iterator return karta hai
- Ek baar mein saara data memory mein nahi rakhta — on-demand generate karta hai
- **yield vs return:** yield se function pause hota hai, next() call pe resume. return se function terminate.
- Generator function call karne pe generator object milta hai, execute nahi hota turant

**Generator Protocol:**
- __iter__ aur __next__ implement karta hai automatically
- StopIteration raise hota hai jab generator exhaust ho jaye
- **send():** Generator mein value bhej sakte ho
- **throw():** Generator mein exception raise karo
- **close():** Generator ko gracefully stop karo

**Generator Expression:**
- Comprehension jaisa syntax but parentheses mein
- Memory efficient — list nahi banta, ek ek value generate hoti hai
- Large datasets process karne ke liye ideal

**yield from (Python 3.3+):**
- Sub-generator ko delegate karo
- Nested generators simplify karne ke liye
- Coroutine communication ke liye bhi useful

**Use Cases:**
- Large file processing (line by line)
- Infinite sequences
- Pipeline processing (data transformation chain)
- Memory-efficient data processing
- Lazy evaluation

### 4.3 Context Managers

**Context Manager kya hai?**
- Resource management pattern — setup aur cleanup automatically handle karo
- `with` statement se use hota hai
- **Protocol:** __enter__ (setup) aur __exit__ (cleanup) methods
- __exit__ ko exception info milti hai (exc_type, exc_val, exc_tb) — True return kare toh exception suppress

**contextlib module:**
- **@contextmanager decorator:** Generator-based context manager — yield se pehle setup, yield ke baad cleanup. Simpler than class-based.
- **suppress():** Specific exceptions ignore karo
- **redirect_stdout/redirect_stderr:** Output redirect karo
- **ExitStack:** Multiple context managers dynamically manage karo

**Common Use Cases:**
- File handling (auto close)
- Database connections (auto commit/rollback)
- Lock management (threading)
- Temporary directory/file
- Timer/profiling
- Transaction management

---

## 5. Concurrency & Parallelism

### 5.1 GIL (Global Interpreter Lock)
- **CPython mein ek mutex lock** jo allow karta hai ki ek time pe sirf ek thread Python bytecode execute kare
- **Why exists:** CPython ka memory management (reference counting) thread-safe nahi hai — GIL protect karta hai
- **Impact:** Multi-threaded Python programs CPU-bound tasks ke liye ek core se zyada use nahi kar sakti
- **I/O-bound tasks pe:** GIL release hota hai I/O wait ke time — threads useful hain I/O-bound mein
- **CPU-bound ke liye:** multiprocessing use karo (separate processes, separate GIL)
- **GIL alternatives:** Jython (no GIL), IronPython (no GIL), PyPy (has GIL but faster), nogil experimental builds
- **PEP 703 (Python 3.13+):** Experimental free-threaded build — no GIL option

### 5.2 Threading
- **threading module:** Multiple threads ek process mein
- **Thread:** Lightweight — shared memory space
- **Use for:** I/O-bound tasks (network calls, file I/O, database queries)
- **NOT for:** CPU-bound tasks (GIL bottleneck)
- **Thread safety:** Shared data access ke liye Lock, RLock, Semaphore, Event, Condition use karo
- **Race condition:** Multiple threads same data modify karein simultaneously — Lock se prevent
- **Deadlock:** Two threads ek dusre ka lock wait karein — timeout ya lock ordering se prevent
- **ThreadPoolExecutor:** Thread pool manage karta hai — concurrent.futures module
- **Daemon threads:** Main thread end hone pe automatically terminate hoti hain

### 5.3 Multiprocessing
- **multiprocessing module:** Separate processes spawn karo — har ek apna GIL aur memory space
- **Use for:** CPU-bound tasks (data processing, calculations, ML training)
- **Process:** Heavy — separate memory, inter-process communication (IPC) needed
- **Communication:** Queue, Pipe, shared memory (Value, Array), Manager
- **ProcessPoolExecutor:** Process pool manage karta hai
- **Pool.map():** Data ko parallel chunk mein process karo
- **Tradeoff:** Process creation overhead zyada — chhote tasks ke liye overkill

### 5.4 Asyncio
- **Single-threaded concurrent programming** — event loop based
- **async/await syntax (Python 3.5+)**
- **Coroutine:** async def se define — await se pause, event loop dusra coroutine run kare
- **Event Loop:** Coroutines schedule aur manage karta hai
- **Use for:** High-concurrency I/O-bound (thousands of network connections)
- **NOT for:** CPU-bound tasks
- **asyncio.gather():** Multiple coroutines concurrently run karo
- **asyncio.create_task():** Background task create karo
- **aiohttp:** Async HTTP client/server
- **asyncio vs threading:** Asyncio zyada scalable (10,000+ connections), threading limited by OS thread limit

### 5.5 Comparison Table

| Feature | Threading | Multiprocessing | Asyncio |
|---------|-----------|-----------------|---------|
| GIL affected | Yes | No (separate processes) | Yes (but single thread) |
| Best for | I/O-bound | CPU-bound | High-concurrency I/O |
| Memory | Shared | Separate | Shared (single thread) |
| Overhead | Low | High | Very Low |
| Complexity | Medium (locks) | Medium (IPC) | High (async mindset) |
| Scalability | 100s of threads | 10s of processes | 10,000s of coroutines |

---

## 6. Memory Management & Garbage Collection

### 6.1 Memory Management
- **Everything is an object** in Python — har cheez heap memory pe stored
- **Reference Counting:** Primary mechanism — har object ka reference count hota hai. Zero hone pe immediately deallocate.
- **Private Heap:** Python ka apna memory manager — OS se memory allocate karta hai
- **PyMalloc:** Python ka custom memory allocator — small objects (<=512 bytes) ke liye optimized
- **Memory Pools:** Blocks → Pools → Arenas architecture. Small objects ke liye pre-allocated memory pools.
- **Object interning:** Small integers (-5 to 256) aur common strings cached — magar deliberately rely mat karo

### 6.2 Garbage Collection
- **Reference Counting:** Immediate but circular references handle nahi kar sakta
- **Generational GC:** Circular references ke liye — `gc` module
  - **Generation 0:** Newly created objects — frequently scanned
  - **Generation 1:** Survived one collection — less frequently scanned
  - **Generation 2:** Long-lived objects — rarely scanned
- **Threshold:** gc.get_threshold() — default (700, 10, 10). 700 allocations after cleanup triggers Gen 0 collection
- **gc.collect():** Manual garbage collection trigger
- **Weak References (weakref module):** Object reference without increasing reference count — cache ke liye useful
- **Memory Leaks in Python:** Circular references with __del__, global variables growing, large caches, unclosed resources
- **Detection:** tracemalloc module, objgraph, memory_profiler, gc.get_objects()
- **__slots__:** Class mein __dict__ replace karo fixed attributes se — memory saving (especially many instances)

---

## 7. Design Patterns in Python

### 7.1 Creational Patterns
- **Singleton:** Ek class ka sirf ek instance. Implementation: __new__ override, metaclass, module-level instance, decorator.
  - Python mein modules already singleton hain — import system cache karta hai
- **Factory Method:** Object creation ko subclass pe delegate karo — client ko exact class pata nahi hoti
- **Abstract Factory:** Related objects ka family create karo without concrete classes specify kiye
- **Builder:** Complex object step by step construct karo — Python mein fluent interface ya keyword arguments se

### 7.2 Structural Patterns
- **Adapter:** Incompatible interfaces ko compatible banao — wrapper class
- **Decorator:** Object ko dynamically extra functionality add karo (Python decorator se alag concept, but Python decorator isko implement kar sakta hai)
- **Facade:** Complex subsystem ke liye simple interface — library wrapper
- **Proxy:** Object ka surrogate — lazy loading, access control, logging

### 7.3 Behavioral Patterns
- **Observer:** Pub/Sub pattern — subject change hone pe observers notify
- **Strategy:** Algorithm family define karo, interchangeable banao — Python mein functions as first-class objects se simple
- **Iterator:** Collection traverse karo without internal structure expose kiye — Python ka __iter__/__next__ protocol
- **Template Method:** Algorithm ka skeleton define karo, steps subclass override kare
- **Command:** Request ko object mein encapsulate karo — undo/redo, queuing

**Python-specific patterns:**
- **Mixin:** Multiple inheritance se reusable behavior add karo (LoginRequiredMixin in Django)
- **Borg/Monostate:** Shared state across instances (alternative to Singleton)
- **EAFP (Easier to Ask Forgiveness than Permission):** try/except prefer karo over if/else check — Pythonic
- **LBYL (Look Before You Leap):** Pehle check karo — non-Pythonic generally

---

## 8. Testing & Debugging

### 8.1 Testing Concepts

**unittest (Built-in):**
- Python ka standard testing framework
- TestCase class inherit karo
- setUp/tearDown methods (before/after each test)
- setUpClass/tearDownClass (before/after all tests in class)
- assert methods: assertEqual, assertTrue, assertRaises, assertIn, etc.

**pytest (Industry Standard):**
- Simple — plain functions + assert statement
- **Fixtures:** Setup/teardown — dependency injection style. Scopes: function, class, module, session.
- **Parametrize:** Ek test, multiple inputs — @pytest.mark.parametrize
- **Markers:** Tests categorize karo: @pytest.mark.slow, @pytest.mark.skip, @pytest.mark.xfail
- **Conftest.py:** Shared fixtures across modules
- **Plugins:** pytest-cov (coverage), pytest-mock, pytest-asyncio, pytest-xdist (parallel)

**Testing Concepts:**
- **Unit Test:** Single function/method test (isolated, mocked dependencies)
- **Integration Test:** Multiple components together test
- **End-to-End (E2E):** Full workflow test (user perspective)
- **TDD (Test Driven Development):** Test pehle likho, code baad mein — Red → Green → Refactor
- **Coverage:** kitna code tested hai — 80%+ generally target. 100% coverage != bug-free
- **Mocking:** External dependencies replace karo (unittest.mock — Mock, patch, MagicMock)
- **Monkey Patching:** Runtime pe attribute/method replace (pytest monkeypatch fixture)

### 8.2 Debugging Tools
- **pdb:** Python built-in debugger — breakpoint() function (Python 3.7+)
- **ipdb:** Enhanced pdb with IPython features
- **IDE Debugger:** VS Code/PyCharm — breakpoints, watch, step through
- **logging module:** print se better — levels (DEBUG, INFO, WARNING, ERROR, CRITICAL), handlers, formatters
- **traceback module:** Exception details programmatically access
- **cProfile:** Performance profiling — function call time + count
- **line_profiler:** Line-by-line execution time
- **memory_profiler:** Memory usage per line
- **py-spy:** Production profiling — no code change needed
- **tracemalloc:** Memory allocation tracking
- **Django Debug Toolbar:** Django apps ke liye — queries, templates, signals track

---

## 9. Python Internals

### 9.1 How Python Executes Code
1. **Source Code (.py)** → Lexer (tokenize) → Parser (AST - Abstract Syntax Tree)
2. **AST** → Compiler → **Bytecode (.pyc)** — __pycache__ folder mein cached
3. **Bytecode** → Python Virtual Machine (PVM) → Execution
- **dis module:** Bytecode inspect karo — function ka bytecode decompile
- **Bytecode cached:** .pyc files — agar source change nahi hua toh recompile nahi hota (faster startup)
- **CPython:** Reference implementation (C mein written). Alternatives: PyPy (JIT), Jython (JVM), IronPython (.NET)

### 9.2 Python Object Model
- **Everything is an object:** int, functions, classes, modules — sab objects hain
- **type:** Sabhi classes ka metaclass — type(int) → type, type(type) → type
- **object:** Sabhi classes ka base class — inheritance chain ka root
- **Attribute lookup order:** Instance __dict__ → Class __dict__ → Parent classes (MRO) → __getattr__
- **Descriptor protocol:** Attribute access ko customize karne ka mechanism
- **__dict__:** Object ke attributes ka dictionary. __slots__ define karo toh __dict__ nahi banta (memory save).

### 9.3 Important Python 3.10+ Features
- **Structural Pattern Matching (match/case) — Python 3.10:**
  - Switch-case jaisa but bahut powerful
  - Pattern types: literal, capture, wildcard, class, sequence, mapping, OR
  - Guard conditions (if clause in case)
  
- **Exception Groups (Python 3.11):**
  - Multiple exceptions ek saath raise aur catch
  - except* syntax — partial exception handling
  - Useful for async code jahan multiple errors simultaneously

- **Python 3.12:**
  - Type parameter syntax (Generics simplified)
  - Per-interpreter GIL (subinterpreters)
  - Improved error messages

- **Python 3.13+:**
  - Experimental free-threaded build (no GIL)
  - JIT compiler (experimental)

---

## 10. Interview Questions & Answers

### Q1: `is` vs `==` ka kya difference hai?
**Answer:**
- `==` **equality** check karta hai — values same hain. __eq__ method call hota hai internally.
- `is` **identity** check karta hai — dono same object hain memory mein (same id()).
- None check ke liye `is None` use karo, `== None` nahi.
- Small integers (-5 to 256) interned hote hain — `is` True aa sakta hai, but rely mat karo.
- Strings bhi sometimes interned hote hain — implementation dependent.
- **Rule:** Values compare karne ke liye `==`, identity check ke liye `is`.

### Q2: Deep Copy vs Shallow Copy explain karein
**Answer:**
- **Shallow Copy (copy.copy):** Naya object banta hai, but nested objects ke references SAME rehte hain. Top level naya, inner level shared.
- **Deep Copy (copy.deepcopy):** Completely independent copy — nested objects bhi recursively copy hote hain.
- **Assignment (=):** Copy nahi hota — same object ka new reference. Dono variables same object point karein.
- **List slicing (lst[:])** aur **list(lst):** Shallow copy create karta hai.
- **When Deep Copy:** Nested mutable objects independent chahiye — complex data structures.
- **Circular references:** deepcopy handle karta hai (memo dict se).

### Q3: Closure kya hota hai?
**Answer:**
- Ek nested function jo outer function ke variables ko remember karta hai — even after outer function return ho chuki ho.
- **Three conditions:** Nested function hona chahiye, outer function ka variable use kare, outer function return kare inner function ko.
- **Free variables:** Outer function ke variables jo inner function access karta hai — __closure__ attribute mein stored.
- **nonlocal keyword:** Closure ke andar outer variable ko modify karne ke liye (Python 3+).
- **Use cases:** Decorators, callback functions, factory functions, data hiding.
- **vs Class:** Closure lightweight alternative hai simple state ke liye.

### Q4: Duck Typing kya hai?
**Answer:**
- "If it walks like a duck and quacks like a duck, then it's a duck"
- Object ka type check nahi karte — object kya kar sakta hai (methods/attributes) woh dekhte hain.
- Python mein isinstance() check ki zaroorat kam — bas required method call try karo.
- **EAFP (Easier to Ask Forgiveness than Permission):** try/except use karo, isinstance nahi.
- **Protocols (Python 3.8+):** Duck typing ko type hints ke saath — structural subtyping.
- **Benefit:** Flexible, loosely coupled code. Interface explicitly implement karne ki zaroorat nahi.

### Q5: @staticmethod vs @classmethod vs instance method?
**Answer:**
- **Instance method:** self milta hai (instance reference). Object ka data access/modify kare. Most common.
- **@classmethod:** cls milta hai (class reference). Class pe operate kare, instance pe nahi. Factory methods ke liye best (alternate constructors).
- **@staticmethod:** Na self na cls. Utility function jo class se logically related hai but instance ya class data access nahi karta.
- **When classmethod:** Alternative constructors (from_json, from_string), subclass mein correctly work kare.
- **When staticmethod:** Pure utility, no state needed.

### Q6: Module import hone pe kya hota hai?
**Answer:**
1. **sys.modules check:** Pehle cache mein check — agar already imported, cached version return.
2. **Module search:** sys.path mein module dhundho (current dir → installed packages → stdlib).
3. **Module execution:** Module ka code top-to-bottom execute hota hai — sab top-level statements run hote hain.
4. **Module object create:** Module ke namespace mein variables/functions/classes store.
5. **Cache:** sys.modules mein cache — next import pe re-execute nahi hota.
- **Circular imports:** Module A imports B, B imports A — partially loaded module mil sakta hai. Solution: Import restructure, lazy import.
- **__name__ == "__main__":** Direct run pe __name__ = "__main__", import pe __name__ = module_name.
- **Relative imports:** from . import module — package ke andar. Absolute imports preferred generally.

### Q7: GIL ko detail mein explain karein
**Answer:**
- CPython mein ek mutex lock — ek time pe sirf ek thread Python bytecode execute kare.
- **Why:** CPython reference counting thread-safe nahi hai. Fine-grained locking complex + slow hoti.
- **I/O operations pe GIL release hota hai** — file read, network call, sleep ke time dusre threads run ho sakte hain.
- **CPU-bound:** GIL bottleneck — solution: multiprocessing, C extensions (NumPy), Cython.
- **I/O-bound:** GIL problem nahi — threading works well.
- **Workaround strategies:** multiprocessing, C extensions, asyncio, alternative interpreters (PyPy, Jython).
- **Future:** PEP 703 — no-GIL build experimental hai Python 3.13+.

### Q8: Memory leak kaise detect aur fix karein?
**Answer:**
- **Common causes:** Circular references with __del__, growing global data structures, unclosed connections/files, large caches without eviction, event listeners not removed.
- **Detection tools:**
  - tracemalloc: Memory allocation track karo — snapshots compare
  - objgraph: Object reference graphs visualize
  - memory_profiler: Line-by-line memory usage
  - gc.get_objects(): All tracked objects list
  - gc.garbage: Uncollectable objects
- **Fixes:** weakref use karo (caches), context managers (resource cleanup), LRU cache with maxsize, del unnecessary references, gc.collect() force collection.

### Q9: LEGB Rule explain karein
**Answer:**
- Python variable lookup order: **L → E → G → B**
- **L (Local):** Current function ke andar defined
- **E (Enclosing):** Outer/enclosing function ke variables — closures mein
- **G (Global):** Module level pe defined variables
- **B (Built-in):** Python ke built-in names (print, len, True, etc.)
- **global keyword:** Function ke andar global variable modify karne ke liye
- **nonlocal keyword:** Enclosing function ka variable modify karne ke liye
- **Shadowing:** Inner scope mein same name ka variable — outer scope ka variable hide hota hai

### Q10: __new__ vs __init__ ka difference?
**Answer:**
- **__new__:** Object **creation** — memory allocate, new instance return kare. cls milta hai (class).
- **__init__:** Object **initialization** — already created object ko setup kare. self milta hai (instance).
- **Call order:** __new__ pehle → phir __init__
- **__new__ use cases:** Singleton pattern, immutable types customize (str, int subclass), object creation control.
- **Usually:** __init__ hi use hota hai. __new__ rare cases mein.
- **Immutable types:** int, str customize karne ke liye __new__ zaruri — __init__ mein value change nahi ho sakta.

### Q11: Important Magic/Dunder Methods explain karein
**Answer:**
- **Object Creation:** __new__ (create), __init__ (initialize), __del__ (destructor — unreliable, avoid)
- **String Representation:** __repr__ (developer), __str__ (user), __format__ (custom formatting)
- **Comparison:** __eq__, __ne__, __lt__, __gt__, __le__, __ge__ — @functools.total_ordering se simplify
- **Arithmetic:** __add__, __sub__, __mul__, __truediv__, __mod__, __pow__
- **Container:** __len__, __getitem__, __setitem__, __delitem__, __contains__, __iter__
- **Callable:** __call__ — object ko function jaisa call karo
- **Context Manager:** __enter__, __exit__
- **Attribute Access:** __getattr__ (fallback), __getattribute__ (always), __setattr__, __delattr__
- **Hashing:** __hash__ — dict/set ke liye. __eq__ override karo toh __hash__ bhi karo.

### Q12: Monkey Patching kya hai?
**Answer:**
- **Runtime pe class ya module ke attributes/methods change karna**
- Dynamic language feature — Python mein possible because classes mutable hain
- **Use cases:** Testing mein mocking (replacing methods), third-party library bugs fix, hotfixes without redeployment
- **Risks:** Code unpredictable, debugging mushkil, upgrades break ho sakte hain, implicit dependencies
- **Best practice:** Sirf testing mein use karo (unittest.mock.patch), production mein avoid karo
- **pytest monkeypatch fixture:** Safe monkey patching — test end pe automatically revert

### Q13: `with` statement internally kaise kaam karta hai?
**Answer:**
- Context Manager Protocol: __enter__ aur __exit__ methods
- **Flow:**
  1. Context manager ka __enter__ call hota hai
  2. Return value `as` variable mein assign hoti hai
  3. with block execute hota hai
  4. __exit__ call hota hai — chahe exception aaye ya na aaye
- **__exit__ parameters:** exc_type, exc_val, exc_tb — None if no exception
- **__exit__ returns True:** Exception suppress (swallow) hota hai
- **__exit__ returns False/None:** Exception propagate hota hai
- **Multiple context managers:** Ek with statement mein comma-separated (Python 3.1+) ya nested

### Q14: Coroutines vs Generators ka difference?
**Answer:**
- **Generator:** Data produce karta hai — yield se values generate
- **Coroutine:** Data consume + produce dono — async/await se define (Python 3.5+)
- **Generator:** Pull-based — consumer pull kare (next())
- **Coroutine:** Push-based + scheduled — event loop manage kare
- **Generator:** Single function — sequential
- **Coroutine:** Concurrent execution — I/O wait mein dusra coroutine run kare
- **Legacy coroutine:** Generator-based (@asyncio.coroutine + yield from) — deprecated
- **Modern coroutine:** async def + await — standard approach

### Q15: Python Performance Optimization Tips
**Answer:**
- **Profile first:** Premature optimization avoid karo. cProfile, py-spy se bottleneck dhundho.
- **Algorithm:** Right data structure + algorithm > micro-optimization. O(n) vs O(n²) matter karta hai.
- **Built-in functions:** C mein implemented — map, filter, sorted, sum, min, max tez hain
- **List comprehension:** Regular loop se ~30-40% faster (C-level optimization)
- **Generators:** Large data ke liye — memory efficient, lazy evaluation
- **String join:** Loop mein + concatenation O(n²) — "".join() use karo O(n)
- **Local variables:** Global se faster — function ke andar rakhho
- **__slots__:** Memory save for many instances — __dict__ overhead remove
- **functools.lru_cache:** Repeated computations cache karo
- **Concurrency:** I/O-bound → asyncio/threading, CPU-bound → multiprocessing
- **C Extensions:** NumPy, Cython — performance-critical code ke liye
- **PyPy:** Alternative interpreter with JIT compiler — 5-10x faster for long-running code

---

## Quick Revision - One Liners

| Concept | Key Point |
|---------|-----------|
| GIL | Ek time pe sirf ek thread Python bytecode execute kare |
| Mutable | list, dict, set — in-place modify ho sakte hain |
| Immutable | int, str, tuple — naya object banta hai modify pe |
| Decorator | Function jo dusre function ko modify kare |
| Generator | yield se lazy iterator — memory efficient |
| Closure | Inner function remembers outer variables |
| Metaclass | Class ki class — class creation control |
| Descriptor | __get__, __set__, __delete__ protocol |
| MRO | C3 Linearization — method resolution order |
| *args/**kwargs | Variable positional / keyword arguments |
| Context Manager | __enter__ + __exit__ — resource management |
| LEGB | Local → Enclosing → Global → Built-in |
| Deep Copy | Fully independent copy (nested bhi) |
| Shallow Copy | New object but nested references shared |
| asyncio | Single-thread async I/O — event loop based |
| multiprocessing | Separate processes — CPU-bound ke liye |
| threading | Shared memory threads — I/O-bound ke liye |
| Duck Typing | Type nahi, behavior check karo |
| EAFP | try/except prefer — Pythonic |
| __slots__ | Memory optimize — no __dict__ |
| f-string | Fastest string formatting (3.6+) |
| TimSort | Python sort algorithm — merge + insertion hybrid |
| @property | Getter/Setter Pythonic way mein |
| walrus := | Assign + use in expression (3.8+) |
| Protocol | Structural subtyping — duck typing + type hints |

---

*10+ Years Experience Level - Python Complete Theory Guide (No Code)*
