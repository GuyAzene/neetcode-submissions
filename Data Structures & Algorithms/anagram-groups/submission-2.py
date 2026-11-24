class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        d = defaultdict(list)
        for m in strs:
            letters = [0]*26
            for n in m:
                letters[ord(n)-ord('a')]+=1
            d[tuple(letters)].append(m)
    
        return list(d.values())