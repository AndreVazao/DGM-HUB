# DGM-HUB Benchmark Report

Generated: 2026-06-04 11:01 UTC  
Platform: win32  
Python: 3.12.6

## 1. Repo Scan

| Files | Time (s) | Memory (MB) | Journal size |
|------:|---------:|------------:|-------------:|
| 100 | 2.04 | 0.0 | 6 KB |
| 1,000 | 7.85 | 0.1 | 54 KB |
| 10,000 | 39.95 | 0.8 | 538 KB |

## 2. Execution Engine

| Commands | Time (s) | Throughput (cmd/s) | Avg latency | Errors |
|----------:|---------:|--------------------:|------------:|-------:|
| 1 | 0.53 | 1.9 | 525.1 ms | 0 |
| 100 | 47.53 | 2.1 | 475.3 ms | 0 |
| 1,000 | 589.08 | 1.7 | 589.1 ms | 0 |

## 3. Test Pipeline

| Stack | Size | Modules | Time (s) | Success |
|-------|------|--------:|---------:|--------:|
| PY | small | 2 | 7.97 | ✅ |
| PY | medium | 10 | 7.54 | ✅ |
| PY | large | 30 | 10.29 | ✅ |
| NODE | small | 2 | 3.51 | ✅ |
| NODE | medium | 10 | 7.04 | ✅ |
| NODE | large | 30 | 31.75 | ✅ |

## 4. Long Running Stress (1 000 cycles)

| Metric | Value |
|--------|-------|
| Total cycles | 1,000 |
| Errors | 0 |
| Latency avg / p50 / p95 / p99 | 671.6 ms / 440.4 ms / 1445.7 ms / 2288.6 ms |
| Memory start → end | 0.0 MB → 0.9 MB |
| **Memory growth** | **+0.9 MB** |
| File descriptor leak | 0 |
| Journal lines | 1,000 |
| Journal corruption | 0 |
| Journal size | 204 KB |

### Memory over time

| Cycle | Memory (MB) |
|------:|------------:|
| 100 | 0.8 |
| 200 | 0.9 |
| 300 | 0.9 |
| 400 | 0.9 |
| 500 | 0.9 |
| 600 | 0.9 |
| 700 | 0.9 |
| 800 | 0.9 |
| 900 | 0.9 |
| 1,000 | 0.9 |

## Conclusions

✅ No critical issues found.
