import argparse

parser = argparse.ArgumentParser(description='Change Prompt')
parser.add_argument('-in_file', default='train.json', help='In file')
parser.add_argument('-out_file', default='src.train', help='Out file')
parser.add_argument('-in_prompt', default='tgt.train', help='In prompt')
parser.add_argument('-out_prompt', default='tgt.train', help='Out prompt')
parser.add_argument('-slot_dict_file', default='', help='Change slot target via dict')
args = parser.parse_args()

if args.slot_dict_file:
    dic = {}
    with open(args.slot_dict_file, 'r') as reader:
        for l in reader:
            k, v = l.strip().split(':')
            dic[k] = v

with open(args.in_file, 'r', encoding='utf-8') as reader, open(args.out_file, 'w', encoding='utf-8') as writer:
    for l in reader:
        l=l.strip()
        assert(l.startswith(args.in_prompt))
        l=l.replace(args.in_prompt, args.out_prompt)
        if args.slot_dict_file:
            new_target = dic[l[len(args.out_prompt):]]
            l = l[:len(args.out_prompt)] + new_target
        writer.write(l+'\n')