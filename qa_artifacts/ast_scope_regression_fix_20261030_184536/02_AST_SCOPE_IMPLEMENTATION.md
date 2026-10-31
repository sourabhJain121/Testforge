# 02 — AST Scope-Aware Extraction Implementation

**Audit & Fix Timestamp:** `2026-10-30T18:45:36+05:30`  
**Modified Files:**
- `testforge/agents.py`
- `testforge/adk_generator.py`

---

## 1. Lexical Scope Visitor (`ScopeVisitor`)

In `testforge/agents.py`, `extract_function_signatures` was rewritten using an `ast.NodeVisitor` that maintains explicit lexical stacks (`class_stack` and `func_stack`).

```python
class ScopeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.class_stack: List[str] = []
        self.func_stack: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._record_func(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._record_func(node, is_async=True)
```

---

## 2. Scope & Method Classification Matrix

Each callable node is categorized across four dimensions:

| Construct | `scope` | `parent_class` | `parent_function` | `method_type` | `is_method` | `qualified_name` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Top-Level Function** | `"module"` | `None` | `None` | `None` | `False` | `fn_name` |
| **Instance Method** | `"class"` | `ClassDef.name` | `None` | `"instance"` | `True` | `Class.fn_name` |
| **Static Method (`@staticmethod`)** | `"class"` | `ClassDef.name` | `None` | `"staticmethod"` | `True` | `Class.fn_name` |
| **Class Method (`@classmethod`)** | `"class"` | `ClassDef.name` | `None` | `"classmethod"` | `True` | `Class.fn_name` |
| **Property (`@property`)** | `"class"` | `ClassDef.name` | `None` | `"property"` | `True` | `Class.fn_name` |
| **Nested Function** | `"nested"` | Context-dependent | `EnclosingFn` | `None` | `False` | `Fn.<locals>.inner` |

### Parameter Normalization:
- **Instance Methods & Properties:** Leading parameter `self` is stripped from `pos_args` and `required_pos`.
- **Class Methods:** Leading parameter `cls` is stripped from `pos_args` and `required_pos`.
- **Static Methods & Module Functions:** All parameters are preserved.

---

## 3. Signature-Aware Argument Construction (`build_nominal_arguments`)

In `testforge/agents.py`:
- `build_nominal_arguments(sig)` now permits static methods (`method_type == "staticmethod"`) and class methods (`method_type == "classmethod"`) to receive nominal arguments without requiring instance instantiation.
- Added heuristic support for payload and data inputs (`"data" in p_low -> '"test"'`).
- Continues to return `None` for instance methods, properties, and ambiguous/unbounded varargs without defaults.

---

## 4. Scope-Aware Test Generation in `ADKModelBridge`

In `testforge/adk_generator.py`:
`_synthesize_deterministic_tests` inspects callable scopes and generates strictly valid imports and invocations:

1. **Top-Level Module Function:**
   ```python
   from target import calculate_discount
   result = calculate_discount(10.0, 2, False)
   ```
2. **Static Method:**
   ```python
   from target import RequestEncodingMixin
   result = RequestEncodingMixin._encode_params("test")
   ```
3. **Class Method:**
   ```python
   from target import SessionConfig
   result = SessionConfig.default_config()
   ```
4. **Instance Method:**
   ```python
   from target import OrderAccount
   obj = OrderAccount()
   result = obj.deposit(10.0)
   ```

No test ever attempts to import a class method or static method directly as a module attribute (`from target import _encode_params` is permanently eliminated).

