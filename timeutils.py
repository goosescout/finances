from PyQt5.QtCore import QDateTime, QDate, QTime
from datetime import datetime


# класс для работы с датой и временем


class Datetime:
    # создание экземпляра класса
    def __init__(self, time):
        if isinstance(time, QDateTime):
            self.python_time = self.convert_to_python(time)
            self.qt_time = time
        elif isinstance(time, datetime):
            self.python_time = time
            self.qt_time = self.convert_to_qt(time)
        elif isinstance(time, str):
            if time == 'now':
                self.python_time = Datetime(datetime.now()).python_time
                self.qt_time = Datetime(datetime.now()).qt_time
            else:
                self.python_time = self.convert_str_to_python(time)
                self.qt_time = self.convert_to_qt(self.python_time)
        elif isinstance(time, Datetime):
            self.python_time = time.python_time
            self.qt_time = time.qt_time
        else:
            raise ValueError(f'''Wrong input time (it must be datetime, QDateTime, or datetime-like str.)
Your input: {time}, (class: {time.__class__})''')

    # конвертация в тип python (класс datetime)
    def convert_to_qt(self, input_time):
        '''
        requires Python datetime class instance or string like '%Y-%m-%d %H:%M:%S'
        returns Qt DateTime class instance
        '''
        date, time = str(input_time).split()
        cur_year, cur_month, cur_day = map(int, date.split('-')[:3])
        cur_hour, cur_minute = map(int, time.split(':')[:2])
        value = QDateTime()
        value.setDate(QDate(cur_year, cur_month, cur_day))
        value.setTime(QTime(cur_hour, cur_minute))
        return value

    # конвертация в тип qt (QDateTime)
    def convert_to_python(self, input_time):
        '''
        requires Qt DateTime class instance
        returns Python datetime class instance
        '''
        date = input_time.date()
        time = input_time.time()
        return datetime(date.year(), date.month(), date.day(), time.hour(), time.minute(), 0, 0)

    # конвертация строки в тип python (класс datetime)
    def convert_str_to_python(self, input_str):
        '''
        requires string like '%Y-%m-%d %H:%M:%S' or '%d.%m.%Y %H:%M or %Y-%m-%d'
        returns Python datetime class instance
        '''
        try:
            return datetime.strptime(input_str, '%Y-%m-%d')
        except ValueError:
            try:
                return datetime.strptime(input_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return datetime.strptime(input_str, '%d.%m.%Y %H:%M')

    # возвращает год
    def year(self, stringed=True):
        return str(self.qt_time.date().year()) if stringed else int(self.qt_time.date().year())

    # возвращает месяц
    def month(self, stringed=True, fill_zeroes=False):
        if not fill_zeroes:
            return str(self.qt_time.date().month()) if stringed else int(self.qt_time.date().month())
        else:
            return '0' * (2 - len(str(self.qt_time.date().month()))) + str(self.qt_time.date().month())

    # возвращает день
    def day(self, stringed=True, fill_zeroes=False):
        if not fill_zeroes:
            return str(self.qt_time.date().day()) if stringed else int(self.qt_time.date().day())
        else:
            return '0' * (2 - len(str(self.qt_time.date().day()))) + str(self.qt_time.date().day())

    # возвращает час
    def hour(self, stringed=True, fill_zeroes=False):
        if not fill_zeroes:
            return str(self.qt_time.time().hour()) if stringed else int(self.qt_time.time().hour())
        else:
            return '0' * (2 - len(str(self.qt_time.time().hour()))) + str(self.qt_time.time().hour())

    # возвращает минуту
    def minute(self, stringed=True, fill_zeroes=False):
        if not fill_zeroes:
            return str(self.qt_time.time().minute()) if stringed else int(self.qt_time.time().minute())
        else:
            return '0' * (2 - len(str(self.qt_time.time().minute()))) + str(self.qt_time.time().minute())

    # возвращает QDateTime от данного времени
    def qt(self):
        return self.qt_time

    # возвращает datetime от данного времени
    def python(self):
        return self.python_time

    # возвращает красивую строку с представлением данного времени
    def __str__(self):
        return f'{self.day(fill_zeroes=True)}.{self.month(fill_zeroes=True)}.{self.year()} ' +\
            f'{self.hour(fill_zeroes=True)}:{self.minute(fill_zeroes=True)}'

    # возвращает строку со временем
    def str_time(self):
        return f'{self.hour(fill_zeroes=True)}:{self.minute()}'

    # возвращает строку с датой
    def str_date(self):
        return f'{self.day(fill_zeroes=True)}.{self.month(fill_zeroes=True)}.{self.year()}'

    # возвращает строку с датой, которая используетсся в базе данных (DATE)
    def str_db_date(self):
        return self.year() + '-' + self.month(fill_zeroes=True) + '-' + self.day(fill_zeroes=True)

    # возвращает строку с днем и месяцем
    def day_and_month(self):
        return self.day(fill_zeroes=True) + '.' + self.day(fill_zeroes=True)
