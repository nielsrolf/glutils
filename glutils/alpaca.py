from datasets import load_dataset

def load_alpaca():
    dataset = load_dataset("vicgalle/alpaca-gpt4", split="train")
    dataset = dataset.filter(lambda x: x["input"].strip() == "")
    # Turn into list of dicts that only have the 'instruction' key
    dataset = [{"user_prompt": item["instruction"]} for item in dataset]
    return dataset