from gemini_backend_deep_research.graph import graph

state = graph.invoke({"messages": [{"role": "user", "content": "介绍一下故宫"}], "max_research_loops": 3,
                      "initial_search_query_count": 3})
