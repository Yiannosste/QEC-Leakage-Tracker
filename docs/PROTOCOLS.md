# Protocols and verdicts

I wrote and froze each protocol in `protocols/` before reading the test data it applies to, with two exceptions that the amendment log records: amendments 2 and 3 of the first pre-registration were written after some G1 results had been seen (facts.md F2, F7). The freeze times in the table come from the timestamps of the project's own file store, not from the git history of this repository, which starts with the public release. For the next study each protocol should be pushed or tagged before it is run.
"Verdict" is what the pre-set rule returned. Numbers are from facts.md. Anything exploratory or post hoc is
labelled as such in the result reports and never counts towards a verdict.

| file | what it fixes | frozen | verdict |
|---|---|---|---|
| `c3_preregistration.md` | first simulation study, grid G1: d ∈ {3,5,7} × p_L × τ, old HMM tracker, soft-weight rule, controls A/B/A4 | before any production grid ran | positive in simulation (F2): the HMM recovers f = 0.37 to 0.75 of the oracle gain depending on d; soft weights beat hard flags; delayed flags never hurt |
| `c3_preregistration_amendment1.md` and `amendment_log.md` | adds the learned CNN tracker, the 4-state HMM, the rule p_e ← p_e ⊕ c·π, lags {0, 2}; the log dates every amendment and states its effect | before grids G1 to G4 | CNN lag 2 recovers f = 0.60 to 0.90 (F2); amendment 3 (Pauli on return uniform over X/Y/Z) is declared in the log |
| `pilots_preregistration.md` | nine small pilots with fixed success criteria and the verdict words SIGNAL / NO SIGNAL / INCONCLUSIVE | before any pilot | the per-pilot verdicts are not in facts.md; see `docs/working_notes/c3_paper_readiness_report.md` |
| `adaptive_protocol.md` | causal adaptive-weight matching on Willow syndromes (weights for shot k from shots 1 to k−1 only) | before any held-out shot was decoded adaptively | never executed (F7); no result claimed |
| `ibm_protocol.md` | syndrome-only per-detector hidden-state tracker on the ibm_berlin memory runs; tuning on patch q36 only, test on q85 | 21 Oct 2026, before any tracker-based decoding | killed (F4): X against A 84 805 / 85 268 (p = 0.26) on 10 held-out runs; X loses to the static control A4, 49 389 / 53 169 |
| `detect2_protocol.md` (v2 plus Amendment 1) | the new tracker ALL and its ablations on a 6-cell simulation grid; endpoints P1 (detection) and P2 (decoding); development on one seed only | 25 Oct 2026, before any test-seed shot was simulated | P1 and P2 met (F3): AP 0.877 / 0.818 / 0.880 / 0.826 against CNN 0.752 / 0.647 / 0.763 / 0.683; pooled McNemar ALL against CNN 2 840 / 2 551 (p = 8.7e-5). My prediction had been a tie with the CNN |
| `ibm_stab_protocol.md` | tracker ALL, frozen in detect2 and unchanged, on 17 unseen ibm_berlin stability runs; primary endpoint PR1; controls A4, P, X_old; calibration shots never decoded | 25 Oct 2026, before any logical outcome was read; I gave P(met) about 0.25 | PR1 met (F5): X against A 11 374 / 8 502 (p = 1.7e-92); X against A4 10 389 / 8 859; placebo worse than A, 3 346 / 4 959; −20 % failures at T = 100 |
| `v3_dev_protocol.md` (v3) | a guarded tracker v3 (R: readout explaining away; G2: per-run switch-off test), developed on synthetic data only, with the selection rule and the confirmation rule fixed first | 25 Oct 2026, before any v3 result | the selection rule picked R + G2 on seed 7000; the confirmation on seed 8000 failed rule 1 (F6): reset leak-free d = 3 memory 88 / 121, p = 0.027. By that rule v3 was not run on ibm_miami |

Reports without a protocol of their own (observations and scope checks, no decoder was tuned; for the Google 2023 and Willow analyses the tracker settings and the soft-weight rule were those fixed in `c3_preregistration.md`, but the analyses themselves had no separate frozen protocol):
`results/real_data_report.md` (Google 2023 null), `results/willow_scope_report.md` (Willow scope null, predicted
before decoding), `results/miami_precheck.md` (label-free checks of ibm_miami, no logical outcome read),
`docs/working_notes/data_assessment.md`, `docs/working_notes/platform_survey.md`, `docs/working_notes/prior_art_c3.md`, `docs/working_notes/referee_report.md`
and `docs/working_notes/response_to_referee.md`.

Note on wording: the files in `protocols/` are kept exactly as frozen, including their original typography (en dashes in ranges). I did not edit them after the fact.
