"""
build_redesigned_assets.py
Generates the 4 strictly black-and-white vector architecture diagrams (SVG & 300 DPI PNG)
and 1 professional high-contrast benchmark graph for the TestForge WIP Report.
"""
import os
import fitz  # PyMuPDF
import matplotlib.pyplot as plt
import numpy as np

ASSETS_DIR = "/Users/sourabh/TestForge/docs/WIP_REPORT/assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

def svg_to_png(svg_str, png_path, dpi=300):
    doc = fitz.open(stream=svg_str.encode("utf-8"), filetype="svg")
    pix = doc[0].get_pixmap(dpi=dpi)
    pix.save(png_path)
    print(f"Rendered {png_path} ({pix.width}x{pix.height} px)")

# ==============================================================================
# FIGURE 1: OVERALL LAYERED TESTFORGE SYSTEM ARCHITECTURE
# ==============================================================================
def generate_figure1():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 780" width="1000" height="780" style="background:#ffffff; font-family:Arial, Helvetica, sans-serif;">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000" />
    </marker>
    <marker id="arrow-bi" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000" />
    </marker>
  </defs>

  <!-- Title & Frame -->
  <text x="500" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#000000">Figure 1: Overall Layered TestForge System Architecture</text>

  <!-- LAYER 1: User Interaction Layer -->
  <rect x="30" y="40" width="940" height="75" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="40" width="220" height="20" fill="#000000" />
  <text x="40" y="54" font-size="10" font-weight="bold" fill="#ffffff">LAYER 1: USER INTERACTION LAYER</text>
  
  <rect x="50" y="66" width="155" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="127" y="82" text-anchor="middle" font-size="9" font-weight="bold">Source Code Upload</text>
  <text x="127" y="94" text-anchor="middle" font-size="8">Python file / inline paste</text>

  <rect x="220" y="66" width="165" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="302" y="82" text-anchor="middle" font-size="9" font-weight="bold">Target &amp; Config Selector</text>
  <text x="302" y="94" text-anchor="middle" font-size="8">Callables, iterations, budget</text>

  <rect x="400" y="66" width="160" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="480" y="82" text-anchor="middle" font-size="9" font-weight="bold">Job Control &amp; Triggers</text>
  <text x="480" y="94" text-anchor="middle" font-size="8">Start, cancel, retry, export</text>

  <rect x="575" y="66" width="185" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="667" y="82" text-anchor="middle" font-size="9" font-weight="bold">Telemetry &amp; Wiretap</text>
  <text x="667" y="94" text-anchor="middle" font-size="8">WebSocket real-time logs</text>

  <rect x="775" y="66" width="175" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="862" y="82" text-anchor="middle" font-size="9" font-weight="bold">Checkpoints &amp; Replay</text>
  <text x="862" y="94" text-anchor="middle" font-size="8">Revision timeline &amp; audit</text>

  <!-- LAYER 2: API and Application Layer -->
  <rect x="30" y="125" width="940" height="75" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="125" width="220" height="20" fill="#000000" />
  <text x="40" y="139" font-size="10" font-weight="bold" fill="#ffffff">LAYER 2: API &amp; APPLICATION LAYER</text>

  <rect x="50" y="151" width="190" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="145" y="167" text-anchor="middle" font-size="9" font-weight="bold">FastAPI Application</text>
  <text x="145" y="179" text-anchor="middle" font-size="8">Async lifespan, CORS, static</text>

  <rect x="255" y="151" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="365" y="167" text-anchor="middle" font-size="9" font-weight="bold">REST API Endpoints</text>
  <text x="365" y="179" text-anchor="middle" font-size="8">/api/harden, /api/checkpoints, /healthz</text>

  <rect x="490" y="151" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="600" y="167" text-anchor="middle" font-size="9" font-weight="bold">WebSocket Hub &amp; Wiretap</text>
  <text x="600" y="179" text-anchor="middle" font-size="8">/ws/telemetry streaming broadcaster</text>

  <rect x="725" y="151" width="225" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="837" y="167" text-anchor="middle" font-size="9" font-weight="bold">Pydantic Schema Validation</text>
  <text x="837" y="179" text-anchor="middle" font-size="8">Request/response strict models</text>

  <!-- LAYER 3: Agent Orchestration Layer -->
  <rect x="30" y="210" width="940" height="75" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="210" width="240" height="20" fill="#000000" />
  <text x="40" y="224" font-size="10" font-weight="bold" fill="#ffffff">LAYER 3: AGENT ORCHESTRATION LAYER</text>

  <rect x="50" y="236" width="230" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="165" y="252" text-anchor="middle" font-size="9" font-weight="bold">TestForge Orchestrator</text>
  <text x="165" y="264" text-anchor="middle" font-size="8">Lifecycle, async pipeline coordination</text>

  <rect x="300" y="236" width="190" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="395" y="252" text-anchor="middle" font-size="9" font-weight="bold">Reflection &amp; Refinement Loop</text>
  <text x="395" y="264" text-anchor="middle" font-size="8">Multi-iteration budget governor</text>

  <rect x="510" y="236" width="200" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="610" y="252" text-anchor="middle" font-size="9" font-weight="bold">Callback Dispatcher</text>
  <text x="610" y="264" text-anchor="middle" font-size="8">Step-wise stage telemetry emission</text>

  <rect x="730" y="236" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="840" y="252" text-anchor="middle" font-size="9" font-weight="bold">Cancellation &amp; Watchdog</text>
  <text x="840" y="264" text-anchor="middle" font-size="8">Timeout guards, signal handling</text>

  <!-- LAYER 4: Intelligence and Analysis Layer -->
  <rect x="30" y="295" width="940" height="75" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="295" width="240" height="20" fill="#000000" />
  <text x="40" y="309" font-size="10" font-weight="bold" fill="#ffffff">LAYER 4: INTELLIGENCE &amp; ANALYSIS LAYER</text>

  <rect x="50" y="321" width="205" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="152" y="337" text-anchor="middle" font-size="9" font-weight="bold">AST Ingestion &amp; Discovery</text>
  <text x="152" y="349" text-anchor="middle" font-size="8">extract_callable_signatures_ast</text>

  <rect x="270" y="321" width="210" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="375" y="337" text-anchor="middle" font-size="9" font-weight="bold">Intelligent AST Synthesizer</text>
  <text x="375" y="349" text-anchor="middle" font-size="8">Multi-callable, boundary &amp; exception</text>

  <rect x="495" y="321" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="605" y="337" text-anchor="middle" font-size="9" font-weight="bold">Google ADK Runner &amp; Agent</text>
  <text x="605" y="349" text-anchor="middle" font-size="8">Candidate test generator pipeline</text>

  <rect x="730" y="321" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="840" y="337" text-anchor="middle" font-size="9" font-weight="bold">CrewAI Critic &amp; Mutator</text>
  <text x="840" y="349" text-anchor="middle" font-size="8">Surviving mutant diagnosis &amp; triage</text>

  <!-- LAYER 5: Tool Integration Layer -->
  <rect x="30" y="380" width="940" height="75" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="380" width="220" height="20" fill="#000000" />
  <text x="40" y="394" font-size="10" font-weight="bold" fill="#ffffff">LAYER 5: TOOL INTEGRATION LAYER</text>

  <rect x="50" y="406" width="205" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="152" y="422" text-anchor="middle" font-size="9" font-weight="bold">FastMCP Server Core</text>
  <text x="152" y="434" text-anchor="middle" font-size="8">Model Context Protocol endpoint</text>

  <rect x="270" y="406" width="210" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="375" y="422" text-anchor="middle" font-size="9" font-weight="bold">Filesystem MCP Tools</text>
  <text x="375" y="434" text-anchor="middle" font-size="8">read_text_file, list_dir, safe paths</text>

  <rect x="495" y="406" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="605" y="422" text-anchor="middle" font-size="9" font-weight="bold">GitHub MCP Client</text>
  <text x="605" y="434" text-anchor="middle" font-size="8">Offline test doubles &amp; repo info</text>

  <rect x="730" y="406" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="840" y="422" text-anchor="middle" font-size="9" font-weight="bold">A2A Protocol v0.3.0</text>
  <text x="840" y="434" text-anchor="middle" font-size="8">Agent Card (/.well-known/agent.json)</text>

  <!-- LAYER 6: Execution and Validation Layer -->
  <rect x="30" y="465" width="940" height="75" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="465" width="260" height="20" fill="#000000" />
  <text x="40" y="479" font-size="10" font-weight="bold" fill="#ffffff">LAYER 6: EXECUTION &amp; VALIDATION LAYER</text>

  <rect x="50" y="491" width="205" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="152" y="507" text-anchor="middle" font-size="9" font-weight="bold">Subprocess Test Sandbox</text>
  <text x="152" y="519" text-anchor="middle" font-size="8">Isolated pytest execution, timeouts</text>

  <rect x="270" y="491" width="210" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="375" y="507" text-anchor="middle" font-size="9" font-weight="bold">AST Mutation Engine</text>
  <text x="375" y="519" text-anchor="middle" font-size="8">AOR, ROR, COR, CRP, LCR operators</text>

  <rect x="495" y="491" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="605" y="507" text-anchor="middle" font-size="9" font-weight="bold">Mutant Execution &amp; Triage</text>
  <text x="605" y="519" text-anchor="middle" font-size="8">Killed, survived, equivalent matrix</text>

  <rect x="730" y="491" width="220" height="38" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="840" y="507" text-anchor="middle" font-size="9" font-weight="bold">Coverage &amp; Security Guards</text>
  <text x="840" y="519" text-anchor="middle" font-size="8">Statement coverage, clean-code integrity</text>

  <!-- LAYER 7: State and Persistence Layer -->
  <rect x="30" y="550" width="940" height="120" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="550" width="260" height="20" fill="#000000" />
  <text x="40" y="564" font-size="10" font-weight="bold" fill="#ffffff">LAYER 7: STATE &amp; PERSISTENCE LAYER</text>

  <!-- Blackboard Box inside Layer 7 -->
  <rect x="45" y="575" width="670" height="85" fill="#ffffff" stroke="#000000" stroke-width="1" stroke-dasharray="3,3" />
  <text x="55" y="590" font-size="9" font-weight="bold">Blackboard Controller (RLock Synchronization, Revision Counter, Atomic Snapshots)</text>
  
  <rect x="55" y="598" width="115" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="112" y="612" text-anchor="middle" font-size="8" font-weight="bold">TargetSpace</text>
  <text x="112" y="624" text-anchor="middle" font-size="7">Source code</text>
  <text x="112" y="634" text-anchor="middle" font-size="7">AST callables</text>
  <text x="112" y="644" text-anchor="middle" font-size="7">Module SHA-256</text>

  <rect x="180" y="598" width="115" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="237" y="612" text-anchor="middle" font-size="8" font-weight="bold">SuiteSpace</text>
  <text x="237" y="624" text-anchor="middle" font-size="7">Baseline tests</text>
  <text x="237" y="634" text-anchor="middle" font-size="7">Candidate tests</text>
  <text x="237" y="644" text-anchor="middle" font-size="7">Validated suite</text>

  <rect x="305" y="598" width="115" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="362" y="612" text-anchor="middle" font-size="8" font-weight="bold">MutantSpace</text>
  <text x="362" y="624" text-anchor="middle" font-size="7">Mutant diffs</text>
  <text x="362" y="634" text-anchor="middle" font-size="7">Execution matrix</text>
  <text x="362" y="644" text-anchor="middle" font-size="7">Killed / survived</text>

  <rect x="430" y="598" width="115" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="487" y="612" text-anchor="middle" font-size="8" font-weight="bold">CriticSpace</text>
  <text x="487" y="624" text-anchor="middle" font-size="7">Critic guidance</text>
  <text x="487" y="634" text-anchor="middle" font-size="7">Diagnostic tips</text>
  <text x="487" y="644" text-anchor="middle" font-size="7">Iteration count</text>

  <rect x="555" y="598" width="145" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="627" y="612" text-anchor="middle" font-size="8" font-weight="bold">MetricsSpace</text>
  <text x="627" y="624" text-anchor="middle" font-size="7">Coverage % (stmt/line)</text>
  <text x="627" y="634" text-anchor="middle" font-size="7">Raw / Adjusted Score %</text>
  <text x="627" y="644" text-anchor="middle" font-size="7">Runtime execution time</text>

  <!-- SQLite DB box -->
  <rect x="735" y="575" width="220" height="85" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="845" y="594" text-anchor="middle" font-size="10" font-weight="bold">SQLite Persistence Store</text>
  <text x="845" y="610" text-anchor="middle" font-size="8">testforge_checkpoints.db</text>
  <text x="845" y="624" text-anchor="middle" font-size="8">• 1,104 Atomic Checkpoints</text>
  <text x="845" y="636" text-anchor="middle" font-size="8">• Checkpoint Replay Engine</text>
  <text x="845" y="648" text-anchor="middle" font-size="8">• Full SHA-256 Provenance Log</text>

  <!-- Inter-layer Flow Connectors -->
  <!-- Layer 1 to 2 -->
  <line x1="140" y1="115" x2="140" y2="125" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="600" y1="125" x2="600" y2="115" stroke="#000000" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#arrow)" />
  <line x1="860" y1="115" x2="860" y2="125" stroke="#000000" stroke-width="1" marker-end="url(#arrow)" />

  <!-- Layer 2 to 3 -->
  <line x1="165" y1="200" x2="165" y2="210" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="600" y1="210" x2="600" y2="200" stroke="#000000" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#arrow)" />

  <!-- Layer 3 to 4 -->
  <line x1="200" y1="285" x2="200" y2="295" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="600" y1="285" x2="600" y2="295" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="840" y1="295" x2="840" y2="285" stroke="#000000" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#arrow)" />

  <!-- Layer 4 to 5 & 6 -->
  <line x1="375" y1="370" x2="375" y2="380" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="605" y1="370" x2="605" y2="380" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="840" y1="370" x2="840" y2="465" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />

  <!-- Layer 6 to 7 -->
  <line x1="200" y1="540" x2="200" y2="575" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="375" y1="540" x2="375" y2="575" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <line x1="605" y1="540" x2="605" y2="575" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />

  <!-- Blackboard to SQLite -->
  <line x1="715" y1="620" x2="735" y2="620" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />

  <!-- LEGEND -->
  <rect x="30" y="685" width="940" height="50" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="40" y="702" font-size="9" font-weight="bold">DIAGRAM LEGEND &amp; CONNECTIONS:</text>
  
  <line x1="220" y1="698" x2="270" y2="698" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="280" y="702" font-size="8">Synchronous Control / Data Flow</text>

  <line x1="450" y1="698" x2="500" y2="698" stroke="#000000" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#arrow)" />
  <text x="510" y="702" font-size="8">Asynchronous Callback / Feedback / Telemetry</text>

  <line x1="740" y1="698" x2="790" y2="698" stroke="#000000" stroke-width="1.5" stroke-dasharray="1,2" marker-end="url(#arrow)" />
  <text x="800" y="702" font-size="8">Subprocess Sandboxed Boundary</text>

  <text x="40" y="722" font-size="8" fill="#333333">Note: All multi-agent interactions are coordinated strictly through the Orchestrator and mediated via Blackboard shared state with RLock synchronization.</text>
