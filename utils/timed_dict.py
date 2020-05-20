from threading import Timer
from time import sleep
from utils.utils import myprint as print


# Stores the results and removes them after `secs` seconds
class TimedDict(dict):
    def __init__(self, secs=1, exclude=None):
        if exclude is None:
            self.exclude = tuple()
        else:
            try:
                self.exclude = tuple(exclude)
            except TypeError:
                self.exclude = exclude
        self.secs = secs
        self.threads = {}
        
    def close(self):
        for thread in self.threads.values():
            thread.cancel()
    
    def __setitem__(self, key, value):
        if key in self.threads:
            self.threads[key].cancel()
            print(f'Updated value of {key}', 'New keys:', list(self.threads.keys()))
        else:
            print(f'Stored value of {key}', 'New keys', list(self.threads.keys()) + [key])
        if not isinstance(value, self.exclude):
            thread = Timer(self.secs, self.timeout, (key,))
            thread.setDaemon(True)
            thread.start()
            self.threads[key] = thread
        return super().__setitem__(key, value)
    
    def timeout(self, key):
        del self.threads[key]
        print(f'Removed value of {key}', list(self.threads.keys()))
        super().__delitem__(key)
    
    def __delitem__(self, key):
        if isinstance(self[key], self.exclude):
            return super().__delitem__(key)
        

if __name__ == '__main__':
    res = TimedDict(7)
    res['A'] = 5
    sleep(3)
    print(res, res.threads)
    res['A'] = 6
    sleep(3)
    print(res, res.threads)
    res['A'] = 7
    sleep(3)
    print(res, res.threads)
    res['B'] = 3
    sleep(3)
    print(res, res.threads)
    sleep(3)
    print(res, res.threads)
    sleep(3)
    print(res, res.threads)
    sleep(3)
    print(res, res.threads)
    sleep(3)
    print(res, res.threads)
    res.close()