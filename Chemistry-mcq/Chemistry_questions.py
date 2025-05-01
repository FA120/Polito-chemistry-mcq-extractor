from pdfminer.high_level import extract_text
import re
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
POLIQUIZ = "poliquiz eng.pdf"
LESSONS_FILE = "lessons.txt"
REMOVED_LINES = ["Machine Translated","police","/2023","/90","poliquiz"]
LAST_QUESTION_PAGE = 88
NUM_QUESTIONS = 496

def extract_pages():
    pages = []
    try:
        pages = (extract_text(POLIQUIZ)).split('\x0c')[:-1]
    except Exception as error:
        print(f"Error!: {error}")
    return pages

def set_up_lines(page):
    lines = page.split('\n')
    removed_indexes = []
    for i , line in enumerate(lines):
        for removable in REMOVED_LINES:
            if line.count(removable)>0:
                removed_indexes.append(i)
    for index in sorted(removed_indexes, reverse=True):
        del lines[index]
    while lines.count('')>0:
        lines.remove('')
    return lines

def correct_line(line):
    match = re.search('\d+\.\s*$', line)
    done = False
    if match is not None:
        line = line[match.span()[0]:] + line[:match.span()[0]]
        print(f"corrected line: {line}")
        done = True
    return line,done

def get_questions(page):
    questions = dict()
    lines = set_up_lines(page)
    for i, line in enumerate(lines):
        lines[i], done = correct_line(line)
        if done:
            tmp = lines[i]
            lines[i] = lines[i-1]
            lines[i-1] = tmp
    page_text = '\n'.join(lines)
    matches = list(re.finditer("^\d+\.",page_text,flags=re.MULTILINE))
    for i in range(len(matches)-1):
        current_match = matches[i]
        next_match = matches[i+1]
        questions[int(current_match.group(0)[:-1])] = page_text[current_match.start():next_match.start()]
    questions[int(matches[-1].group(0)[:-1])] = page_text[matches[-1].start():]
    return questions

def get_answers(page):
    lines = set_up_lines(page)
    answers = dict()
    for _,line in enumerate(lines):
        line = line.rstrip()
        line = line.replace('to','a').replace('and','e').replace('_','').replace(' ','')
        quest_num = ""
        is_number = line[0].isdigit()
        for char in line:
            if is_number:
                if char.isdigit():
                    quest_num +=char
                else:
                    is_number = False
                    answers[int(quest_num)] = char.lower()
                    quest_num = ""
            else:
                if char.isdigit():
                    quest_num += char
                    is_number = True
    return answers

def get_all_questions(pages):
    questions = dict()
    for i in range(LAST_QUESTION_PAGE):
        questions.update(get_questions(pages[i]))
    return questions

def get_all_answers(pages):
    answers = dict()
    for i in range(LAST_QUESTION_PAGE,len(pages)):
        answers.update(get_answers(pages[i]))
    return answers

def get_lessons():
    L = []
    try:
        with open(LESSONS_FILE) as file:
            for line in file:
                L.append(line.rstrip())
    except OSError as Error:
        exit(f"Error: Can't get the lessons: {Error}")
    return L

def update(questions, answers, question_number,question_text,answer_text):
    question_text.delete("1.0",END)
    question_text.insert("1.0",questions[question_number])
    answer_text.set(answers[question_number])

def save(question,answer,filename):
    print(f"saving {question} with answer {answer} in file {filename}-mcq.md")
    result = "\n>[!question]\n>" + question.replace("\n","\n>") +"\n\n>[!answer]- Answer: \n>" + answer.upper() + "\n" 
    try:
        with open(filename+"-mcq.md","a") as file:
            file.write(result)
    except OSError as error:
        messagebox.showerror("Error",f"{error}")
    else:
        messagebox.showinfo("question saved",f"question saved in {filename}")

def set_up_window(questions, answers):
    root = Tk()
    root.title("Setting up questions")
    mainframe = ttk.Frame(root)
    mainframe.grid(column=0,row=0)
    list_lessons = StringVar(value=get_lessons())
    lessons = Listbox(mainframe,listvariable=list_lessons, height=20,width=60,exportselection=False)
    lessons.grid(column=0,row=0)

    question_number_string =  StringVar()
    question_number_string.set("1")
    question = Text(mainframe,width = 80, height = 20)
    question.grid(column=1,row=0)
    question.insert("1.0",questions[1])

    answer_text = StringVar(value=answers[1])
    answer = Entry(mainframe, textvariable=answer_text)
    answer.grid(column=1,row=1)

    questions_list = ttk.Spinbox(mainframe, from_=1, to=NUM_QUESTIONS, textvariable=question_number_string, command=lambda: update(questions,answers,int(question_number_string.get()),question,answer_text))
    questions_list.grid(column=1,row=2)

    save_button = Button(mainframe,text="Save",command=lambda: save(question.get("1.0",END),answer.get(),lessons.get(lessons.curselection()[0])))
    save_button.grid(column=2,row=2)
    root.mainloop()
    return root

def main():
    pages = extract_pages()
    questions = get_all_questions(pages)
    answers = get_all_answers(pages)
    set_up_window(questions,answers)

if __name__ == "__main__":
    main()