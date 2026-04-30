import sqlite3
from config import DATABASE

# Список всех доступных навыков для проекта.
skills = [(_,) for _ in (['Python', 'SQL', 'API', 'Telegram'])]

# Список всех возможных статусов проекта.
statuses = [(_,) for _ in (['На этапе проектирования', 'В процессе разработки', 'Разработан. Готов к использованию.', 'Обновлен', 'Завершен. Не поддерживается'])]

class DB_Manager:
    def __init__(self, database):
        # Инициализация менеджера БД с указанием файла базы данных.
        self.database = database
        
    def create_tables(self):
        # Создание таблиц, если их ещё нет.
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            FOREIGN KEY(project_id) REFERENCES projects(project_id),
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                        )''')
            conn.commit()

    def __executemany(self, sql, data):
        # Выполнение нескольких SQL-запросов INSERT/UPDATE/DELETE за одну транзакцию.
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    def __select_data(self, sql, data=tuple()):
        # Выполнение SELECT-запроса и возврат всех найденных строк.
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
        
    def default_insert(self):
        # Заполнение таблиц skills и status начальными значениями.
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)

    def insert_project(self, data):
        # Добавление одного или нескольких проектов в таблицу projects.
        sql = 'INSERT OR IGNORE INTO projects (user_id, project_name, description, url, status_id) VALUES (?, ?, ?, ?, ?)'
        self.__executemany(sql, data)

    def insert_skill(self, user_id, project_name, skill):
        # Привязка навыка к проекту по имени проекта и id пользователя.
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)

    def get_statuses(self):
        # Получение списка всех статусов проекта.
        sql = 'SELECT status_id, status_name FROM status ORDER BY status_id'
        return self.__select_data(sql)
        
    def get_status_id(self, status_name):
        # Получение id статуса по имени.
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res:
            return res[0][0]
        else:
            return None

    def get_projects(self, user_id):
        # Получение списка проектов для пользователя.
        sql = '''SELECT project_id, project_name, description, url, status_id FROM projects WHERE user_id = ? ORDER BY project_id'''
        return self.__select_data(sql, data=(user_id,))
        
    def get_project_id(self, project_name, user_id):
        # Поиск id проекта по имени и id пользователя.
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?', data=(project_name, user_id,))[0][0]
        
    def get_skills(self):
        # Получение списка всех навыков.
        return self.__select_data(sql='SELECT * FROM skills')
    
    def get_project_skills(self, project_name):
        # Возврат всех навыков, связанных с проектом, в виде строки через запятую.
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
JOIN project_skills ON projects.project_id = project_skills.project_id 
JOIN skills ON skills.skill_id = project_skills.skill_id 
WHERE project_name = ?''', data=(project_name,))
        return ', '.join([x[0] for x in res])
    
    def get_project_info(self, user_id, project_name):
        # Получение информации о проекте вместе со статусом.
        sql = """
SELECT project_name, description, url, status_name FROM projects 
JOIN status ON
status.status_id = projects.status_id
WHERE project_name=? AND user_id=?
"""
        return self.__select_data(sql=sql, data=(project_name, user_id))

    def update_projects(self, param, data):
        # Обновление указанного поля проекта по project_id и user_id.
        sql = f'UPDATE projects SET {param} = ? WHERE user_id = ? AND project_id = ?'
        self.__executemany(sql, [data]) 

    def delete_project(self, user_id, project_id):
        # Удаление проекта из базы данных.
        sql = 'DELETE FROM projects WHERE user_id = ? AND project_id = ?'
        self.__executemany(sql, [(user_id, project_id)])
    
    def delete_skill(self, project_id, skill_id):
        # Удаление навыка из проекта.
        sql = 'DELETE FROM project_skills WHERE project_id = ? AND skill_id = ?'
        self.__executemany(sql, [(project_id, skill_id)])

if __name__ == '__main__':
    # Создаем таблицы и заполняем начальные значения при запуске модуля напрямую.
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()

    