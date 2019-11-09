from threading import Timer


# класс таймера, который выполняет определенную функцию в отдельном потоке


class MyTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self.timer_ = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    # функция, которая запускает сама себя через интервал
    def run_(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    # функция старта
    def start(self):
        if not self.is_running:
            self.timer_ = Timer(self.interval, self.run_)
            self.timer_.start()
            self.is_running = True

    # функция остановки
    def stop(self):
        self.timer_.cancel()
        self.is_running = False