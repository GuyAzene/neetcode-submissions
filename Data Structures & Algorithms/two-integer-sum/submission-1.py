class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        ht = {}
        for index, num in enumerate(nums):
            if target-num in ht.keys():
                return [ht[target-num], index]
            ht[num] = index
            