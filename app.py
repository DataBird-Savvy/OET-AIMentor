from flask import Flask, render_template, request, session, jsonify, url_for
from src.OETWriting import OETWritingTaskAssistant
from src.OETListening import OETListeningTaskAssistant
from src.OETReading import OETReadingTaskAssistant
from logger import logging
import requests
import json
import time
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
app.secret_key=os.getenv("APP_KEY")
DB_TASKA="db/readingpartA_topics.db"
DB_TASKB="db/readingpartB_inputs_3Q.db"
DB_TASKC="db/readingpartC_topicsforRAG.db"



@app.route('/')
def index():
    logging.info("Accessed the index page")
    return render_template('index.html')

@app.route('/writing_task', methods=['GET', 'POST'])
def writing_task():
    writing_assistant = OETWritingTaskAssistant()
    logging.info(f"Entered writing_task route with method:{request.method} ", )
    task_question = session.get('task_question', '')
    time_allowed = session.get('time_allowed', 45)
    session['time_allowed'] = time_allowed

    if request.method == 'POST':
        button_clicked = request.form.get('submit_button')
        logging.info(f"Button clicked: {button_clicked}")

        if button_clicked == 'submit':
            writer_input = request.form.get('writer_input', '')
            if not writer_input:
                feedback = 'Please provide input for feedback.'
                logging.warning("No writer input provided")
            else:
                feedback = writing_assistant.get_feedback_and_score(writer_input)
                logging.info(f"Generated feedback: {feedback}")
            
            feedback_got = True
            session['feedback'] = feedback
            return render_template('WritingTask.html', 
                                   task_question=task_question, 
                                   time_allowed=time_allowed, 
                                   feedback=feedback, 
                                   feedback_got=feedback_got, 
                                   next_got=False)

        elif button_clicked == 'next':
            next_task = writing_assistant.generate_task_question()
            session['task_question'] = next_task
            session['feedback'] = False
            logging.info(f"Generated new task question: {next_task}")
            return render_template('WritingTask.html', 
                                   task_question=next_task, 
                                   time_allowed=time_allowed, 
                                   feedback='', 
                                   feedback_got=False, 
                                   next_got=True)

    elif request.method == 'GET':
        task_question = writing_assistant.task_question
        session['task_question'] = task_question
        logging.info(f"Retrieved task question for GET: {task_question}")
        return render_template('WritingTask.html', task_question=task_question, time_allowed=time_allowed, feedback=None, feedback_got=False, next_got=False)

    return render_template('WritingTask.html', 
                           task_question='', 
                           time_allowed=time_allowed, 
                           feedback=None, 
                           feedback_got=False, 
                           next_got=False)
    
    #--------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------ 

