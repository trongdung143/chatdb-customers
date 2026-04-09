def fix_model_name(usage_records):
    new_records = {}
    for model_name, rec in usage_records.items():
        new_name = model_name[: len(model_name) // 2]
        new_records[new_name] = rec
    return new_records
