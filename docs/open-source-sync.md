# Daily open-source sync

The owner can enable daily maintenance with `"open_source_sync": {"enabled": true}` in the local project settings. Keep a dedicated checkout and work on `sync/YYYY-MM-DD`.

1. Compare local workflow improvements with the public version. Choose changes that work for another project; keep identities, accounts, private conversations and deployment settings local. Normally observe a new change for a day; an explicitly requested batch follows the owner’s chosen scope.
2. Port each improvement using the public project’s names and existing structure. Give each behavior change a focused test. Use one reviewable commit per improvement and the owner’s configured noreply author.
3. Run the repository’s normal checks and scan the complete source manifest for private content. Keep public artwork and version choices with the owner.
4. Write `attachments/open-source-sync/YYYY-MM-DD.md`. Its first line is `Review: pending Claude`, `Review: returned: reason`, `Review: approved`, or `Review: none needed`. Include an improvement/source/public-location/commit/result table, omitted items with reasons, branch, diff summary, validation and privacy-scan result.
5. The lead reviews the batch and records the decision. Returned work goes to GPT. After 22:00 the flow check reports a missing daily record. Repository publication uses the owner’s existing authorization; preparation alone grants a review-ready branch.

Use [the review template](../templates/open-source-review.md).
