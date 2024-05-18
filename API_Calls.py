# Imports
from openai import OpenAI
import json
import re
import os
from tqdm import tqdm
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_name", type=str, default="GSM-IC_2step")
parser.add_argument("--dataset_dir", type=str, default="data/")
parser.add_argument("--model_name", type=str, default="gpt-3.5")
parser.add_argument("--num_questions", type=int, default=None)
parser.add_argument("--debug_print", action="store_true", default=False)
args = parser.parse_args()
args_dict = vars(args)

dataset_name = args_dict["dataset_name"]
dataset_dir = args_dict["dataset_dir"]
model_name = args_dict["model_name"]
num_questions = args_dict["num_questions"]
debug_print = args_dict["debug_print"]

model = "gpt-3.5-turbo" if model_name == 'gpt-3.5' else None

API_KEY = os.getenv('API_KEY')
# API_KEY = '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'

def extract_questions_and_answers(json_file_name):
    """
    takes the json_file_name and populate two lists, new_questions
    and answers then return the tuple
    """
    with open(json_file_name, 'r') as file:
        data = json.load(file)
    
    new_questions = []
    answers = []
    
    for item in data:
        new_questions.append(item.get('new_question'))
        answers.append(item.get('answer'))
    
    return new_questions, answers


def test_extraction():
    """
    This function tests extract_questions_and_answers by calling and print
    the output of the second entry of new_questions and answers
    """
    new_questions, answers = extract_questions_and_answers('GSM-IC_2step.json')
    print(new_questions[1])
    print(answers[1])



def get_model_responses(system_prompt: dict, question: str):
    client = OpenAI(
        api_key = API_KEY
    )

    system_prompt.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model=model,
        messages=system_prompt,
        max_tokens=1500,
        n = 1,
        temperature= 0.1
    )

    return response.choices[0].message.content # return responses


def extract_final_answer(response_text):
    # Define the regular expression pattern to find 'Answer:' followed by a number
    pattern = re.compile(r'####\s*(\d+)', re.IGNORECASE)
    
    # # Initialize an empty list to store the extracted answers
    # answers = []
    
    # # Loop through each response in the input list
    # for response in response_text:
    #     # Search for the pattern in the response
    match = pattern.search(response_text)
    if match:
        # Extract the number after 'Answer:' and convert it to an integer
        answer = match.group(1)
            # # Add the answer to the list
            # answers.append(answer)
    else:
        answer = None
    return answer#s


def coq_system_prompt():
    """
    This function Defines the Chain of Code system prompt
    """
    sys_prompt = [{"role":"system", "content": 
                    "You are an expert who always write a pseudocode about a math problem "
                    "before start answering the question itself. In the end of the answer, "
                    "you should extract and print the final numeric answer that contains "
                    "only numbers, not symbols or signs, and doing so by begins with ####"}
                #  {"role":"user", "content": "I know there's something in the wake of your smile"},
                #  {"role":"assistant", "content": "I get a notion from the look in your eyes, yeah"},
                #  {"role":"user", "content": "You've built a love but that love falls apart"},
                #  {"role":"assistant", "content": ""},
                #  {"role":"user", "content": ""}
                ]    
    return sys_prompt

def cot_system_prompt():
    """
    This function Defines the Chain of Thought system prompt
    """
    sys_prompt = [{"role":"system", "content": 
                    "You are an expert at solving math problem, you should think step by step "
                    "before start answering the question itself. In the end of the answer, "
                    "you should extract and print the final numeric answer that contains "
                    "only numbers, not symbols or signs, and doing so by begins with ####"}
                #  {"role":"user", "content": "I know there's something in the wake of your smile"},
                #  {"role":"assistant", "content": "I get a notion from the look in your eyes, yeah"},
                #  {"role":"user", "content": "You've built a love but that love falls apart"},
                #  {"role":"assistant", "content": ""},
                #  {"role":"user", "content": ""}
                ]    
    return sys_prompt

def main():
    # Load datasets ##TODO: add an option to use huggingface to load datasets
    questions, answers = extract_questions_and_answers(f"{dataset_name}.json")
    # Subset q/a for faster testing
    n = len(questions) if num_questions == None else num_questions
    questions_first_n, answers_first_n = questions[:n], answers[:n]

    # Initialize variables to record the responses
    coq_answers = []
    cot_answers = []
    
    # Initialize success for both methods to be 0
    cot_success = 0
    coq_success = 0
    total_wrong_format = 0
    
    pbar = tqdm(range(n))
    for i in pbar:
        question, answer = questions_first_n[i], answers_first_n[i]

        match = False
        while not match: # Keep sending requests until format matches
            coq_output = get_model_responses(coq_system_prompt(), question)
            coq_response = extract_final_answer(coq_output)
            match = True if coq_response != None else False
            total_wrong_format += 1 if not match else 0

        match = False
        while not match: # Keep sending requests until format matches
            cot_output = get_model_responses(cot_system_prompt(), question)
            cot_response = extract_final_answer(cot_output)
            match = True if cot_response != None else False
            total_wrong_format += 1 if not match else 0
        
        # Record the outputs
        coq_answers.append({"question_id":i+1, "Q": question, "O": coq_output, "A": coq_response})
        cot_answers.append({"question_id":i+1, "Q": question, "O": cot_output, "A": cot_response})

        # Compute and update success rate
        coq_success += (answer == coq_response)
        cot_success += (answer == cot_response)
        pbar.set_postfix({"coq acc": "{:.2f}".format(coq_success/(i+1)*100), "cot acc": "{:.2f}".format(cot_success/(i+1)*100})

    # Debugging purposes:
    # print(responses)
    # print(answers[0:2])

    print("Success Rate for CoC is:", coq_success/n)
    print("Success Rate for CoT is:", cot_success/n)
    if debug_print == True:
        print(f"Total counts of incorrect format answers: {total_wrong_format}")

    # Save the results
    with open(dataset_dir+dataset_name+"_coc.json", "w") as file:
        json.dump(coq_answers, file, indent=4)
    file.close()

    with open(dataset_dir+dataset_name+"_cot.json", "w") as file:
        json.dump(cot_answers, file, indent=4)
    file.close()


if __name__ == "__main__":
    main()

    
    
    
    
