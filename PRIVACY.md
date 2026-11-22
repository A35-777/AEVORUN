# Privacy Statement

AEVORUN is designed from the ground up with a **strict offline-first, zero-telemetry architecture**.

### 1. No Code Transmitted Off-Premises
When you run `aevorun analyze`, your source code is parsed in memory using Python's native `ast` library on your local CPU. Neither your source code, AST trees, nor file paths are transmitted across the network.

### 2. Zero Foundation Models / External Inference APIs
AEVORUN-T1 does not make calls to remote LLM endpoints (e.g. OpenAI, Anthropic, Google). All inference executes locally on your CPU using PyTorch weights (`model/checkpoint.pt`) stored on your machine.

### 3. No Tracking or Analytics
AEVORUN contains zero analytics, tracking scripts, crash report phone-homes, or telemetry beacons. No user behavior is collected.

### 4. Deterministic Local Execution
The model executes deterministically given identical code inputs, ensuring reproducible CI/CD pipeline runs without remote dependency risks.
