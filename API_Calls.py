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

model = "gpt-3.5-turbo" if model_name == 'gpt-3.5' else "gpt-4o" if model_name == 'gpt-4o' else "gpt-4-turbo" if model_name == 'gpt-4' else None

# API_KEY = os.getenv('API_KEY')
API_KEY = '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'

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
        temperature= 0
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


def coc_system_prompt():
    """
    This function Defines the Chain of Code system prompt
    """
    sys_prompt = [{"role": "system", 
                   "content": "Solve grade school math problem. Be aware to ignore irrelevant information given in the questions."
                    # "content": "You are an expert who always writes a pseudocode about a math problem "
                    #            "before start answering the question itself. Feel free to ignore irrelevant information given in the questions. In the end of the answer, "
                    #            "you should extract and print the final numeric answer that contains "
                    #            "only numbers, not symbols or signs, and doing so by begins with ####"
                  }
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
    sys_prompt = [{"role": "system",
                   "content": "Solve grade school math problem. Feel free to ignore irrelevant information given in the questions."
                #    "content": "You are an expert at solving math problem, you should think step by step "
                #               "before start answering the question itself. Feel free to ignore irrelevant information given in the questions. In the end of the answer, "
                #               "you should extract and print the final numeric answer that contains "
                #               "only numbers, not symbols or signs, and doing so by begins with ####"
                  }
                #  {"role":"user", "content": "I know there's something in the wake of your smile"},
                #  {"role":"assistant", "content": "I get a notion from the look in your eyes, yeah"},
                #  {"role":"user", "content": "You've built a love but that love falls apart"},
                #  {"role":"assistant", "content": ""},
                #  {"role":"user", "content": ""}
                ]    
    return sys_prompt

def convert_to_int(number):
    if number.isdigit():
        return int(number)
    return int(''.join(number.split(',')))

def main():
    # Load datasets ##TODO: add an option to use huggingface to load datasets
    questions, answers = extract_questions_and_answers(f"{dataset_name}.json")
    # Subset q/a for faster testing
    n = len(questions) if num_questions == None else num_questions
    questions_first_n, answers_first_n = questions[:n], answers[:n]


    prompt = """
Q: Elsa has 5 apples. Anna has 2 more apples than Elsa. Liz has 4 peaches. How many apples do they have together?
"""
    ltm_sol = """
A: Let's break down this problem: 1. How many apples does
Anna have? 2. How many apples do Elsa and Anna have
together?
1. Anna has 2 more apples than Elsa. So Anna has 2 + 5 = 7
apples.
2. Elsa and Anna have 5 + 7 = 12 apples together.
#### 12
"""
    cot_sol = """
A: Anna has 2 more apples than Elsa, so Anna has 2 + 5 = 7
apples. Elsa and Anna have 5 + 7 = 12 apples together. 
#### 12
"""
    coc_sol = """
A: Let's write down the pseudocode.
1. Find how many apples Elsa has.
2. Find how many apple Anna has.
3. Sum the two numbers.

Next, let's run the pseudocode line by line.
1. Elsa has 5 apples.
2. Anna has 5 + 2 = 7 apples.
3. 5 + 7 = 12.
#### 12
"""
    prompt = """
Q: Steve is 5'6\". He grows 6 inches. The height of Emma is 8 feet. How tall is Steve in inches?
"""
    coc_sol = """
A: Let's write down the pseudocode. 
1. Convert Steve's height from feet to inches. 
2. Add the growth in inches to Steve's height. 

Next, let's run the pseudocode line by line. 
1. Steve's height in inches is 5 * 12 + 6 = 66 inches. 
2. After growing 6 inches, Steve's height becomes 66 + 6 = 72 inches. 
#### 72
"""
    cot_sol = """
Steve is 5'6\" tall, which is equivalent to 5 x 12 + 6 = 66 inches. 
After growing 6 inches, Steve's height becomes 66 + 6 = 72 inches. 
Therefore, Steve is 72 inches tall. 
#### 72
"""

    prompt = """
Officer Hopps has to give out 200 tickets in May. The first 15 days he averages 8 tickets a day. Officer Hopps' mother bought 200 bus tickets in Feburary. How many does he have to average each day for the rest of the month to reach his required goal?
"""
    coc_sol = """
A: Let's write down the pseudocode. 
1. Calculate the total tickets given out in the first 15 days: 15 days * 8 tickets/day = 120 tickets. 
2. Calculate the remaining tickets needed to reach the goal: 200 tickets - 120 tickets = 80 tickets. 
3. Calculate the number of days left in the month: 31 days in May - 15 days = 16 days. 
4. Calculate the average number of tickets Officer Hopps needs to give out each day for the rest of the month: 80 tickets / 16 days = 5 tickets/day. 
#### 5
"""
    cot_sol = """
To find out how many tickets Officer Hopps has to average each day for the rest of the month to reach his goal, we first need to calculate how many tickets he has already given out in the first 15 days. 

In the first 15 days, Officer Hopps gave out 15 days * 8 tickets/day = 120 tickets. 
He still needs to give out 200 tickets in total, so he needs to give out 200 total tickets - 120 tickets already given = 80 tickets in the remaining days. 

There are 31 days in May, so Officer Hopps has 31 days - 15 days = 16 days left to give out the remaining tickets. 

To find out how many tickets he needs to average each day for the rest of the month, we divide the remaining tickets by the remaining days: 80 tickets / 16 days = 5 tickets/day.

Therefore, Officer Hopps needs to average 5 tickets per day for the rest of the month to reach his goal.

#### 5
"""
    instruction = """
Your should end with ####XXX, where you replace XXX with ONLY the final answer number.
"""

    # Initialize variables to record the responses
    coc_answers = []
    cot_answers = []
    wrong_answers = []
    
    # Initialize success for both methods to be 0
    cot_success = 0
    coc_success = 0
    total_wrong_format = 0
    
    pbar = tqdm(range(n))
    for i in pbar:
        question, answer = questions_first_n[i], answers_first_n[i]

        match = False
        count = 0
        while not match: # Keep sending requests until format matches
            coc_output = get_model_responses(coc_system_prompt(), prompt + coc_sol + "\n\nQ: " + question + instruction + "\nA: Let's write down the pseudocode: ")
            coc_response = extract_final_answer(coc_output)
            match = True if coc_response != None else False
            total_wrong_format += 1 if not match else 0
            count += 1 if not match else 0
            if count > 5:
                coc_response = -1
                break

        match = False
        count = 0
        while not match: # Keep sending requests until format matches
            cot_output = get_model_responses(cot_system_prompt(), prompt + cot_sol + "\n\nQ: " + question + instruction + "\nA: Let's think step by step:  ")
            cot_response = extract_final_answer(cot_output)
            match = True if cot_response != None else False
            total_wrong_format += 1 if not match else 0
            count += 1 if not match else 0
            if count > 5:
                cot_response = -1
                break
        
        # Record the outputs
        coc_answers.append({"question_id":i+1, "Q": question, "O": coc_output, "A": coc_response})
        cot_answers.append({"question_id":i+1, "Q": question, "O": cot_output, "A": cot_response})

        # Compute and update success rate
        answer = convert_to_int(answer)
        coc_success += (answer == int(coc_response))
        cot_success += (answer == int(cot_response))
        pbar.set_postfix({"coc acc": "{:.2f}".format(coc_success/(i+1)*100), "cot acc": "{:.2f}".format(cot_success/(i+1)*100)})

        if answer != int(coc_response):
            wrong_answers.append({"question_id":i+1, "Q": question, "A0": answer, "O1": coc_output, "A1": coc_response, "O2": cot_output, "A2": cot_response})
        
    # Debugging purposes:
    # print(responses)
    # print(answers[0:2])

    print("Success Rate for CoC is:", coc_success/n)
    print("Success Rate for CoT is:", cot_success/n)
    
    if debug_print == True:
        print(f"Total counts of incorrect format answers: {total_wrong_format}")

    # Save the results
    with open(f"{dataset_dir}{dataset_name}_coc_{model_name}_{num_questions}.json", "w") as file:
        json.dump(coc_answers, file, indent=4)
    file.close()

    with open(f"{dataset_dir}{dataset_name}_cot_{model_name}_{num_questions}.json", "w") as file:
        json.dump(cot_answers, file, indent=4)
    file.close()

    with open(f"{dataset_dir}{dataset_name}_wrong_{model_name}_{num_questions}.json", "w") as file:
        json.dump(wrong_answers, file, indent=4)
    file.close()


if __name__ == "__main__":
    main()

    
    
    
    