@app.route('/listening_task', methods=['GET', 'POST'])
def listening_task():
    
    listening_assistant = OETListeningTaskAssistant()
    logging.info("Entered listening_task route with method: %s", request.method)
    time_allowed = session.get('time_allowed', 45)
    session['time_allowed'] = time_allowed

    if request.method == 'POST':
        button_clicked = request.form.get('submit_button', '')
        logging.info("Button clicked: " )

        if button_clicked == 'next':
            current_index = session.get('current_index', 0)
            next_index = current_index + 1
            session['current_index'] = next_index

            logging.info("Current index:%s , Next index: %s ", current_index, next_index)

            cyclic_gen = listening_assistant.cyclic_iterator(next_index)
            next_task = next(cyclic_gen)
            session['user_query'] = next_task

            filtered_A, filtered_B, filtered_C, audiofile_path = listening_assistant.search_and_retrieve(next_task)
            audiofile_path = url_for('static', filename='artifacts/' + audiofile_path)

            logging.info(f"Next task details: {filtered_A}, {filtered_B}, {filtered_C}, {audiofile_path}")
            return render_template('ListeningTask.html', 
                                   task_question=filtered_A, 
                                   next_got=True, 
                                   time_allowed=time_allowed, 
                                   audio_file=audiofile_path, 
                                   feedback=None, 
                                   filtered_B=filtered_B,
                                   filtered_C=filtered_C, 
                                   feedback_got=False)

        elif button_clicked != 'next':
            data = request.get_json()
            logging.info(f"Received JSON data: {data}")

            if data:
                user_txtanswers = data.get('textAnswers')
                user_mcqanswers = data.get('mcqAnswers')
                user_query = session.get("user_query", " ")
                ans_1_24, ans25_42 = listening_assistant.retrieve_answerpart(user_query)
                feedback_content = listening_assistant.feedback(user_txtanswers, ans_1_24, user_mcqanswers, ans25_42)

                logging.info(f"Feedback content: {feedback_content}")
                return jsonify({
                    'task_question': data.get('task'),
                    'audiofile_path': data.get('audioUrl'),
                    'feedback': feedback_content
                })

    elif request.method == 'GET':
        logging.info("Initial GET request for reading_task")
        cyclic_gen = listening_assistant.cyclic_iterator(idx=0)
        user_query = next(cyclic_gen)
        session['current_index'] = 0
        session['user_query'] = user_query
        
        filtered_A, filtered_B, filtered_C, audiofile_path = listening_assistant.search_and_retrieve(user_query)
        audiofile_path = url_for('static', filename='artifacts/' + audiofile_path)
        
        return render_template('ListeningTask.html', task_question=filtered_A, next_got=False, time_allowed=time_allowed, audio_file=audiofile_path, feedback=None, filtered_B=filtered_B, filtered_C=filtered_C, feedback_got=False)
    
    return render_template('ListeningTask.html', 
                           filtered_A='', 
                           next_got=False, 
                           time_allowed=time_allowed, 
                           audio_file='', 
                           feedback=None, 
                           feedback_got=False)
    
    
#--------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------ 

