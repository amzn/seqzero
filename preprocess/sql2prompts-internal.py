import argparse
import os

from sql2prompts import proc_sql, proc_where, recover_sql


parser = argparse.ArgumentParser(description='Calculate Acc')
parser.add_argument('-in_src_file', default='train.json', help='In file')
parser.add_argument('-in_tgt_file', default='train.json', help='In file')
parser.add_argument('-out_src', default='src.train', help='Out src file')
parser.add_argument('-out_tgt', default='tgt.train', help='Out tgt file')
parser.add_argument('-out_prompt', default='prompt.train', help='Out tgt file')
parser.add_argument('-clause', default='all', help='Processing SQL clause')
parser.add_argument('-num', type=int, default=0, help='Number of examples')
parser.add_argument('-prompt', action='store_true', help='Whether to change to nl prompt')
parser.add_argument('-in_order', default='select', help='select or from first')
parser.add_argument('-out_order', default='select', help='select or from first')
args = parser.parse_args()

def proc_pair(sent, sql_list, args):
    sents = []
    sqls = []
    prompts = []
    processed_sqls = proc_sql(sql_list)
    if args.out_order == 'from':
        special_tokens = ['from', 'select', 'where', 'group', 'order']
    else:
        special_tokens = ['select', 'from', 'where', 'group', 'order']

    if args.clause == 'where' or args.clause == 'where_zero':
        prompt, sql = proc_where(processed_sqls, special_tokens, args)
        sqls.append(sql)
        prompts.append(prompt)
    else:
        sqls.append(recover_sql(processed_sqls, special_tokens, args))
    sents.append(sent)
    #print(sqls[0])'''
    return sents, sqls, prompts

sents = []
sqls = []

def make_dir(path):
    print(path)
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

make_dir(args.out_src)
make_dir(args.out_tgt)
make_dir(args.out_prompt)

org_sents = []
org_sqls = []

attribute_list= ['price', 'size', 'subscribe', 'delivery', 'brand']

with open(args.in_src_file) as in_src_file, open(args.in_tgt_file) as in_tgt_file, open(args.out_src, 'w') as out_src_file, open(args.out_tgt, 'w') as out_tgt_file, open(args.out_prompt, 'w') as out_prompt_file:
    l = 0
    for line in in_src_file:
        org_sents.append(line.strip())
    for line in in_tgt_file:
        org_sqls.append(line.strip())
    for sent, sql in zip(org_sents, org_sqls):
        sents.append(sent.strip().lower())

        sql_list_org = sql.strip().replace('(', ' ( ').replace(')', ' ) ').split()
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
        if args.clause == 'where_condition' or args.clause == 'where_match':
            fsents, fsqls = [sent], [' '.join(sql_list)]
        else:
            fsents, fsqls, _ = proc_pair(sent, sql_list, args)
        
        for s, sl in zip(fsents, fsqls):
            sl = ' '.join(sl.split())
            assert(sl.startswith('select * from asins , the setence requires matchingalgorithm ') or sl.startswith('select * from asins where matchingalgorithm '))
            sl = sl.replace('select * from asins , the setence requires matchingalgorithm ', '').replace('select * from asins where matchingalgorithm ', '')
            #print('!!!', sl)
            sll = sl.split()
            assert(sll[0] == '(')
            num = 1
            for i in range(1, len(sll)):
                if sll[i] == '(':
                    num +=1
                if sll[i] == ')':
                    num-=1
                    if num == 0:
                        break
            
            if args.clause == 'where_condition':
                if i+1==len(sll):
                    sll = ['none']
                else:
                    if not sll[i+1] == 'and':
                        sll = sll[i+1:]
                        #print(sll)
                    else:
                        sll = sll[i+2:]
                        assert(sll[0] in attribute_list)

                sl = 'the condition is : ' +' '.join(sll)
                fprompt = 'the condition is : '
            elif args.clause == 'where_match':
                sll = ['matching', 'algorithm'] + sll[:i+1]
                sl = ' '.join(sll)
                fprompt = 'matching algorithm ( '
            else:

                if i+1==len(sll):
                    continue
                assert(sll[i+1] == 'and')

                sll = sll[i+2:]
            
                assert(sll[0] in attribute_list)

                if sll[0] not in ['price', 'size']:
                    continue

                sl = 'the sentence requires ' +' '.join(sll[:2])
                fprompt = 'the sentence requires ' +' '.join(sll[:1])

            out_src_file.write(s + "\n")
            out_tgt_file.write(sl + "\n")
            out_prompt_file.write(fprompt + "\n")

