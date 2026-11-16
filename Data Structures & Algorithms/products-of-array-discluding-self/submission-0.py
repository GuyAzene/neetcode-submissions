class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        ## check for 1>0's 
        if nums.count(0) > 1:
            return [0]*len(nums)
        
        if nums.count(0) == 1:
            idx = nums.index(0)
            product = 1
            for i in range(len(nums)):
                if i != idx:
                    product *= nums[i]
            ls = [0]*len(nums)
            ls[idx] = product
            return ls

        product = 1
        for i in range(len(nums)):
            product *= nums[i]
        ls = [product]*len(nums)
        for i in range(len(nums)):
            ls[i] = int(ls[i]/nums[i])
        return ls