: '# Query (compositional/template) split
python json_to_flat_org.py --tokenise_sql --query_split --input_file ../raw_data/geography.json --output_prefix ../parser/data/aligned_data/geo/query
python split_input_output_sql.py -in_file ../parser/data/aligned_data/geo/query.train -out_src ../parser/data/geo_sql_query/src.train -out_tgt ../parser/data/geo_sql_query/tgt.train
python split_input_output_sql.py -in_file ../parser/data/aligned_data/geo/query.dev -out_src ../parser/data/geo_sql_query/src.dev -out_tgt ../parser/data/geo_sql_query/tgt.dev
python split_input_output_sql.py -in_file ../parser/data/aligned_data/geo/query.test -out_src ../parser/data/geo_sql_query/src.test -out_tgt ../parser/data/geo_sql_query/tgt.test 

# Query (compositional/template) split sqlfrom select where group order clauses
for split in train dev test
do 
    for clause in sqlfrom select where group order
    do
        python sql2prompts.py -in_order select -out_order from -clause $clause -prompt -in_file ../parser/data/aligned_data/geo/query.$split -out_src ../parser/data/geo_sql_query_$clause/src.$split -out_tgt ../parser/data/geo_sql_query_$clause/tgt.$split -out_prompt ../parser/data/geo_sql_query_$clause/prompt.$split
    done
done '

# Query (compositional/template) split, "From" clause w/o alias
python sql2nested-prompts.py -in_file ../parser/data/aligned_data/geo/query.train -out_src ../parser/data/geo_sql_query_from/src.train -out_tgt ../parser/data/geo_sql_query_from/tgt.train
python sql2nested-prompts.py -in_file ../parser/data/aligned_data/geo/query.dev -out_src ../parser/data/geo_sql_query_from/src.dev -out_tgt ../parser/data/geo_sql_query_from/tgt.dev
python sql2nested-prompts.py -in_file ../parser/data/aligned_data/geo/query.test -out_src ../parser/data/geo_sql_query_from/src.test -out_tgt ../parser/data/geo_sql_query_from/tgt.test 


: 'for split in train dev test
do 
    for clause in where_zero where_condition where_match
    do
        python sql2prompts-internal.py -in_order select -out_order select -clause $clause -prompt -in_src_file /Users/jingfe/sem_parses/SUBS-Semantic-Parsing/data/internal_sql_query_comp/src.$split -in_tgt_file /Users/jingfe/sem_parses/SUBS-Semantic-Parsing/data/internal_sql_query_comp/tgt.$split -out_src /Users/jingfe/sem_parses/SUBS-Semantic-Parsing/data/internal_sql_query_$clause/src.$split -out_tgt /Users/jingfe/sem_parses/SUBS-Semantic-Parsing/data/internal_sql_query_$clause/tgt.$split -out_prompt /Users/jingfe/sem_parses/SUBS-Semantic-Parsing/data/internal_sql_query_$clause/prompt.$split
    done
done '