import yaml, os
cfg = {}
cfg["window_step_ms"] = 10
cfg["train_dir"] = "/w/trained/hey_donut"
cfg["features"] = [
    # our wake word
    {"features_dir": "/w/features/positive", "sampling_weight": 2.0,
     "penalty_weight": 1.0, "truth": True, "truncation_strategy": "truncate_start", "type": "mmap"},
    # near-misses: donut / donuts / do not / doughnut / hey donna ...
    {"features_dir": "/w/features/adversarial", "sampling_weight": 4.0,
     "penalty_weight": 1.0, "truth": False, "truncation_strategy": "truncate_start", "type": "mmap"},
    # general negatives
    {"features_dir": "/w/negatives/speech/speech", "sampling_weight": 10.0,
     "penalty_weight": 1.0, "truth": False, "truncation_strategy": "random", "type": "mmap"},
    {"features_dir": "/w/negatives/dinner_party/dinner_party", "sampling_weight": 10.0,
     "penalty_weight": 1.0, "truth": False, "truncation_strategy": "random", "type": "mmap"},
    {"features_dir": "/w/negatives/no_speech/no_speech", "sampling_weight": 5.0,
     "penalty_weight": 1.0, "truth": False, "truncation_strategy": "random", "type": "mmap"},
    # validation/testing ambient only
    {"features_dir": "/w/negatives/dinner_party_eval/dinner_party_eval", "sampling_weight": 0.0,
     "penalty_weight": 1.0, "truth": False, "truncation_strategy": "split", "type": "mmap"},
]
cfg["training_steps"] = [10000]
cfg["positive_class_weight"] = [1]
cfg["negative_class_weight"] = [20]
cfg["learning_rates"] = [0.001]
cfg["batch_size"] = 128
cfg["time_mask_max_size"] = [0]; cfg["time_mask_count"] = [0]
cfg["freq_mask_max_size"] = [0]; cfg["freq_mask_count"] = [0]
cfg["eval_step_interval"] = 500
cfg["clip_duration_ms"] = 1500
cfg["target_minimization"] = 0.9
cfg["minimization_metric"] = None
cfg["maximization_metric"] = "average_viable_recall"
os.makedirs("/w/trained", exist_ok=True)
with open("/w/training_parameters.yaml", "w") as f:
    yaml.dump(cfg, f)
print("  config written")
for feat in cfg["features"]:
    d = feat["features_dir"]
    subs = [s for s in os.listdir(d)] if os.path.isdir(d) else ["MISSING"]
    print(f"   {os.path.basename(d):22} {subs}")
