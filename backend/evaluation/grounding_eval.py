def evaluation_grounding(answer,context):
    overlap=set(answer.lower().split()) & set(context.lower().split())

    return len(overlap)/max(len(answer.split()),1)