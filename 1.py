from typing import List


class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:

        n = len(heights)

        # 构建从左往右的单调栈
        left_k = [-1] * len(heights)
        left_stack = []
        for i, h in enumerate(heights):
            if not left_stack or heights[left_stack[-1]] <= h:
                left_stack.append(i)
            else:
                while left_stack and heights[left_stack[-1]] > h:
                    l_id = left_stack.pop()
                    left_k[l_id] = i - l_id - 1
                left_stack.append(i)


        # 从右到左的单调栈
        right_k = [-1] * len(heights)
        right_stack = []
        for i in range(n-1, -1, -1):
            h = heights[i]
            if not right_stack or heights[right_stack[-1]] <= h:
                right_stack.append(i)
            else:
                while right_stack and heights[right_stack[-1]] > h:
                    l_id = right_stack.pop()
                    right_k[l_id] = l_id - i - 1
                right_stack.append(i)

        # 以每个数为最高点，找左 和 右的小于他的
        ans = 0
        for i, h in enumerate(heights):
            k = 1

            k_r = right_k[i]
            if k_r == -1:
                k += i
            else:
                k += k_r

            k_l = left_k[i]
            if k_l == -1:
                k += n - i - 1
            else:
                k += k_l

            ans = max(h*k, ans)
        return ans
if __name__ == "__main__":
    s = Solution()
    print(s.largestRectangleArea([2,1,5,6,2,3]))