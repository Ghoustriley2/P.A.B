import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = '7550380859:AAFMbI92s-Wf51cBLMSgQUq8_JLOMt-WFwI'
DATA_FILE = 'userdata.json'

RANKS = ['E', 'D', 'C', 'B', 'A', 'S']
MAX_PLACE = 50

XP_VALUES = {
    'лёгкая': 5,
    'средняя': 10,
    'сложная': 20,
    'нереальная': 40,
    'тигриный': 80,
    'дракон': 150,
    'демон': 250,
    'божественный': 500
}

DEFAULT_SKILLS = ['Python', 'HTML/CSS', 'JavaScript', 'Git', 'Алгоритмы']

def load_data():
    if not os.path.isfile(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_user_profile(user_id):
    skills = {skill: {'xp': 0} for skill in DEFAULT_SKILLS}
    return {
        'xp': 0,
        'rank': 'E',
        'place': MAX_PLACE,
        'level': 0,
        'skills': skills,
        'tasks_completed': 0,
        'registered': True
    }

def rank_index(rank):
    return RANKS.index(rank)

def update_rank_and_place(user_data, all_users):
    if user_data['place'] == 1:
        cur_rank_i = rank_index(user_data['rank'])
        if cur_rank_i < len(RANKS) - 1:
            new_rank = RANKS[cur_rank_i + 1]
            user_data['rank'] = new_rank
            user_data['place'] = MAX_PLACE
            return True
    return False

def recalc_places(data):
    for rank in RANKS:
        users_in_rank = [(uid, udata['xp']) for uid, udata in data.items() if udata['rank'] == rank]
        users_in_rank.sort(key=lambda x: x[1], reverse=True)
        for place, (uid, _) in enumerate(users_in_rank, start=1):
            data[uid]['place'] = place if place <= MAX_PLACE else MAX_PLACE

async def registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id in data and data[user_id].get('registered', False):
        await update.message.reply_text('Вы уже зарегистрированы и не можете зарегистрироваться повторно.')
        return

    data[user_id] = create_user_profile(user_id)
    save_data(data)
    await update.message.reply_text('Регистрация прошла успешно! Добро пожаловать в Ассоциацию Программирования.')

async def complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get('registered', False):
        await update.message.reply_text('Вы не зарегистрированы. Используйте /registration для регистрации.')
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text('Использование: /complete <сложность> <навык>\nПример: /complete лёгкая Python')
        return

    difficulty = args[0].lower()
    skill = ' '.join(args[1:])

    if difficulty not in XP_VALUES:
        await update.message.reply_text(f'Неверная сложность. Возможные варианты: {", ".join(XP_VALUES.keys())}')
        return
    if skill not in data[user_id]['skills']:
        await update.message.reply_text(f'Навык "{skill}" не найден в вашем профиле.')
        return

    xp_gained = XP_VALUES[difficulty]
    user = data[user_id]

    user['xp'] += xp_gained
    user['skills'][skill]['xp'] += xp_gained
    user['tasks_completed'] += 1

    recalc_places(data)

    promoted = update_rank_and_place(user, data)
    if promoted:
        await update.message.reply_text(f'Поздравляем! Вы повышены до ранга {user["rank"]} и занимаете место {user["place"]}.')
    else:
        await update.message.reply_text(f'Задание выполнено! Вы получили {xp_gained} XP.\nТекущий ранг: {user["rank"]}, место в топе: {user["place"]}')

    save_data(data)

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get('registered', False):
        await update.message.reply_text('Вы не зарегистрированы. Используйте /registration для регистрации.')
        return

    user = data[user_id]
    text = (
        f'Ваш текущий ранг: {user["rank"]}\n'
        f'Место в топе вашего ранга: {user["place"]}\n'
        f'Всего выполнено заданий: {user["tasks_completed"]}\n'
        f'Общий опыт (XP): {user["xp"]}\n'
        f'Уровень (LVL): {user["level"]}\n\n'
        'Для подробностей по навыкам используйте команду /skills'
    )
    await update.message.reply_text(text)

async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get('registered', False):
        await update.message.reply_text('Вы не зарегистрированы. Используйте /registration для регистрации.')
        return

    user = data[user_id]
    lines = ['Навыки и прогресс по ним:\n']
    for skill, info in user['skills'].items():
        xp = info['xp']
        rank_i = 0
        if xp >= 1000:
            rank_i = 5
        elif xp >= 600:
            rank_i = 4
        elif xp >= 300:
            rank_i = 3
        elif xp >= 150:
            rank_i = 2
        elif xp >= 50:
            rank_i = 1
        rank = RANKS[rank_i]
        lines.append(f'{skill}: XP = {xp}, Ранг навыка = {rank}')
    await update.message.reply_text('\n'.join(lines))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Список доступных команд:\n"
        "/registration — зарегистрироваться в системе\n"
        "/complete <сложность> <навык> — выполнить задание и получить XP\n"
        "/progress — посмотреть свой ранг, место и прогресс\n"
        "/skills — посмотреть навыки и их XP\n"
        "/completehelp — список всех сложностей и доступных навыков\n"
        "/help — показать это сообщение"
    )
    await update.message.reply_text(help_text)

async def completehelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    difficulties = '\n'.join([f'- {k} ({v} XP)' for k, v in XP_VALUES.items()])
    skills = '\n'.join([f'- {s}' for s in DEFAULT_SKILLS])

    text = (
        "Сложности заданий и опыт за них:\n"
        f"{difficulties}\n\n"
        "Навыки, которые можно прокачивать:\n"
        f"{skills}"
    )
    await update.message.reply_text(text)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('registration', registration))
    app.add_handler(CommandHandler('complete', complete))
    app.add_handler(CommandHandler('progress', progress))
    app.add_handler(CommandHandler('skills', skills))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('completehelp', completehelp))

    print('Бот запущен...')
    app.run_polling()

if __name__ == '__main__':
    main()