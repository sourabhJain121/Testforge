# TestForge — Phase 2A.1: MCP Bounded Downloads Security Report

**Date:** 2026-10-30  
**Phase:** 2A.1 (MCP Network Security Remediation)  
**Target Module:** `testforge/mcp_server.py`  
**Status:** REMEDIATED & VERIFIED  

---

## 1. Vulnerability Background

The independent security review for Phase 2A identified two download-related denial-of-service and memory exhaustion risks in `testforge/mcp_server.py`:
1. `_make_github_request()` called unbounded `resp.read().decode("utf-8")`. A malicious or unexpectedly large API payload could saturate host memory.
2. `get_file_contents()` decoded base64 payloads directly via `base64.b64decode(content_b64)` without validating that the resulting binary or decoded string complied with file size ceilings.

---

## 2. Remediation Implementation

The download pathways in `testforge/mcp_server.py` now reuse `bounded_read()` and standard size thresholds from `testforge/network_security.py`:
- `DEFAULT_MAX_SOURCE_SIZE_BYTES = 500 * 1024` (500 KB default file ceiling)
- `DEFAULT_MAX_TOTAL_BYTES = 10 * 1024 * 1024` (10 MB default API JSON ceiling)
- `bounded_read()`
- `PayloadTooLargeError`

### 2.1 Bounded Stream Reading in `_make_github_request`
- **Location:** `testforge/mcp_server.py:189-195`
- **Implementation:**
  ```python
  with safe_opener.open(req, timeout=10.0) as resp:
      data_bytes = bounded_read(resp, max_bytes=max_bytes)
      data_str = data_bytes.decode("utf-8", errors="replace")
      return json.loads(data_str)
  ```
- **Defense-in-Depth Controls:**
  1. *Early Content-Length Check:* Inspects HTTP `Content-Length`. If declared bytes exceed `max_bytes` or are negative, raises `PayloadTooLargeError` prior to reading any body bytes.
  2. *Chunked Enforcement:* Reads in 64 KB increments (`DEFAULT_CHUNK_SIZE`). Maintains a running counter of received bytes and aborts immediately if the limit is breached, defeating compression bombs and infinite streaming attacks.
  3. *Resource Cleanup:* Encloses streams in `try...finally:` blocks ensuring `resp.close()` is executed on both success and error.

### 2.2 Dual-Stage Base64 Size Enforcement in `get_file_contents`
- **Location:** `testforge/mcp_server.py:236-249`
- **Implementation:**
  ```python
  content_b64 = data.get("content", "")
  # Stage 1: Protect against memory inflation prior to base64 decoding
  if len(content_b64) > int(max_file_size_bytes * 1.4) + 1024:
      raise PayloadTooLargeError(
          f"Base64 encoded content size ({len(content_b64)} chars) exceeds maximum allowable limit for {max_file_size_bytes} bytes."
      )
  import base64
  decoded_bytes = base64.b64decode(content_b64)
  # Stage 2: Enforce exact binary size limit
  if len(decoded_bytes) > max_file_size_bytes:
      raise PayloadTooLargeError(
          f"Decoded file size ({len(decoded_bytes)} bytes) exceeds maximum allowable limit of {max_file_size_bytes} bytes."
      )
  ```
- **Benefits:**
  - Prevents allocating multi-megabyte binary bytearrays in memory for oversized files.
  - Rejects oversized files cleanly with `PayloadTooLargeError`, returning zero partial content to downstream agents.

---

## 3. Verification & Test Evidence

Tested via `tests/test_mcp_network_security.py` using real transport dispatch:
- `test_oversized_response_with_content_length`: **PASSED** (Rejects before stream read when `Content-Length > max_bytes`)
- `test_oversized_response_without_content_length`: **PASSED** (Chunk counter aborts stream when missing header)
- `test_base64_payload_exceeding_limit`: **PASSED** (Rejects base64 content exceeding `max_file_size_bytes`)
- `test_normal_base64_file_retrieval`: **PASSED** (Retrieves, decodes, and hashes valid file within limits)
- `test_response_cleanup_on_failure`: **PASSED** (Confirmed socket and stream descriptor closure on failure)

Zero partial files or corrupted data are returned to clients on error.

