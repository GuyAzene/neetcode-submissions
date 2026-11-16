class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        di = {}
        for i in range(len(nums)):
            if di.get(target-nums[i], -1) != -1:
                return [di[target-nums[i]], i]
            di[nums[i]] = i