class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if len(s)!=len(t):
            return False

        freq_s = {}
        freq_t = {}
        for l in s:
            freq_s[l] = freq_s.get(l, 0)+1
        for l in t:
            freq_t[l] = freq_t.get(l, 0)+1

        for l in s:
            if freq_s.get(l, 0) != freq_t.get(l, 0):
                return False
        return True

