# Multi-State License Compliance Graph & Renewal Engine — Architecture

## The problem, in one sentence
A money-services company operating in 12 states must hold the right license in
each state, satisfy each state's ongoing requirements, and renew each one on
that state's own cadence — and the source of truth is a pile of PDFs and, in
some states, literally a fax number.

## Why this is a graph, not a spreadsheet
The obligations are *relational*. A state offers license types. A license type
imposes requirements. A requirement renews on a cadence and sometimes *depends
on* another requirement (you can't file the annual report until the surety bond
is on file). An entity *holds* licenses and *operates in* states. The question
"what does Acme Payments owe by March?" is a graph traversal: start at the
entity, walk to its states, walk to the license types it holds there, walk to
the requirements those impose, compute each due date. A flat table forces you to
denormalize all of that and recompute it by hand every time a rule changes.

## The node types (vertices)
- `state`        — a U.S. jurisdiction (CA, TX, NY, ...)
- `license_type` — e.g. "Money Transmitter License", "Consumer Lender License"
- `requirement`  — a concrete obligation: annual report, surety bond, exam, fee
- `entity`       — a company we track compliance for

## The edge types (directed, typed)
- `offers`        state        -> license_type   (this state has this license)
- `requires`      license_type -> requirement    (holding it imposes this)
- `renews_every`  requirement  -> requirement     (self-cadence, months on the edge)
- `depends_on`    requirement  -> requirement     (must file B before A)
- `holds`         entity       -> license_type    (in a given state)
- `operates_in`   entity       -> state

## Storage decision
We model this in **plain Postgres** with an adjacency-list edge table, NOT
Neo4j. A dedicated graph DB buys you nothing at this scale and adds an operational
dependency; adjacency lists in Postgres traverse fine with recursive CTEs and
keep the whole system runnable with one container. The graph *model* is what
matters — the store is an implementation detail.

## The pipeline, end to end
1. Extract requirements + deadlines from regulator docs with an LLM  (Step 3)
2. Load them as nodes + typed edges into the graph                    (Step 4)
3. Traverse entity -> states -> licenses -> requirements              (Step 5)
4. Compute due dates from cadences; classify upcoming/due/lapsed       (Step 6)
5. An AI agent drafts the filing checklist, grounded in the graph      (Step 7)
6. Ground every agent claim in a real node; refuse ungrounded ones     (Step 8)
7. Serve it over an API with an append-only audit trail                (Step 9)
