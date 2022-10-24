import copy
from tree import Tree
import time
import pickle


class SimpleExplain:

    def __init__(self, tree: Tree):
        self.code_list = tree.inter.code_list  # 中间代码四元式
        self.func_define = tree.semantics_table.func  # 查表传递参数
        ''' func_define 结构
        self.func[name] = {
            'return': return_type,
            'args': args,
            'start': start  # 函数开始执行的位置
        }
        '''
        self.func_dict = {
            'name': None,
            'var': dict(),
            'return': None,
            'step': 0  # 执行到哪一步了
        }
        self.args = []  # 保存传递的参数
        self.func = []

    def find_var(self, var):
        return int(self.func[-1]['var'].get(var, var))

    def set_var(self, var, value):
        self.func[-1]['var'][var] = int(self.find_var(value))

    def add_func(self, func_name):
        self.func.append(copy.deepcopy(self.func_dict))
        self.func[-1]['name'] = func_name

    def run(self):
        i = 0
        while True:
            # print(self.code_list[i])
            arg0, arg1, arg2, arg3 = self.code_list[i]
            if arg0 == 'main':
                self.add_func('main')
                start_time = time.time()
            elif arg0 == 'sys':
                end_time = time.time()
                print(f'程序运行{end_time - start_time} s')
                break
            elif arg0 == 'j':
                i = arg3
                continue
            elif arg0 == 'jz':
                if self.find_var(arg1) == 0:
                    i = arg3
                    continue
            elif arg0 == 'jnz':
                if self.find_var(arg1) != 0:
                    i = arg3
                    continue
            elif arg0 == '=':
                self.set_var(arg3, arg1)
            elif arg0 in ['+', '-', '*', '/', '%']:
                if arg0 == '+':
                    self.set_var(arg3, self.find_var(arg1) + self.find_var(arg2))
                elif arg0 == '-':
                    self.set_var(arg3, self.find_var(arg1) - self.find_var(arg2))
                elif arg0 == '*':
                    self.set_var(arg3, self.find_var(arg1) * self.find_var(arg2))
                elif arg0 == '/':
                    self.set_var(arg3, self.find_var(arg1) / self.find_var(arg2))
                elif arg0 == '%':
                    self.set_var(arg3, self.find_var(arg1) % self.find_var(arg2))
            elif arg0 == '!':
                self.set_var(arg3, not self.find_var(arg1))
            elif arg0 in ['>', '>=', '<', '<=', '==', '!=', '&&', '||']:
                if arg0 == '>':
                    self.set_var(arg3, int(self.find_var(arg1) > self.find_var(arg2)))
                elif arg0 == '>=':
                    self.set_var(arg3, int(self.find_var(arg1) >= self.find_var(arg2)))
                elif arg0 == '<':
                    self.set_var(arg3, int(self.find_var(arg1) < self.find_var(arg2)))
                elif arg0 == '<=':
                    self.set_var(arg3, int(self.find_var(arg1) <= self.find_var(arg2)))
                elif arg0 == '==':
                    self.set_var(arg3, int(self.find_var(arg1) == self.find_var(arg2)))
                elif arg0 == '!=':
                    self.set_var(arg3, int(self.find_var(arg1) != self.find_var(arg2)))
                elif arg0 == '&&':
                    if self.find_var(arg1) and self.find_var(arg2):
                        self.set_var(arg3, 1)
                    else:
                        self.set_var(arg3, 0)
                elif arg0 == '||':
                    if self.find_var(arg1) or self.find_var(arg2):
                        self.set_var(arg3, 1)
                    else:
                        self.set_var(arg3, 0)
            elif arg0 == 'para':
                self.args.append(self.find_var(arg1))
            elif arg0 == 'call':
                if arg1 == 'read':
                    self.set_var(arg3, input('read:'))
                elif arg1 == 'write':
                    for j in range(len(self.args)):
                        head = self.args.pop(0)
                        print(head, end='\t')
                    print()
                else:
                    self.func[-1]['step'] = i + 1
                    self.add_func(arg1)
                    # 传递参数
                    define_arg = self.func_define.get(arg1).get('args')
                    for _, id in define_arg:
                        self.set_var(id, self.find_var(self.args.pop(0)))
                    # 保存返回值
                    self.func[-1]['return'] = arg3
                    # 跳转执行
                    i = self.func_define.get(arg1).get('start')
                    continue
            elif arg0 == 'ret':
                return_var = self.func[-1].get('return')  # 保存到的变量名
                if arg1:
                    return_value = self.find_var(arg1)
                    self.func.pop()  # 函数出栈
                    self.set_var(return_var, return_value)  # 返回值保存
                i = self.func[-1].get('step')
                continue
            i += 1


if __name__ == '__main__':
    try:
        f = open("tree.pkl", "rb")
        tree = pickle.load(f)
        explain = SimpleExplain(tree)
        explain.run()
    except RecursionError as e:
        print('程序执行失败!')
    except FileNotFoundError:
        print('程序执行失败:\n（1）请检查是否生成了中间代码')
