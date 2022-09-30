TASK=data/geo_sql_query_order
PARAM='-large'


for SPLIT in train dev test
do
  for LANG in src tgt
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
  --target-lang "tgt" \
  --trainpref "${TASK}/train.bpe" \
  --validpref "${TASK}/dev.bpe" \
  --destdir "${TASK}/bin-large/" \
  --workers 60 \
  --srcdict util_files/bart.large/dict.txt \
  --tgtdict util_files/bart.large/dict.txt; 



: 'TOTAL_NUM_EPOCHS=100
WARMUP_UPDATES=500   
LR=1e-5
MAX_TOKENS=1024
UPDATE_FREQ=1
BART_PATH=util_files/bart.large/model.pt

CUDA_VISIBLE_DEVICES=$1 fairseq-train "${TASK}/bin-large" \
    --restore-file $BART_PATH \
    --max-tokens $MAX_TOKENS \
    --task translation \
    --source-lang src --target-lang tgt \
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


for f in $TASK/bart-checkpoints$PARAM/checkpoint37.pt
do 
    echo '------------------------------------------------------------'
    echo $f
    CUDA_VISIBLE_DEVICES=$1 python semantic_parsing.py --model-dir $(dirname $f) --model-file $(basename $f) --src $TASK/src.test --out $TASK/pred$PARAM.test --data-dir ${TASK}/bin-large/ --prompt-file "${TASK}/prompt_seq.test" 
    python acc_sql.py -pred $TASK/pred$PARAM.test -gold $TASK/tgt.test
done
