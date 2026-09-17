# Security Log AI Agent

A privacy-focused AI system for analyzing and investigating large-scale server and security logs using efficient data processing, DuckDB, agent tools, LangGraph, and a local Large Language Model (LLM).

The project is designed for environments where log data may contain sensitive internal information and therefore should not be sent to external AI services.

---

## 1. Project Goal

The goal of this project is to build an AI-assisted security log investigation system capable of working with very large log datasets.

The system should eventually allow a user to ask questions such as:

```text
Investigate IP 34.83.25.237
```

or:

```text
Show me unusual authentication activity.
```

or:

```text
What important security events happened today?
```

The AI agent should determine which investigation tools are needed, retrieve only the relevant evidence from the logs, and use a **local LLM** to analyze and explain the results.

---

## 2. Important Design Principle

The LLM must **NOT** read the raw log files directly.

The real logs are extremely large, with a single day containing more than 20 million events and more than 10 GB of data.

Therefore, the architecture is designed as:

```text
Raw Security Logs
        ↓
Streaming / Parsing
        ↓
Normalization
        ↓
Parquet
        ↓
DuckDB
        ↓
Filtering / Aggregation
        ↓
Agent Tools
        ↓
LangGraph
        ↓
Local LLM
        ↓
Investigation Report
```

DuckDB and the query layer reduce millions of events into a small amount of relevant evidence before anything is passed to the LLM.

---

# 3. Dataset

The current data comes from OSSEC/Wazuh-style security and server logs.

The original logs are stored as **JSON Lines / NDJSON**.

Each line represents one independent JSON event:

```text
{event 1}
{event 2}
{event 3}
...
```

This is important because the files should be processed as streams instead of loading the entire JSON file into memory.

### Real Data Scale

One analyzed daily log contained:

```text
20,726,160 events
```

This corresponds to approximately:

```text
~240 events/second
```

The daily raw file is larger than 10 GB.

Because of this size, development is currently performed using a systematically distributed sample from the full day.

The current sample contains:

```text
100,126 events
```

and spans approximately the entire 24-hour period.

---

# 4. Current Architecture

The completed part of the system is:

```text
JSONL Logs
    ↓
Log Reader
    ↓
Normalizer
    ↓
Schema Profiler
    ↓
Parquet Ingestion
    ↓
DuckDB
    ↓
Query Layer
    ↓
Security Investigation Tools
```

The next development stage is:

```text
Security Investigation Tools
    ↓
LangChain Tools
    ↓
LangGraph Agent
    ↓
Local LLM
    ↓
Security Investigation Report
```

---

# 5. Project Structure

```text
Security-Log-AI-Agent/
│
├── Data_Cyper/
│   ├── sample_logs.json
│   ├── sample_100k.json
│   │
│   └── processed/
│       └── logs_100k.parquet
│
├── src/
│   ├── __init__.py
│   ├── log_reader.py
│   ├── log_normalizer.py
│   ├── log_statistics.py
│   ├── schema_profiler.py
│   ├── log_query.py
│   ├── log_ingestion.py
│   ├── duckdb_query.py
│   └── tools.py
│
├── tests/
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

Some data files may intentionally be absent from Git because security logs, generated Parquet datasets, and large/compressed files should not be committed to the repository.

---

# 6. Components

## `log_reader.py`

Streams JSONL logs one event at a time.

This avoids:

```python
json.load(huge_file)
```

which would be unsuitable for multi-GB log files.

Conceptually:

```text
10+ GB file
   ↓
event
   ↓
event
   ↓
event
   ↓
...
```

Memory usage therefore remains manageable.

---

## `log_normalizer.py`

Converts heterogeneous log events into a common schema.

Different decoders contain different fields, so this layer extracts common fields such as:

```text
timestamp
event_id

agent_id
agent_name
agent_ip

manager_name
decoder
location

rule_id
rule_level
rule_description

source_ip
source_port
destination_ip
destination_port

source_user
destination_user

http_method
http_status
http_host
http_uri
http_user_agent

message
```

IP addresses are validated using Python's `ipaddress` module to prevent invalid values from being treated as IP addresses.

---

## `schema_profiler.py`

Used to understand the real structure of the logs before designing the normalized schema.

The logs are heterogeneous.

Important decoders found in the sample include:

```text
npm_access_new
json
zeus
solaris_bsm
ossec
auditd
syscollector
systemd
kernel
docker
rootcheck
sshd
pam
```

For example, `npm_access_new` contains HTTP-related fields including:

```text
srcip
status
method
host
uri
length
sent_to
user_agent
referrer
upstream_status
```

While `sshd` contains fields such as:

```text
srcip
srcport
srcuser
```

Therefore, fields must not be assumed to exist for every decoder.

---

## `log_statistics.py`

Provides basic statistics over normalized log streams.

Examples include:

```text
Total events
First timestamp
Last timestamp
Events per second
Top agents
Top decoders
Rule-level distribution
Top source IPs
Top destination IPs
```

This component was particularly useful during initial data exploration and validation.

---

## `log_ingestion.py`

Converts normalized JSONL events into Parquet.

The ingestion process is:

```text
JSONL
  ↓