</svg>
"""
    svg_path = os.path.join(ASSETS_DIR, "figure1_system_architecture.svg")
    png_path = os.path.join(ASSETS_DIR, "figure1_system_architecture.png")
    with open(svg_path, "w") as f:
        f.write(svg)
    svg_to_png(svg, png_path, dpi=300)

# ==============================================================================
# FIGURE 2: MULTI-AGENT EXECUTION AND COORDINATION WORKFLOW
# ==============================================================================
def generate_figure2():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 780" width="1000" height="780" style="background:#ffffff; font-family:Arial, Helvetica, sans-serif;">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000" />
    </marker>
  </defs>

  <!-- Title -->
  <text x="500" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#000000">Figure 2: Multi-Agent Execution and Coordination Workflow</text>

  <!-- Stage 1 & 2: User Submission & Ingestion -->
  <rect x="40" y="45" width="200" height="48" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="140" y="63" text-anchor="middle" font-size="9" font-weight="bold">1. User Submits Source</text>
  <text x="140" y="76" text-anchor="middle" font-size="8">FastAPI /api/harden (POST)</text>
  <text x="140" y="86" text-anchor="middle" font-size="7" fill="#444444">Validates payload schema</text>

  <line x1="240" y1="69" x2="280" y2="69" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="280" y="45" width="200" height="48" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="380" y="63" text-anchor="middle" font-size="9" font-weight="bold">2. Orchestrator Init</text>
  <text x="380" y="76" text-anchor="middle" font-size="8">Job lifecycle &amp; Blackboard init</text>
  <text x="380" y="86" text-anchor="middle" font-size="7" fill="#444444">Allocates job_id &amp; thread RLock</text>

  <line x1="480" y1="69" x2="520" y2="69" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="520" y="45" width="210" height="48" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="625" y="63" text-anchor="middle" font-size="9" font-weight="bold">3. Source Ingestion &amp; AST</text>
  <text x="625" y="76" text-anchor="middle" font-size="8">extract_callable_signatures_ast</text>
  <text x="625" y="86" text-anchor="middle" font-size="7" fill="#444444">Defuses prompt injection; SHA-256</text>

  <line x1="730" y1="69" x2="770" y2="69" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="770" y="45" width="190" height="48" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="865" y="63" text-anchor="middle" font-size="9" font-weight="bold">4. Populate TargetSpace</text>
  <text x="865" y="76" text-anchor="middle" font-size="8">Callables, params, types</text>
  <text x="865" y="86" text-anchor="middle" font-size="7" fill="#444444">Checkpoint rev 1 to SQLite</text>

  <!-- Transition down from Row 1 to Row 2 -->
  <line x1="865" y1="93" x2="865" y2="125" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <!-- Stage 5 to 8: Test Generation & Baseline -->
  <rect x="760" y="125" width="210" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="865" y="142" text-anchor="middle" font-size="9" font-weight="bold">5. Intelligent Synthesizer</text>
  <text x="865" y="155" text-anchor="middle" font-size="8">Multi-callable coverage engine</text>
  <text x="865" y="166" text-anchor="middle" font-size="7" fill="#444444">Type-driven asserts &amp; boundaries</text>

  <line x1="760" y1="151" x2="720" y2="151" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="510" y="125" width="210" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="615" y="142" text-anchor="middle" font-size="9" font-weight="bold">6. Google ADK Generator</text>
  <text x="615" y="155" text-anchor="middle" font-size="8">LLM agent candidate generation</text>
  <text x="615" y="166" text-anchor="middle" font-size="7" fill="#444444">Writes candidate test suite to SuiteSpace</text>

  <line x1="510" y1="151" x2="470" y2="151" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="260" y="125" width="210" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="365" y="142" text-anchor="middle" font-size="9" font-weight="bold">7. Subprocess Validation</text>
  <text x="365" y="155" text-anchor="middle" font-size="8">Isolated pytest execution</text>
  <text x="365" y="166" text-anchor="middle" font-size="7" fill="#444444">Verifies all generated tests pass</text>

  <line x1="260" y1="151" x2="220" y2="151" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="40" y="125" width="180" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="130" y="142" text-anchor="middle" font-size="9" font-weight="bold">8. Baseline Suite Ready</text>
  <text x="130" y="155" text-anchor="middle" font-size="8">Coverage measurement</text>
  <text x="130" y="166" text-anchor="middle" font-size="7" fill="#444444">Logs baseline line/stmt coverage</text>

  <!-- Transition down from Row 2 to Row 3 -->
  <line x1="130" y1="177" x2="130" y2="210" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <!-- Stage 9 to 12: Mutation Engine & Critic -->
  <rect x="40" y="210" width="200" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="140" y="227" text-anchor="middle" font-size="9" font-weight="bold">9. AST Mutation Generator</text>
  <text x="140" y="240" text-anchor="middle" font-size="8">Generates AOR, ROR, COR mutants</text>
  <text x="140" y="251" text-anchor="middle" font-size="7" fill="#444444">Saves mutant AST diffs to MutantSpace</text>

  <line x1="240" y1="236" x2="280" y2="236" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="280" y="210" width="210" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="385" y="227" text-anchor="middle" font-size="9" font-weight="bold">10. Subprocess Mutant Run</text>
  <text x="385" y="240" text-anchor="middle" font-size="8">Sandbox pytest per mutant</text>
  <text x="385" y="251" text-anchor="middle" font-size="7" fill="#444444">Captures killed, survived, timeout</text>

  <line x1="490" y1="236" x2="530" y2="236" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="530" y="210" width="200" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="630" y="227" text-anchor="middle" font-size="9" font-weight="bold">11. Evaluate Metrics</text>
  <text x="630" y="240" text-anchor="middle" font-size="8">Raw &amp; adjusted mutation score</text>
  <text x="630" y="251" text-anchor="middle" font-size="7" fill="#444444">Triage equivalent mutants</text>

  <line x1="730" y1="236" x2="770" y2="236" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="770" y="210" width="190" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="865" y="227" text-anchor="middle" font-size="9" font-weight="bold">12. CrewAI Critic</text>
  <text x="865" y="240" text-anchor="middle" font-size="8">Diagnose surviving mutants</text>
  <text x="865" y="251" text-anchor="middle" font-size="7" fill="#444444">Writes directives to CriticSpace</text>

  <!-- Transition down from Row 3 to Decision Node -->
  <line x1="865" y1="262" x2="865" y2="300" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <!-- DECISION NODE: Target Mutation Score Achieved? -->
  <polygon points="500,295 680,345 500,395 320,345" fill="#ffffff" stroke="#000000" stroke-width="2" />
  <text x="500" y="340" text-anchor="middle" font-size="10" font-weight="bold">Target Score Met OR</text>
  <text x="500" y="354" text-anchor="middle" font-size="10" font-weight="bold">Budget Exhausted?</text>

  <!-- Connect from 12 to Decision -->
  <path d="M 865 300 L 865 345 L 680 345" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <!-- Branch NO: Reflection and Refinement -->
  <path d="M 320 345 L 180 345 L 180 430" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />
  <text x="250" y="338" font-size="9" font-weight="bold" fill="#000000">[NO: Iterate Loop]</text>

  <rect x="60" y="430" width="240" height="55" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="180" y="448" text-anchor="middle" font-size="9" font-weight="bold">13. Test Suite Refinement</text>
  <text x="180" y="461" text-anchor="middle" font-size="8">Synthesizes targeted test cases</text>
  <text x="180" y="473" text-anchor="middle" font-size="7" fill="#444444">Kills surviving mutants using critic hints</text>

  <!-- Loop back from Refinement to Sandbox Validation -->
  <path d="M 180 485 L 180 520 L 385 520 L 385 262" fill="none" stroke="#000000" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arr)" />
  <text x="280" y="535" font-size="8" font-weight="bold">Iterate: Re-execute in Sandbox &amp; Re-evaluate Mutants</text>

  <!-- Branch YES: Final Export & Persistence -->
  <line x1="500" y1="395" x2="500" y2="440" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />
  <text x="510" y="420" font-size="9" font-weight="bold" fill="#000000">[YES: Success Criteria Met]</text>

  <rect x="380" y="440" width="240" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="500" y="457" text-anchor="middle" font-size="9" font-weight="bold">14. Clean-Code Integrity Check</text>
  <text x="500" y="470" text-anchor="middle" font-size="8">Verify target source SHA-256 untouched</text>
  <text x="500" y="481" text-anchor="middle" font-size="7" fill="#444444">Zero mutation leakage to original file</text>

  <line x1="500" y1="492" x2="500" y2="525" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="380" y="525" width="240" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="500" y="542" text-anchor="middle" font-size="9" font-weight="bold">15. Final Suite Validation &amp; Hash</text>
  <text x="500" y="555" text-anchor="middle" font-size="8">Full regression run &amp; SHA-256 seal</text>
  <text x="500" y="566" text-anchor="middle" font-size="7" fill="#444444">Candidate &amp; validated hashes match</text>

  <line x1="500" y1="577" x2="500" y2="610" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <!-- Final Stages: Checkpoint & UI Broadcast -->
  <rect x="220" y="610" width="260" height="55" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="350" y="628" text-anchor="middle" font-size="9" font-weight="bold">16. SQLite Checkpoint Persistence</text>
  <text x="350" y="641" text-anchor="middle" font-size="8">Save final snapshot &amp; stage 'FINALIZED'</text>
  <text x="350" y="653" text-anchor="middle" font-size="7" fill="#444444">Audit log written to testforge_checkpoints.db</text>

  <line x1="480" y1="637" x2="530" y2="637" stroke="#000000" stroke-width="1.5" marker-end="url(#arr)" />

  <rect x="530" y="610" width="270" height="55" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="665" y="628" text-anchor="middle" font-size="9" font-weight="bold">17. Telemetry Broadcast &amp; UI Export</text>
  <text x="665" y="641" text-anchor="middle" font-size="8">WebSocket /ws/telemetry status 'COMPLETED'</text>
  <text x="665" y="653" text-anchor="middle" font-size="7" fill="#444444">Export test_hardened.py to user dashboard</text>

  <!-- Cancellation & Timeout Guard Box -->
  <rect x="40" y="695" width="920" height="55" fill="#ffffff" stroke="#000000" stroke-width="1" stroke-dasharray="2,2" />
  <text x="50" y="712" font-size="9" font-weight="bold">WATCHDOG, TIMEOUT &amp; CANCELLATION GUARDS:</text>
  <text x="50" y="726" font-size="8">• Subprocess Timeout: Individual test execution terminated if latency exceeds sandbox limit (15.0s / 30.0s).</text>
  <text x="50" y="738" font-size="8">• User Cancellation: /api/harden/cancel/{job_id} triggers threading.Event termination flag, saving checkpoint before safe exit.</text>
</svg>
"""
    svg_path = os.path.join(ASSETS_DIR, "figure2_execution_workflow.svg")
    png_path = os.path.join(ASSETS_DIR, "figure2_execution_workflow.png")
    with open(svg_path, "w") as f:
        f.write(svg)
    svg_to_png(svg, png_path, dpi=300)

