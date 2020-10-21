import joblib
import datetime as dt
from creme import metrics
import sys
""" import resource

def memory_limit():
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 / 2, hard))

def get_memory():
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free_memory += int(sline[1])
    return free_memory """

if __name__ == '__main__':
    #memory_limit() # Limitates maximun memory usage to half
    try:
        time = dt.datetime.now()
        model = joblib.load("ARFRegressionModel")
        print("Took", dt.datetime.now() - time, "seconds to load model")

        dob = dt.datetime.now()
        metrics = {
            "ESPsensormae" : metrics.MAE(),
            "ESPsensorrmse" : metrics.RMSE()
        }
        data = {
            "model": model,
            "date_of_birth": dob,
            "metrics": metrics
        }
        print("Inside save_device Process. Saving device")
        time = dt.datetime.now()
        joblib.dump(
            data, "Models\\teste")
        print("Took", dt.datetime.now() - time, "seconds to save model")
        
    except MemoryError:
        sys.stderr.write('\n\nERROR: Memory Exception\n')
        sys.exit(1)

