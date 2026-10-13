# Performance workflow

Optimization starts from evidence about the target engine and its workload. Without that evidence, give hypotheses and a measurement plan, not conclusions.

## Evidence first

1. **Baseline.** Record the exact statement, its parameter values, the runtime or bytes or credits it uses, how often it runs, and the environment where it was measured.
2. **Plan.** Get the estimated plan from a non-executing command. Get an actual plan only when authorized, following [safety-and-execution.md](safety-and-execution.md).
3. **Data facts.** Collect row counts, predicate selectivity, statistics freshness, data distribution and skew, and the existing indexes, partitioning, or clustering.
4. **Hypothesis.** Name the plan step or resource that dominates and why.
5. **Change.** Make one change at a time, and show that it returns the same result as before.
6. **Re-measure.** Compare under the same conditions: the same parameters, data volume, and cache state.

When the user cannot provide evidence, list what to collect and the commands that collect it without executing the statement.

## Reading plans

Estimated plans come from statistics; actual plans report what happened in one run. A large gap between estimated and actual row counts usually points to stale statistics, correlated predicates, or parameter-dependent plans, and is often the real problem.

No plan operator is good or bad by itself. A full or sequential scan can be the best plan for a small table or when most rows qualify, and an index scan that reads many scattered rows can be slower.

Plan cost numbers are internal units of one engine and one plan. Do not read them as time and do not compare them across engines.

A plan compiled for one parameter value can be poor for another. Check the overlay for how the engine reuses plans for parameterized statements.

## Claims

Do not promise a speedup figure. When the user asks for a target such as "80% faster", explain which measurements would show whether a change reaches it and offer candidate changes ranked by evidence, with no predicted percentage.

An index is not "required" without the plan, the selectivity of the predicates it serves, and the write workload. Every index costs write time, storage, and maintenance, and building one can lock the table or take long; the overlay describes online options.

A rewrite counts as an optimization only when it returns the same result for all inputs. Check it against the rewrites listed in [universal-correctness.md](universal-correctness.md#result-grain-and-joins).

## Engine families

Transactional row stores (PostgreSQL, MySQL, MariaDB, SQL Server, Oracle, and usually SQLite): the main levers are selective access paths and indexes, join order and algorithms, statistics, lock contention and transaction length, write amplification from indexes, and application patterns such as one query per row.

Analytical engines (BigQuery, Snowflake, DuckDB): the main levers are data read (bytes or partitions scanned), column pruning, partition and cluster pruning, data layout, compute size, result caching, and memory spills. Index checklists from transactional engines do not transfer. BigQuery analytical tables and standard Snowflake tables do not offer ordinary B-tree indexes for scan tuning; Snowflake hybrid tables and DuckDB have different index capabilities. Check the target overlay and table kind.

SQLite and DuckDB run inside the application process, so the host's memory, disk, and concurrency model limit them.

## Recommendation format

For each recommendation, give:

1. the evidence that motivates it;
2. the hypothesis it tests;
3. the change;
4. why the result stays the same;
5. the expected direction of the effect, without a figure;
6. how to measure it;
7. its costs and risks.
