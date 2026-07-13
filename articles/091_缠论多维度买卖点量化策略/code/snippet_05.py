class Chan_Strategy:
    def __init__(self, include=True, build_pivot=False):
        self.k_list = []
        self.chan_k_list = []
        self.fx_list = []
        self.stroke_list = []
        self.line_list = []
        self.line_index = {}
        self.line_feature = []
        self.s_feature = []
        self.x_feature = []
        self.pivot_list = []
        self.trend_list = []
        self.buy_list = []
        self.x_buy_list = []
        self.sell_list = []
        self.x_sell_list = []
        self.macd = {}
    def on_bar(self, bar: BarData):
        self.on_period(bar)
    def on_period(self, bar: BarData):
        self.k_list.append(bar)
        if self.include:
            self.on_process_k_include(bar)
        else:
            self.on_process_k_no_include(bar)
    # 其他方法如 on_process_k_include, on_process_fx, on_stroke 等...
