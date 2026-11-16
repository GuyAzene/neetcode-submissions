class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        freq_d = {}
        for st in strs:
            freq = [0]*26
            for ch in st:
                freq[ord(ch)-ord('a')]+=1
            key = tuple(freq)
            if key not in freq_d:
                freq_d[key] = []
            freq_d[key].append(st)
        return list(freq_d.values())