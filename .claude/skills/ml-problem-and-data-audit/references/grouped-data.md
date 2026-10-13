# Grouped data

Read this when one entity produces several rows: patients with many encounters, customers with many orders, devices, households, sites, stores, or authors.

## Find the unit of independence

List every column that identifies a repeating entity and count rows per entity. Rows from the same entity share information (its traits, measurement habits, and labels), so a random row split lets the model recognize entities instead of generalizing. Nested structures, such as patients within hospitals, need a decision about which level the model must generalize to.

## Choose the evaluation population

| Deployment scores | Evaluation |
|---|---|
| Only unseen entities | Group-disjoint split: no entity appears in more than one of train, validation, and test |
| Seen and unseen entities | Usually chronological: train on earlier rows, evaluate on later rows, and report seen and unseen entities as separate slices |
| Seen entities only | A chronological split within entities; a random row split still leaks later rows of the same entity |

Ask the owner when the deployment population is unclear; the answer changes every reported number.

## Checks

- For unseen-entity evaluation, use grouped splitters: group K-fold, stratified group K-fold for imbalanced targets, or group shuffle split for a single holdout.
- Compute entity-level aggregates and target encodings within training folds. An entity mean computed over all rows leaks evaluation labels.
- Check the group-size distribution: a few very large groups can dominate a fold.
- Count the group IDs shared by training and evaluation, and record the count in the split configuration. It must be zero when the evaluation represents unseen entities. In a chronological evaluation of known entities, shared IDs are expected; report seen and unseen entities as separate slices.

Source: [scikit-learn, Cross-validation iterators for grouped data](https://scikit-learn.org/stable/modules/cross_validation.html).
