def normalize_usage(model_name: str, raw) -> dict:
    if raw.usage_metadata:
        raw_usage = dict(raw.usage_metadata)

        input_details = raw_usage.pop("input_token_details", {}) or {}
        output_details = raw_usage.pop("output_token_details", {}) or {}

        raw_usage["input_token_details"] = {
            "audio": 0,
            "cache_read": input_details.get("cache_read", 0),
        }
        raw_usage["output_token_details"] = {
            "audio": 0,
            "reasoning": output_details.get("reasoning", 0),
        }

        return {
            model_name: raw_usage,
        }

    token_usage = raw.response_metadata["token_usage"]
    return {
        model_name: {
            "input_tokens": token_usage["prompt_tokens"],
            "output_tokens": token_usage["completion_tokens"],
            "total_tokens": token_usage["total_tokens"],
            "input_token_details": {
                "audio": 0,
                "cache_read": token_usage["prompt_tokens_details"].get(
                    "cached_tokens", 0
                ),
            },
            "output_token_details": {
                "audio": 0,
                "reasoning": token_usage["completion_tokens_details"].get(
                    "reasoning_tokens", 0
                ),
            },
        }
    }


def merge_usage(u1, u2):
    result = {}

    models = set(u1.keys()) | set(u2.keys())

    for model in models:
        if model not in u1:

            result[model] = u2[model].copy()
            result[model]["input_token_details"] = u2[model][
                "input_token_details"
            ].copy()
            result[model]["output_token_details"] = u2[model][
                "output_token_details"
            ].copy()
            continue

        if model not in u2:

            result[model] = u1[model].copy()
            result[model]["input_token_details"] = u1[model][
                "input_token_details"
            ].copy()
            result[model]["output_token_details"] = u1[model][
                "output_token_details"
            ].copy()
            continue

        m1 = u1[model]
        m2 = u2[model]

        result[model] = {
            "input_tokens": m1.get("input_tokens", 0) + m2.get("input_tokens", 0),
            "output_tokens": m1.get("output_tokens", 0) + m2.get("output_tokens", 0),
            "total_tokens": m1.get("total_tokens", 0) + m2.get("total_tokens", 0),
            "input_token_details": {
                "audio": m1.get("input_token_details", {}).get("audio", 0)
                + m2.get("input_token_details", {}).get("audio", 0),
                "cache_read": m1.get("input_token_details", {}).get("cache_read", 0)
                + m2.get("input_token_details", {}).get("cache_read", 0),
            },
            "output_token_details": {
                "audio": m1.get("output_token_details", {}).get("audio", 0)
                + m2.get("output_token_details", {}).get("audio", 0),
                "reasoning": m1.get("output_token_details", {}).get("reasoning", 0)
                + m2.get("output_token_details", {}).get("reasoning", 0),
            },
        }

    return result


def response_detail(response):
    return response.get("raw"), response.get("parsed")
