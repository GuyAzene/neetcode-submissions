# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        t_ls = ListNode()
        head = t_ls
        while list1 or list2:
            if not list1 or list2 and list2.val <= list1.val:
                t_ls.next = list2
                list2 = list2.next
                t_ls = t_ls.next
            elif not list2 or list1 and list1.val <= list2.val:
                t_ls.next = list1
                list1 = list1.next
                t_ls = t_ls.next
        return head.next

