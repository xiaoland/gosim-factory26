增量assistant语义流：由inventory needs_new_read的base/A/B/C逐记录提取全部assistant text/thinking，保留原path/line/msgID；工具参数仅前300字符供导航，不是完整动作阅读，工具结果须回原件。按timestamp+prose+工具导航指纹去重复响应；源文件仍全部保留。该提取本身不等于语义阅读。
