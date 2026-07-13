def get_stock_pool():
    index_rank = []
    for index in g.index_pool:
        score = get_socre(index)
        index_rank.append((index, score))
    index_rank = sorted(index_rank, key=lambda x: x[1], reverse=True)
    index_dict = dict(index_rank)
    record(黄金=round(index_dict['518880.XSHG'], 2))
    record(纳指=round(index_dict['513100.XSHG'], 2))
    record(成长=round(index_dict['159915.XSHE'], 2))
    record(价值=round(index_dict['510180.XSHG'], 2))
    return tuple(index[0] for index in index_rank)

复制
