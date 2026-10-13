# Duplicates in images, video, and text

Read this when items can repeat in altered form: images of the same subject or lesion, frames from one video, crops and zoom levels, scans of one patient, documents from one thread or source, chunks of one document, templated messages, or datasets merged from overlapping sources.

## Split by the generating unit

Split by the unit that produced the items (patient, lesion, video, source document, thread, author), not by file. Frames of one video or chunks of one document on both sides of a split measure memorization rather than generalization.

## Find duplicates before splitting

| Kind | Methods |
|---|---|
| Exact | Hashes (sha256) of normalized file or text content |
| Near-duplicate images | Perceptual hashes, such as pHash or dHash, with a Hamming-distance threshold; embedding cosine similarity |
| Near-duplicate text | Hashes of normalized text; MinHash or shingling with a Jaccard threshold; embedding similarity |

Record the method, threshold, and counts in the data report, and review a sample of pairs near the threshold by eye. Merge duplicates into one group so that they land in the same split, or drop them, and record which. After splitting, check overlap between training and evaluation again.

## Merged and public sources

Overlapping public datasets often contain the same items under different IDs; check overlap between sources before combining them. When fine-tuning a pretrained model, a public test set may already be part of its pretraining data. Prefer evaluation data the pretrained model cannot have seen, or state the risk.

## Training path only

Augmentation, synthetic examples, and oversampling apply to training data only. Evaluation uses the original items.

## Slices

Report results by source, site, device, or capture conditions when these vary; an aggregate score can hide a failing source.

Source: [Google Machine Learning Crash Course, Dividing the original dataset](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets).
