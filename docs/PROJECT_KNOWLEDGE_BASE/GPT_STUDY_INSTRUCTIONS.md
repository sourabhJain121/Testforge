# INSTRUCTIONS FOR GPT: HOW TO STUDY & EXPLAIN TESTFORGE
## Prompt Engineering Guide for AI Models Ingesting the TestForge Knowledge Base

**Document Version:** 2.0.0  
**Target Ingestor:** Large Language Models (GPT-4, Claude 3.5 Sonnet, Gemini 1.5 Pro)  
**Authoritative Location:** `docs/PROJECT_KNOWLEDGE_BASE/GPT_STUDY_INSTRUCTIONS.md`

---

## 1. INGESTION ORDER & READING SEQUENCE

When ingesting this project repository or answering technical viva questions, read the documentation files in the following strict order:

1. **Step 1: The Executive Summary**  
   Read [`GPT_PROJECT_CONTEXT.md`](GPT_PROJECT_CONTEXT.md) and [`PROJECT_MASTER_GUIDE.md`](PROJECT_MASTER_GUIDE.md) to understand the high-level purpose: **Autonomous Agentic Mutation Testing & Self-Hardening Test Suites**.
2. **Step 2: The Core Architecture**  
   Read [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) and [`COMPLETE_FILE_AND_MODULE_MAP.md`](COMPLETE_FILE_AND_MODULE_MAP.md) to understand the six layers, the FastAPI backend, and the exact source code files.
3. **Step 3: Multi-Agent Coordination & Protocols**  
   Read [`AGENTIC_SYSTEM_DEEP_DIVE.md`](AGENTIC_SYSTEM_DEEP_DIVE.md) and [`BLACKBOARD_MCP_A2A_CREWAI_ADK_GUIDE.md`](BLACKBOARD_MCP_A2A_CREWAI_ADK_GUIDE.md) to master the five specialized agents, the typed in-memory Blackboard, FastMCP servers, CrewAI Critic, Google ADK, and Linux Foundation A2A v0.3.0 discovery card.
4. **Step 4: Testing Engine & Mutation Theory**  
   Read [`TEST_GENERATION_AND_MUTATION_TESTING.md`](TEST_GENERATION_AND_MUTATION_TESTING.md) to understand AST mutation operators, granular scenario synthesis (`normal`, `boundary`, `negative`, `exception`), and Rice's Theorem on equivalent mutants.
5. **Step 5: Security & Defensive Boundaries**  
   Read [`SECURITY_AND_RELIABILITY.md`](SECURITY_AND_RELIABILITY.md) to explain the 84 passed security tests, socket monkey-patch egress blocking, SSRF defenses, and XML prompt injection boundaries.
6. **Step 6: Academic Defense & Viva Q&A**  
   Read [`ACADEMIC_REQUIREMENTS_AND_VIVA.md`](ACADEMIC_REQUIREMENTS_AND_VIVA.md) which contains the complete defense of the 11 Phase 2 Academic Requirements and answers to 30 challenging technical viva questions.
7. **Step 7: Limitations & Future Roadmap**  
   Read [`PROJECT_LIMITATIONS_AND_ROADMAP.md`](PROJECT_LIMITATIONS_AND_ROADMAP.md) to remain intellectually honest about known boundaries.

---

## 2. CRITICAL RULES & INTELLECTUAL HONESTY FOR GPT

When discussing TestForge with users, students, or university evaluators, you must adhere strictly to these principles:

### Rule 1: Never Misrepresent Local Determinism as Live Cloud API Spending
- TestForge runs with **$0.00 external LLM expenditure** during local evaluation. It implements local bridge adapters (`CrewAILLMBridge`, `ADKModelBridge`) that perform deterministic AST scenario synthesis and semantic diff analysis offline.
- Do NOT claim that thousands of dollars of OpenAI/Anthropic API calls were made. State clearly that live API keys are supported via `.env`, but deterministic local mode was used for 100% reproducible academic evaluation.

### Rule 2: Never Claim 100% Equivalent Mutant Detection
- If asked about equivalent mutants, cite **Rice's Theorem**: perfectly detecting all equivalent mutants in arbitrary Turing-complete code is mathematically undecidable.
- Explain that TestForge uses static pattern heuristics (dead-code analysis, algebraic identities) to flag suspects in `CriticSpace`, but does not claim impossible general-case equivalence proofs.

### Rule 3: Clarify the Single Frontend Architecture
- The legacy Streamlit frontend (Port 8501) was **permanently disabled and retired**.
- The only supported user interface is the HTML5/CSS3/Vanilla JavaScript single-page application hosted on **FastAPI Port 8000** (`http://127.0.0.1:8000/`).

### Rule 4: State Deployment Reality Transparently
- The project includes a fully verified, multi-stage production `Dockerfile` with a non-root security user (`testforge:10001`) and `docker-compose.yml`.
- However, the system is evaluated locally; no live public cloud cluster (e.g. AWS ECS/GCP Cloud Run) was provisioned for this academic evaluation to maintain zero operational expense.

### Rule 5: Distinguish Test Suite Hardening from Automated Program Repair (APR)
- TestForge strengthens the **test suite** by generating tests that kill mutants. It does not fix bugs in the original target source code itself.

