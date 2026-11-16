class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        profit = 0
        min_saw = prices[0]
        max_saw = prices[0]
        for i in range(len(prices)):
            if(prices[i]-min_saw>=profit):
                max_saw = prices[i]
                profit = max_saw - min_saw
            if(prices[i]<=min_saw):
                min_saw = prices[i]
        return profit