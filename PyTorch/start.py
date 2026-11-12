import torch
import numpy as np

class practice:
    def __init__(self):
        self.tensor1 = torch.tensor([[1,2,3], [4,5,6], [7,8,9]])
        self.tensor2 = torch.tensor(1.5)
        self.tensor3 = torch.tensor([1, 2, 3])
        self.tensor4 = torch.tensor([[2,5,3], [9,8,6], [6,7,7]])

    def task_1(self): # index through matrix, multiply / add them and print shapes
        a = self.tensor1[:2, :2] # find top left 2x2 values
        print(a)
        print(a.shape)
        b = self.tensor1 * 10
        print(b)
        print(b.shape)
        c = self.tensor1 + self.tensor1
        print(c)
        print(c.shape)
        d = self.tensor1 * self.tensor4
        print(d)
        print(d.shape)

    def task_2(self): # indexing throughout the matrix
        middleRow = self.tensor1[1] # find center row
        print(middleRow)
        lastColumn = self.tensor1[:, 2:3] # find last column (kept in matrix column form)
        print(lastColumn)
        centerNum = self.tensor1[1, 1] # find center value
        print(centerNum)

    def task_3(self): # matrix multiplication
        a = self.tensor1 @ self.tensor4
        print(a)

a = practice()
a.task_3()