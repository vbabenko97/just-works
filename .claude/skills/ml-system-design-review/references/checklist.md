> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim.

# ML Design Doc Review Checklist — 14 Groups

Group names are verbatim from the source checklist; template section names are verbatim from the source template. They intentionally differ — use this mapping table to locate what each group evaluates.

| Checklist group | Template section(s) evaluated |
|---|---|
| Problem Definition | I. Problem Definition |
| Metrics and Losses | II. Metrics and Losses |
| Data Considerations | III. Dataset |
| Validation Schemas | IV. Validation Schema |
| Baseline Solutions | V. Baseline Solution |
| Error Analysis | VI. Error Analysis |
| Training Pipeline | VII. Training Pipeline |
| Feature Engineering | VIII. Features |
| System Architecture | XII. Serving and Inference + X. Integration (cross-cutting) |
| Integration | X. Integration |
| Documentation | the doc itself: organization, diagrams, glossary, version history |
| Evaluation Strategy | IX. Measuring and Reporting |
| Implementation Plan | cross-cutting: timeline and resources anywhere in the doc; blocker-level gap if absent in a production doc |
| Maintenance and Operations | XI. Monitoring |

## 1. Problem Definition

- Clear problem statement with measurable objectives
- Scope, constraints, and stakeholders identified
- Business justification and cost of the status quo
- Existing solutions analyzed; risks assessed; success criteria defined

## 2. Metrics and Losses

- Business metrics and model metrics defined
- Loss function justified and linked to business goals
- Trade-offs named; measurement framework in place

## 3. Data Considerations

- Sources identified; quality and freshness assessed
- Labeling process planned with QA and cost
- ETL pipeline designed; data quality checks defined
- Privacy/security measures; versioning; storage requirements; metadata usage

## 4. Validation Schemas

- Requirements defined; schema designed
- Data leakage prevented; temporal aspects handled
- Cross-validation strategy set; update frequency planned

## 5. Baseline Solutions

- Constant baseline defined with a measured floor
- Model and feature baselines selected; comparison methodology planned
- Minimum acceptable performance stated; improvement metrics defined

## 6. Error Analysis

- Learning-curve and residual analysis planned
- Edge cases identified; failure modes monitored
- Error tracking designed; improvement process defined

## 7. Training Pipeline

- Architecture designed; tools selected
- Preprocessing planned; experiment tracking and model versioning set up
- Resources allocated; process documented; monitoring configured

## 8. Feature Engineering

- Selection criteria defined; initial features listed
- Feature tests and monitoring planned
- Dependencies documented; computational constraints considered; update plan exists

## 9. System Architecture

- Infrastructure requirements and scalability considered
- Latency defined; security measures specified
- Integration points and deployment strategy documented

## 10. Integration

- API interfaces designed; SLAs defined
- Release cycle and fallback strategies planned
- Operational procedures, monitoring/alerts, incident response, deployment docs in place

## 11. Documentation

- Clear organization and technical detail
- Diagrams present and labeled; references included
- Terminology glossary; version history; maintenance and update guidelines

## 12. Evaluation Strategy

- Success metrics defined; A/B testing methodology specified
- Performance benchmarks set; monitoring approach and alert thresholds defined

## 13. Implementation Plan

- Realistic timeline; resources specified
- Dependencies identified; risks assessed with mitigations

## 14. Maintenance and Operations

- Monitoring configured; update procedures defined
- Backup strategies; incident response planned
- Data drift planning; resource scaling strategy
