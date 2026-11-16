class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        dic_r = {}
        dic_c = {}
        dic_s = {}
        for row in range(len(board)):
            for col in range(len(board)):
                # row = row
                # col = col
                # subbox = (int(row/3)+1, int(col/3)+1)
                if board[row][col] == ".":
                    continue
                if (row, board[row][col]) in dic_r or (col, board[row][col]) in dic_c or (int(row/3)+1, int(col/3)+1 , board[row][col]) in dic_s:
                   return False
                
                dic_r[(row, board[row][col])] = 1
                dic_c[(col, board[row][col])] = 1
                dic_s[(int(row/3)+1, int(col/3)+1 , board[row][col])] = 1
        return True