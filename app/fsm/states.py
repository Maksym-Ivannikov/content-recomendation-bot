from aiogram.fsm.state import State, StatesGroup

class CreateRec(StatesGroup):
    choose_type = State()
    ask_title = State()
    ask_desc = State()
    confirm = State()

class CreateQuiz(StatesGroup):
    ask_title = State()
    ask_type = State()
    ask_desc = State()
    confirm = State()
    q_text = State()
    q_options = State()
    q_correct = State()

class RunQuiz(StatesGroup):
    choose_cat = State()
    choose_quiz = State()
    answering = State()  # carries quiz_id + q_idx
    finished = State()
