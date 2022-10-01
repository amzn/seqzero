import torch
from fairseq.models.bart import BARTModel
import argparse
from constraint import build_trie, build_partial_trie

GEO_FUN_KWARGS = dict(beam=1, lenpen=1.0, max_len_b=200, min_len=1)


def build_prefixes_from_file(bart, file):
    ret = []
    with open(file, "r", encoding="utf-8") as reader:
        for line in reader:
            sent = " ".join(line.strip().split())
            prefix_tokens = bart.bpe.encode(sent)
            if len(prefix_tokens.split(" ")) > min(bart.max_positions) - 2:
                prefix_tokens = " ".join(prefix_tokens.split(" ")[: min(bart.max_positions) - 2])
            bpe_prefix = "</s> <s> " + prefix_tokens+ " </s>"
            
            prefix_tokens = bart.task.source_dictionary.encode_line(bpe_prefix, append_eos=False) 
            ret.append(prefix_tokens.tolist())
    return ret

def build_partial_prefixes_from_file(bart, file):
    ret = []
    with open(file, "r", encoding="utf-8") as reader:
        for line in reader:
            sent = " ".join(line.strip().split())
            prefix_tokens = bart.bpe.encode(" "+sent)
            if len(prefix_tokens.split(" ")) > min(bart.max_positions) - 2:
                prefix_tokens = " ".join(prefix_tokens.split(" ")[: min(bart.max_positions) - 2])
            bpe_prefix = prefix_tokens
            
            prefix_tokens = bart.task.source_dictionary.encode_line(bpe_prefix, append_eos=False) 
            ret.append(prefix_tokens.tolist())
    return ret
    
