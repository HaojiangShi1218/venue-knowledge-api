# Manual Query Pack — Baseline Validation

## Purpose

This manual query pack is intended to validate the baseline lexical/rule-based functionality of the Venue Knowledge Assistant API.

It covers:

- direct policy lookup
- feature lookup
- numeric/capacity constraints
- multi-constraint ranking
- partial-match caution behavior
- policy detail extraction
- insufficient-evidence fallback

These queries are not meant to exhaustively test every possible scenario. They are meant to verify that the baseline behaves reasonably before submission packaging or future semantic enhancements.

---

## Recommended setup before running

1. Start from a clean database state if possible.
2. Seed only the intended sample data from `sample_data/`.
3. Run indexing so document chunks are available.
4. Use Swagger UI or `curl` to execute the queries below.

---

## Expected baseline behaviors

Across the query pack, the system should generally demonstrate:

- direct factual/policy queries return relevant excerpts
- topic-aligned chunks are surfaced as sources
- numeric constraints materially affect ranking/confidence
- strong-fit queries rank better candidates first
- weak-fit queries return cautious answers
- low-evidence queries do not bluff or overclaim

---

## Query 1 — Direct policy lookup

### Query
`Which venues allow outside catering?`

### What this checks
- policy keyword matching
- direct policy chunk retrieval
- source excerpt relevance
- reasonably high confidence for a clear direct match

### Expected behavior
- Harbor Loft should be the strongest result
- source excerpt should be directly about outside catering
- answer should be direct and grounded

---

## Query 2 — Feature lookup

### Query
`Which venues have built-in AV?`

### What this checks
- feature extraction and matching
- AV normalization
- whether AV-related chunks are surfaced instead of unrelated policy chunks

### Expected behavior
- Skyline Foundry should be highly relevant
- source excerpt should mention built-in AV support or equivalent AV features
- answer should stay grounded in the retrieved text

---

## Query 3 — Capacity-constrained query (moderate threshold)

### Query
`Which venues can host 100 people?`

### What this checks
- structured capacity matching
- venue ranking under numeric constraints
- whether venues below the threshold are penalized

### Expected behavior
- Skyline Foundry should be relevant because capacity is 120
- Harbor Loft may be less suitable because capacity is 80
- Cambridge Private Table should be less suitable because capacity is 40

---

## Query 4 — Capacity-constrained query (higher threshold)

### Query
`Which venues can host 130 people?`

### What this checks
- stronger numeric filtering/penalty behavior
- partial/no-match handling when no venue clearly satisfies the requirement

### Expected behavior
- no venue should look like a strong clear match based on the sample data
- answer should be cautious
- confidence should not be high

---

## Query 5 — Multi-constraint weak-fit query

### Query
`Which venues are best for a 150-person launch event with built-in AV?`

### What this checks
- multi-constraint parsing
- capacity mismatch penalties
- event-type + feature matching
- partial-match answer behavior
- topic-aligned source selection

### Expected behavior
- no venue should be presented as a clear full match
- answer should be cautious
- sources should be about launch/event fit and AV support, not unrelated policy text
- confidence should be materially lower than a direct policy query

---

## Query 6 — Multi-constraint better-fit query

### Query
`Which venues are best for a 110-person launch event with built-in AV?`

### What this checks
- whether ranking improves when capacity becomes satisfiable
- whether the system can identify the strongest available candidate
- whether source ordering remains topic-aligned

### Expected behavior
- Skyline Foundry should become a stronger candidate
- Harbor Loft may remain partially relevant
- answer may still be cautious, but ranking should be more sensible than the 150-person case

---

## Query 7 — Specific cancellation detail query

### Query
`What are the cancellation rules for Harbor Loft?`

### What this checks
- specific policy detail extraction
- exact phrase/value retrieval
- whether the answer comes from relevant cancellation text

### Expected behavior
- source excerpt should mention the refund/cancellation condition
- answer should be direct and grounded
- unrelated feature or catering excerpts should not be prioritized

---

## Query 8 — Policy search by condition

### Query
`Which venues offer a full refund if cancelled 14 days in advance?`

### What this checks
- phrase matching on specific policy language
- structured or document-level retrieval of precise conditions
- whether the system can answer with a specific venue rather than broad partial matches

### Expected behavior
- Harbor Loft should be the strongest result
- excerpt should mention the 14-day full refund rule

---

## Query 9 — Low-evidence negative query

### Query
`Which venues have valet parking?`

### What this checks
- insufficient-evidence fallback
- whether the system avoids bluffing when the sample data does not clearly support the request

### Expected behavior
- answer should be cautious
- confidence should be low
- system should not invent valet parking support

---

## Query 10 — Broader no-match query

### Query
`Which venues are best for a wedding reception with outdoor garden seating?`

### What this checks
- low-evidence/no-match behavior for broader concepts not supported by the sample data
- whether the system avoids overfitting weak lexical overlap

### Expected behavior
- answer should indicate insufficient evidence or only weak partial relevance
- confidence should be low
- sources, if returned, should not be presented as strong support for garden/wedding requirements

---

## Suggested validation notes template

For each query, record:

- **Query**
- **Answer quality**: correct / partially correct / incorrect
- **Confidence appropriateness**: low / medium / high / too high / too low
- **Source relevance**: relevant / partially relevant / off-topic
- **Comments**

Example:

```md
### Query
Which venues allow outside catering?

- Answer quality: correct
- Confidence appropriateness: reasonable
- Source relevance: relevant
- Comments: Harbor Loft returned with direct policy excerpt
```

---

## Submission-readiness guideline

The baseline can be considered submission-ready when this manual query pack shows:

- direct policy/feature queries behave correctly
- multi-constraint queries behave cautiously when needed
- stronger candidates rank above weaker ones under numeric constraints
- low-evidence queries do not bluff
- source excerpts stay aligned with the actual question topic

At that point, remaining improvements should be documented as future semantic/hybrid retrieval enhancements rather than baseline blockers.
