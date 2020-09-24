from multiprocessing import Process, Pipe
import time

class Worker(Process):

    def __init__(self):
        self._p_con, self._c_con = Pipe()
        Process.__init__(self, args=self._c_con)
        self.is_running = True
        self.escafia = True


    def test(self, i):
        print("cacacaccacacac + " + i)

    def run(self):
        while self.is_running:
            print ('In %s' % self.name)
            Worker.escafia = False
        return
    
    def get_escafia(self):
        return self.escafia
    
    def stop(self):
        self.is_running=False

if __name__ == '__main__':
    jobs = []
    for i in range(5):
        p = Worker()
        p.daemon = True
        jobs.append(p)
        p.start()
    time.sleep(5)
    for j in jobs:
        print(j.get_escafia())
        j.stop()