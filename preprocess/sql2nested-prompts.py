import argparse
import os
import json

parser = argparse.ArgumentParser(description='Calculate Acc')
parser.add_argument('-in_file', default='train.json', help='In file')
parser.add_argument('-out_src', default='src.train', help='Out src file')
parser.add_argument('-out_tgt', default='tgt.train', help='Out tgt file')
parser.add_argument('-clause', default='from', help='Processing SQL clause')
parser.add_argument('-num', type=int, default=0, help='Number of examples')
parser.add_argument('-bos', action='store_true', help='Prepend bos')
args = parser.parse_args()

table_list = ['state', 'border_info', 'city', 'highlow', 'river', 'mountain', 'road', 'lake', 'derived_table', 'derived_field']
operation_list = ['max', 'sum', 'count', 'distinct', 'avg']
agg_operation_list = ['max', 'sum', 'count', 'avg']

def proc_simple_sql(sql_list):
    sub_sqls = {'select':[], 'from':[], 'where':[], 'group':[], 'order':[]}
    special_tokens = ['select', 'from', 'where', 'group', 'order']
    for t in special_tokens:
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
    #if len(sub_sqls['from'])>0:
    #    print(sub_sqls['from']) 
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

def delete_as(as_sql):
    return as_sql.split(' as ')[0]

def proc_from(sql_from):
    assert(sql_from[0:4]=='from')
    sql_from = sql_from[5:]
    sqls = sql_from.split(' , ')
    #print('!!!!', sql_from)
    processed_sqls = []
    for s in sqls:
        #print(s)
        if ' join ' in s:
            assert('left outer join' in s)
            a, b = s.split(' on ')
            b = b.replace('=', 'equals').replace('.', "'s").replace(' alias0', '').replace(' alias1', '')
            #print(a, '##$', b)
            a = a.split(' left outer join ')
            processed_sqls.append(delete_as(a[0]) + ' , ' + delete_as(a[1]) + ' joint where ' + b)
        else:
            processed_sqls.append(delete_as(s).replace('CT', 'constructed table'))
    #print(processed_sqls)
    return 'the answer can be looked up from ' + ' , '.join(processed_sqls)

def proc_select_operation(sql_select):
    assert(sql_select[0:6]=='select')
    sql_select = sql_select[7:]
    
    sqls = sql_select.split()
    if sqls[0] not in table_list:
        #if not sqls[0] in operation_list:
        #    print(sqls[0])
        assert(sqls[0] in operation_list)
        return 'the sentence asks ' + (sqls[0] if not sqls[0] == 'avg' else 'average')
    else:
        return 'the sentence asks no operation'

def proc_select_column(sql_select):
    assert(sql_select[0:6]=='select')
    sql_select = sql_select[7:]
    #print(sql_select)
    if ',' in sql_select:
        sqls_list = sql_select.split(',')
    else:
        sqls_list = [sql_select]
    processed_sqls_list = []
    for sqls in sqls_list:
        if '/' in sqls:
            processed_sqls_list.extend(sqls.split('/'))
        else:
            processed_sqls_list.append(sqls)
    sqls_list = []
    #print(processed_sqls_list)
    for sql in processed_sqls_list:
        
        sqls = sql.split()
        if sqls[0] not in table_list:
        # if not sqls[0] in operation_list:
        #    print(sqls[0])
            if sqls[0] in agg_operation_list:
                if not (sqls[1] == '(' and sqls[-1] == ')'):
                    print('!!!', sqls, sql[1], sql[-1])
                assert(sqls[1] == '(' and sqls[-1] == ')')
                sqls = sqls[2:-1]
            else:
                assert(sqls[0] == 'distinct')
                sqls = sqls[1:]
        final_sqls = []
        for t in sqls:
            if 'alias' in t:
                continue
            if t == '.':
                final_sqls.append("'s")
            else:
                final_sqls.append(t)
        sqls_list.append(' '.join(final_sqls))
    #print(' and '.join(sqls_list))
    # TODO divided by
    return ' and '.join(sqls_list)

def proc_where(sql_where):
    assert(sql_where[0:5]=='where')
    sql_where = sql_where[6:]
    #sqls = sql_where.split(' , ')
    print('!!!!', sql_where)
    '''processed_sqls = []
    for s in sqls:
        #print(s)
        if ' join ' in s:
            assert('left outer join' in s)
            a, b = s.split(' on ')
            b = b.replace('=', 'equals').replace('.', "'s").replace(' alias0', '').replace(' alias1', '')
            #print(a, '##$', b)
            a = a.split(' left outer join ')
            processed_sqls.append(delete_as(a[0]) + ' , ' + delete_as(a[1]) + ' joint where ' + b)
        else:
            processed_sqls.append(delete_as(s).replace('CT', 'constructed table'))
    #print(processed_sqls)'''
    return 'the answer can be looked up from '



def proc_pair(sent, sql_list):
    sents = []
    sqls = []
    processed_sqls = proc_sql(sql_list)
    
    '''print(sent)
    print(' '.join(sql_list))
    print(json.dumps(processed_sqls, indent=4, sort_keys=True))
    print('---------------------------')'''

    if args.clause == 'select_operation':
        assert(len(processed_sqls['parent_sql']['select'])>0)
        sqls.append(proc_select_operation(processed_sqls['parent_sql']['select']))
        sents.append(sent)
    elif args.clause == 'select_column':
        assert(len(processed_sqls['parent_sql']['select'])>0)
        sqls.append(proc_select_column(processed_sqls['parent_sql']['select']))
        sents.append(sent)
    elif args.clause == 'where':
        '''if (not 'where' in processed_sqls['parent_sql']) or len(processed_sqls['parent_sql']['where'])<=0:
            print(sent)
            print(' '.join(sql_list))
            print(json.dumps(processed_sqls, indent=4, sort_keys=True))
            print('---------------------------')'''
        if len(processed_sqls['parent_sql']['where'])==0:
            sqls.append("the constraint is none")
        else:    
            sqls.append(proc_where(processed_sqls['parent_sql']['where']))
        sents.append(sent) 
    else:
        assert(len(processed_sqls['parent_sql']['from'])>0)
        sqls.append(proc_from(processed_sqls['parent_sql']['from']))
        sents.append(sent)
    #print(sqls[0])
    return sents, sqls

def make_dir(path):
    print(path)
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

make_dir(args.out_src)
make_dir(args.out_tgt)

sents = []
sqls = []
with open(args.in_file) as in_file, open(args.out_src, 'w') as out_src_file, open(args.out_tgt, 'w') as out_tgt_file:
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
            '''if 'alias' in t:
                assert(len(t)==6)
                continue
            if flag == 1:
                flag = 0
                continue
            if t.lower() == 'as':
                print(sql_list_org[i+1].lower())
                assert(sql_list_org[i+1].lower() in table_list)
                flag = 1
                continue'''
            sql_list.append(t.lower())
        sqls.append(sql_list)

        l+=1
        if args.num>0 and l>=args.num:
            break

    assert(len(sents) == len(sqls))
    for sent, sql_list in zip(sents, sqls):
        fsents, fsqls = proc_pair(sent, sql_list)
        for s, sl in zip(fsents, fsqls):
            if args.bos:
                out_src_file.write("<s> " + s + "\n")
            else:
                out_src_file.write(s + "\n")
            if args.bos:
                out_tgt_file.write(' '.join(["<s>"] + sl.split()) + "\n")
            else:
                out_tgt_file.write(' '.join(sl.split()) + "\n")


