class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        dic_r = set()
        dic_c = set()
        dic_s = set()
        for row in range(len(board)):
            for col in range(len(board)):
                # row = row
                # col = col
                # subbox = (int(row/3)+1, int(col/3)+1)
                if board[row][col] == ".":
                    continue
                if (row, board[row][col]) in dic_r or (col, board[row][col]) in dic_c or (int(row/3)+1, int(col/3)+1 , board[row][col]) in dic_s:
                   return False
                
                dic_r.add((row, board[row][col]))
                dic_c.add((col, board[row][col]))
                dic_s.add((int(row/3)+1, int(col/3)+1 , board[row][col]))
        return True