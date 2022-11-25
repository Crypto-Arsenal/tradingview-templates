class Strategy(StrategyBase):
    def __init__(self):
        self.period = 60
        self.subscribed_books = {}
        self.options = {}

    def on_tradingview_signal(self, signal, candles):
        exchange, pair, base, quote = CA.get_exchange_pair()

        """
        Calculate New Position
        """
        self.newPositionSize = None

        log = signal.get('log')

        CA.log('📩 TradingView log: ' + str(log))

        items = log.split("/")  # comment/market_position/market_position_size

        if items and len(items) >= 2:
            self.prevTVPositionSide = items[2]
            self.newTVPositionSide = items[1]  # market_position: long, short, flat
        else:
            CA.log('⛔ Invalid signal')
            return

        self.prevCAPositionSize, self.curCAPositionSide = self.get_total_position_size_and_side()

        # Already in sync
        if self.newTVPositionSide == self.curCAPositionSide:
            CA.log('⚠️ Position already synced')
            return

        # Entry Long
        if self.newTVPositionSide == "long":
            if self.curCAPositionSide == "short": # long -> short
                CA.place_order(exchange, pair, action='close_short', conditional_order_type='OTO', percent=100,
                                   child_conditional_orders=[{'action': 'open_long',  'percent': 100}])
            elif self.curCAPositionSide == "flat":  # long -> flat
                CA.place_order(exchange, pair, action='open_long', percent=100)
        # Entry Short
        elif self.newTVPositionSide == "short":
            if self.curCAPositionSide == "long": # short -> long
                    CA.place_order(exchange, pair, action='close_long', conditional_order_type='OTO', percent=100,
                                   child_conditional_orders=[{'action': 'open_short',  'percent': 100}])
            elif self.curCAPositionSide == "flat":  # short -> flat
                CA.place_order(exchange, pair, action='open_short', percent=100)
        # No position
        elif self.newTVPositionSide == "flat":
            if self.curCAPositionSide == "short":  # flat -> short
                CA.place_order(exchange, pair, action='close_short', percent=100)
            elif self.curCAPositionSide == "long":  # flat -> long
                CA.place_order(exchange, pair, action='close_long', percent=100)
        else:
            CA.log("⛔ No action")
            return

    def trade(self, candles):
        pass
    
    def on_order_state_change(self,  order):
        if order.status == CA.OrderStatus.FILLED:
            CA.log('🎉 LATEST POS: ' + str(self.get_total_position_size_and_side()[0]))

        # return current total position: -n 0, +n  where n is number of contracts
    def get_total_position_size_and_side(self):
        exchange, pair, base, quote = CA.get_exchange_pair()

        curTotalPositionSize = None
        total_long_position_size = None
        total_short_position_size = None

        long_position = CA.get_position(exchange, pair, CA.PositionSide.LONG)
        if long_position:
            total_long_position_size = long_position.total_size

        short_position = CA.get_position(exchange, pair, CA.PositionSide.SHORT)
        if short_position:
            total_short_position_size = short_position.total_size

        if total_long_position_size is None and total_short_position_size is None:
            curTotalPositionSize = (0, 'flat')

        if total_long_position_size is not None:
            curTotalPositionSize = (abs(total_long_position_size), 'long')

        if total_short_position_size is not None:
            curTotalPositionSize = (-1 * abs(total_short_position_size), 'short')

        return curTotalPositionSize
