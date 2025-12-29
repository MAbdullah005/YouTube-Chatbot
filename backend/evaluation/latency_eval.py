def latency_eval(llm_time,db_time,total_time):

  metrics = {
     "llm_time": llm_time,
     "db_time":db_time,
     "total_time": total_time
    }
  
  return metrics