# ==============================================================================
# FIGURE 3: BLACKBOARD SHARED-STATE ARCHITECTURE
# ==============================================================================
def generate_figure3():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="1000" height="700" style="background:#ffffff; font-family:Arial, Helvetica, sans-serif;">
  <defs>
    <marker id="arrow3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000" />
    </marker>
  </defs>

  <!-- Title -->
  <text x="500" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#000000">Figure 3: Blackboard Shared-State Architecture and Agent Access Patterns</text>

  <!-- Top Controller Box -->
  <rect x="180" y="45" width="640" height="70" fill="#ffffff" stroke="#000000" stroke-width="2" />
  <text x="500" y="66" text-anchor="middle" font-size="12" font-weight="bold">Blackboard Controller (testforge/blackboard.py:Blackboard)</text>
  <text x="500" y="82" text-anchor="middle" font-size="9">• Thread Synchronization: threading.RLock (atomic read/write across all partitions)</text>
  <text x="500" y="96" text-anchor="middle" font-size="9">• Monotonic Revision Counter: revision: int | Timestamps: created_at, updated_at</text>
  <text x="500" y="108" text-anchor="middle" font-size="8" fill="#444444">• Checkpoint Hooks: save_checkpoint_to_db() snapshots full state on key milestones</text>

  <!-- Left: Agents Pool -->
  <rect x="30" y="150" width="200" height="380" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="30" y="150" width="200" height="22" fill="#000000" />
  <text x="130" y="165" text-anchor="middle" font-size="10" font-weight="bold" fill="#ffffff">PARTICIPATING AGENTS</text>

  <!-- Agent 1 -->
  <rect x="42" y="185" width="176" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="130" y="202" text-anchor="middle" font-size="9" font-weight="bold">TargetManagerAgent</text>
  <text x="130" y="215" text-anchor="middle" font-size="8">Ingestion &amp; AST Analysis</text>
  <text x="130" y="227" text-anchor="middle" font-size="7" fill="#333333">Writes: TargetSpace</text>

  <!-- Agent 2 -->
  <rect x="42" y="250" width="176" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="130" y="267" text-anchor="middle" font-size="9" font-weight="bold">TestGenAgent / ADK</text>
  <text x="130" y="280" text-anchor="middle" font-size="8">Synthesis &amp; Refinement</text>
  <text x="130" y="292" text-anchor="middle" font-size="7" fill="#333333">Reads: Target, Critic | Writes: Suite</text>

  <!-- Agent 3 -->
  <rect x="42" y="315" width="176" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="130" y="332" text-anchor="middle" font-size="9" font-weight="bold">EvaluatorAgent</text>
  <text x="130" y="345" text-anchor="middle" font-size="8">Sandbox &amp; Mutation Engine</text>
  <text x="130" y="357" text-anchor="middle" font-size="7" fill="#333333">Reads: Suite | Writes: Mutant, Metrics</text>

  <!-- Agent 4 -->
  <rect x="42" y="380" width="176" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="130" y="397" text-anchor="middle" font-size="9" font-weight="bold">CriticAgent (CrewAI)</text>
  <text x="130" y="410" text-anchor="middle" font-size="8">Diagnostic Evaluation</text>
  <text x="130" y="422" text-anchor="middle" font-size="7" fill="#333333">Reads: Mutant, Suite | Writes: Critic</text>

  <!-- Agent 5 -->
  <rect x="42" y="445" width="176" height="52" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="130" y="462" text-anchor="middle" font-size="9" font-weight="bold">OrchestratorAgent</text>
  <text x="130" y="475" text-anchor="middle" font-size="8">Workflow &amp; Budget Control</text>
  <text x="130" y="487" text-anchor="middle" font-size="7" fill="#333333">Coordinates read/writes &amp; checkpts</text>

  <!-- Middle: The 5 Dedicated Partitions -->
  <rect x="270" y="150" width="460" height="380" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="270" y="150" width="460" height="22" fill="#000000" />
  <text x="500" y="165" text-anchor="middle" font-size="10" font-weight="bold" fill="#ffffff">BLACKBOARD STATE PARTITIONS (DECOUPLED SUBSPACES)</text>

  <!-- Partition 1: TargetSpace -->
  <rect x="285" y="185" width="430" height="58" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="295" y="201" font-size="9" font-weight="bold">1. TargetSpace (target_space)</text>
  <text x="295" y="215" font-size="8">• Source code string &amp; AST tree</text>
  <text x="295" y="226" font-size="8">• Discovered callables: 10/10 signatures, parameters, return types</text>
  <text x="295" y="237" font-size="8">• Security flags: safe AST imports, defused prompt injection, module SHA-256</text>

  <!-- Partition 2: SuiteSpace -->
  <rect x="285" y="250" width="430" height="58" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="295" y="266" font-size="9" font-weight="bold">2. SuiteSpace (suite_space)</text>
  <text x="295" y="280" font-size="8">• Candidate test suites generated by Intelligent Synthesizer / Google ADK</text>
  <text x="295" y="291" font-size="8">• Validated test suite (passed in sandbox with zero execution errors)</text>
  <text x="295" y="302" font-size="8">• Suite SHA-256 cryptographic provenance hash: 7aa66bf4...</text>

  <!-- Partition 3: MutantSpace -->
  <rect x="285" y="315" width="430" height="58" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="295" y="331" font-size="9" font-weight="bold">3. MutantSpace (mutant_space)</text>
  <text x="295" y="345" font-size="8">• Generated AST mutants: operator type (AOR, ROR, COR), AST line, node diff</text>
  <text x="295" y="356" font-size="8">• Execution results: Killed (176), Survived (82), Timed out (0)</text>
  <text x="295" y="367" font-size="8">• Verified equivalent mutants list (24 rounding/constant mutants)</text>

  <!-- Partition 4: CriticSpace -->
  <rect x="285" y="380" width="430" height="58" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="295" y="396" font-size="9" font-weight="bold">4. CriticSpace (critic_space)</text>
  <text x="295" y="410" font-size="8">• CrewAI diagnostic evaluation reports on surviving mutants</text>
  <text x="295" y="421" font-size="8">• Synthesis recommendations: boundary inputs (e.g. 99.99), exception checks</text>
  <text x="295" y="432" font-size="8">• Reflection iteration counter &amp; convergence flags</text>

  <!-- Partition 5: MetricsSpace -->
  <rect x="285" y="445" width="430" height="58" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="295" y="461" font-size="9" font-weight="bold">5. MetricsSpace (metrics_space)</text>
  <text x="295" y="475" font-size="8">• Coverage metrics: statement coverage % (100% discount, 90.15% logistics)</text>
  <text x="295" y="486" font-size="8">• Mutation scores: Raw (68.22%) and Adjusted (75.21%) scores</text>
  <text x="295" y="497" font-size="8">• Performance KPIs: execution latencies, pass counts, test execution duration</text>

  <!-- Right: Persistence Store -->
  <rect x="760" y="150" width="210" height="380" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <rect x="760" y="150" width="210" height="22" fill="#000000" />
  <text x="865" y="165" text-anchor="middle" font-size="10" font-weight="bold" fill="#ffffff">PERSISTENCE STORE</text>

  <rect x="775" y="195" width="180" height="130" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="865" y="215" text-anchor="middle" font-size="10" font-weight="bold">SQLite Database</text>
  <text x="865" y="230" text-anchor="middle" font-size="8">testforge_checkpoints.db</text>
  <text x="865" y="248" text-anchor="middle" font-size="8">• Schema: checkpoints table</text>
  <text x="865" y="262" text-anchor="middle" font-size="8">• checkpoint_id (chk_...)</text>
  <text x="865" y="276" text-anchor="middle" font-size="8">• stage (INGEST, EVAL, etc.)</text>
  <text x="865" y="290" text-anchor="middle" font-size="8">• revision counter (int)</text>
  <text x="865" y="304" text-anchor="middle" font-size="8">• serialized JSON state blob</text>
  <text x="865" y="318" text-anchor="middle" font-size="8">• SHA-256 state hash</text>

  <rect x="775" y="345" width="180" height="150" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="865" y="365" text-anchor="middle" font-size="10" font-weight="bold">Audit &amp; Replay Engine</text>
  <text x="865" y="385" text-anchor="middle" font-size="8">• Total Records: 1,104</text>
  <text x="865" y="400" text-anchor="middle" font-size="8">• Historical Replay API</text>
  <text x="865" y="415" text-anchor="middle" font-size="8">• State Rollback Support</text>
  <text x="865" y="430" text-anchor="middle" font-size="8">• Provenance Audit Trail</text>
  <text x="865" y="445" text-anchor="middle" font-size="8">• Crash Recovery Guard</text>

  <!-- Connectors -->
  <!-- Top Controller to Middle Partitions -->
  <line x1="500" y1="115" x2="500" y2="150" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />

  <!-- Agents to Partitions -->
  <line x1="218" y1="211" x2="285" y2="211" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />
  <line x1="218" y1="276" x2="285" y2="276" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />
  <line x1="218" y1="341" x2="285" y2="341" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />
  <line x1="218" y1="406" x2="285" y2="406" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />
  <line x1="218" y1="471" x2="285" y2="471" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />

  <!-- Partitions to SQLite -->
  <line x1="715" y1="260" x2="775" y2="260" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />
  <line x1="715" y1="420" x2="775" y2="420" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow3)" />

  <!-- Bottom Explanatory Notes -->
  <rect x="30" y="550" width="940" height="90" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="40" y="570" font-size="9" font-weight="bold">KEY ARCHITECTURAL GUARANTEES OF THE TESTFORGE BLACKBOARD:</text>
  <text x="40" y="588" font-size="8">• Strict Decoupling: Agents never communicate directly peer-to-peer; all coordination occurs through typed partition updates.</text>
  <text x="40" y="602" font-size="8">• Concurrency Safety: Python's threading.RLock ensures re-entrant atomic partition writes during asynchronous agent execution.</text>
  <text x="40" y="616" font-size="8">• Full Provenance: Every mutation, test suite revision, and critique is versioned monotonically and checkpointed into SQLite.</text>
  <text x="40" y="630" font-size="8">• Replay Reproducibility: Any historical run can be precisely reconstructed and inspected from its persisted JSON snapshot.</text>