@torch.no_grad()
def generate(bart, infile, outfile="bart_hypo.txt", bsz=32, n_obs=None, store_score = False, prompt_file = "", constraints = False, **eval_kwargs):
    count = 1

    certainty_list = []
    prompt_list = []
    if prompt_file:
        with open(prompt_file) as reader:
            for line in reader:
                prompt_list.append(line.strip())
    prev_count = 0

    with open(infile) as source, open(outfile, "w") as fout:
        sline = source.readline().strip()
        slines = [sline]
        for sline in source:
            if n_obs is not None and count > n_obs:
                break
            if count % bsz == 0:
                if prompt_file:
                    eval_kwargs["diff_prompts"] = prompt_list[prev_count: count]
                    prev_count=count
                if store_score:
                    hypotheses_batch = bart.sample(slines, return_hypo = True, constraints = constraints, **eval_kwargs)
                    for hypothesis in hypotheses_batch:
                        scores = torch.tensor([float(elem["first_token_score"].item()) for elem in hypothesis[1]])
                        probs = torch.exp(scores)/torch.sum(torch.exp(scores))
                        certainty_list.append(probs[0])
                        assert(len(hypothesis[0])==len(probs))
                        fout.write(hypothesis[0][0] + "\t" + str((probs[0]-probs[1]).item()) + "\n")
                else:
                    hypotheses_batch = bart.sample(slines, constraints = constraints, **eval_kwargs)
                    for hypothesis in hypotheses_batch:
                        fout.write(hypothesis + "\n")
                        fout.flush()

                slines = []
            slines.append(sline.strip())
            count += 1

        if slines != []:
            if prompt_file:
                eval_kwargs["diff_prompts"] = prompt_list[prev_count:]
                prev_count=count
            if store_score:
                hypotheses_batch = bart.sample(slines, return_hypo = True, constraints = constraints, **eval_kwargs)
                for hypothesis in hypotheses_batch:
                    scores = torch.tensor([float(elem["first_token_score"].item()) for elem in hypothesis[1]])
                    probs = torch.exp(scores)/torch.sum(torch.exp(scores))
                    certainty_list.append(probs[0])
                    assert(len(hypothesis[0])==len(probs))
                    fout.write(hypothesis[0][0] + "\t" + str((probs[0]-probs[1]).item()) + "\n")
                    '''for i, hypo in enumerate(hypothesis[0]):
                        fout.write(hypo + "\t" + str(probs[i].item()) + "\n")

                    fout.write( "\n")
                    fout.flush()'''
            else:
                hypotheses_batch = bart.sample(slines, constraints = constraints, **eval_kwargs)
                for hypothesis in hypotheses_batch:
                    fout.write(hypothesis + "\n")
                    fout.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-dir",
        required=True,
        type=str,
        default="bart.large.cnn/",
        help="path containing model file",
    )
    parser.add_argument(
        "--model-file",
        default="checkpoint_best.pt",
        help="where in model_dir are weights saved",
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        type=str,
        default="bart.large.cnn/",
        help="path containing rc_dict.txt",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="",
        help="prompt",
    )
    parser.add_argument(
        "--src", default="test.source", help="text to parse", type=str
    )
    parser.add_argument(
        "--out", default="test.hypo", help="where to save parses", type=str
    )
    parser.add_argument(
        "--prefix-file", default="/home/ec2-user/quic-efs/user/jingfe/sem_parses/my_code/prefixes.txt", help="where to find prefixe trees", type=str
    )
    parser.add_argument("--bsz", default=32, help="parsing batch size", type=int)
    parser.add_argument(
        "--n", default=None, help="how many examples to parse", type=int
    )
    parser.add_argument(
        "--store-score", help='store score.', action='store_true'
    )
    parser.add_argument(
        "--partial-trie", help='use partial constrined decoding', action='store_true'
    )
    parser.add_argument(
        "--constraints", help='whether there are lexical constraints.', action='store_true'
    )
    parser.add_argument(
        "--no-hard-constraint", help='whether there are lexical constraints.', action='store_true'
    )
    parser.add_argument(
        "--prompt-file", default="", help="where to find prefixe trees", type=str
    )
    parser.add_argument('--weight-ensemble', type=float, default=0.0)
    parser.add_argument('--prediction-weight', type=float, default=1.0)
    parser.add_argument('--use-prefix-constriant', help='Use prefix constriants.', action='store_true')
    parser.add_argument('--sort-by-first-token', help='Use acore of first token after prefix to sort.', action='store_true')
    args = parser.parse_args()
    eval_kwargs = GEO_FUN_KWARGS
    eval_kwargs["prefix"] = args.prompt
    if args.model_dir == "pytorch/fairseq":
        bart = torch.hub.load("pytorch/fairseq", args.model_file)
    else:
        bart = BARTModel.from_pretrained(
            args.model_dir,
            checkpoint_file=args.model_file,
            data_name_or_path=args.data_dir,
            task="translation",
            weight_emsemble=args.weight_ensemble,
        )
    bart = bart.eval()
    if args.use_prefix_constriant:
        
        if args.partial_trie:
            prefixes = build_partial_prefixes_from_file(bart, args.prefix_file)
            trie = build_partial_trie(prefixes, len(bart.task.source_dictionary))
            eval_kwargs["prefix_allowed_tokens_fn"]=lambda batch_id, sent: trie.get(sent.tolist())
        else:
            prefixes = build_prefixes_from_file(bart, args.prefix_file)
            trie = build_trie(prefixes)
            eval_kwargs["prefix_allowed_tokens_fn"]=lambda batch_id, sent: trie.get(sent.tolist())
    if args.sort_by_first_token:
        eval_kwargs["sort_by_first_token"]=True
    eval_kwargs["prediction_weight"]=args.prediction_weight
    eval_kwargs["hard_constraint"] = not args.no_hard_constraint
    if torch.cuda.is_available():
        bart = bart.cuda().half()
    generate(
        bart, args.src, bsz=args.bsz, n_obs=args.n, outfile=args.out, store_score = args.store_score, prompt_file = args.prompt_file, constraints = args.constraints, **eval_kwargs
    )


if __name__ == "__main__":
    main()
