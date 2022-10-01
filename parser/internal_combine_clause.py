import argparse

parser = argparse.ArgumentParser(description='Change Prompt')
parser.add_argument('-in_condition_file', default='train.json', help='In file')
parser.add_argument('-in_match_file', default='train.json', help='In file')
parser.add_argument('-out_pred_file', default='src.train', help='Out file')
parser.add_argument('-in_gold_file', default='tgt.train', help='In prompt')
parser.add_argument('-out_gold_file', default='tgt.train', help='Out prompt')
args = parser.parse_args()

conditions = []
matches = []

attribute_list= ['price', 'size', 'subscribe', 'delivery', 'brand']
with open(args.in_condition_file, 'r', encoding='utf-8') as in_condition_file, open(args.in_match_file, 'r', encoding='utf-8') as in_match_file, open(args.out_pred_file, 'w', encoding='utf-8') as out_pred_file:
    for l in in_condition_file:
        conditions.append(l.strip())
    for l in in_match_file:
        matches.append(l.strip())
    assert(len(conditions)==len(matches))
    for con, ma in zip(matches, conditions):
        assert(ma.startswith("the condition is : "))
        ma_l = ma[len("the condition is : "):].split()
        if ma_l[0] in attribute_list:
            ma_l = ['and'] + ma_l
        elif ma_l[0] == 'none':
            assert(len(ma_l)==1)
            ma_l = []
        else:
            assert(ma_l[0] == 'order')
        sql = 'select * from asins where '+ ' '.join(con.split()+ma_l)
        out_pred_file.write(sql+'\n')

with open(args.in_gold_file, 'r', encoding='utf-8') as in_gold_file, open(args.out_gold_file, 'w', encoding='utf-8') as out_gold_file:
    for l in in_gold_file:
        sql = ' '.join(l.strip().replace('(', ' ( ').replace(')', ' ) ').split()).replace('matchingalgorithm', 'matching algorithm')
        out_gold_file.write(sql+'\n')
