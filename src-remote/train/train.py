#!/usr/bin/env python3

import os
import random
import shutil
import logging
import transformers
import torch

import numpy as np
import torch.distributed as dist

from datetime import datetime
from dataclasses import field, dataclass
from utils.util import set_logger, print_args

from utils.loader import PROCESSOR
from utils.trainer import LoggerCallback, RemoveStateCallback

from transformers.tokenization_utils import AddedToken
from datasets import load_dataset, concatenate_datasets
from transformers import (
    Trainer,
    set_seed,
    AutoConfig,
    AutoTokenizer, 
    HfArgumentParser,
    TrainingArguments, 
    LlamaForCausalLM,
    AutoModelForCausalLM,
    default_data_collator
)

logger = logging.getLogger()

@dataclass
class DataArguments:

    no_timestamps: bool = field(default=False)
    no_load_model_pararmeters: bool = field(default=False)

    # data
    train_file: str = field(default=None)
    train_coef: str = field(default=None)
    delete_long_sample: bool = field(default=False)

    # process
    max_len: int = field(default=2048)
    processor: str = field(default='code_dialogue')
    preprocessing_num_workers: int = field(default=64)
    
    # model
    model_cfg: str = field(default="data/models/starcoder")
    flash_attention: bool = field(default=False)

    resume_from: str = field(default=None)

    # output
    stream: bool = field(default=False)


def resize(model, tokenizer, special_tokens):
    if len(special_tokens) == 0:
        return

    additional_special_tokens = tokenizer.additional_special_tokens + special_tokens
    additional_special_tokens = [AddedToken(t) for t in additional_special_tokens]

    num_new_tokens = tokenizer.add_special_tokens(dict(additional_special_tokens=additional_special_tokens))

    if num_new_tokens == 0:
        return

    model.resize_token_embeddings(len(tokenizer), pad_to_multiple_of=128)

    if num_new_tokens > 0:
        input_embeddings = model.get_input_embeddings().weight.data
        output_embeddings = model.get_output_embeddings().weight.data

        input_embeddings_avg = input_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)
        output_embeddings_avg = output_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)

        input_embeddings[-num_new_tokens:] = input_embeddings_avg
        output_embeddings[-num_new_tokens:] = output_embeddings_avg

