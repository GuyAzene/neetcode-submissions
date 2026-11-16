class Solution:
    def hasDuplicate(self, nums: List[int]) -> bool:
        dupes = {}
        for i in nums:
            if dupes.get(i,0) == 1:
                return True
            dupes[i] = 1
        return False
        