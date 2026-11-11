def problem_one():
    L = [73, 74, 75, 71, 69, 72, 76, 73]
    result = []
    for i in range(len(L)): 
        x = L[i]
        c = [] 
        for q in range(i + 1, len(L)):
            if L[q] > x: 
                c.append(q)
        if c:
            result.append(min(c) - i)
        else:
            result.append(0)
    return result

def problem_two():
    nums = [2, 7, 11, 15]
    target = 13
    correctList = []
    for i in range(len(nums)):
        x = nums[i]
        for q in range(i + 1, len(nums)):
            if x + nums[q] == target:
                correctList.append(i)
                correctList.append(q)
    return correctList

def problem_three():
    string = "abcabcdehja"
    best = 0
    for i in range(len(string)):
        seen = set()
        for r in range(i, len(string)):
            if string[r] in seen:
                break
            else:
                seen.add(string[r])
        best = max(best, len(seen))
    return best

def problem_four():
    string = "[{[{[{(((((())))))}]}]}]"
    stack = []
    for i in range(len(string)):
        if string[i] == "{" or string[i] == "[" or string[i] == "(":
            stack.append(string[i])
        elif string[i] == "}" or string[i] == "]" or string[i] == ")":
            if string[i] == "}" and len(stack) > 0 and stack[-1] == "{":
                stack.pop()
            elif string[i] == "]" and len(stack) > 0 and stack[-1] == "[":
                stack.pop()
            elif string[i] == ")" and len(stack) > 0 and stack[-1] == "(":
                stack.pop()
            else:
                return("Invalid")
    if len(stack) == 0:
        return("Valid")
    else:
        return("Invalid")

def problem_five():
    Intervals = [[8,10],[15,18],[1,3],[2,6]]
    Intervals.sort(key = lambda x: x[0])
    result = [Intervals[0]]
    for i in range(1, len(Intervals)):
        if Intervals[i][0] <= result[-1][1]:
            result[-1][1] = max(result[-1][1], Intervals[i][1])
        else:
            result.append(Intervals[i])
    return(result)

def problem_six():
    heights = [1,8,6,2,5,4,8,3,7]
    list = []
    for i in range(len(heights)):
        z = heights[i]
        for q in range(len(heights)):
            x = q - i
            y = x * min((heights[q], heights[i]))
            list.append(y)
    return(max(list))

def problem_seven():
    array = [-1, 0, 1, 2, -1, -4]
    triplets = []
    seen = set()
    for i in range(len(array)):
        num1 = array[i]
        for q in range(len(array)):
            num2 = array[q]
            for x in range(len(array)):
                num3 = array[x]
                if i != q and q != x and i != x:
                    if num1 + num2 + num3 == 0:
                        triplet = sorted((num1, num2, num3))
                        triplets.append(triplet)
    for w in reversed(range(len(triplets))):
        for p in reversed(range(w)): 
            if triplets[w] == triplets[p]:
                del triplets[w]
                break
    return(triplets)

def problem_eight():
    array = ["eat","tea","tan","ate","nat","bat"]
    a = {}
    for i in range(len(array)):
        key = "".join(sorted(array[i]))
        if key in a:
            a[key].append(array[i])
        else:
            a[key] = [array[i]]
    return(a)

def binary_search():
    nums = [-1, 0, 3, 5, 9, 12]
    target = 12
    low = 0
    high = len(nums) - 1
    while low <= high:
        middle = (low + high) // 2
        if nums[middle] == target:
            return middle
        if nums[middle] > target:
            high = middle - 1
        if nums[middle] < target:
            low = middle + 1

def fluency_pass():
    # brute force O(n^2) - could optimize to O(n) with Kadane's Algorithm
    array = [-2,1,-3,4,-1,2,1,-5,4]
    sums = []
    for i in range(len(array)):
        for x in range(i, len(array)):
            s = sum(array[i:x+1])
            sums.append(s)
    return max(sums)

def kadane():
    array = [-2,1,-3,4,-1,2,1,-5,4]
    current_sum = array[0]
    best_sum = array[0]
    for i in range(1, len(array)):
        current_sum = max(array[i], current_sum + array[i])
        best_sum = max(best_sum, current_sum)
    return best_sum

def trees():
    class TreeNode:
        def __init__(self, value):
            self.value = value
            self.right = None
            self.left = None

    a = TreeNode(5)
    a.right = TreeNode(8)
    a.left = TreeNode(3)
    a.left.right = TreeNode(4)
    a.left.left = TreeNode(1)

    b = TreeNode(10)
    b.right = TreeNode(15)
    b.right.right = TreeNode(20)
    b.left = TreeNode(6)
    b.left.right = TreeNode(8)
    b.left.left = TreeNode(4)

    def inorder(node):
        if node is None:
            return 
        inorder(node.left)
        print(node.value)
        inorder(node.right)

    return inorder(b)

def recursion(n):
    if n == 0:
        return 1
    return n * recursion(n - 1)

def treepractice():
    class tree():
        def __init__(self, value):
            self.value = value
            self.right = None
            self.left = None

    test = tree(2)
    test.right = tree(3)
    test.left = tree(4)

    def trees(node):
        if node is None:
            return
        trees(node.left)
        print(node.value)
        trees(node.right)

    return trees(test)

