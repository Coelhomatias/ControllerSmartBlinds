from multiprocessing import Process, Pipe
import time

class Worker(Process):

    def __init__(self):
        Process.__init__(self)
        self.is_running = True
        self.escafia = True

    def run(self):
        while self.is_running:
            print ('In %s' % self.name)
            self.set_escafia()
        return
    
    def set_escafia(self):
        self.escafia = False

    def get_escafia(self):
        return self.escafia

if __name__ == '__main__':
    p = Worker()
    p.start()
    time.sleep(1)
    print(p.get_escafia())
    p.terminate()
    p.join()
    print(p.get_escafia())
    p.start()
    p.terminate()
    p.join()
