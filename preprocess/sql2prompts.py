import argparse
import os

def proc_simple_sql(sql_list):
    sub_sqls = {'select':[], 'from':[], 'where':[], 'group':[], 'order':[]}
    special_tokens = ['select', 'from', 'where', 'group', 'order']
    for t in special_tokens:
        if not (sql_list.count(t)==0 or sql_list.count(t)==1):
            print(sql_list)
        assert(sql_list.count(t)==0 or sql_list.count(t)==1)
    while len(sql_list)>0:
        assert(sql_list[0] in special_tokens)
        flag = 0
        idx = 0
        for i, t in enumerate(sql_list[1:]):
            if t in special_tokens:
                flag = 1
                idx = i+1
                break
        if flag==1:
            sub_sqls[sql_list[0]] = ' '.join(sql_list[:idx])
            sql_list = sql_list[idx:]
        else:
            sub_sqls[sql_list[0]] = ' '.join(sql_list)
            sql_list = []
    return sub_sqls
    

def proc_sql(sql_list):
    sub_sqls = [] 
    while True:
        flag = 0
        idx = 0
        for i, t in enumerate(sql_list):
            if t == '(' and sql_list[i+1] == 'select':
                flag = 1
                idx = i
                break
        if flag == 0:
            break
        lb = 1
        end_idx = idx + 1
        while lb>0:
            if sql_list[end_idx] == ')':
                lb-=1
            if sql_list[end_idx] == '(':
                lb+=1
            end_idx+=1
        sub_sqls.append(sql_list[idx: end_idx])
        sql_list = sql_list[:idx] + (['CT'] if sql_list[idx-1] == 'from' else ['CV']) + sql_list[end_idx:]
    child_sqls = []
    for sql in sub_sqls:
        assert(sql[0]=='(' and sql[-1]==')')
        child_sqls.append(proc_sql(sql[1: -1]))

    return {'parent_sql': proc_simple_sql(sql_list), 'child_sqls': child_sqls}

def recover_sql_given_out_st(sqls, out_special_tokens, args):
    if args.in_order == 'from':
        special_tokens = ['from', 'select', 'where', 'group', 'order']
    else:
        special_tokens = ['select', 'from', 'where', 'group', 'order']
    dic = {}
    child_sqls = sqls['child_sqls']
    for st in special_tokens:
        if len(sqls['parent_sql'][st]) > 0:
            sql_tokens = sqls['parent_sql'][st].split()
            nested_sql_tokens = []
            for t in sql_tokens:
                if t == 'CT' or t == 'CV':
                    nested_sql_tokens.append('(')
                    nested_sql_tokens.extend(recover_sql(child_sqls[0], out_special_tokens, args).split())
                    nested_sql_tokens.append(')')
                    child_sqls = child_sqls[1:]
                else:
                    nested_sql_tokens.append(t)
            dic[st] = nested_sql_tokens
    return dic
    


def recover_sql(sqls, special_tokens, args):
    dic = recover_sql_given_out_st(sqls, special_tokens, args)
    final_sql = []
    for st in special_tokens:
        if st in dic:
            final_sql.extend(dic[st])
    return  ' '.join(final_sql)


def proc_prev_sql(dic, special_tokens, token, prompt, content):
    token_id = special_tokens.index(token)
    
    final_sql = []
    for st in special_tokens[:token_id]:
        if st in dic:
            final_sql.extend(dic[st])
    final_sql.extend(prompt.split())
    out_prompt = ' '.join(final_sql)
    final_sql.extend(content)
    return out_prompt, ' '.join(final_sql)

def proc_from(sqls, special_tokens, args):
    dic = recover_sql_given_out_st(sqls, special_tokens, args)
    if args.prompt:
        prompt = 'the sentence talks about'
    else:
        prompt = 'from'
    assert('from' in dic)
    if 'from' in dic:
        assert(dic['from'][0]=='from')
        content = dic['from'][1:]
    else:
        content = ['none']
    return proc_prev_sql(dic, special_tokens, 'from', prompt, content)

def proc_select(sqls, special_tokens, args):
    dic = recover_sql_given_out_st(sqls, special_tokens, args)
    if args.prompt:
        prompt = ', the sentence asks to select'
    else:
        prompt = 'select'
    assert('select' in dic)
    if 'select' in dic:
        assert(dic['select'][0]=='select')
        content = dic['select'][1:]
    else:
        content = ['none']
    return proc_prev_sql(dic, special_tokens, 'select', prompt, content)

def proc_where(sqls, special_tokens, args):
    dic = recover_sql_given_out_st(sqls, special_tokens, args)
    if args.prompt:
        prompt = ', the setence requires'
    else:
        prompt = 'where'
    if 'where' in dic:
        assert(dic['where'][0]=='where')
        content = dic['where'][1:]
    else:
        content = ['none']
    return proc_prev_sql(dic, special_tokens, 'where', prompt, content)

