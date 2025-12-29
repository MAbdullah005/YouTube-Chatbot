def evaluate_retrieval(query,retrived_doc):
    relevance=0
    for doc in retrived_doc:
        
        if any(word in doc.lower() for word in query.lower().split()):
            relevance+=1

    return relevance/len(retrived_doc)
