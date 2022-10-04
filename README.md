# SeqZero

This repo contains codes for the following paper: 

*Jingfeng Yang, Haoming Jiang, Qingyu Yin, Danqing Zhang, Bing Yin, Diyi Yang.* SEQZERO: Few-shot Compositional Semantic Parsing with Sequential Prompts and Zero-shot Models. (NAACL' 2022 Findings)

If you would like to refer to it, please cite the paper mentioned above. 


## Requirements
* Python >= 3.8
* Pytorch >= 11.1
* fairseq (our adapted version in `parser/fairseq`)

## Environment

```
conda create --name seqzero_env python=3.8
conda activate seqzero_env
```

If you are using A100, you probably need to change cuda version >= 11.0. Assume it is installed, then run:
```
export CUDA_HOME="/usr/local/cuda-11.1" 
export LD_LIBRARY_PATH="/usr/local/cuda-11.1/lib64:$LD_LIBRARY_PATH" 
export PATH="/usr/local/cuda-11.1/bin:$PATH"
```
where `/usr/local` is your cuda location, and 11.1 is your cuda version. 

Make sure that cudnn is also installed, see [instructions](https://docs.nvidia.com/deeplearning/cudnn/install-guide/index.html#installlinux-tar).

```
conda install pytorch torchvision torchaudio cudatoolkit=11.1 -c pytorch
```

```
cd parsers/fairseq 
pip install --editable ./ 
cd .. 
cd ..
```

Export python path:
```
export PYTHONPATH="${PYTHONPATH}:loc/seqzero/parser/fairseq"
```
where `loc` is your location of the repo.

## Data Preperation
```
cd preprocess 
bash split_sql.sh 
cd .. 
```

Download `encoder.json`, `vocab.bpe` to `parser/util_files/bart.large` by running:
```
cd parser/util_files/bart.large
wget -N 'https://dl.fbaipublicfiles.com/fairseq/gpt2_bpe/encoder.json' 
wget -N 'https://dl.fbaipublicfiles.com/fairseq/gpt2_bpe/vocab.bpe' 
cd .. 
cd ..
cd ..
```

Download `dict.txt`, `model.pt` from [bart.large.tar.gz](https://dl.fbaipublicfiles.com/fairseq/models/bart.large.tar.gz) to `parser/util_files/bart.large` according to [faiseq bart doc](https://github.com/facebookresearch/fairseq/blob/main/examples/bart/README.md). 

## Run on GeoQuery

First, run:
```
cd parser
```

### Prerequisites
Run:
```
mkdir data/geo_sql_query_from/bart-checkpoints-large 
mkdir data/geo_sql_query_select/bart-checkpoints-large 
mkdir data/geo_sql_query_where/bart-checkpoints-large 
mkdir data/geo_sql_query_group/bart-checkpoints-large 
mkdir data/geo_sql_query_order/bart-checkpoints-large 
```
For the purpose of ensemble, copy `util_files/bart.large/model.pt` to `data/geo_sql_query_from/bart-checkpoints-large`.

### Prerequisites of Direct Inference/Parsing w/o Training (Default)
Download [checkpoint38.pt](https://seqzero.s3.amazonaws.com/checkpoint38.pt) to `data/geo_sql_query_from/bart-checkpoints-large`

Download [checkpoint23.pt](https://seqzero.s3.amazonaws.com/checkpoint23.pt) to `data/geo_sql_query_select/bart-checkpoints-large`

Download [checkpoint99.pt](https://seqzero.s3.amazonaws.com/checkpoint99.pt) to `data/geo_sql_query_where/bart-checkpoints-large`

Download [checkpoint10.pt](https://seqzero.s3.amazonaws.com/checkpoint10.pt) to `data/geo_sql_query_group/bart-checkpoints-large`

Download [checkpoint37.pt](https://seqzero.s3.amazonaws.com/checkpoint37.pt) to `data/geo_sql_query_order/bart-checkpoints-large`

### Inference/Parsing 
To conduct zero-shot, few-shot model and emsemble model inference on `FROM` clause, run:
```
bash new_query_sql_bart_large_from_prediction_ensemble.sh 0
```
Note that `new_query_sql_bart_large_from.sh` is the implementation of weight ensemble, which does not perform as well as prediction emsemble after rescaling. The reason is stated in our paper.

Conduct inference on other clauses sequentially:
```
bash new_query_sql_bart_large_select.sh 0 
bash new_query_sql_bart_large_where.sh 0 
bash new_query_sql_bart_large_group.sh 0 
bash new_query_sql_bart_large_order.sh 0
```

### Training (Optional)
To train models, reuse commented training code in `new_query_sql_bart_large_from_prediction_ensemble.sh`, `new_query_sql_bart_large_select.sh`, `new_query_sql_bart_large_where.sh`, `new_query_sql_bart_large_group.sh`, `new_query_sql_bart_large_order.sh`.

## Run on EcommerceQuery

First, run:
```
cd parser
```

### Prerequisites
Run:
```
mkdir data/internal_sql_query_where_match/bart-checkpoints-large 
mkdir data/internal_sql_query_where_condition/bart-checkpoints-large 
```
For the purpose of ensemble, copy `util_files/bart.large/model.pt` to `data/internal_sql_query_where_condition/bart-checkpoints-large`.

### Prerequisites of Direct Inference/Parsing w/o Training (Default)
Download [checkpoint15.pt](https://seqzero.s3.amazonaws.com/checkpoint15.pt) to `data/internal_sql_query_where_match/bart-checkpoints-large`

Download [checkpoint21.pt](https://seqzero.s3.amazonaws.com/checkpoint21.pt) to `data/internal_sql_query_where_condition/bart-checkpoints-large`

### Inference/Parsing 
Conduct inference on `match` part of `WHERE` clause:
```
bash internal_query_sql_bart_large_where_match.sh 0
```

Conduct emsemble model inference on `condition` part of `WHERE` clause:
```
bash internal_query_sql_bart_large_where_condition_prediction_ensemble.sh 0
```

Conduct few-shot model inference on `condition` part of `WHERE` clause:
```
bash internal_query_sql_bart_large_where_condition.sh 0
```
### Training (Optional)
To train models, reuse commented training code in `internal_query_sql_bart_large_where_match.sh`, `internal_query_sql_bart_large_where_condition_prediction_ensemble.sh`, `internal_query_sql_bart_large_where_condition.sh`.

## Some Constrained Decoding and Ensemble Options of our Adpated Fairseq

Several arguments are available to run `python semantic_parsing.py`, which enables Constrained Decoding and Ensemble based on Fairseq.

`--model-file`: providing two models separated by `:` means ensemble of them.
`--prediction-weight`: ensemble weight of two models's prediction scores after constrained rescaling of the second model's probablitity.
`--weight-ensemble`: use weight ensemble instead of prediction score ensemble of two models.
`--use-prefix-constriant`: use prefix-constrained decoding to alow generating only specific tokens given prefix, see [details](https://arxiv.org/abs/2010.00904).
`--prefix-file`: the file containing allowed sequences to build trie for prefix-constrained decoding, not that this is a hard constraint, which means those sequences are the only allowed generated sequences.
`--partial-trie --no-hard-constraint`: use soft partial-prefix-constrained decoding, which means the prefix does not necessarily start at the beginning position. In this case, the rescaled prediction scores according to partial prefixed will be ensembled woth the first model.
`--weight-ensemble`: use weight ensemble instead of prediction score ensemble of two models.
`--prompt`: prompt for generation, which means generated first several tokens are constrained to be the provides prompt.
`--prompt-file`: the file containing prompts for generation, which means generated first several tokens are constrained to be the provides prompt. Different input could have different prompt provides. Thus, the number of lines in the propt file should be the same as the number of lines in the input file.

## Aknowledgement

Parsers are adapted from [fairseq](https://github.com/pytorch/fairseq).

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

