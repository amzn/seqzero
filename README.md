## SeqZero

This repo contains codes for the following paper: 

*Jingfeng Yang, Haoming Jiang, Qingyu Yin, Danqing Zhang, Bing Yin, Diyi Yang.* SEQZERO: Few-shot Compositional Semantic Parsing with Sequential Prompts and Zero-shot Models. (NAACL' 2022 Findings)

If you would like to refer to it, please cite the paper mentioned above. 


## Getting Started
These instructions will get you running the codes.

### Requirements
* Pytorch 
* fairseq

### Data Preperation
```
bash split_sql.sh 
```

### Run on GeoQuery

Run for SUBS data augmentation:
```
bash run_subs.sh 
```
Run BART or LSTM parser:
```
bash new_aug_query_gold_span_logic_bart_large.sh ||
bash new_aug_query_induce_logic_copy.sh
```
Refer to other bash files for other settings.

### Run on EcommerceQuery
Run for SUBS data augmentation:
```
python recomb_scan.py
```
Run parser:
```
bash scan_right_aug.sh
```
Refer to other bash files for other settings.

## Aknowledgement

Parsers are adapted from [fairseq](https://github.com/pytorch/fairseq).

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

