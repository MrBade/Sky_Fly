import time
import threading


class MyThread(threading.Thread):
    def __init__(self, func, args, kwargs):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            return None


def print_tips(tips=""):
    def _print_tips(func):
        def warpper(*args, **kwargs):
            print(tips)
            return func(*args, **kwargs)
        return warpper
    return _print_tips


def print_func_process(funcname=""):
    def _print_func_process(func):
        def warpper(*args, **kwargs):
            print(funcname + "Start...", end="  ")
            ret = func(*args, **kwargs)
            print("Done")
            return ret
        return warpper
    return _print_func_process


def cal_time(func):
    def warpper(*args, **kwargs):
        s = time.time()
        ret = func(*args, **kwargs)
        print("The Function expended time is %f" % round(time.time() - s, 4))
        return ret
    return warpper


def thread_dec(func):
    def warpper(*args, **kwargs):
        thread = MyThread(func, args=args, kwargs=kwargs)
        # time.sleep(0.001)
        thread.start()
        # thread.join(1)
        thread_ret = thread.get_result()
        return thread_ret
    return warpper


if __name__ == "__main__":
    @thread_dec
    def a(a, l=1):
        print(a, end=" ")
        time.sleep(0.5)
        print(l)
        time.sleep(0.5)
    s = time.time()
    for i in range(3):
        a(i, l=i+1)
        a(i+2, l=i+3)
    print(time.time() - s)
