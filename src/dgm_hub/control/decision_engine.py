class DecisionEngine:

    def should_continue(self, iteration, success, error_rate):
        if success:
            return False

        if iteration >= 3:
            return False

        if error_rate > 0.7:
            return False

        return True
