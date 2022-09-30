TASK=data/geo_sql_query_from
PARAM='-large'

inprompt="the answer can be looked up from "
outprompt="the sentence talks about "

python change_prompt.py -in_file $TASK/tgt.train -out_file $TASK/tgt_prompt.train -in_prompt "$inprompt" -out_prompt "$outprompt"
python change_prompt.py -in_file $TASK/tgt.dev -out_file $TASK/tgt_prompt.dev -in_prompt "$inprompt" -out_prompt "$outprompt"
python change_prompt.py -in_file $TASK/tgt.test -out_file $TASK/tgt_prompt.test -in_prompt "$inprompt" -out_prompt "$outprompt"
python change_prompt.py -in_file prefixes.txt -out_file prompt_prefixes.txt -in_prompt "$inprompt" -out_prompt "$outprompt"

for SPLIT in train dev test
do
  for LANG in src tgt_prompt
  do
    python -m examples.roberta.multiprocessing_bpe_encoder \
    --encoder-json util_files/bart.large/encoder.json \
    --vocab-bpe util_files/bart.large/vocab.bpe \
    --inputs "$TASK/$LANG.$SPLIT" \
    --outputs "$TASK/$SPLIT.bpe.$LANG" \
    --workers 60;
  done
done

fairseq-preprocess \
  --source-lang "src" \
  --target-lang "tgt_prompt" \
  --trainpref "${TASK}/train.bpe" \
  --validpref "${TASK}/dev.bpe" \
  --destdir "${TASK}/bin-large-prompt/" \
  --workers 60 \
  --srcdict util_files/bart.large/dict.txt \
  --tgtdict util_files/bart.large/dict.txt; 



: 'TOTAL_NUM_EPOCHS=100
WARMUP_UPDATES=500   
LR=1e-5
MAX_TOKENS=1024
UPDATE_FREQ=1
BART_PATH=/home/ec2-user/quic-efs/user/jingfe/util_files/bart.large/model.pt

CUDA_VISIBLE_DEVICES=$1 fairseq-train "${TASK}/bin-large-prompt" \
    --restore-file $BART_PATH \
    --max-tokens $MAX_TOKENS \
    --task translation \
    --source-lang src --target-lang tgt_prompt \
    --truncate-source \
    --layernorm-embedding \
    --share-all-embeddings \
    --share-decoder-input-output-embed \
    --reset-optimizer --reset-dataloader --reset-meters \
    --required-batch-size-multiple 1 \
    --arch bart_large \
    --criterion label_smoothed_cross_entropy \
    --label-smoothing 0.1 \
    --dropout 0.1 --attention-dropout 0.1 \
    --weight-decay 0.01 --optimizer adam --adam-betas "(0.9, 0.999)" --adam-eps 1e-08 \
    --clip-norm 0.1 \
    --lr $LR --max-epoch $TOTAL_NUM_EPOCHS \
    --fp16 --update-freq $UPDATE_FREQ \
    --skip-invalid-size-inputs-valid-test \
    --find-unused-parameters \
    --save-dir "$TASK/bart-checkpoints$PARAM"; '

echo "$outprompt"

for f in $TASK/bart-checkpoints$PARAM/checkpoint38*
do 
    for lambda in 0 1 0.22
    do
        echo '------------------------------------------------------------'
        echo $f
        echo $lambda
        CUDA_VISIBLE_DEVICES=$1 python semantic_parsing.py --model-dir $(dirname $f) --model-file "$(basename $f):model.pt" --src $TASK/src.test --out $TASK/pred-ensemble$PARAM.test --data-dir "${TASK}/bin-large-prompt/" --use-prefix-constriant --prompt "$outprompt" --prefix-file prompt_prefixes.txt --prediction-weight=$lambda 
        python acc_sql.py -pred $TASK/pred-ensemble$PARAM.test -gold $TASK/tgt_prompt.test
        python normalize_and_generate_prompt.py -in_file $TASK/pred-ensemble$PARAM.test -out_file data/geo_sql_query_select/prompt_seq.test -reg_term "from" -in_prompt "the sentence talks about" -out_prompt " , the sentence asks to select" -from_clause 
    done
done
