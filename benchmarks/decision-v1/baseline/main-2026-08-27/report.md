# Storyboard benchmark — main-2026-08-27

Suite: `decision-v1` · Storyboard Studio `0.2.0` · 20 raw runs

| Mode | Average | Content | Design | Coherence | Editability | Provenance | Privacy | Reproducibility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| local | 99.8/100 | 20.0/20 | 19.8/20 | 20.0/20 | 10.0/10 | 10.0/10 | 10.0/10 | 10.0/10 |
| optional-provider | 90.8/100 | 14.8/20 | 20.0/20 | 20.0/20 | 10.0/10 | 6.0/10 | 10.0/10 | 10.0/10 |

## Raw results

- `onboarding-pilot` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `onboarding-pilot` / `optional-provider`: **92.0/100** (provider used: `local`, network: `not-sent`)
- `analytics-vendor` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `analytics-vendor` / `optional-provider`: **88.0/100** (provider used: `local`, network: `not-sent`)
- `recovery-drill` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `recovery-drill` / `optional-provider`: **92.0/100** (provider used: `local`, network: `not-sent`)
- `support-routing` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `support-routing` / `optional-provider`: **92.0/100** (provider used: `local`, network: `not-sent`)
- `retention-policy` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `retention-policy` / `optional-provider`: **90.0/100** (provider used: `local`, network: `not-sent`)
- `office-lease` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `office-lease` / `optional-provider`: **92.0/100** (provider used: `local`, network: `not-sent`)
- `api-deprecation` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `api-deprecation` / `optional-provider`: **90.0/100** (provider used: `local`, network: `not-sent`)
- `nonprofit-crm` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `nonprofit-crm` / `optional-provider`: **92.0/100** (provider used: `local`, network: `not-sent`)
- `accessibility-remediation` / `local`: **100.0/100** (provider used: `local`, network: `offline`)
- `accessibility-remediation` / `optional-provider`: **90.0/100** (provider used: `local`, network: `not-sent`)
- `packaging-change` / `local`: **98.0/100** (provider used: `local`, network: `offline`)
- `packaging-change` / `optional-provider`: **90.0/100** (provider used: `local`, network: `not-sent`)

## Known limitations

- The deterministic rubric checks published structural signals; it is not a human or vision-language-model judgment of presentation quality.
- The baseline inspects PPTX structure but does not run PowerPoint, Keynote, or Google Slides; viewer compatibility remains a separate release gate.
- All briefs and evidence are synthetic fixtures, so this benchmark is not user research or proof of real-world usefulness.
- Unless provider network access is explicitly enabled, the optional-provider lane records a not-configured fallback and does not measure model quality.
- Reproducibility compares canonical story semantics; PPTX ZIP bytes may differ because package metadata and compression are not a semantic contract.

> Scores describe this fixture and rubric only. They do not establish factual truth, real-user value, or universal visual quality.
