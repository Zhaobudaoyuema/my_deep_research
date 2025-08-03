# my_deep_research
1. langgraph 需要定义state，代表这个流 每个节点的数据传递实体
2. 定义图的时候 还可以加上input 和 output，用于可见性。
3. 时间旅行：通过保存的每一步的输出，作为检查点。和唯一的threadid，可以回滚到之前执行过的一步。
4. 人工介入：执行到该节点就中断，在另外一个地方 使用相同的threaid触发。