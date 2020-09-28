import joblib
import datetime as dt
from creme import metrics

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
    data, "Models\\teste" + '.gz', compress=('gzip', 3))
print("Took", dt.datetime.now() - time, "seconds to save model")