stream events
  ↓
normalize
  ↓
process in chunks
  ↓
PyArrow
  ↓
Parquet
```

A fixed PyArrow schema is used to avoid type inference problems between chunks.

Parquet uses compression and provides a much more efficient analytical representation of the logs.

---

# 7. Why Parquet?

Raw JSON is useful as the original source format but inefficient for repeatedly analyzing millions of events.

Parquet provides:

* Columnar storage
* Compression
* Efficient analytical queries
* Reduced disk usage
* Fast integration with DuckDB

The development sample containing approximately 100,000 events becomes only a few MB after conversion to Parquet.

---

# 8. Why DuckDB?

DuckDB is used as the analytical query engine.

Instead of repeatedly scanning and parsing the raw JSON logs in Python:

```text
Python
  ↓
Read JSON
  ↓
Parse
  ↓
Filter
```

the system can query Parquet directly:

```text
DuckDB
   ↓
Parquet
   ↓
Relevant rows only
```

This becomes especially important when moving from the development sample to millions of events.

---

# 9. `duckdb_query.py`

`DuckDBLogQuery` provides the main query abstraction over the Parquet logs.

Implemented capabilities include queries for:

```text
Total events
Top agents
Top decoders
Events by agent

HTTP method distribution
HTTP status distribution

High-severity security events
HTTP errors
Top HTTP source IPs

IP activity
IP summary
```

SQL should remain inside this layer rather than being placed inside the agent or `main.py`.

Conceptually:

```text
Agent
   ↓
Tool
   ↓
DuckDBLogQuery
   ↓
SQL
   ↓
Parquet
```

---

# 10. IP Investigation

One of the first investigation capabilities implemented is IP investigation.

## `ip_activity()`

Retrieves individual events associated with a source IP.

Example concept:

```text
34.83.25.237
      ↓
GET /gateway/.env
GET /server-info.php
```

The returned events include useful context such as:

```text
timestamp
agent
decoder
rule
source IP
HTTP method
HTTP status
host
URI
message
```

---

## `ip_summary()`

Instead of sending many raw events to the LLM, this function generates aggregated information about an IP.

It includes:

```text
Total events
First seen
Last seen
Number of agents
Number of hosts
Number of URIs
HTTP status distribution
Top hosts
Top URIs
```

This allows the future agent to inspect the summary first and request detailed events only when necessary.

---

# 11. Agent-Friendly Output

DuckDB normally returns results as tuples.

For example:

```python
(
    "34.83.25.237",
    "GET",
    "404"
)
```

The query layer now converts relevant results into dictionaries:

```python
{
    "source_ip": "34.83.25.237",
    "http_method": "GET",
    "http_status": "404"
}
```

This makes the results easier to serialize as JSON and easier for future agent tools and the LLM to understand.

---

# 12. `tools.py`

This is the boundary between the data/query system and the future AI agent.

The first investigation capability is:

```python
investigate_ip(ip)
```

It combines:

```text
ip_summary()
+
ip_activity()
```

Conceptually:

```text
investigate_ip()
       │
       ├── ip_summary()
       │
       └── ip_activity()
       │
       ▼
Structured Evidence
```

The function currently works independently of LangGraph.

This is intentional.

Each layer should be tested before adding the AI layer.

---

# 13. Current Handoff Point

Development has reached:

```text
Raw Logs                    ✅
Streaming                    ✅
Normalization                ✅
Schema Profiling             ✅
Statistics                   ✅
Parquet Ingestion            ✅
DuckDB                       ✅
Query Layer                  ✅
Security Queries             ✅
IP Investigation             ✅
Agent-friendly dictionaries  ✅
Basic Tool Layer             ✅

────────────────────────────────

LangChain Tool conversion     NEXT
LangGraph Agent               NEXT
Local LLM                     NEXT
Agent reasoning               NEXT
Investigation reports         NEXT
```

This is the recommended point to continue development.

---

# 14. Next Development Stage

The next developer should start from `src/tools.py`.

The recommended order is:

```text
1. Convert investigation functions into LangChain-compatible tools

2. Test each tool independently

3. Build the LangGraph workflow

4. Connect a local LLM

5. Allow the LLM to select appropriate tools

