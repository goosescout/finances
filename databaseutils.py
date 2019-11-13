import sqlite3
from datetime import datetime
from timeutils import Datetime


# классы для работой с базой данных


# константы с названиями
INCOME = 'Incomes'
EXPANCE = 'Expances'


class Database:
    def __init__(self, name):
        self.connection = sqlite3.connect(name)
        self.cursor = self.connection.cursor()

    # возвращает всех список доходов/расходов как экземпляры класса Item
    def get_total_result(self, table):
        result = self.cursor.execute(f'SELECT * FROM {table}').fetchall()
        return list(map(lambda x: Item(x), result))

    # добавляет элемент в таблицу, принимает на вход экземпляр класса Item
    def add_item(self, item):
        self.cursor.execute(f"""INSERT INTO {item.income_or_expance()}(name, item_sum, type, category, time, place)
        VALUES(?, ?, ?, ?, ?, ?)""", item.get_list())
        self.connection.commit()

    # изменяет элемент в таблице, принимает на вход экземпляр класса Item
    def edit_item(self, item):
        self.cursor.execute(f"""UPDATE {item.income_or_expance()}
        SET name = ?, item_sum = ?, type = ?, category = ?, time = ?, place = ?
        WHERE id = ?""", item.get_list(include_id=True))
        self.connection.commit()

    # удаляет элемент из таблицы, принимает на вход экземпляр класса Item
    def delete_item(self, item):
        self.cursor.execute(f"""DELETE FROM {item.income_or_expance()}
        WHERE id = ?""", (item.get_id(),))
        self.connection.commit()

    # получение бюджета на месяц
    def get_month_budget(self):
        result = self.cursor.execute(
            "SELECT month_budget FROM Other").fetchall()
        return result[0][0]

    # устанавливает бюджет на месяц
    def set_month_budget(self, value):
        self.cursor.execute(f"""UPDATE Other
        SET month_budget = ?""", (value,))
        self.connection.commit()

    # возвращает список с доходами за месяц
    def get_month_earned(self):
        result = []
        for i in range(1, int(Datetime('now').day()) + 1):
            i = '0' * (2 - len(str(i))) + str(i)
            cur_date = Datetime(Datetime('now').year() +
                                '-' + Datetime('now').month() + '-' + i)
            for income in self.get_total_result(INCOME):
                if ((income.get_type() == 0 and income.get_time() == cur_date.str_db_date()) or
                    (income.get_type() == 1 and int(Datetime(income.get_time()).year()) >= int(cur_date.year())) or
                    (income.get_type() == 2 and int(Datetime(income.get_time()).day()) == cur_date.python().isoweekday()) or
                    (income.get_type() == 3 and int(Datetime(income.get_time()).day()) == int(cur_date.day())) or
                        (income.get_type() == 3 and int(Datetime(income.get_time()).day()) == int(cur_date.day()) and
                         int(Datetime(income.get_time()).month()) == int(cur_date.month()))):
                    income.time = cur_date
                    result.append(income)
        return result

    # возвращает список с расходами за месяц
    def get_month_spent(self):
        result = []
        for i in range(1, int(Datetime('now').day()) + 1):
            i = '0' * (2 - len(str(i))) + str(i)
            cur_date = Datetime(Datetime('now').year() +
                                '-' + Datetime('now').month() + '-' + i)
            for expance in self.get_total_result(EXPANCE):
                if ((expance.get_type() == 0 and expance.get_time() == cur_date.str_db_date()) or
                    (expance.get_type() == 1 and int(Datetime(expance.get_time()).year()) >= int(cur_date.year())) or
                    (expance.get_type() == 2 and int(Datetime(expance.get_time()).day()) == cur_date.python().isoweekday()) or
                    (expance.get_type() == 3 and int(Datetime(expance.get_time()).day()) == int(cur_date.day())) or
                        (expance.get_type() == 3 and int(Datetime(expance.get_time()).day()) == int(cur_date.day()) and
                         int(Datetime(expance.get_time()).month()) == int(cur_date.month()))):
                    expance.time = cur_date
                    result.append(expance)
        return result

    # получнение строки типа предмета
    def get_type(self, item):
        result = self.cursor.execute(
            "SELECT name FROM Types WHERE id = ?", (item.get_type(),)).fetchall()
        return result[0][0]

class Item:
    def __init__(self, values):
        self.id_ = values[0]
        self.name = str(values[1])
        self.sum_ = int(values[2])
        self.type_ = int(values[3])
        self.category = values[4]
        self.time = values[5]
        self.place = values[6]

    # получение типа (доход или расход)
    def income_or_expance(self):
        return INCOME if self.category is None else EXPANCE

    # получение id
    def get_id(self):
        return self.id_

    # получение названия
    def get_name(self):
        return self.name

    # получение суммы
    def get_sum(self):
        return self.sum_

    # получение типа
    def get_type(self):
        return self.type_

    # получение категории
    def get_category(self):
        return self.category

    # получение времени
    def get_time(self):
        return self.time

    # получение места
    def get_place(self):
        return self.place

    # получение списка со всеми значениями (id можно включить или выключить)
    def get_list(self, include_id=False):
        return [self.name, self.sum_, self.type_, self.category, self.time, self.place, self.id_]\
            if include_id else [self.name, self.sum_, self.type_, self.category, self.time, self.place]

    def __str__(self):
        return ', '.join(map(str, [self.name, self.sum_, self.type_, self.category, self.time, self.place, self.id_]))
