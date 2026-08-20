class SignalEngine:

    def generate(self, spread, spread_mean, params, position_silver, execution_spread):

        # -----------------------------------
        # NO POSITION → ENTRY
        # -----------------------------------
        if position_silver == 0 and execution_spread is None:

            if spread <= spread_mean - params["buy_threshold"]:
                return "BUY"

            if spread >= spread_mean + params["sell_threshold"]:
                return "SELL"

            return None

        # -----------------------------------
        # LONG SPREAD → EXIT
        # -----------------------------------
        if position_silver == 1:

            # target hit
            if spread >= execution_spread + params["target"]:
                return "SELL"

            # stoploss hit
            if spread <= execution_spread - params["stoploss"]:
                return "SELL"

            return None

        # -----------------------------------
        # SHORT SPREAD → EXIT
        # -----------------------------------
        if position_silver == -1:

            # target hit
            if spread <= execution_spread - params["target"]:
                return "BUY"

            # stoploss hit
            if spread >= execution_spread + params["stoploss"]:
                return "BUY"

            return None

        return None