def graphs():
    graph = {
        "A": ["B", "C"],
        "B": ["A", "D"],
        "C": ["A"],
        "D": ["B"]
    } 
    def dfs(graph, node, visited):
        if node in visited:
            return
        visited.add(node)
        print(node)
        for neighbor in graph[node]:
            dfs(graph, neighbor, visited)

    return(dfs(graph, "A", set()))

def two_sum():
    nums = [2, 7, 10, 15, 9, 8, 18]
    target = 12
    seen = {}
    for i in range(len(nums)):
        complement = target - nums[i]
        if complement in seen:
            return [seen[complement], i]
        else:
            seen[nums[i]] = i

def sliding_window():
    nums = [2, 1, 5, 1, 3, 2]
    list = []
    k = 3
    x = sum(nums[:k])
    list.append(x)
    for i in range(k, len(nums)):
        x = x + nums[i] - nums[i - k]
        list.append(x)
    return max(list)
        
    # for i in range(len(nums)):
    #    x = sum(nums[i:k])
    #    list.append(x)
    #    k = k+1
    # return max(list)

def longest_substring(s=["a", "a", "b", "d", "v", "d", "f", "c", "d", "a", "b", "c"]):
    # O(n): one pass, left only moves forward, dict remembers each character's last index
    last_seen = {}
    left = 0
    best = 0
    for right in range(len(s)):
        if s[right] in last_seen and last_seen[s[right]] >= left:
            left = last_seen[s[right]] + 1
        last_seen[s[right]] = right
        best = max(best, right - left + 1)
    return best
    
def variable_size():
    pass

def island_number():
    grid = [
        ["1","1","0","0","0"],
        ["1","1","0","0","0"],
        ["0","0","1","0","0"],
        ["0","0","0","1","1"]
    ]
    def get_neighbors(row, col, grid):
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        for dr, dc in directions:
            r = row + dr
            c = col + dc
            if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                neighbors.append((r, c))
        return neighbors

    def dfs(row, col, grid, visited):
        if (row, col) in visited:
            return
        visited.add((row, col))
        for r, c in get_neighbors(row, col, grid):
            if grid[r][c] == "1" and (r, c) not in visited:
                dfs(r, c, grid, visited)

def bintree():
    class TreeNode:
        def __init__(self, val=0, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right

    def invertTree(root):
        if root is None:
            return None
        root.left, root.right = root.right, root.left
        invertTree(root.left)
        invertTree(root.right)
        return root

    root = TreeNode(4)
    root.left = TreeNode(2)
    root.right = TreeNode(7)
    root.left.left = TreeNode(1)
    root.left.right = TreeNode(3)
    root.right.left = TreeNode(6)
    root.right.right = TreeNode(9)

    inverted = invertTree(root)
    return inverted.val, inverted.left.val, inverted.right.val

def graphtraversal():
    graph = {
        "A": ["B", "C"],
        "B": ["A", "D"],
        "C": ["A"],
        "D": ["B"]
    }

    def dfs(node, visited):
        if node in visited:
            return
        visited.add(node)
        print(node)
        for neighbor in graph[node]:
            dfs(neighbor, visited)

    from collections import deque
    def bfs(start):
        queue = deque([start])
        visited = {start}
        while queue:
            node = queue.popleft()
            print(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

    print("DFS:")
    dfs("A", set())
    print("BFS:")
    bfs("A")

# SessionManager
# Servers are passed in at setup. Sessions start and end over time, each with a string ID.
# start_session: assign the new session to a server so sessions stay spread evenly across servers.
# end_session: remove the session from whichever server owns it.
# get_current_allocation: return, for each server, the set of session IDs it currently owns.
# Stub from the interview:

class SessionManager:
    def __init__(self, servers: set[str]):
        self.allocation = {}
        self.session = {}
        for server in servers: self.allocation[server] = set()

    def start_session(self, session_id: str) -> None:
        a = min(len(self.allocation))
        self.session[a].add(session_id)

    def end_session(self, session_id: str) -> None:
        pass

    def get_current_allocation(self) -> dict[str, set[str]]:
        pass



print("Select Problem")
answer = input()
if answer == "1":
    print(problem_one())
if answer == "2":
    print(problem_two())
if answer == "3":
    print(problem_three())
if answer == "4":
    print(problem_four())
if answer == "5":
    print(problem_five())
if answer == "6":
    print(problem_six())
if answer == "7":
    print(problem_seven())
if answer == "8":
    print(problem_eight())
if answer == "9":
    print(binary_search())
if answer == "10":
    print(fluency_pass())
if answer == "11":
    print(kadane())
if answer == "12":
    print(trees())
if answer == "13":
    print(recursion())
if answer == "14":
    print(treepractice())
if answer == "15":
    print(graphs())
if answer == "16":
    print(two_sum())
if answer == "17":
    print(sliding_window())
if answer == "18":
    print(longest_substring())
if answer == "19":
    print(variable_size())
if answer == "20":
    print(bintree())