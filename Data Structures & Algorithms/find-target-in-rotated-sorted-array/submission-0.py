class Solution:
    def search(self, nums: List[int], target: int) -> int:
        #[3,4,5][6,1,2]
        st = 0
        en = len(nums)-1
        while en > st:
            half = (en+st)//2
            left_h = half
            right_h = half+1
            
            if nums[st] <= nums[left_h]:
                if nums[st] <= target <= nums[left_h]:
                    en = left_h
                else:
                    st = right_h

            else:
                if nums[right_h] <= target <= nums[en]:
                    st = right_h
                else:
                    en = left_h
            
        return st if nums[st] == target else -1