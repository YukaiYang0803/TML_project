# Imports
from openai import OpenAI
import json
import re
import os
from tqdm import tqdm
import argparse
import json
from numpy.random import seed, randint

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_name", type=str, default="GSM-IC_2step")
parser.add_argument("--dataset_dir", type=str, default="data/")
parser.add_argument("--dataset_size", type=int, default=100)
# parser.add_argument("--num_questions", type=int, default=None)
# parser.add_argument("--num_passed_questions",type=int,default=30)
parser.add_argument("--debug_print", action="store_true", default=False)
args = parser.parse_args()
args_dict = vars(args)

dataset_name = args_dict["dataset_name"]
dataset_dir = args_dict["dataset_dir"]
dataset_size = args_dict["dataset_size"]
debug_print = args_dict["debug_print"]

# No API key is needed in this part

with open("data/EIE_raw_passed_questions.json") as file:
    passed_data = json.load(file)
question_ids = [d['question_id'] for d in passed_data]
# question_id
# Q

with open("EIE_raw.json") as file:
    data = json.load(file)

with open("EIE-IC_templates.json") as file:
    templates = json.load(file)

off_topics = {"human": templates["off_topic_contexts"], "non-human": templates["off_topic_contexts_nonhuman"]}
overlapp_roles = ['sister', 'brother', 'father', 'mother']
non_overlapp_roles = ['Ada', 'Emma', 'Jack', 'Tom']

new_ds = []
seed(0) # Add a random seed for reproducibility


def add_context(question, context):
    first_question_mark = question.find("?")
    first_period_mark = question.find(".")
    if first_period_mark < first_question_mark: # There is a fact sentence before the question sentence
        return question[:first_period_mark+1] + f" {context}" + question[first_period_mark+1:]
    else:
        return f"{context} " + question


# Will need:
# original_question
# answer
# new_question
# role
# number_min and number_max
# sentence_template
# role_label (overlapped or not)
# sentence_label (in/off-topic)

for _ in range(dataset_size):
    for i, idx in enumerate(question_ids):
        question = data["examples"][idx]["input"]
        num_min, num_max = templates["questions"][i]["min_number"], templates["questions"][i]["max_number"]
        human_or_not = templates["questions"][i]["human"]
        in_topic_or_not = randint(2) # randint(2) means 0 or 1 (50/50)
        role_overlapp_or_not = randint(2)

        # determine the topic of the context
        template_id = randint(4)
        if in_topic_or_not == True:
            template = templates["questions"][i]["in_topic_contexts"][template_id]
        else:
            template = off_topics["human"][template_id] if human_or_not == True else off_topics["non-human"][template_id]
            # generate the role of the context
            role_id = randint(4)
            if human_or_not == False: # Non-human object: keep it unchanged
                role = role
            else:
                if role_overlapp_or_not == True:
                    role = templates["questions"][i]["role"] + "'s " + overlapp_roles[role_id]
                else:
                    role = non_overlapp_roles[role_id]
            # generate the number in the context
            number = randint(num_min//3,num_max*3+1)
        
        context = template.replace("[ROLE]", role)
        context = context.replace("[NUMBER]", str(number))
        
        # Add the context to the original question
        new_question = add_context(question, context)
        new_question += "\n" # Start the choices from the next line
        options = data["examples"][idx]["target_scores"]
        # Iterate through the options to build the multiple choice string and get the truth label
        truth_label = -1
        for idx, option in enumerate(options.keys()):
            new_question += f"{chr(65 + idx)}. {option}\n"
            if options[option] == 1:
                truth_label = idx
        new_ds.append({
            "original_question": passed_data[i]["Q"],
            "answer": truth_label,
            "new_question": new_question,
            "role": role,
            "human": human_or_not,
            "min_number": num_min,
            "max_number": num_max,
            "sentence_template": template,
            "role_label": "overlapped" if role_overlapp_or_not else "nonoverlapped",
            "sentence_label": "in_topic" if in_topic_or_not else "out_topic"
        })
        pass


with open(f"{dataset_name}.json", "w") as file:
    json.dump(new_ds, file, indent=4)
file.close()