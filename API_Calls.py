# Imports
from openai import OpenAI
import json
import re
import os

API_KEY = os.getenv('API_KEY')

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



def get_model_responses(system_prompt: dict, questions: list):
    client = OpenAI(
        api_key = API_KEY
    )
    responses = []

    for question in questions:
        system_prompt.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=system_prompt,
            max_tokens=1500,
            n = 1,
            temperature= 0.1
        )
        responses.append(response.choices[0].message.content)
    return responses


def extract_final_answer(response_text):
    # Define the regular expression pattern to find 'Answer:' followed by a number
    pattern = re.compile(r'####\s*(\d+)', re.IGNORECASE)
    
    # Initialize an empty list to store the extracted answers
    answers = []
    
    # Loop through each response in the input list
    for response in response_text:
        # Search for the pattern in the response
        match = pattern.search(response)
        if match:
            # Extract the number after 'Answer:' and convert it to an integer
            answer = match.group(1)
            # Add the answer to the list
            answers.append(answer)
    
    return answers


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
    questions, answers = extract_questions_and_answers('GSM-IC_2step.json')
    # Subset q/a for faster testing
    n = 10
    questions_first_n = questions[:n]
    answers_first_n = answers[:n]
    coq_output = get_model_responses(coq_system_prompt(), questions_first_n[0:20])
    cot_output = get_model_responses(cot_system_prompt(), questions_first_n[0:20])
    coq_responses = extract_final_answer(coq_output)
    cot_responses = extract_final_answer(cot_output)

    # Initialize success for both methods to be 0
    cot_success = 0
    coq_success = 0

    min_length = min(len(answers_first_n), len(coq_responses), len(cot_responses))

    for i in range(min_length):
        if answers[i] == cot_success[i]:
            cot_success += 1
        
        if answers[i] == coq_success[i]:
            coq_success += 1
    
    # Debugging purposes:
    # print(responses)
    # print(answers[0:2])

    print("Success Rate for CoC is:", coq_success/min_length)
    print("Success Rate for CoT is:", cot_success/min_length)





if __name__ == "__main__":
    main()

    
    
    
    