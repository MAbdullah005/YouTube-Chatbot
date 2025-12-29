def llm_faithfullness_eval(llm,context,answer):
    eval_prompt = f"""
    CONTEXT:
    {context}

    ANSWER:
    {answer}

    Is the answer fully Supported the by the context?
    Reply YES or NO.
    """
    result = llm.invoke(eval_prompt)
    return result.content.strip()