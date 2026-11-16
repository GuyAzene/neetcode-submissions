# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        old_head = head
        
        if old_head is None:
            return old_head
            
        while old_head.next != None:
            temp = old_head.next.next
            temp_head = head
            head = old_head.next
            head.next = temp_head
            old_head.next=temp
        return head
