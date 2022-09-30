## SeqZero

This repo contains codes for the following paper: 

*Jingfeng Yang, Haoming Jiang, Qingyu Yin, Danqing Zhang, Bing Yin, Diyi Yang.* SEQZERO: Few-shot Compositional Semantic Parsing with Sequential Prompts and Zero-shot Models. (NAACL' 2022 Findings)

If you would like to refer to it, please cite the paper mentioned above. 


## Getting Started
These instructions will get you running the codes.

### Requirements
* Pytorch 
* fairseq (our adapted version)

### Env

```
conda create --name seqzero_env python=3.8
coda activate seqzero_env
```

If you are using A100, you probably need to change cuda version >= 11.0. Assume it is installed, the run:
```
export CUDA_HOME="/usr/local/cuda-11.1" &&
export LD_LIBRARY_PATH="/usr/local/cuda-11.1/lib64:$LD_LIBRARY_PATH" &&
export PATH="/usr/local/cuda-11.1/bin:$PATH"
```
where /usr/local is your cuda location, 11.1 is your cuda version. 

Make sure that cudnn is also installed. [Instructions](https://docs.nvidia.com/deeplearning/cudnn/install-guide/index.html#installlinux-tar)

```
conda install pytorch torchvision torchaudio cudatoolkit=11.1 -c pytorch
```

```
cd parsers/fairseq &&
pip install --editable ./ &&
cd .. &&
cd ..
```

Export python path:
```
export PYTHONPATH="${PYTHONPATH}:loc/seqzero/parser/fairseq"
```
where loc is your location of the repo.

### Data Preperation
```
cd preprocess &&
bash split_sql.sh &&
cd .. 
```

### Run on GeoQuery

First, run:
```
cd parser
```

If directly running inference/parsing w/o training, run:
```
mkdir data/geo_sql_query_from/bart-checkpoints-large &&
mkdir data/geo_sql_query_select/bart-checkpoints-large &&
mkdir data/geo_sql_query_where/bart-checkpoints-large &&
mkdir data/geo_sql_query_group/bart-checkpoints-large &&
mkdir data/geo_sql_query_order/bart-checkpoints-large 
```
download checkpoint38.pt to data/geo_sql_query_from/bart-checkpoints-large
download checkpoint23.pt to data/geo_sql_query_select/bart-checkpoints-large
download checkpoint99.pt to data/geo_sql_query_where/bart-checkpoints-large
download checkpoint10.pt to data/geo_sql_query_group/bart-checkpoints-large
download checkpoint37.pt to data/geo_sql_query_order/bart-checkpoints-large 


Download encoder.json, vocab.bpe to parser/util_files/bart.large by running:
```
cd util_files/bart.large &
wget -N 'https://dl.fbaipublicfiles.com/fairseq/gpt2_bpe/encoder.json' &
wget -N 'https://dl.fbaipublicfiles.com/fairseq/gpt2_bpe/vocab.bpe' &
cd .. &
cd ..
```

Download dict.txt, model.pt from [bart.large.tar.gz](https://dl.fbaipublicfiles.com/fairseq/models/bart.large.tar.gz) to parser/util_files/bart.large according to [faiseq bart doc](https://github.com/facebookresearch/fairseq/blob/main/examples/bart/README.md). For the purpose of ensemble, copy model.pt to data/geo_sql_query_from/bart-checkpoints-large.

To conduct zero-shot, few-shot model and emsemble model inference on from clause, run:
```
cd parser &&
bash new_query_sql_bart_large_from_prediction_ensemble.sh 0
```
Note that new_query_sql_bart_large_from.sh is the implementation of weight ensemble, which does not perform as well as prediction emsemble after rescaling. The reason is stated in our paper.

Run on other clauses sequentially:

```
bash new_query_sql_bart_large_select.sh 0 &
bash new_query_sql_bart_large_where.sh 0 &
bash new_query_sql_bart_large_group.sh 0 &
bash new_query_sql_bart_large_order.sh 0
```

To train models, reuse commented code in new_query_sql_bart_large_from_prediction_ensemble.sh, new_query_sql_bart_large_select.sh,new_query_sql_bart_large_where.sh, new_query_sql_bart_large_group.sh,
bash new_query_sql_bart_large_order.sh

## Aknowledgement

Parsers are adapted from [fairseq](https://github.com/pytorch/fairseq).

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