</svg>
"""
    svg_path = os.path.join(ASSETS_DIR, "figure3_blackboard_architecture.svg")
    png_path = os.path.join(ASSETS_DIR, "figure3_blackboard_architecture.png")
    with open(svg_path, "w") as f:
        f.write(svg)
    svg_to_png(svg, png_path, dpi=300)

# ==============================================================================
# FIGURE 4: MUTATION-GUIDED TEST GENERATION AND REFINEMENT
# ==============================================================================
def generate_figure4():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="1000" height="700" style="background:#ffffff; font-family:Arial, Helvetica, sans-serif;">
  <defs>
    <marker id="arrow4" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000" />
    </marker>
  </defs>

  <!-- Title -->
  <text x="500" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#000000">Figure 4: Mutation-Guided Test Generation, Evaluation, and Refinement Loop</text>

  <!-- Top Ingestion & Analysis Flow -->
  <rect x="30" y="45" width="170" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="115" y="63" text-anchor="middle" font-size="9" font-weight="bold">Target Source Code</text>
  <text x="115" y="76" text-anchor="middle" font-size="8">Python Module (.py)</text>
  <text x="115" y="87" text-anchor="middle" font-size="7" fill="#444444">SHA-256 seal captured</text>

  <line x1="200" y1="71" x2="235" y2="71" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <rect x="235" y="45" width="175" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="322" y="63" text-anchor="middle" font-size="9" font-weight="bold">AST Parsing &amp; Scope</text>
  <text x="322" y="76" text-anchor="middle" font-size="8">ast.parse() visitor</text>
  <text x="322" y="87" text-anchor="middle" font-size="7" fill="#444444">extract_callable_signatures</text>

  <line x1="410" y1="71" x2="445" y2="71" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <rect x="445" y="45" width="180" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="535" y="63" text-anchor="middle" font-size="9" font-weight="bold">Callable Discovery</text>
  <text x="535" y="76" text-anchor="middle" font-size="8">10/10 Callables Identified</text>
  <text x="535" y="87" text-anchor="middle" font-size="7" fill="#444444">Types, defaults, signatures</text>

  <line x1="625" y1="71" x2="660" y2="71" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <rect x="660" y="45" width="310" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="815" y="63" text-anchor="middle" font-size="9" font-weight="bold">Intelligent Test Synthesis</text>
  <text x="815" y="76" text-anchor="middle" font-size="8">Boundary Values + Negative Exceptions + Normal Flows</text>
  <text x="815" y="87" text-anchor="middle" font-size="7" fill="#444444">Synthesizes candidate test functions for all callables</text>

  <!-- Transition to Baseline Execution -->
  <line x1="815" y1="97" x2="815" y2="130" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <!-- Middle Execution & Mutation Section -->
  <rect x="660" y="130" width="310" height="55" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="815" y="148" text-anchor="middle" font-size="9" font-weight="bold">Baseline Sandbox Execution</text>
  <text x="815" y="161" text-anchor="middle" font-size="8">Isolated pytest in temporary subprocess sandbox</text>
  <text x="815" y="173" text-anchor="middle" font-size="7" fill="#444444">Must pass 100% before mutation (e.g. 11/11 or 64/64)</text>

  <line x1="660" y1="157" x2="610" y2="157" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <rect x="360" y="130" width="250" height="55" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="485" y="148" text-anchor="middle" font-size="9" font-weight="bold">AST Mutation Generation</text>
  <text x="485" y="161" text-anchor="middle" font-size="8">ASTMutator applies mutation operators:</text>
  <text x="485" y="173" text-anchor="middle" font-size="7" fill="#444444">AOR (+/-), ROR (&gt;/&gt;=), COR (and/or), CRP, LCR</text>

  <line x1="360" y1="157" x2="310" y2="157" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <rect x="30" y="130" width="280" height="55" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="170" y="148" text-anchor="middle" font-size="9" font-weight="bold">Mutant Execution &amp; Triage Engine</text>
  <text x="170" y="161" text-anchor="middle" font-size="8">Run test suite against each AST mutant</text>
  <text x="170" y="173" text-anchor="middle" font-size="7" fill="#444444">evaluate_mutants() with timeout guard</text>

  <!-- Connect to Mutant Classification Boxes -->
  <line x1="170" y1="185" x2="170" y2="225" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <!-- Four Mutant Classification Categories -->
  <rect x="30" y="225" width="220" height="85" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="140" y="244" text-anchor="middle" font-size="9" font-weight="bold">KILLED MUTANTS</text>
  <text x="140" y="259" text-anchor="middle" font-size="8">• Test suite fails on mutant</text>
  <text x="140" y="273" text-anchor="middle" font-size="8">• Correct defect detection</text>
  <text x="140" y="287" text-anchor="middle" font-size="8">• Discount: 17 | Logistics: 176</text>
  <text x="140" y="300" text-anchor="middle" font-size="7" fill="#444444">Added to killed_mutants set</text>

  <rect x="270" y="225" width="220" height="85" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="380" y="244" text-anchor="middle" font-size="9" font-weight="bold">SURVIVING MUTANTS</text>
  <text x="380" y="259" text-anchor="middle" font-size="8">• All tests still pass</text>
  <text x="380" y="273" text-anchor="middle" font-size="8">• Exposes test inadequacy</text>
  <text x="380" y="287" text-anchor="middle" font-size="8">• Discount: 2 | Logistics: 82</text>
  <text x="380" y="300" text-anchor="middle" font-size="7" fill="#444444">Routed to Critic for triage</text>

  <rect x="510" y="225" width="220" height="85" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="620" y="244" text-anchor="middle" font-size="9" font-weight="bold">EQUIVALENT MUTANTS</text>
  <text x="620" y="259" text-anchor="middle" font-size="8">• Syntactically different</text>
  <text x="620" y="273" text-anchor="middle" font-size="8">• Semantically identical</text>
  <text x="620" y="287" text-anchor="middle" font-size="8">• Discount: 1 | Logistics: 24</text>
  <text x="620" y="300" text-anchor="middle" font-size="7" fill="#444444">Excluded from adjusted denom</text>

  <rect x="750" y="225" width="220" height="85" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="860" y="244" text-anchor="middle" font-size="9" font-weight="bold">UNREACHED MUTANTS</text>
  <text x="860" y="259" text-anchor="middle" font-size="8">• Located in uncovered lines</text>
  <text x="860" y="273" text-anchor="middle" font-size="8">• Coverage gap indicator</text>
  <text x="860" y="287" text-anchor="middle" font-size="8">• Discount: 0 | Logistics: 13</text>
  <text x="860" y="300" text-anchor="middle" font-size="7" fill="#444444">Triggers new callable inputs</text>

  <!-- Connect Surviving Mutants to Analysis -->
  <line x1="380" y1="310" x2="380" y2="350" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <!-- Surviving Mutant Analysis & Critic Guidance -->
  <rect x="180" y="350" width="640" height="65" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="500" y="369" text-anchor="middle" font-size="10" font-weight="bold">Surviving Mutant Diagnostic Analysis (CrewAI Critic)</text>
  <text x="500" y="385" text-anchor="middle" font-size="8">• Identifies exact operator and boundary (e.g., price &gt; 100 mutated to price &gt;= 100)</text>
  <text x="500" y="398" text-anchor="middle" font-size="8">• Prescribes exact diagnostic test input: generate float value 99.99 to kill boundary mutant</text>
  <text x="500" y="410" text-anchor="middle" font-size="7" fill="#444444">Writes actionable feedback to Blackboard critic_space</text>

  <!-- Refinement Generation -->
  <line x1="500" y1="415" x2="500" y2="445" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <rect x="250" y="445" width="500" height="52" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="500" y="463" text-anchor="middle" font-size="9" font-weight="bold">Targeted Test Refinement &amp; Assertion Hardening</text>
  <text x="500" y="476" text-anchor="middle" font-size="8">Synthesizes targeted test assertions killing the surviving mutants</text>
  <text x="500" y="488" text-anchor="middle" font-size="7" fill="#444444">Appends tests into candidate suite; updates suite SHA-256 hash</text>

  <!-- Loop back arrow to Sandbox execution -->
  <path d="M 750 471 L 860 471 L 860 185" fill="none" stroke="#000000" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arrow4)" />
  <text x="870" y="330" font-size="8" font-weight="bold">Re-run Sandbox &amp; Re-evaluate</text>

  <!-- Final Validation & Clean-Code Integrity -->
  <line x1="500" y1="497" x2="500" y2="530" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow4)" />

  <rect x="180" y="530" width="640" height="70" fill="#ffffff" stroke="#000000" stroke-width="2" />
  <text x="500" y="550" text-anchor="middle" font-size="10" font-weight="bold">Final Validation &amp; Clean-Code Integrity Verification</text>
  <text x="500" y="566" text-anchor="middle" font-size="8">1. SHA-256 Target Integrity Guard: Verifies original source code file is untouched (0 mutation pollution)</text>
  <text x="500" y="579" text-anchor="middle" font-size="8">2. Suite Cryptographic Provenance: Candidate suite hash == Validated suite hash == Blackboard suite hash</text>
  <text x="500" y="592" text-anchor="middle" font-size="8">3. Export Hardened Suite: Generates test_hardened.py with 100% callable coverage &amp; verified mutation score</text>

  <!-- Bottom Explanatory Notes -->
  <rect x="30" y="620" width="940" height="55" fill="#ffffff" stroke="#000000" stroke-width="1" />
  <text x="40" y="638" font-size="9" font-weight="bold">MUTATION SCORE MATHEMATICAL DEFINITIONS:</text>
  <text x="40" y="652" font-size="8">• Raw Mutation Score = (Killed Mutants / Total Mutants) × 100   [Discount: 17/19 = 89.47% | Logistics: 176/258 = 68.22%]</text>
  <text x="40" y="666" font-size="8">• Adjusted Mutation Score = (Killed Mutants / (Total Mutants - Equivalent Mutants)) × 100   [Discount: 17/18 = 94.44% | Logistics: 176/234 = 75.21%]</text>
</svg>
"""
    svg_path = os.path.join(ASSETS_DIR, "figure4_mutation_refinement.svg")
    png_path = os.path.join(ASSETS_DIR, "figure4_mutation_refinement.png")
    with open(svg_path, "w") as f:
        f.write(svg)
    svg_to_png(svg, png_path, dpi=300)

