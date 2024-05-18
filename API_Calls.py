# Imports
from openai import OpenAI
import json
import re

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



def get_model_responses(questions: list):
    client = OpenAI(
        api_key = "sk-proj-A1tljddWFSF8RMO4NMD0T3BlbkFJzSIODvwSb7siVk7rpNHC"
    )
    responses = []

    # System Prompt and few-shot examples
    messages_list = [{"role":"system", "content": 
                    "I am a helpful assistant that can solve math problems "
                    "by first write pseudocode to reflect the problem and then answer question based on "
                    "the pseudocode I just wrote. When outputing the final arithmetic answer, I should "
                    "always start with \"Answer:\"."}
                #  {"role":"user", "content": "I know there's something in the wake of your smile"},
                #  {"role":"assistant", "content": "I get a notion from the look in your eyes, yeah"},
                #  {"role":"user", "content": "You've built a love but that love falls apart"},
                #  {"role":"assistant", "content": ""},
                #  {"role":"user", "content": ""}
                ]    

    for question in questions:
        messages_list.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            engine="text-davinci-003",
            prompt=question,
            max_tokens=150,
            n = 1,
            temperature= 0.1
        )
        responses.append(response.choices[0].text.strip())
    return responses


def extract_final_answer(response_text: list):
    # Use a single pattern to identify the final answer
    pattern = r"Answer:\s*(.*)"
    
    match = re.search(pattern, response_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # If no pattern matched, return the entire response (or handle as needed)
    return response_text.strip()

def main():
    pass




if __name__ == "__main__":
    # main()
    test_extraction()
    
    
    