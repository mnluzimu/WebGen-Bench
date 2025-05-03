#!/usr/bin/env python3

import re
import torch
import logging

import copy
from transformers import AutoTokenizer

logger = logging.getLogger()

PROCESSOR = dict()
IGNORE_INDEX = -100

def registry(name):

    def _registry(_class):
        PROCESSOR[name] = _class
        return _class
    
    return _registry

class BaseProcessor:

    def group_texts(self, examples, tokenizer, max_len):
        input_ids, labels = [], []
        final_input_ids, final_labels = [], []
        
        for _input_ids, _labels in zip(examples['input_ids'], examples['labels']):
            if len(input_ids) + len(_input_ids) > max_len:
                pad_num = max_len - len(input_ids)
                final_input_ids.append(input_ids + [tokenizer.pad_token_id] * pad_num)
                final_labels.append(labels + [IGNORE_INDEX] * pad_num)

                input_ids, labels = [], []
                
            input_ids.extend(_input_ids)
            labels.extend(_labels)
        
        if len(input_ids) > 0:
            pad_num = max_len - len(input_ids)
            final_input_ids.append(input_ids + [tokenizer.pad_token_id] * pad_num)
            final_labels.append(labels + [IGNORE_INDEX] * pad_num)

        return {
            "input_ids": torch.tensor(final_input_ids).long(),
            "labels": torch.tensor(final_labels).long()
        }


@registry('qwen_agent')
class DialogueProcessor(BaseProcessor):

    special_token = ['<|im_start|>', '<|im_end|>']
    
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

    def get_special_token(self):
        return self.special_token

    def process_input(self, example):
        messages = example["messages"]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        return dict(text=text)

    def process_tokenize(self, examples, tokenizer, max_len, delete_long_sample):
        IGNORE_INDEX = -100  # constant to mark tokens that are ignored
        input_ids_list = []
        labels_list = []
        
        for text in examples['text']:
            # Tokenize without truncation or padding yet
            tokenized = tokenizer(text, truncation=False, padding=False)
            tokens = tokenized['input_ids']
            # Make a copy for labels
            labels = tokens.copy()
            # Convert token ids to token strings to locate special tokens and roles
            token_strs = tokenizer.convert_ids_to_tokens(tokens)

            ignore_segment = False  # flag indicating that we are in a segment to ignore
            i = 0
            while i < len(tokens):
                token = token_strs[i]
                # Check for the beginning of a message block
                if token == '<|im_start|>':
                    # Look ahead for the role token (should be the next token)
                    if i + 1 < len(tokens):
                        role_token = token_strs[i+1].strip()  # remove any extraneous whitespace
                        if role_token in ['user', 'system']:
                            # mark the role token itself as ignored
                            labels[i+1] = IGNORE_INDEX
                            ignore_segment = True
                            # Move index forward so that the role token is processed and then continue.
                            i += 2
                            continue
                # Check for the end marker
                if token == '<|im_end|>':
                    if ignore_segment:
                        labels[i] = IGNORE_INDEX
                        ignore_segment = False
                        i += 1
                        continue
                # If we are within an ignored segment, mark this token as ignore
                if ignore_segment:
                    labels[i] = IGNORE_INDEX
                i += 1

            # Handle length: if the tokenized sequence exceeds the maximum allowed length,
            # either truncate (if delete_long_sample is False) or (if deletion is enabled) leave it as is.
            if len(tokens) > max_len - 1:
                if not delete_long_sample:
                    tokens = tokens[:max_len-1] + [tokenizer.eos_token_id]
                    labels = labels[:max_len-1] + [tokenizer.eos_token_id]
                # Otherwise, you could choose to skip this sample entirely (not shown)
            else:
                tokens = tokens + [tokenizer.eos_token_id]
                labels = labels + [tokenizer.eos_token_id]
            
            input_ids_list.append(tokens)
            labels_list.append(labels)
        
        return {
            "input_ids": input_ids_list,
            "labels": labels_list
        }