# ==============================================================================
# FIGURE 7: BENCHMARK GRAPH (Initial Baseline vs Hardened Raw vs Hardened Adjusted)
# ==============================================================================
def generate_figure7():
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    benchmarks = ["Discount Benchmark\n(discount.py, 19 mutants)", "Logistics Engine\n(uploaded_logistics_engine.py, 258 mutants)"]
    
    # Data
    baseline = [5.26, 3.10]
    hardened_raw = [89.47, 68.22]
    hardened_adj = [94.44, 75.21]
    
    x = np.arange(len(benchmarks))
    width = 0.24

    # High contrast monochrome/grayscale bars
    rects1 = ax.bar(x - width, baseline, width, label="Initial Mutation Baseline", color="#E0E0E0", edgecolor="#000000", linewidth=1.2)
    rects2 = ax.bar(x, hardened_raw, width, label="Hardened Raw Mutation Score", color="#777777", edgecolor="#000000", linewidth=1.2)
    rects3 = ax.bar(x + width, hardened_adj, width, label="Hardened Adjusted Mutation Score", color="#111111", edgecolor="#000000", linewidth=1.2)

    ax.set_ylabel("Mutation Score (%)", fontsize=11, fontweight="bold", color="#000000")
    ax.set_title("Figure 7: Mutation Score Progression — Baseline vs. Hardened Suites", fontsize=12, fontweight="bold", pad=16, color="#000000")
    ax.set_xticks(x)
    ax.set_xticklabels(benchmarks, fontsize=10, fontweight="bold", color="#000000")
    ax.set_ylim(0, 115)
    
    # Grid lines - light horizontal only
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#888888")
    ax.set_axisbelow(True)

    # Spines
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#000000")
        ax.spines[spine].set_linewidth(1.2)

    # Add labels on top of bars
    def autolabel(rects, is_dark=False):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"{height:.2f}%",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha="center", va="bottom",
                        fontsize=9, fontweight="bold", color="#000000")

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3, is_dark=True)

    # Legend
    ax.legend(loc="upper left", frameon=True, edgecolor="#000000", facecolor="#ffffff", fontsize=9)

    plt.tight_layout()
    graph_path = os.path.join(ASSETS_DIR, "figure7_benchmark_comparison.png")
    plt.savefig(graph_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Generated {graph_path}")

if __name__ == "__main__":
    generate_figure1()
    generate_figure2()
    generate_figure3()
    generate_figure4()
    generate_figure7()
    print("All assets generated successfully!")

