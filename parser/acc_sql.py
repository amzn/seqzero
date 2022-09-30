import argparse

parser = argparse.ArgumentParser(description='Calculate Acc')
parser.add_argument('-pred', default='', help='Predited file')
parser.add_argument('-gold', default='', help='Gold file')
parser.add_argument('-v', action='store_true', help='Gold file')
args = parser.parse_args()

def addToken(t, sent):
    if len(t)>1 and t[-1]=='(':
        sent.append(t[:-1].lower().replace('-', '_'))
        sent.append('(')
    elif len(t)>1 and t[-1]==')':
        sent.append(t[:-1].lower().replace('-', '_'))
        sent.append(')')
    else:
        sent.append(t.lower().replace('-', '_'))

def readPredGold(pred_arg, gold_arg):

    pred_sents=[]
    gold_sents=[]

    with open(pred_arg) as pred_file, open(gold_arg) as gold_file:
        for line in pred_file:
            sent = line.strip().split()
            pred_sents.append(sent)
        for line in gold_file:
            gold_sents.append(line.strip().split())
    assert(len(pred_sents)==len(gold_sents))

    return pred_sents, gold_sents

def compute_acc(pred_sents, gold_sents):
    total_num = 0
    correct_num = 0
    for pred, gold in zip(pred_sents,gold_sents):
        if len(gold)>0:
            total_num+=1
            if ''.join(pred)==''.join(gold):
                correct_num+=1
            else:
                if args.v:
                    print(''.join(gold))
                    print(''.join(pred))
                    print('---------------------------')
                pass
    print('Correct: %d, Total: %d, Acc: %f'% (correct_num, total_num, correct_num/total_num))


if __name__ == "__main__":
    pred_sents, gold_sents = readPredGold(args.pred, args.gold)
    compute_acc(pred_sents, gold_sents)