def train():
    parser = HfArgumentParser((DataArguments, TrainingArguments))

    data_args, training_args = parser.parse_args_into_dataclasses()

    training_args._frozen = False

    if not data_args.no_timestamps:
        timestr = datetime.now().strftime("-%m%d%H%M")
        training_args.output_dir = training_args.output_dir + timestr

    training_args.logging_dir = os.path.join(training_args.output_dir, 'logging')

    if os.path.exists(training_args.output_dir):
        if training_args.overwrite_output_dir:
            if training_args.process_index == 0:
                shutil.rmtree(training_args.output_dir)
        else:
            raise ValueError(f"Output directory ({training_args.output_dir}) already exists. Use --overwrite_output_dir to overcome.")
    
    if training_args.world_size > 1:
        dist.barrier()
    
    if training_args.process_index == 0:
        os.makedirs(training_args.output_dir)
    
    if training_args.world_size > 1:
        dist.barrier()
    
    set_seed(training_args.seed)

    node_rank = int(os.getenv('GROUP_RANK', '0'))

    for _logger in [logger, transformers.utils.logging.get_logger(), logging.getLogger('DeepSpeed')]:
        set_logger(_logger, training_args.local_rank, data_args.stream, os.path.join(training_args.output_dir, f'log-node-{node_rank}.log'))

    logger.warning("Device: %s, rank: %s, world size: %s", training_args.device, training_args.process_index, training_args.world_size)

    if training_args.world_size > 1:
        dist.barrier()

    print_args(data_args, 'Data Arguments')
    print_args(training_args, 'Training Arguments')

    processor = PROCESSOR[data_args.processor](model_path=data_args.model_cfg)

    config = AutoConfig.from_pretrained(data_args.model_cfg, trust_remote_code=True)
    config.use_cache = False

    if data_args.no_load_model_pararmeters:
        model = AutoModelForCausalLM.from_config(config, trust_remote_code=True, attn_implementation = "flash_attention_2")
    else:
        model = AutoModelForCausalLM.from_pretrained(data_args.model_cfg, config=config, torch_dtype=torch.bfloat16, trust_remote_code=True, attn_implementation = "flash_attention_2")
    # tokenizer = AutoTokenizer.from_pretrained(data_args.model_cfg, legacy=False, use_fast=True)
    tokenizer = AutoTokenizer.from_pretrained(data_args.model_cfg, trust_remote_code=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    resize(model, tokenizer, processor.get_special_token())
    
    train_sets = []
    for src in data_args.train_file.split(','):
        if os.path.isdir(src):
            train_sets.append(load_dataset('json', data_files=[os.path.join(src, file) for file in os.listdir(src)], split='train'))
        else:
            train_sets.append(load_dataset('json', data_files=src, split='train'))
    
    lengths = np.array([_set.shape[0] for _set in train_sets])
    logger.info("Data Lengths: %s", lengths)

    if data_args.train_coef is not None:
        
        coefs = np.array([float(_coef) for _coef in data_args.train_coef.split(',')])
        coefs = coefs / coefs.sum()

        sample_nums = np.max(lengths / coefs) * coefs

        logger.info("Sampled Lengths: %s", sample_nums)

        rand = random.Random(training_args.seed)
        for i, _sample_num in enumerate(sample_nums):
            indices = list(range(lengths[i]))

            main_indices = indices * int(_sample_num // lengths[i])
            if _sample_num % lengths[i] > 0:
                main_indices += rand.sample(indices, int(_sample_num % lengths[i]))
            
            train_sets[i] = train_sets[i].select(main_indices)

    for i in range(1, len(train_sets)):
        train_sets[i] = train_sets[i].cast(train_sets[0].features)

    train_sets = concatenate_datasets(train_sets)
    logger.info('Total %d case', len(train_sets))

    with training_args.main_process_first(desc="dataset map inputs"):
        train_sets = train_sets.map(
            processor.process_input,
            load_from_cache_file=False,
            num_proc=data_args.preprocessing_num_workers,
            desc="Running dialogue mapping on dataset",
        )
    
    process_batch_size = min(1000, len(train_sets))

    column_names = list(train_sets.features)
    with training_args.main_process_first(desc="dataset map tokenization"):
        train_sets = train_sets.map(
            processor.process_tokenize,
            fn_kwargs={
                "tokenizer": tokenizer, 
                "max_len": data_args.max_len,
                "delete_long_sample": data_args.delete_long_sample
            },
            batched=True,
            load_from_cache_file=False,
            remove_columns=column_names,
            batch_size=process_batch_size,
            num_proc=data_args.preprocessing_num_workers,
            desc="Running tokenizer on dataset",
        )
    
    logger.info('Total %d case after filter', len(train_sets))
    
    with training_args.main_process_first(desc="Log a few random samples from the training set"):
        for index in random.sample(range(len(train_sets)), 20):
            label_tokens = []
            for label in train_sets[index]['labels']:
                if label >= 0:
                    label_tokens.append(tokenizer.convert_ids_to_tokens(label))
                else:
                    label_tokens.append('<|ignore|>')

            vocab_size = tokenizer.vocab_size
            for token_id in train_sets[index]['input_ids']:
                if token_id < 0 or token_id >= vocab_size:
                    logger.info(f"Invalid token ID found: {token_id}")

            logger.info(
                "Sample %d of the raw training set:\n\ninput_tokens: %s\n\n%s\n\nlabel_tokens: %s",
                index, 
                train_sets[index]['input_ids'],
                tokenizer.convert_ids_to_tokens(train_sets[index]['input_ids']), 
                label_tokens
            )
    
    train_sets = train_sets.shuffle(seed=training_args.seed)
    column_names = list(train_sets.features)
    with training_args.main_process_first(desc="dataset map grouping"):
        train_sets = train_sets.map(
            processor.group_texts,
            fn_kwargs={
                "tokenizer": tokenizer, 
                "max_len": data_args.max_len
            },
            batched=True,
            load_from_cache_file=False,
            remove_columns=column_names,
            batch_size=process_batch_size,
            num_proc=data_args.preprocessing_num_workers,
            desc=f"Grouping texts in chunks of {data_args.max_len}",
        )
    
    with training_args.main_process_first(desc="Log a few random samples from the grouped training set"):
        for index in random.sample(range(len(train_sets)), 3):
            logger.info(
                "Sample %d of the merged training set:\n\n%s",
                index, tokenizer.decode(train_sets[index]['input_ids'])
            )

    trainer = Trainer(
        args=training_args,
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_sets,
        callbacks=[LoggerCallback, RemoveStateCallback],
        data_collator=default_data_collator,
    )

    trainer.train(resume_from_checkpoint=data_args.resume_from)
    
    trainer.save_model(training_args.output_dir)

if __name__ == "__main__":

    try:
        train()
    except Exception as e:
        logging.exception(e)
        exit(-1)
