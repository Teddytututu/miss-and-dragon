# Offline report format

## 1. Delivery
Compose with report_kit.py, run check_report.py, address errors and assess warnings, then submit the page to its reviewer.

## 2. Page order
Start with a complete conclusion as the title. Answer the research question and show the main comparison. Each section has a bold claim, a short explanation, a figure and an exact-value table. End with the next question and experiment. Put detailed methods in a disclosure.

## 3. Sentences
Use concrete subjects, actions, sample counts and evaluation methods. Explain a new term when it first appears.

## 4. Figures
Use bars for method comparisons, diverging for paired wins and losses, lines for changes over steps or budget, photo for observed images, table for exact values and terms for definitions. Assign each method a consistent color. Include the baseline and computation costs.

## 5. Fictional example
Replace “Method comparison” with “Method A answers more questions under the same budget.” For a teaching example: Method A answers 23 of 40 fictional questions, Method B answers 18, and each uses 50 computations. The example is synthetic; project reports use their own observations.

## 6. Decisions
Send the evidence, two interpretations and a recommendation to the research lead. Continue authorized independent work while that decision is pending.

## 7. Reader content and logs
Keep the question, findings, comparisons and implications in the report. Store operational checks, filenames and provenance in a separate record. Regenerate the complete report when findings change.

## 8. Components
See example_build.py for Colors, page, section, figure, bars, diverging, lines, table, terms, next_steps, photo, raw and write. Supply an accessible description for every figure.

## 9. User-facing documentation
1. Begin with what you want to do and the result you receive; place technical details in links or disclosures and assistant commands in the corresponding contract.
2. Keep the user prompt to one sentence and a link; put detailed instructions at that destination.
3. Use you, Claude and GPT consistently; retain Owner, Lead and Executor as code identifiers.
4. Use plain titles and concrete descriptions of actions and results.
5. List the actual items and explain unfamiliar terms.
6. Check feature claims against implementation and distinguish working behavior from proposals.
7. Preserve the user's writing and submit editorial suggestions for their decision.
8. Use consistent identity colors, one instance of each label and a varied hierarchy of cards. Generate both languages together and add missing glyphs to a licensed font subset.
9. Open GitHub links and verify them; use complete raw URLs for source images and working relative links for page navigation.
10. Preview both languages at desktop and mobile widths; run the project's line-ending, regression and privacy checks before review.
