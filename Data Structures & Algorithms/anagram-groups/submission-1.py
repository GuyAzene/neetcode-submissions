class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        d = {}
        for m in strs:
            letters = [0]*26
            for n in m:
                letters[ord(n)-ord('a')]+=1
            key = tuple(letters)
            if key not in d:
                d[key] = []
            d[key].append(m)
    
        return list(d.values())