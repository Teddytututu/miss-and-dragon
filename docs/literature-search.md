# Find papers through citation links

Start with 5–12 close seeds: direct predecessors, theoretical sources and known competitors. Have the lead review them. Broad surveys and highly cited background papers often create more noise than useful neighbours.

1. Follow both directions: references for sources and citations for later work. `python scripts/citation_chain.py seeds.txt output --hop2 2` deduplicates paper IDs and records how many seeds link to each candidate; connected neighbours can seed a second citation hop. Each seed-file line contains an arXiv ID and an optional comment after `#`.
2. Fill coverage gaps using the owner’s existing library access to Scopus or Web of Science, lawful open-access pages and publisher links. Record actual query and access outcomes separately. Account access follows existing authorization.
3. Add searches using mechanism synonyms from the project, rather than relying on the project’s own terminology. Merge results into the same candidate table.
4. Read each abstract and give it a grade and reason: A, direct comparison; B, useful method, measurement, theory, data or baseline; C, context; D, unrelated. Read the first page or introduction when the abstract is missing.
5. Read A papers in full. Record what was measured, how it differs from the project and whether to cite, compare or revise a claim.
6. Test coverage using known required answers supplied by the lead. Expand again from new A papers. The lead samples discarded candidates and checks close comparisons against the original paper.

Present the novelty conclusion first, then the closest-work table, a map of useful directions and the full graded candidate CSV. Keep access logs and reading-status evidence in a companion record.

For daily discovery use a fresh dated output directory: `python scripts/citation_chain.py seeds.txt output/YYYY-MM-DD --since YYYY-MM-DD --exclude seen.csv`. Daily mode follows citations only, filters dates and skips paper IDs already recorded in the `paperId` column. Date-free records stay outside this date filter. Read and grade new candidates before choosing a short useful digest; record sent paper IDs. Cached responses resume interrupted runs; a fresh dated directory refreshes discovery. Respect provider rate limits and retry later when necessary.
