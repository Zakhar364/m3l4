from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

# Инициализация телеграм-бота и скрытой клавиатуры.
bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove()

# Текст кнопки отмены во всех меню.
cancel_button = "Отмена 🚫"

def cansel(message):
    # Отправить пользователю сообщение об отмене и убрать клавиатуру.
    bot.send_message(message.chat.id, "Отменено 🚫 Если нужно, введи /info для помощи", reply_markup=hideBoard)
  
def no_projects(message):
    # Сообщение, когда у пользователя нет проектов.
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!\nМожешь добавить их с помощью команды /new_project ✨')


def gen_inline_markup(rows):
    # Создать инлайн-клавиатуру с одной кнопкой в строке.
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup


def gen_markup(rows):
    # Создать клавиатуру с вариантами и кнопкой отмены.
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup


# Сопоставление атрибутов проекта с текстом запроса и полем в БД.
attributes_of_projects = {
    'Имя проекта': ["Введите новое имя проекта", "project_name"],
    'Описание': ["Введите новое описание проекта", "description"],
    'Ссылка': ["Введите новую ссылку на проект", "url"],
    'Статус': ["Выберите новый статус задачи", "status_id"]
}


def info_project(message, user_id, project_name):
    # Получить данные проекта и отправить пользователю.
    project_info = manager.get_project_info(user_id, project_name)
    if not project_info:
        bot.send_message(message.chat.id, 'Проект не найден 😕')
        return
    info = project_info[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Навыки пока не добавлены'
    bot.send_message(message.chat.id, f"""📌 Project name: {info[0]}
📝 Description: {info[1]}
🔗 Link: {info[2]}
📌 Status: {info[3]}
💡 Skills: {skills}
""")


@bot.message_handler(commands=['start'])
def start_command(message):
    # Обработка команды /start: приветствие и список команд.
    bot.send_message(message.chat.id, """Привет! 👋 Я бот-менеджер проектов.
Помогу тебе сохранить твои проекты и информацию о них.🙂
""")
    info(message)
    

@bot.message_handler(commands=['info'])
def info(message):
    # Отправка справочной информации о командах.
    bot.send_message(message.chat.id,
"""
Вот команды, которые могут тебе помочь:

/new_project - используй для добавления нового проекта 🚀
/skills - добавь навык проекту 🔧
/projects - посмотри свои проекты 📁
/delete - удаляй проект ❌
/update_projects - редактируй данные проекта ✏️

Также ты можешь ввести имя проекта и узнать информацию о нем!""")
    


@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    # Начало создания нового проекта: запрос имени.
    bot.send_message(message.chat.id, "Введите название проекта 📝")
    bot.register_next_step_handler(message, name_project)


def name_project(message):
    # Сохранение имени проекта и переход к запросу описания.
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "Введите описание проекта 📝")
    bot.register_next_step_handler(message, description_project, data=data)


def description_project(message, data):
    # Сохранение описания и переход к запросу ссылки.
    data.append(message.text)
    bot.send_message(message.chat.id, "Введите ссылку на проект 🔗")
    bot.register_next_step_handler(message, link_project, data=data)


def link_project(message, data):
    # Добавление ссылки и показ списка статусов.
    data.append(message.text)
    statuses = [x[1] for x in manager.get_statuses()]
    bot.send_message(message.chat.id, "Выбери статус проекта 📌", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)


def callback_project(message, data, statuses):
    # Сохранение проекта, если выбран правильный статус.
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "⚠️ Ты выбрал статус не из списка, попробуй еще раз!", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    bot.send_message(message.chat.id, "Проект сохранен ✅")


@bot.message_handler(commands=['skills'])
def skill_handler(message):
    # Запрос проекта для добавления навыка.
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[1] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект, для которого нужно добавить навык 🧩', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)


def skill_project(message, projects):
    # Проверка выбранного проекта и запрос навыка.
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз! 📌', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, 'Выбери навык 💡', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)


def set_skill(message, project_name, skills):
    # Сохранение выбранного навыка для проекта.
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, '⚠️ Выбранный навык не найден, попробуй снова', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(message.chat.id, f'Навык {skill} добавлен проекту {project_name} ✅')


@bot.message_handler(commands=['projects'])
def get_projects(message):
    # Показывает все проекты пользователя с ссылками.
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name: {x[1]} \nLink: {x[3]}\n" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[1] for x in projects]))
    else:
        no_projects(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Обработка нажатия на инлайн-кнопку с названием проекта.
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)


@bot.message_handler(commands=['delete'])
def delete_handler(message):
    # Запрос проекта для удаления.
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name: {x[1]} \nLink: {x[3]}\n" for x in projects])
        projects = [x[1] for x in projects]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)


def delete_project(message, projects):
    # Удаление выбранного проекта.
    project = message.text
    user_id = message.from_user.id

    if message.text == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз! ⛔', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'Проект {project} удален! 🗑️')


@bot.message_handler(commands=['update_projects'])
def update_project(message):
    # Запрос проекта для редактирования.
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[1] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)


def update_project_step_2(message, projects):
    # Проверка выбранного проекта для изменений.
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так! 🤔 Выбери проект, который хочешь изменить еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте ✏️", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)


def update_project_step_3(message, project_name):
    # Выбор поля проекта для обновления.
    attribute = message.text
    reply_markup = None
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй еще раз! ⚠️", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup = gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup=reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])


def update_project_step_4(message, project_name, attribute):
    # Применение обновления к выбранному проекту.
    update_info = message.text
    if attribute == "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
            return
        else:
            bot.send_message(message.chat.id, "⚠️ Был выбран неверный статус, попробуй еще раз!", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    user_id = message.from_user.id
    project_id = manager.get_project_id(project_name, user_id)
    data = (update_info, user_id, project_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "Готово! Обновления внесены ✅")


@bot.message_handler(func=lambda message: True)
def text_handler(message):
    # Обработка любого произвольного текста пользователя.
    user_id = message.from_user.id
    projects = [x[1] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "Тебе нужна помощь? 🤔")
    info(message)


if __name__ == '__main__':
    # Создать БД, заполнить стартовыми данными и запустить бота.
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()
    bot.infinity_polling()
