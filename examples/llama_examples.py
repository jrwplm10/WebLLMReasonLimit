import argparse
import os, sys
import numpy as np
import pandas as pd
import time
import gc
import re
import random
import copy
import math
from matplotlib import pyplot as plt

import transformers
import torch

from transformers import LlamaForCausalLM, LlamaTokenizerFast

# Example I've compiled from a bunch of my llama code.
# Not super organized.
# jlim@wpi.edu

# Example code for using transformers with the model. I used this as a starting point:
# https://medium.com/@lucnguyen_61589/llama-2-using-huggingface-part-1-3a29fdbaa9ed

KEYPATH = "/some/path/to/huggingface/key"
with open(KEYPATH, 'r') as f:
    API_KEY = f.readline()
    API_KEY = API_KEY.rstrip('\n')

TEST_MODEL = "Llama-3.2-3B-Instruct"
MODEL_REPO = "meta-llama/Llama-3.2-3B-Instruct"  # Other model does not have a chat template; no chat support?

GEN_TEMP = 1.0

EOT_STR = "<|eot_id|>"

DEVICE_STR = 'cuda'

MAX_NEW_TOKENS = 5  # need this much longer for sentences.

def main():
    print("Initializing model & pipeline...")
    # Model, tokenizer, pipeline init
    device_map_setting = DEVICE_STR  # 'auto'  # 'cuda'

    model = transformers.AutoModelForCausalLM.from_pretrained(
        MODEL_REPO,
        token=API_KEY,
        device_map=device_map_setting
    )

    # Set to eval mode!
    # https://discuss.huggingface.co/t/inference-without-gradient-computation/14449
    model.eval()

    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_REPO, token=API_KEY)

    if torch.cuda.is_available():
        print("GPU available...")
    else:
        print("No GPU available...")

    pipeline = transformers.pipeline(
        "text-generation",
        model=model,
        torch_dtype=torch.float16,  # Probably won't work on cpu...
        tokenizer=tokenizer,
        device_map=device_map_setting,
    )

    eval_task_prompt = (
        "PUT MODEL PROMPT HERE. '{q1}'\n")

    phrase_to_substitute = "Some stuff"

    num_queries = 5

    # Choose random qqp

    model_query = [{"role": "user", "content": eval_task_prompt.format(q1=phrase_to_substitute)}]

    # one-time query
    prompt = pipeline.tokenizer.apply_chat_template(model_query, tokenize=False, add_generation_prompt=True)

    print("Model Prompt~~~~~~~~~~~~~~")
    print(prompt)

    for a in range(num_queries):
        encoded_query_request = pipeline.tokenizer(prompt, return_tensors="pt",
                                                   padding=False)  # Keeping padding off for now.

        # No gradients!
        with torch.no_grad():
            # Put on proper device?
            # Inspiration: https://discuss.huggingface.co/t/device-map-auto-with-error-expected-all-tensors-to-be-on-the-same-device/31938/6
            encoded_query_request.to(DEVICE_STR)

            generated_output = pipeline.model.generate(**encoded_query_request, do_sample=True, temperature=GEN_TEMP,
                                                       max_new_tokens=MAX_NEW_TOKENS,
                                                       return_dict_in_generate=True, output_scores=True,
                                                       output_logits=True,
                                                       pad_token_id=pipeline.tokenizer.eos_token_id)

            # Model always repeats the starting tokens; always take new tokens only.
            generated_output = generated_output.sequences[0][encoded_query_request['input_ids'].shape[1]:]

            # Detokenize, convert to lowercase.
            generated_output = pipeline.tokenizer.decode(generated_output)

        del encoded_query_request

        print("Model response # " + str(a) + " ~~~~~~~~~~~~~~~~~~~~~:")
        print(generated_output)

if __name__ == "__main__":
    main()