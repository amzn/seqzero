import argparse
import os

parser = argparse.ArgumentParser(description='Calculate Acc')
parser.add_argument('-in_file', default='train.json', help='In file')
parser.add_argument('-out_src', default='src.train', help='Out src file')
parser.add_argument('-out_tgt', default='tgt.train', help='Out tgt file')
parser.add_argument('-num', type=int, default=0, help='Number of examples')
parser.add_argument('-bos', action='store_true', help='Prepend bos')
args = parser.parse_args()

def make_dir(path):
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

make_dir(args.out_src)
make_dir(args.out_tgt)

table_list = ['state', 'border_info', 'city', 'highlow', 'river', 'mountain', 'road', 'lake', 'derived_table', 'derived_field']
with open(args.in_file) as in_file, open(args.out_src, 'w') as out_src_file, open(args.out_tgt, 'w') as out_tgt_file:
    l = 0
    for line in in_file:
        sent, sql = line.strip().split('|||')
        if args.bos:
            out_src_file.write("<s> " + sent.strip().lower() + "\n")
        else:
            out_src_file.write(sent.strip().lower() + "\n")

        sql_list_org = sql.strip().split()
        assert(sql_list_org[-1]==';')
        sql_list_org = sql_list_org[:-1]
        sql_list = []
        flag = 0
        for i, t in enumerate(sql_list_org):
            sql_list.append(t.lower())
        if args.bos:
            out_tgt_file.write(' '.join(["<s>"] + sql_list) + "\n")
        else:
            out_tgt_file.write(' '.join(sql_list) + "\n")
        l+=1
        if args.num>0 and l>=args.num:
            break
