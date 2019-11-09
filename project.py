import sys
import os
import pymorphy2
import matplotlib.pyplot as plt
import time

from timeutils import Datetime
from timer import MyTimer
from databaseutils import Database, Item, INCOME, EXPANCE

from datetime import datetime, timedelta
from PyQt5 import uic
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime, QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QInputDialog, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QSound, QSoundEffect


MORPH = pymorphy2.MorphAnalyzer()  # переменная для преобразования слов
CONVENTOR = {
    0: 'единоразовый',
    1: 'ежедневный',
    2: 'еженедельный',
    3: 'ежемесячный',
    4: 'ежегодный'
}  # переменная для конвертации типа


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('finances.ui', self)

        self.stack.setCurrentIndex(0)  # установка первой страницы
        self.database = Database('finances.db')  # подключение базы данных

        self.update_main_window()

        self.timer = MyTimer(86400, self.update_data)  # таймер
        self.download_error.hide()
        self.download_success.hide()
        self.help_text.hide()

        # подключение функций
        self.edit_income.clicked.connect(self.edit_incomes_func)
        self.add_income.clicked.connect(self.add_item_func)
        self.edit_expance.clicked.connect(self.edit_expances_func)
        self.add_expance.clicked.connect(self.add_item_func)
        self.back_from_income.clicked.connect(self.go_back)
        self.back_from_expance.clicked.connect(self.go_back)
        self.incomes_list.itemDoubleClicked.connect(self.item_clicked)
        self.expances_list.itemDoubleClicked.connect(self.item_clicked)
        self.edit_budget.clicked.connect(self.edit_budget_func)
        self.plot.clicked.connect(self.plot_expances)
        self.back_from_plot.clicked.connect(self.go_back_to_expances)
        self.download.clicked.connect(self.download_charts)
        self.help.clicked.connect(self.alter_help)

    # функция для справки
    def alter_help(self):
        if self.help.text().endswith('⯈'):
            self.help.setText('справка ⯆')
            self.help_text.show()
        else:
            self.help.setText('справка ⯈')
            self.help_text.hide()

    # добавление элемента (вызывает форму изменения)
    def add_item_func(self):
        self.form = EditForm(self, self.get_current_table())
        self.form.show()

    # меняет текущую страницу
    def edit_incomes_func(self):
        self.stack.setCurrentIndex(1)
        self.update_current_list()

    # меняет текущую страницу
    def edit_expances_func(self):
        self.stack.setCurrentIndex(2)
        self.update_current_list()

    # изменяет элемент, если нажать на него два раза
    def item_clicked(self, item):
        index = self.get_current_list().row(item)
        self.form = EditForm(self, self.get_current_table(), self.items[index])
        self.form.show()

    # удаление элемента при нажатии клавиши delete
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            index = self.get_current_list().currentRow()
            if index != -1:
                self.delete_item(self.items[index])

    # изменение значения бюджета
    def edit_budget_func(self):
        value, ok_button_pressed = QInputDialog.getInt(self, "Введите число",
                                                       "Ваш новый месячный бюджет:",
                                                       self.database.get_month_budget(),
                                                       0, 999999999, 1)
        if ok_button_pressed:
            self.database.set_month_budget(value)
        self.update_main_window()

    # сколько заработано за месяц (сумма)
    def get_month_earned_sum(self):
        items = self.database.get_month_earned()
        return sum([elem.get_sum() for elem in items])

    # сколько потрачено за месяц (сумма)
    def get_month_spent_sum(self):
        items = self.database.get_month_spent()
        return sum([elem.get_sum() for elem in items])

    # обновление главного окна
    def update_main_window(self):
        word = MORPH.parse('рубль')[0]

        result = word.make_agree_with_number(self.get_month_earned_sum()).word
        self.income_label.setText(
            f'Доход: {self.get_month_earned_sum()} {result}')
        self.income_label.adjustSize()

        result = word.make_agree_with_number(self.get_month_spent_sum()).word
        self.expance_label.setText(
            f'Расход: {self.get_month_spent_sum()} {result}')
        self.expance_label.adjustSize()

        self.edit_income.move(
            20 + max(self.income_label.width(), self.expance_label.width()), 45)
        self.edit_expance.move(
            20 + max(self.income_label.width(), self.expance_label.width()), 80)

        result = word.make_agree_with_number(
            self.database.get_month_budget() - self.get_month_spent_sum()).word
        self.budget_label.setText(
            'Остаток бюджета на месяц: ' +
            f'{self.database.get_month_budget() - self.get_month_spent_sum()} {result}')
        self.budget_label.adjustSize()
        self.edit_budget.move(20 + self.budget_label.width(), 10)

    # возвращает на начальную страницу
    def go_back(self):
        self.stack.setCurrentIndex(0)
        self.update_main_window()

    # возвращение на страницу с расходами
    def go_back_to_expances(self):
        self.stack.setCurrentIndex(2)
        self.update_current_list()
        self.download_success.hide()

    # принимает элемент и добавляет/изменяет его в базе данных
    def data_reciever(self, item):
        if item.get_id() is None:
            self.database.add_item(item)
        else:
            self.database.edit_item(item)
        self.update_current_list()

    # обновление текущего списка доходов/расходов
    def update_current_list(self):
        self.get_current_list().clear()
        self.items = self.database.get_total_result(self.get_current_table())
        self.items.sort(key=lambda x: x.get_name())  # сортировка по имени
        self.items.sort(key=lambda x: Datetime(x.get_time()).minute(
            stringed=False))  # сортировка по минутам
        self.items.sort(key=lambda x: Datetime(x.get_time()).hour(
            stringed=False))  # сортировка по часам
        self.items.sort(key=lambda x: Datetime(x.get_time()).day(
            stringed=False))  # сортировка по дням
        for item in self.items:
            word = MORPH.parse('рубль')[0]
            result = word.make_agree_with_number(item.get_sum()).word
            if item.get_type() == 0:
                self.get_current_list().addItem(
                    f'{item.get_name()}, {Datetime(item.get_time()).str_date()}: {item.get_sum()} {result}, {item.get_place()} ({CONVENTOR[item.get_type()]})'
                    if item.get_place() else f'{item.get_name()}, {Datetime(item.get_time()).str_date()}: {item.get_sum()} {result} ({CONVENTOR[item.get_type()]})')
            elif item.get_type() == 1:
                self.get_current_list().addItem(
                    f'{item.get_name()}, каждый день с {Datetime(item.get_time()).year()} года: {item.get_sum()} {result}, {item.get_place()} ({CONVENTOR[item.get_type()]})'
                    if item.get_place() else f'{item.get_name()}, каждый день с {Datetime(item.get_time()).year()} года: {item.get_sum()} {result} ({CONVENTOR[item.get_type()]})')
            elif item.get_type() == 2:
                self.get_current_list().addItem(
                    f'{item.get_name()}, каждый {Datetime(item.get_time()).day()} день недели: {item.get_sum()} {result}, {item.get_place()} ({CONVENTOR[item.get_type()]})'
                    if item.get_place() else f'{item.get_name()}, каждый {Datetime(item.get_time()).day()} день недели: {item.get_sum()} {result} ({CONVENTOR[item.get_type()]})')
            elif item.get_type() == 3:
                self.get_current_list().addItem(
                    f'{item.get_name()}, каждый {Datetime(item.get_time()).day()} день месяца: {item.get_sum()} {result}, {item.get_place()} ({CONVENTOR[item.get_type()]})'
                    if item.get_place() else f'{item.get_name()}, каждый {Datetime(item.get_time()).day()} день месяца: {item.get_sum()} {result} ({CONVENTOR[item.get_type()]})')
            elif item.get_type() == 4:
                self.get_current_list().addItem(
                    f'{item.get_name()}, каждый {Datetime(item.get_time()).day_and_month()} день года: {item.get_sum()} {result}, {item.get_place()} ({CONVENTOR[item.get_type()]})'
                    if item.get_place() else f'{item.get_name()}, каждый {Datetime(item.get_time()).day_and_month()} день года: {item.get_sum()} {result} ({CONVENTOR[item.get_type()]})')

        # обновление дополнительно списка (с поэтапными доходами/расходами)
        self.get_current_month_list().clear()
        items = self.database.get_month_earned() if self.get_current_table(
        ) == INCOME else self.database.get_month_spent()
        for item in reversed(items):
            word = MORPH.parse('рубль')[0]
            result = word.make_agree_with_number(item.get_sum()).word
            self.get_current_month_list().addItem(
                f'{item.get_name()}, {Datetime(item.get_time()).str_date()}: {item.get_sum()} {result}, {item.get_place()}'
                if item.get_place() else f'{item.get_name()}, {Datetime(item.get_time()).str_date()}: {item.get_sum()} {result}')

    # возвращает имя текущей таблицы для работы
    def get_current_table(self):
        if self.stack.currentIndex() == 1:
            return INCOME
        elif self.stack.currentIndex() == 2:
            return EXPANCE

    # возвращает текущий виджет списка
    def get_current_list(self):
        return self.incomes_list if self.get_current_table() == INCOME else self.expances_list

    # возвращает текущий виджет списка с поэтапными расходами
    def get_current_month_list(self):
        return self.month_incomes_list if self.get_current_table() == INCOME else self.month_expances_list

    # удаляет элемент из базы данных
    def delete_item(self, item):
        self.database.delete_item(item)
        self.update_current_list()

    # обнавляет всю информацию. Вызывается каждый день (если программу не закрывать)
    # из-за того, функция выполняется в другом потоке, ей необходима своя собственная база данных
    # (так как нельзя использовать одну и ту же базу данных в разных потоках)
    def update_data(self):
        prev_database = self.database
        self.database = Database('finances.db')
        self.update_current_list()
        self.update_main_window()
        self.database = prev_database

    # построение графика
    def simple_plot(self, widget, labels, sizes, keep=False, name='chart', fmt='png'):
        # красивая пометка на графике
        def get_label(value, total):
            absolute = int(value / 100 * sum(total))
            return f'{round(value, 2)}%\n({absolute} руб.)'

        if labels:
            fig, axes = plt.subplots()
            axes.pie(sizes, labels=labels, autopct=lambda x: get_label(x, sizes),
                     shadow=True, startangle=90)
            axes.axis('equal')
            plt.savefig(name + '.' + fmt, fmt=fmt)

            if widget is not None:
                pixmap = QPixmap(name + '.' + fmt)
                widget.setPixmap(pixmap)
                if not keep:
                    os.remove(name + '.' + fmt)
            else:
                return name + '.' + fmt
        else:
            widget.setText('Нет расходов')

    # получение данных для графика
    def get_chart_data(self, type_):
        if type_ == 'category':
            categories = {
                'другое': 0,
                'еда': 0,
                'одежда': 0,
                'электроника': 0
            }

            for expance in self.database.get_month_spent():
                categories[expance.get_category()] += expance.get_sum()

            labels = [elem for elem in categories.keys()
                      if categories[elem] != 0]
            sizes = [elem for elem in categories.values() if elem != 0]
        elif type_ == 'place':
            places = {'Неизвестно': 0}

            for expance in self.database.get_month_spent():
                if expance.get_place() is not None:
                    if expance.get_place() in places.keys():
                        places[expance.get_place()] += expance.get_sum()
                    else:
                        places[expance.get_place()] = expance.get_sum()
                else:
                    places['Неизвестно'] += expance.get_sum()

            labels = [elem for elem in places.keys() if places[elem] != 0]
            sizes = [elem for elem in places.values() if elem != 0]
        return labels, sizes

    # функция построения графиков расходов
    def plot_expances(self):
        # график расходов по категориям
        labels, sizes = self.get_chart_data('category')
        self.simple_plot(self.pie_chart_1, labels, sizes)

        # график расходов по местам
        labels, sizes = self.get_chart_data('place')
        self.simple_plot(self.pie_chart_2, labels, sizes)

        self.stack.setCurrentIndex(3)

    # скачивает графики
    def download_charts(self):
        try:
            directory = QFileDialog.getExistingDirectory(
                self, 'Выбирете папку для сохранения')
            labels, sizes = self.get_chart_data('category')
            self.simple_plot(None, labels, sizes, keep=True, name='Chart_1')
            os.rename(os.path.dirname(os.path.abspath('Chart_1.png')
                                      ) + '\\Chart_1.png', directory + '/Chart_1.png')

            labels, sizes = self.get_chart_data('place')
            self.simple_plot(None, labels, sizes, keep=True, name='Chart_2')
            os.rename(os.path.dirname(os.path.abspath('Chart_2.png')
                                      ) + '\\Chart_2.png', directory + '/Chart_2.png')
        except FileExistsError:
            self.download_error.show()
            self.download_success.hide()
        else:
            self.download_error.hide()
            self.download_success.show()

    # остановка таймера при выходе из программы
    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