def proc_group(sqls, special_tokens, args):
    dic = recover_sql_given_out_st(sqls, special_tokens, args)
    if args.prompt:
        prompt = ', the setence requires to group by'
    else:
        prompt = 'group by'
    if 'group' in dic:
        assert(dic['group'][0]=='group' and dic['group'][1]=='by')
        content = dic['group'][2:]
    else:
        content = ['none']
    return proc_prev_sql(dic, special_tokens, 'group', prompt, content)

def proc_order(sqls, special_tokens, args):
    dic = recover_sql_given_out_st(sqls, special_tokens, args)
    if args.prompt:
        prompt = ', the setence requires the result to be ordered by'
    else:
        prompt = 'order by'
    if 'order' in dic:
        assert(dic['order'][0]=='order' and dic['order'][1]=='by')
        content = dic['order'][2:]
    else:
        content = ['none']
    return proc_prev_sql(dic, special_tokens, 'order', prompt, content)

def proc_pair(sent, sql_list, args):
    sents = []
    sqls = []
    prompts = []
    processed_sqls = proc_sql(sql_list)
    if args.out_order == 'from':
        special_tokens = ['from', 'select', 'where', 'group', 'order']
    else:
        special_tokens = ['select', 'from', 'where', 'group', 'order']

    if args.clause == 'sqlfrom':
        prompt, sql = proc_from(processed_sqls, special_tokens, args)
        sqls.append(sql)
        prompts.append(prompt)
    elif args.clause == 'select':
        prompt, sql = proc_select(processed_sqls, special_tokens, args)
        sqls.append(sql)
        prompts.append(prompt)
    elif args.clause == 'where':
        prompt, sql = proc_where(processed_sqls, special_tokens, args)
        sqls.append(sql)
        prompts.append(prompt)
    elif args.clause == 'group':
        prompt, sql = proc_group(processed_sqls, special_tokens, args)
        sqls.append(sql)
        prompts.append(prompt)
    elif args.clause == 'order':
        prompt, sql = proc_order(processed_sqls, special_tokens, args)
        sqls.append(sql)
        prompts.append(prompt)
    else:
        sqls.append(recover_sql(processed_sqls, special_tokens, args))
    sents.append(sent)
    return sents, sqls, prompts

def make_dir(path):
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate Acc')
    parser.add_argument('-in_file', default='train.json', help='In file')
    parser.add_argument('-out_src', default='src.train', help='Out src file')
    parser.add_argument('-out_tgt', default='tgt.train', help='Out tgt file')
    parser.add_argument('-out_prompt', default='prompt.train', help='Out tgt file')
    parser.add_argument('-clause', default='all', help='Processing SQL clause')
    parser.add_argument('-num', type=int, default=0, help='Number of examples')
    parser.add_argument('-prompt', action='store_true', help='Whether to change to nl prompt')
    parser.add_argument('-in_order', default='select', help='select or from first')
    parser.add_argument('-out_order', default='select', help='select or from first')
    args = parser.parse_args()

    table_list = ['state', 'border_info', 'city', 'highlow', 'river', 'mountain', 'road', 'lake', 'derived_table', 'derived_field']
    operation_list = ['max', 'sum', 'count', 'distinct', 'avg']
    agg_operation_list = ['max', 'sum', 'count', 'avg']


    sents = []
    sqls = []

    make_dir(args.out_src)
    make_dir(args.out_tgt)
    make_dir(args.out_prompt)

    with open(args.in_file) as in_file, open(args.out_src, 'w') as out_src_file, open(args.out_tgt, 'w') as out_tgt_file, open(args.out_prompt, 'w') as out_prompt_file:
        l = 0
        for line in in_file:
            sent, sql = line.strip().split('|||')
            sents.append(sent.strip().lower())

            sql_list_org = sql.strip().split()
            assert(sql_list_org[-1]==';')
            sql_list_org = sql_list_org[:-1]
            sql_list = []
            flag = 0
            for i, t in enumerate(sql_list_org):
                sql_list.append(t.lower())
            sqls.append(sql_list)

            l+=1
            if args.num>0 and l>=args.num:
                break

        assert(len(sents) == len(sqls))
        for sent, sql_list in zip(sents, sqls):
            fsents, fsqls, fprompts = proc_pair(sent, sql_list, args)
            for s, sl, p in zip(fsents, fsqls, fprompts):
                #print(sl)
                out_src_file.write(s + "\n")
                out_tgt_file.write(' '.join(sl.split()) + "\n")
                out_prompt_file.write(' '.join(p.split()) + "\n")

