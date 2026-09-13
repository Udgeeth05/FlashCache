from cache.predictive_warmer import PredictiveWarmer


predictor = PredictiveWarmer(
    max_keys=3
)


print("==============================")
print("Predictive Warmer Test")
print("==============================")


# Simulate application traffic

requests = [
    "1",
    "2",
    "1",
    "3",
    "1",
    "2",
    "1",
    "4",
    "2",
    "1"
]


for key in requests:
    predictor.record_access(key)


print("\nAccess counts:")
print(predictor.get_access_counts())


print("\nPredicted hot keys:")
print(predictor.get_hot_keys())


print("\nExpected hot-key order:")
print("['1', '2', '3']")