@app.route('/reading_task', methods=['GET', 'POST'])
def reading_task():
    
    reading_assistant=OETReadingTaskAssistant()
    
    logging.info("Entered reading_task route with method: %s", request.method)
    time_allowed = session.get('time_allowed', 45)
    session['time_allowed'] = time_allowed

    if request.method == 'POST':
        button_clicked = request.form.get('submit_button', '')
        logging.info(f"Button clicked:  {button_clicked}")

        if button_clicked == 'next':
            
            current_index = session.get('current_index', 0)
            next_index = current_index + 1
            session['current_index'] = next_index
           
            inputsA = reading_assistant.get_cyclic_inputs(DB_TASKA)
            cyclic_gen = reading_assistant.cyclic_iterator(idx=next_index,inputs=inputsA)
            topic = next(cyclic_gen)
            session['topic'] = topic
            taskA_prompt = reading_assistant.retrieve_taskA_prompt(topic)
            taskA=reading_assistant.rag_taskpart(taskA_prompt)
            taskAQA_prompt=reading_assistant.retrieve_qaA_prompt(taskA)
            taskAQA=reading_assistant.rag_taskpartQA(taskAQA_prompt)
                       
            inputsB = reading_assistant.get_cyclic_inputs(DB_TASKB)
            cyclic_gen = reading_assistant.cyclic_iterator(idx=next_index, inputs=inputsB)
            prompt_B = next(cyclic_gen)
            
            # -------------------------------finetuned model with ollama--------------------------------
            # response_textB=[]
            # url = "http://localhost:11434/api/generate"
            # model_name = "hf.co/jiya2/fineTuned_OETReadingPartB_Llama-3.2-1B-bnb-4bit_3Q_19_12:F16"
            # # task_B_list = []  # List to store responses
            # data = {
            #     "model": model_name,
            #     "prompt": prompt_B
            #         }
            # # Make the API request
            # response = requests.post(url, json=data, stream=True)
            # if response.status_code == 200:
            #     response_text = ""  # Initialize an empty string to accumulate the response
            #     for line in response.iter_lines():
            #         if line:
            #             decoded_line = line.decode("utf-8") if isinstance(line, bytes) else line
            #             try:
            #                 result = json.loads(decoded_line)
            #                 response_text += result.get("response", "")  # Append the result to response_text
            #             except json.JSONDecodeError:
            #                 # Handle cases where decoding the line fails
            #                 print(f"Failed to decode line: {decoded_line}")
            #                 continue

            #     # Add the response to the list
            #     response_textB.append(response_text)
            # else:
            #     # task_B_list.append(f"Error: {response.status_code}")

            
            # -------------------------------finetunemodel using openai--------------------
        
            # response_textB1=reading_assistant.retrive_B(prompt_B)
            # prompt_B = next(cyclic_gen)
          
            response_textB2=reading_assistant.retrive_B(prompt_B)
            
            # ----------------------------------------------------------------------------
       
            
            inputsC = reading_assistant.get_cyclic_inputs(DB_TASKC)
            cyclic_gen = reading_assistant.cyclic_iterator(idx=0,inputs=inputsC)
            topic = next(cyclic_gen)
            taskC_prompt = reading_assistant.retrieve_taskC_prompt(topic)
            taskC1=reading_assistant.rag_taskpart(taskC_prompt)
            taskCQA_prompt=reading_assistant.retrieve_qaC_prompt(taskC1)
            taskCQA1=reading_assistant.rag_taskpartQA(taskCQA_prompt)
            topic = next(cyclic_gen)
            taskC_prompt = reading_assistant.retrieve_taskC_prompt(topic)
            taskC2=reading_assistant.rag_taskpart(taskC_prompt)
            taskCQA_prompt=reading_assistant.retrieve_qaC_prompt(taskC2)
            taskCQA2=reading_assistant.rag_taskpartQA(taskCQA_prompt)
                 
            return render_template('ReadingTask.html', 
                                    task_A=taskA,
                                    task_qa_A=taskAQA,
                                    task_B1= '',
                                    task_B2= response_textB2,
                                    task_C1=taskC1,
                                    task_qa_C1=taskAQA,
                                    task_C2=taskC2,
                                    task_qa_C2=taskCQA2,
                                    next_got=True, 
                                    time_allowed=time_allowed,  
                                    feedback=None, 
                                    feedback_got=False)

        elif button_clicked != 'next':
            data = request.get_json()
            logging.info("Received JSON data: %s", data)

            if data:
                user_txtanswers = data.get('textAnswers')
                mcq_answers_cqa1 = data.get('mcqAnswersCQA1', [])
                mcq_answers_cqa2 = data.get('mcqAnswersCQA2', [])
                alltextCorrectAnswers= data.get('alltextCorrectAnswers')
                allmcqCorrectAnswersB=data.get('allmcqCorrectAnswersB')
                mcqAnswersB=data.get('mcqAnswersB')
                correctAnswers_taskCQA1=data.get('correctAnswers_taskCQA1')
                correctAnswers_taskCQA2=data.get('correctAnswers_taskCQA2')
            
                feedback_content = reading_assistant.feedback(user_txtanswers, alltextCorrectAnswers,allmcqCorrectAnswersB,mcqAnswersB,correctAnswers_taskCQA1,mcq_answers_cqa1,correctAnswers_taskCQA2,mcq_answers_cqa2)
                return jsonify({'task_A': data.get('taskA'),
                    'task_qa_A': data.get('taskAQA'),
                    'task_B1':  data.get('taskB1'),
                    'task_B2':  data.get('taskB2'),
                    'task_C1':data.get('taskC1'),
                    'task_qa_C1':data.get('taskCQA1'),
                    'task_C2':data.get('taskC2'),
                    'task_qa_C2':data.get('taskCQA2'),
                    'next_got': False, 
                    'time_allowed':time_allowed,  
                    'feedback_got':True,
                    'feedback': feedback_content
                })

    elif request.method == 'GET':
      
        logging.info("Initial GET request for reading_task")
        
        inputsA = reading_assistant.get_cyclic_inputs(DB_TASKA)
        cyclic_gen = reading_assistant.cyclic_iterator(idx=0,inputs=inputsA)
        topic = next(cyclic_gen)
        session['current_index'] = 0
        session['topic'] = topic
        taskA_prompt = reading_assistant.retrieve_taskA_prompt(topic)
        taskA=reading_assistant.rag_taskpart(taskA_prompt)
        taskAQA_prompt=reading_assistant.retrieve_qaA_prompt(taskA)
        taskAQA=reading_assistant.rag_taskpartQA(taskAQA_prompt)
    
        logging.info("Task A: %s", taskA)
        logging.info("Task A QA: %s", taskAQA)
        
        inputsB = reading_assistant.get_cyclic_inputs(DB_TASKB)
        cyclic_gen = reading_assistant.cyclic_iterator(idx=0, inputs=inputsB)
        
        prompt_B = next(cyclic_gen)
        # -------------------------------finetuned model with ollama--------------------------------
        # response_textB=[]
        # url = "http://localhost:11434/api/generate"
        # model_name = "hf.co/jiya2/fineTuned_OETReadingPartB_Llama-3.2-1B-bnb-4bit_3Q_19_12:F16"
        # # task_B_list = []  # List to store responses
        # data = {
        #     "model": model_name,
        #     "prompt": f"{prompt_B}and give exact solution in json without verbosity"
        #         }
        # # Make the API request
        # response = requests.post(url, json=data, stream=True)

        # if response.status_code == 200:
        #     response_text = ""  # Initialize an empty string to accumulate the response
        #     for line in response.iter_lines():
        #         if line:
        #             decoded_line = line.decode("utf-8") if isinstance(line, bytes) else line
        #             try:
        #                 result = json.loads(decoded_line)
        #                 response_text += result.get("response", "")  # Append the result to response_text
        #             except json.JSONDecodeError:
        #                 # Handle cases where decoding the line fails
                        # continue

        #     # Add the response to the list
        #     response_textB.append(response_text)
        # else:
        #     print("Error", response.status_code, response.text)
        #     # task_B_list.append(f"Error: {response.status_code}")
        
        
    # -------------------------------finetunemodel using openai--------------------
        
        # response_textB1=reading_assistant.retrive_B(prompt_B)
        # prompt_B = next(cyclic_gen)
        response_textB2=reading_assistant.retrive_B(prompt_B)

        logging.info("Task B2: %s", response_textB2)
        # ----------------------------------------------------------------------------
        
        inputsC = reading_assistant.get_cyclic_inputs(DB_TASKC)
        cyclic_gen = reading_assistant.cyclic_iterator(idx=0,inputs=inputsC)
        
        topic = next(cyclic_gen)
        taskC_prompt = reading_assistant.retrieve_taskC_prompt(topic)
        taskC1=reading_assistant.rag_taskpart(taskC_prompt)
        taskCQA_prompt=reading_assistant.retrieve_qaC_prompt(taskC1)
        taskCQA1=reading_assistant.rag_taskpartQA(taskCQA_prompt)
        logging.info("Task C1: %s", taskC1)
        logging.info("Task CQA1: %s", taskCQA1)
        
        topic = next(cyclic_gen)
        taskC_prompt = reading_assistant.retrieve_taskC_prompt(topic)
        taskC2=reading_assistant.rag_taskpart(taskC_prompt)
        taskCQA_prompt=reading_assistant.retrieve_qaC_prompt(taskC2)
        taskCQA2=reading_assistant.rag_taskpartQA(taskCQA_prompt)
        logging.info("Task C2: %s", taskC2)
        logging.info("Task CQA2: %s", taskCQA2)
        
        return render_template('ReadingTask.html', 
                               task_A=taskA,
                               task_qa_A=taskAQA,
                               task_B1= '',
                               task_B2= response_textB2,
                               task_C1=taskC1,
                               task_qa_C1=taskCQA1,
                               task_C2=taskC2,
                               task_qa_C2=taskCQA2,
                               next_got=False, 
                               time_allowed=time_allowed,  
                               feedback=None, 
                               feedback_got=False)
    
    return render_template('ReadingTask.html', 
                           task_A='', 
                           task_qa_A='',
                           task_B='',
                           task_C1='',
                           task_qa_C1='',
                           task_C2='',
                           task_qa_C2='',
                           next_got=False, 
                           time_allowed=time_allowed, 
                           audio_file='', 
                           feedback=None, 
                           feedback_got=False)

if __name__ == '__main__':
    app.run()
    