class EditForm(QWidget):
    def __init__(self, main_window, form_type, item=None):
        super().__init__()
        uic.loadUi('edit_form.ui', self)
        self.main_window = main_window
        self.form_type = form_type
        self.item = item

        # делаем списки с полями ввобда и заполняем их
        self.times = []
        self.places = []

        for i in range(5):
            exec(f"self.times.append(self.time_{i})")
            exec(f"self.places.append(self.place_{i})")

        # подключаем функции
        self.delete_button.clicked.connect(self.delete_item)
        self.ok.clicked.connect(self.share_data)
        self.back.clicked.connect(self.hide)
        self.addition_button.clicked.connect(self.alter_addition)
        self.type.currentIndexChanged.connect(self.update_stack)

        # меняем названия на нужные
        self.setWindowTitle(
            'Изменение дохода' if self.form_type == INCOME else 'Изменение расхода')
        self.title.setText(
            'Изменение дохода' if self.form_type == INCOME else 'Изменение расхода')
        self.sum_label.setText(
            'Сумма дохода' if self.form_type == INCOME else 'Сумма расхода')
        self.type_label.setText(
            'Тип дохода' if self.form_type == INCOME else 'Тип расхода')
        self.delete_button.setText(
            'Удалить доход' if self.form_type == INCOME else 'Удалить расход')

        # прячем ненужное
        if self.form_type == INCOME:
            self.category_label.hide()
            self.category.hide()
        self.stack.hide()
        if self.item is None:
            self.delete_button.hide()
        self.name_error_label.hide()
        self.sum_error_label.hide()

        # добавляем информацию об элементе, если он был передан
        if self.item:
            self.name.setText(self.item.get_name())
            self.item_sum.setValue(self.item.get_sum())
            self.type.setCurrentIndex(self.item.get_type())
            if item.get_category():
                self.category.setCurrentIndex(
                    self.category.findText(item.get_category()))
            for elem in self.times:
                elem.setDateTime(Datetime(self.item.get_time()).qt())
            if item.get_place():
                for place in self.places:
                    place.setText(str(self.item.get_place()))
        # если нет, то все поля будут пустыми, а в поле времени будет настоящее время
        else:
            for elem in self.times:
                elem.setDateTime(Datetime('now').qt())

        # отдельно заполнить день недели
        self.time_2.setDateTime(Datetime(Datetime('now').year() + '-'
                                         + Datetime('now').month(fill_zeroes=True) + '-0'
                                         + str(Datetime('now').python().isoweekday())).qt())

    # Отправляет запрос на удаление элемента в главное окно
    def delete_item(self):
        self.main_window.delete_item(self.item)
        self.hide()

    # отправка информации об новом/изменённом элементе
    def share_data(self):
        # если есть ошибки в заполнении формы, то показать их и не отправлять данные
        error = False
        if self.name.text() == '':  # нет названия
            self.name_error_label.show()
            error = True
        else:
            self.name_error_label.hide()
        if self.item_sum.value() == 0:  # сумма 0
            self.sum_error_label.show()
            error = True
        else:
            self.sum_error_label.hide()
        if error:
            return

        data = [
            # id (None если это первое создание элемента)
            self.item.get_id() if self.item else None,
            self.name.text(),  # название
            self.item_sum.value(),  # сумма
            self.type.currentIndex(),  # тип
            # категория (None если доход)
            None if self.form_type == INCOME else self.category.currentText(),
            Datetime(self.times[self.type.currentIndex()
                                ].dateTime()).python().date(),  # время
            self.places[self.type.currentIndex()].text()\
            if self.places[self.type.currentIndex()].text() else None  # место (None если не введено)
        ]
        self.main_window.data_reciever(Item(data))  # отправляем данные
        self.hide()  # прячем форму

    # показывает/убирает дополнительную информацию
    def alter_addition(self):
        self.update_stack()
        if self.stack.isHidden():
            self.stack.show()
            self.addition_button.setText('Дополнительно ⯆')
        else:
            self.stack.hide()
            self.addition_button.setText('Дополнительно ⯈')

    # обнавляет список дополнительной информации
    def update_stack(self):
        self.stack.setCurrentIndex(self.type.currentIndex())


def main():
    app = QApplication(sys.argv)
    project = MainWindow()
    project.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