6. Return tool results to the model

7. Generate structured investigation reports

8. Add additional investigation tools when required
```

Do not begin by giving raw logs to the LLM.

---

# 15. Expected Agent Flow

Eventually, the interaction should look like:

```text
User
 │
 │ "Investigate IP 34.83.25.237"
 ▼
Local LLM
 │
 │ decides an IP investigation is required
 ▼
LangGraph
 │
 ▼
investigate_ip
 │
 ├── ip_summary
 │
 └── ip_activity
 │
 ▼
DuckDB
 │
 ▼
Parquet
 │
 ▼
Structured Evidence
 │
 ▼
Local LLM
 │
 ▼
Investigation Report
```

The LLM performs reasoning.

DuckDB performs data retrieval and aggregation.

These responsibilities should remain separated.

---

# 16. Security Interpretation

Do not automatically classify events as attacks based on a single field or HTTP status.

For example:

```text
404
401
403
500
502
```

do not individually prove malicious behavior.

An investigation should correlate multiple dimensions such as:

```text
Source IP
Time
Request frequency
Requested URI
Host
HTTP method
HTTP status
Agent/server
Security rules
Authentication activity
Historical behavior
```

For example, requests attempting to access paths such as:

```text
/.env
/server-info.php
/azure.json
```

may deserve investigation, but the presence of such a request alone should not be treated as proof of a successful attack.

The AI agent should explain evidence and uncertainty rather than blindly label events as malicious.

---

# 17. Privacy Requirement

This is an important requirement of the project.

The logs may contain sensitive organizational information, including:

```text
Internal IP addresses
Server names
Infrastructure information
URLs/endpoints
Authentication events
Security events
User information
```

Therefore:

**Do not upload real company logs to public repositories or external AI services.**

The intended final architecture uses a **local LLM**.

The local model should receive only the relevant evidence selected by the investigation/query layer.

---

# 18. Large Files and Git

Raw logs, generated datasets, compressed archives, environment files, and other sensitive/large files should be excluded through `.gitignore`.

Examples:

```gitignore
# Python
__pycache__/
*.py[cod]

# Virtual environments
.venv/
venv/
ai_env/

# IDE
.vscode/
.idea/

# Environment / secrets
.env

# Logs
*.log
*.jsonl

# Generated Parquet
Data_Cyper/processed/*.parquet

# Archives
*.zip
*.rar
*.7z
*.gz
*.tar
*.tar.gz
*.tgz
*.bz2
*.tar.bz2
*.xz
*.tar.xz

# OS files
.DS_Store
```

Before pushing, always verify:

```bash
git status
```

to ensure no sensitive dataset or log file is accidentally included.

---

# 19. Installation

Create and activate a Python virtual environment.

Then install the dependencies:

```bash
pip install -r requirements.txt
```

The completed data/query layer currently depends primarily on:

```text
duckdb
pyarrow
```

LangChain, LangGraph, and local-model integration dependencies should be added when implementing the next layer.

---

# 20. Running the Current System

The current `main.py` can be used as a simple smoke test.

Run:

```bash
python main.py
```

A simple investigation can call:

```python
investigate_ip(
    "34.83.25.237",
    activity_limit=10
)
```

The expected result is a structured dictionary containing:

```text
IP
Summary
Recent activity
```

If this works, the data, query, and initial tool layers are functioning correctly.

---

# 21. Development Rules

When extending the project, try to preserve these boundaries:

```text
log_reader.py
    → Reading

log_normalizer.py
    → Normalization

log_ingestion.py
    → Storage preparation

duckdb_query.py
    → SQL and data retrieval

tools.py
    → Agent capabilities

LangGraph
    → Workflow / orchestration

Local LLM
    → Reasoning and explanation
```

Avoid placing SQL directly inside the LLM/agent logic.

Avoid loading complete multi-GB files into memory.

Avoid sending raw logs directly to the LLM.

Avoid treating every unusual event as an attack.

Keep evidence retrieval deterministic and let the AI layer reason over the retrieved evidence.

---

# 22. Final Development Direction

The intended final system is:

```text
              Security Analyst
                     │
                     ▼
              Natural Language
                     │
                     ▼
               Local LLM
                     │
                     ▼
                 LangGraph
                     │
             ┌───────┴────────┐
             │                │
      Investigation Tool   Other Tools
             │                │
             └───────┬────────┘
                     ▼
              DuckDB Query Layer
                     │
                     ▼
                  Parquet
                     │
                     ▼
             Security Log Data
```

The project should evolve toward an **AI-assisted investigation system**, not simply an LLM chatbot connected to log files.

The data/query layer has been prepared specifically to make that possible.
