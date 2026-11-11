# TestForge Dynamic Target Manifest (Stage 1 Audit)

**Generated:** Dynamic Git Capture (`git ls-files 'samples/*.py' 'samples/sealed_v2/*.py' | grep -v 'test_'`)  
**AST Engine:** FastMCP `mcp_ast_symbol_analyzer` & `mcp_mutant_generator`  
**Total Tracked Targets:** 56  
**Valid AST Targets:** 52  
**Deliberate Syntax Error Fixtures:** 4  

| Target File | Lines of Code | AST Functions | AST Classes | Mutants Generated |
| :--- | :---: | :---: | :---: | :---: |
| `samples/banking.py` | 20 | 1 | 0 | 23 |
| `samples/currency_converter.py` | 55 | 1 | 0 | 46 |
| `samples/discount.py` | 16 | 1 | 0 | 19 |
| `samples/expression_tokenizer.py` | 108 | 5 | 4 | 76 |
| `samples/generated_create_a_simple_math.py` | 18 | 1 | 0 | 16 |
| `samples/generated_def_broken_func_x.py` | 15 | 1 | 0 | 5 |
| `samples/generated_implement_a_currency_conversion.py` | 34 | 2 | 1 | 31 |
| `samples/generated_implement_a_token_bucket.py` | 44 | 6 | 2 | 30 |
| `samples/generated_making_a_python_file.py` | 398 | 24 | 10 | 200 |
| `samples/generated_rate_limiter_with_token.py` | 16 | 1 | 0 | 18 |
| `samples/generated_stock_trading_order_matching.py` | 16 | 1 | 0 | 18 |
| `samples/github_Python_red_black_tree.py` | 613 | 40 | 1 | 200 |
| `samples/github_requests_cookies.py` | 491 | 52 | 4 | 200 |
| `samples/github_requests_models.py` | 868 | 52 | 5 | 200 |
| `samples/github_requests_sessions.py` | 641 | 29 | 2 | 200 |
| `samples/github_requests_status_codes.py` | 112 | 2 | 0 | 200 |
| `samples/interval_set.py` | 96 | 16 | 2 | 67 |
| `samples/inventory_ledger.py` | 123 | 9 | 4 | 97 |
| `samples/inventory_pricing.py` | 38 | 1 | 0 | 37 |
| `samples/jwt_validator.py` | 154 | 6 | 5 | 147 |
| `samples/lru_cache.py` | 91 | 9 | 2 | 42 |
| `samples/order_fsm.py` | 85 | 7 | 1 | 106 |
| `samples/rate_limiter.py` | 139 | 10 | 3 | 147 |
| `samples/sealed_eval/board_evaluator.py` | 61 | 5 | 0 | 84 |
| `samples/sealed_eval/loan_amortization.py` | 59 | 3 | 0 | 99 |
| `samples/sealed_eval/markdown_parser.py` | 70 | 4 | 0 | 54 |
| `samples/sealed_eval/merkle_tree.py` | 71 | 5 | 0 | 80 |
| `samples/sealed_eval/min_heap.py` | 66 | 9 | 1 | 64 |
| `samples/sealed_eval/url_router.py` | 56 | 5 | 1 | 28 |
| `samples/sealed_v2/bisect_algo.py` | 87 | 4 | 0 | 70 |
| `samples/sealed_v2/fractions_algo.py` | 39 | 9 | 1 | 57 |
| `samples/sealed_v2/heapq_algo.py` | 56 | 7 | 0 | 49 |
| `samples/sealed_v2/shlex_algo.py` | 39 | 1 | 0 | 23 |
| `samples/sealed_v2/statistics_algo.py` | 27 | 4 | 0 | 37 |
| `samples/sealed_v2/textwrap_algo.py` | 39 | 4 | 1 | 23 |
| `samples/sliding_window_rate_limiter.py` | 86 | 7 | 3 | 67 |
| `samples/state_machine.py` | 38 | 1 | 0 | 57 |
| `samples/stats_calculator.py` | 65 | 6 | 0 | 73 |
| `samples/uploaded_01_empty.py` | 0 | 0 | 0 | 0 |
| `samples/uploaded_02_comments_only.py` | 4 | 0 | 0 | 0 |
| `samples/uploaded_03_single_simple_function.py` | 3 | 1 | 0 | 2 |
| `samples/uploaded_04_multiple_functions.py` | 10 | 4 | 0 | 13 |
| `samples/uploaded_05_class_methods.py` | 22 | 5 | 2 | 19 |
| `samples/uploaded_06_complex_typing.py` | 13 | 1 | 0 | 6 |
| `samples/uploaded_07_nested_closures.py` | 9 | 3 | 0 | 5 |
| `samples/uploaded_08_syntax_error.py` | - | - | - | `SYNTAX_ERROR` (Negative Fixture) |
| `samples/uploaded_09_exception_raising.py` | 10 | 1 | 1 | 19 |
| `samples/uploaded_10_heavy_branching.py` | 32 | 1 | 0 | 72 |
| `samples/uploaded_bad.py` | - | - | - | `SYNTAX_ERROR` (Negative Fixture) |
| `samples/uploaded_empty.py` | 0 | 0 | 0 | 0 |
| `samples/uploaded_logistics_engine.py` | 185 | 11 | 2 | 200 |
| `samples/uploaded_no_func.py` | 2 | 0 | 0 | 2 |
| `samples/uploaded_rate_limiter.py` | 30 | 1 | 0 | 38 |
| `samples/uploaded_syntax_bad.py` | - | - | - | `SYNTAX_ERROR` (Negative Fixture) |
| `samples/uploaded_syntax_error.py` | - | - | - | `SYNTAX_ERROR` (Negative Fixture) |
| `samples/uploaded_uploaded_logistics_engine.py` | 185 | 11 | 2 | 200 |
