# TestForge Milestone 2 Empirical Benchmark Summary

- Timestamp: 2026-10-23 14:04:44
- Platform: macOS (Apple Silicon M2 Pro, 10 CPU cores)
- Python Environment: `.venv-release` (Python 3.13.1)

| Workload | Mutants | Valid Rate | Killed | Survived | Equiv | Pot. Eq | Raw Score | Adj Score | Mean Runtime | Deterministic |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| E-Commerce Discount Rules | 19 | 100.0% | 14 | 5 | 0 | 0 | 73.68% | 73.68% | 0.9745s | True |
| Banking Transaction Rules | 23 | 100.0% | 23 | 0 | 0 | 0 | 100.0% | 100.0% | 1.0379s | True |
| Inventory Tier Pricing | 37 | 100.0% | 37 | 0 | 0 | 0 | 100.0% | 100.0% | 1.6488s | True |
| Token Bucket Rate Limiter | 38 | 100.0% | 21 | 17 | 0 | 0 | 55.26% | 55.26% | 1.6006s | True |
