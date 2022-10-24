from graphviz import Digraph
from tabulate import tabulate

tabulate.PRESERVE_WHITESPACE = True  # 保留空格


# 中间代码生成
class IntermediateCode:

    def __init__(self):
        self.code_list = []
        self.temp_no = 0
        self.for_pos_stack = []
        self.for_value_stack = []
        self.if_pos_stack = []
        self.if_value_stack = []

    def catch_main(self):
        self.code_list.append(['main', None, None, None])

    def catch_sys(self):
        self.code_list.append(['sys', None, None, None])

    def inter_print(self):
        header = ['no', 'arg0', 'arg1', 'arg2', 'arg3']
        print('中间代码四元式:')
        print_table = []
        num = 0
        for arg0, arg1, arg2, arg3 in self.code_list:
            print_table.append([num, arg0, arg1, arg2, arg3])
            num += 1
        print(tabulate(print_table, headers=header, tablefmt='fancy_grid'))

    def save(self):
        temp = []
        for data in self.code_list:
            out_str = '%-10s\t%-10s\t%-10s\t%-10s' % (data[0], data[1], data[2], data[3])
            temp.append(out_str.replace('None','    '))

        with open('inter_code.txt', 'w', encoding='utf-8') as fp:
            fp.write('\n'.join(temp))


class Tree:

    def __init__(self, root, name: str):
        self.root = root
        self.child_no = root
        self.name = name
        self.tree_num = 0
        self.flag_root = set()  # 以及遍历过的节点
        self.inter = IntermediateCode()

        '''
        树结构
        '''
        self.tree_dict = {
            0: {
                'name': name,
                'child': []
            }
        }
        self.semantics_table = Semantics()

    def get_leaf(self, root):
        self.flag_root.add(root)
        queue = self.tree_dict.get(root).get('child')
        queue.reverse()
        result = []
        while queue:
            head = queue.pop()
            self.flag_root.add(head)  # 记录遍历过的节点
            if self.tree_dict.get(head).get('child'):
                child = self.tree_dict.get(head).get('child')
                child.reverse()
                queue.extend(child)
            else:
                if self.tree_dict.get(head).get('name') != 'ε':
                    result.append(self.tree_dict.get(head).get('name'))
        return result

    def current_root(self):
        return self.child_no

    def get_child(self, root):
        return self.tree_dict.get(root).get('child')

    def get_parent(self, root):
        for key, value in self.tree_dict.items():
            if root in value.get('child'):
                return key

    def add_child(self, root, name):
        self.child_no = len(self.tree_dict.keys())  # 新建节点
        self.tree_dict[self.child_no] = {
            'name': name,
            'child': []
        }
        # 建立父子关系
        if self.tree_dict.get(root).get('child'):
            self.tree_dict[root]['child'].append(self.child_no)
        else:
            self.tree_dict[root]['child'] = [self.child_no]

    def remove_tree(self, root):
        stack = [root]
        # 删除子节点
        while stack:
            head = stack.pop()
            stack.extend(self.tree_dict.get(head).get('child', []))
            self.tree_dict.pop(head)
        # 删除连接的边
        parent_root = self.get_parent(root)
        # 当前节点设置为删除节点的父节点
        self.tree_dict.get(parent_root).get('child').remove(root)
        self.child_no = parent_root

    def tree_reset(self):
        self.__init__(self.root, self.name)

    def set_name(self, root, name):
        self.child_name[root] = name

    def var_shen_min(self, root):
        self.flag_root.add(root)
        for i in range(root, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')
            if name == '$___shen_min_end':
                self.flag_root.add(i)
                break
            if i in self.flag_root:  # 不重复遍历
                continue
            elif name == '变量类型':
                var_type = ''.join(self.get_leaf(i))
            elif name == '常量类型':
                const_type = ''.join(self.get_leaf(i))
            elif name == '单变量声明':
                child = self.tree_dict.get(i).get('child')
                var_id = ''.join(self.get_leaf(child[0]))
                if len(child) == 3:
                    value = self.total_expr(child[2])
                    self.inter.code_list.append(['=', value, None, var_id])
                    self.semantics_table.add_vari(var_id, var_type, value)
                else:
                    self.get_leaf(i)
                    self.semantics_table.add_vari(var_id, var_type, None)
            elif name == '常量声明表':
                temp = self.get_leaf(i)
                temp.remove(';')
                if ',' in temp:
                    temp.remove(',')
                for k in range(0, len(temp), 3):
                    self.semantics_table.add_const(temp[k], const_type, temp[k + 2])
                    self.inter.code_list.append(['=', temp[k + 2], None, temp[k]])

            self.flag_root.add(i)

    def fu_zhi(self, root):
        self.flag_root.add(root)
        child = self.tree_dict.get(root).get('child')
        id = ''.join(self.get_leaf(child[0]))
        value = None
        for i in range(child[0] + 1, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')
            if name == '$___fu_zhi_end':
                self.flag_root.add(i)
                break
            if i in self.flag_root:  # 不重复遍历
                continue
            elif name == '表达式':
                value = self.total_expr(i)
            self.flag_root.add(i)

        self.inter.code_list.append(['=', value, None, id])

    # 布尔表达式
    def bool_expr(self, root):
        self.flag_root.add(root)
        bool_expr_list = []
        for i in range(root + 1, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')
            if name == '$___bool_expr_end':
                self.flag_root.add(i)
                while len(bool_expr_list) >= 3:
                    arg1 = bool_expr_list.pop(0)
                    opt = bool_expr_list.pop(0)
                    arg2 = bool_expr_list.pop(0)
                    self.inter.code_list.append([opt, arg1, arg2, '$___t' + str(self.inter.temp_no)])
                    bool_expr_list.insert(0, '$___t' + str(self.inter.temp_no))
                    self.inter.temp_no += 1
                break
            if i in self.flag_root:  # 不重复遍历
                continue
            elif name in ['&&', '||']:
                bool_expr_list.append(name)
            elif name == '!':
                self.flag_root.add(i)
                value = self.bool_expr(i + 1)[0]
                self.inter.code_list.append(['!', value, None, '$___t' + str(self.inter.temp_no)])
                bool_expr_list.append('$___t' + str(self.inter.temp_no))
                self.inter.temp_no += 1
            elif name == '布尔表达式':
                bool_expr_list.extend(self.bool_expr(i))
            elif name == '算数表达式':
                bool_expr_list.append(self.expr(i)[0])
            elif name == '关系表达式':
                bool_expr_list.append(self.rel_expr(i))
            self.flag_root.add(i)
        return bool_expr_list

    # 关系表达式
    def rel_expr(self, root):
        self.flag_root.add(root)
        args = []
        for i in range(root, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')
            if name == '$___rel_expr_end':
                self.flag_root.add(i)
                break
            elif i in self.flag_root:  # 不重复遍历
                continue
            elif name == '算数表达式':
                args.append(self.expr(i)[0])
            elif name == '关系运算符':
                opt = ''.join(self.get_leaf(i))

            self.flag_root.add(i)
        return_value = '$___t' + str(self.inter.temp_no)
        self.inter.code_list.append([opt, args[0], args[1], return_value])
        self.inter.temp_no += 1
        return return_value

    def expr(self, root):
        self.flag_root.add(root)
        expr_list = []
        for i in range(root + 1, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')
            if name == '$___expr_end':
                self.flag_root.add(i)
                while len(expr_list) >= 3:
                    arg1 = expr_list.pop(0)
                    opt = expr_list.pop(0)
                    arg2 = expr_list.pop(0)
                    self.inter.code_list.append([opt, arg1, arg2, '$___t' + str(self.inter.temp_no)])
                    expr_list.insert(0, '$___t' + str(self.inter.temp_no))
                    self.inter.temp_no += 1
                break
            if i in self.flag_root:  # 不重复遍历
                continue
            if name == '算数表达式':
                expr_list.extend(self.expr(i))
            if name in ['常量', '变量']:
                expr_list.append(''.join(self.get_leaf(i)))
            elif name in ['+', '-', '*', '/', '%']:
                expr_list.append(name)
            elif name == '函数调用':
                expr_list.append(self.hanshu(i))
            self.flag_root.add(i)
        return expr_list

    def hanshu(self, root):
        child = self.tree_dict.get(root).get('child')
        fun_id = ''.join(self.get_leaf(child[0]))
        args = []
        for i in range(root + 1, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')

            if i in self.flag_root:  # 不重复遍历
                continue
            if name == '$___call_end':
                self.flag_root.add(i)
                break
            if name == '表达式':
                args.append(self.total_expr(i))
            if name == '函数调用':
                self.hanshu(i)
            self.flag_root.add(i)
        for arg in args:
            self.inter.code_list.append(['para', arg, None, None])
        return_value = '$___t' + str(self.inter.temp_no)
        self.inter.code_list.append(['call', fun_id, None, return_value])
        self.inter.temp_no += 1
        return return_value

    # 表达式
    def total_expr(self, root):
        self.flag_root.add(root)
        return_value = None
        for i in range(root, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')
            if name == '$___total_expr_end':
                self.flag_root.add(i)
                break
            elif i in self.flag_root:  # 不重复遍历
                continue
            elif name == '赋值表达式':
                self.fu_zhi(i)
            elif name == '布尔表达式':
                return_value = self.bool_expr(i)[0]

            self.flag_root.add(i)

        return return_value

    def hanshu_define(self, root):
        self.flag_root.add(root)
        return_type_root = self.tree_dict.get(root).get('child')[0]
        id_root = self.tree_dict.get(root).get('child')[1]
        fun_id = ''.join(self.get_leaf(id_root))
        return_type = ''.join(self.get_leaf(return_type_root))
        self.inter.code_list.append([fun_id, None, None, None])
        self.flag_root.add(return_type_root)
        self.flag_root.add(id_root)
        args = []
        for i in range(root, len(self.tree_dict.keys()), 1):
            name = self.tree_dict.get(i).get('name')
            if name == '$___func_define':
                self.flag_root.add(i)
                break
            elif i in self.flag_root:  # 不重复遍历
                continue
            elif name == '函数定义形参':
                child = self.tree_dict.get(i).get('child')
                arg_type = ''.join(self.get_leaf(child[0]))
                arg_id = ''.join(self.get_leaf(child[1]))
                self.flag_root.add(arg_type)
                self.flag_root.add(arg_id)
                args.append([arg_type, arg_id])

            self.flag_root.add(i)
        self.semantics_table.add_func(fun_id, return_type, args, len(self.inter.code_list) - 1)

    # 生成中间代码
    def create_inter(self):
        self.inter.catch_main()
        for k, v in self.tree_dict.items():
            if k in self.flag_root:  # 寻找叶子时已经遍历过的不再遍历
                continue
            elif v.get('name') == '{':
                self.semantics_table.part_no += 1
                self.semantics_table.part_num += 1
            elif v.get('name') == '{':
                self.semantics_table.part_no -= 1
                self.semantics_table.part_num += 1
            elif v.get('name') == 'if为0跳转':
                value = '$___t' + str(self.inter.temp_no - 1)
                self.inter.code_list.append(['jz', value, None, '回填'])
                self.inter.if_pos_stack.append(len(self.inter.code_list) - 1)
            elif v.get('name') == 'if无条件跳转':
                self.inter.code_list.append(['j', None, None, '回填'])
                self.inter.if_pos_stack.append(len(self.inter.code_list) - 1)
            elif v.get('name') == 'if为0跳转回填':
                pos = self.inter.if_pos_stack.pop(0)
                self.inter.code_list[pos][3] = len(self.inter.code_list)
            elif v.get('name') == 'if无条件跳转回填':
                pos = self.inter.if_pos_stack.pop(0)
                self.inter.code_list[pos][3] = len(self.inter.code_list)
            elif v.get('name') == 'while记录回填值':
                re_while_value = len(self.inter.code_list) - 1
            elif v.get('name') == 'while为0跳转':
                value = '$___t' + str(self.inter.temp_no - 1)
                self.inter.code_list.append(['jz', value, None, '回填'])
                while_return_value0 = len(self.inter.code_list) - 1
            elif v.get('name') == 'while无条件跳转':
                self.inter.code_list.append(['j', None, None, '回填'])
                while_return_value1 = len(self.inter.code_list) - 1
            elif v.get('name') == 'while回填':
                self.inter.code_list[while_return_value0][3] = len(self.inter.code_list)
                self.inter.code_list[while_return_value1][3] = re_while_value
            elif v.get('name') == 'for判断跳转':
                self.inter.code_list.append(['j', None, None, '回填'])
                self.inter.for_pos_stack.append(len(self.inter.code_list) - 1)
                # 记录for不为0跳转的值
                self.inter.for_value_stack.append(len(self.inter.code_list))
            elif v.get('name') == 'for记录判断跳转值':
                # 记录for判断跳转的值
                self.inter.for_value_stack.append(len(self.inter.code_list))
            elif v.get('name') == 'for为0跳转':
                value = '$___t' + str(self.inter.temp_no - 1)
                self.inter.code_list.append(['jz', value, None, '回填'])
                self.inter.for_pos_stack.append(len(self.inter.code_list) - 1)
            elif v.get('name') == 'for不为0跳转':
                value = '$___t' + str(self.inter.temp_no - 1)
                self.inter.code_list.append(['jnz', value, None, '回填'])
                self.inter.for_pos_stack.append(len(self.inter.code_list) - 1)
                # 记录for无条件跳转的值
                self.inter.for_value_stack.append(len(self.inter.code_list))
            elif v.get('name') == 'for无条件跳转':
                self.inter.code_list.append(['j', None, None, '回填'])
                self.inter.for_pos_stack.append(len(self.inter.code_list) - 1)
            elif v.get('name') == 'for回填':
                for_any_pos = self.inter.for_pos_stack.pop()  # for无条件跳转位置
                for_re_pos = self.inter.for_pos_stack.pop()  # for判断跳转位置
                for_not_0_pos = self.inter.for_pos_stack.pop()  # for不为0跳转位置
                for_0_pos = self.inter.for_pos_stack.pop()  # for为0跳转位置
                self.inter.code_list[for_0_pos][3] = len(self.inter.code_list)  # 回填为0跳转
                self.inter.code_list[for_not_0_pos][3] = self.inter.for_value_stack.pop()  # 回填不为0跳转
                self.inter.code_list[for_any_pos][3] = self.inter.for_value_stack.pop()  # 回填无条件跳转
                self.inter.code_list[for_re_pos][3] = self.inter.for_value_stack.pop()  # 回填判断跳转
            elif v.get('name') == '函数定义':
                self.hanshu_define(k)
                self.semantics_table.part_no = self.semantics_table.part_num
            elif v.get('name') == 'return语句':
                child = self.tree_dict.get(k).get('child')
                if len(child) == 3:
                    value = self.total_expr(child[1])
                    self.inter.code_list.append(['ret', value, None, None])
            elif v.get('name') == 'ret':
                self.inter.code_list.append(['ret', None, None, None])
            elif v.get('name') in ['变量声明', '常量声明']:
                self.var_shen_min(k)
            elif v.get('name') == '$___sys':
                self.inter.catch_sys()
            elif v.get('name') == '函数调用':
                self.hanshu(k)
            elif v.get('name') == '赋值表达式':
                self.fu_zhi(k)
            elif v.get('name') == '布尔表达式':
                self.bool_expr(k)
        self.inter.save()
        self.inter.inter_print()
        self.semantics_table.info()

    def print_tree(self):
        dot = Digraph(comment='语法树', format='png', encoding='UTF-8')
        for root, value in self.tree_dict.items():
            if root != 0:
                dot.node(str(root), label=value.get('name'), fontname='Microsoft YaHei')
            if root != 0:
                for children in value.get('child'):
                    dot.edge(str(root), str(children), fontname='Microsoft YaHei')
        dot.render(f'output/语法树{self.tree_num}.gv', view=True)
        self.tree_num += 1

    def print_status(self):
        dot = Digraph(comment='状态图', format='png', encoding='UTF-8')
        for root, value in self.tree_dict.items():
            # if root != 0:
            #     dot.node(str(root), label=str(value), fontname='Microsoft YaHei')
            if root != 0:
                for children in value.get('child'):
                    dot.edge(str(root), str(children), fontname='Microsoft YaHei')
        dot.render(f'output/状态图{self.tree_num}.gv', view=True)
        self.tree_num += 1


# 语义
class Semantics:

    def __init__(self):
        self.func = dict()  # 函数表
        self.const = []  # 常量表
        self.vari = []  # 变量表
        self.part_num = 0  # 划分域的个数
        self.part_no = 0  # 域的编号

    def add_func(self, name: str, return_type: str, args: list, start):
        self.func[name] = {
            'return': return_type,
            'args': args,
            'start': start  # 函数开始执行的位置
        }

    # 添加常量
    def add_const(self, name: str, const_type: str, value):
        const_dict = {
            'name': name,
            'type': const_type,
            'value': value,
            'region': 0

        }
        self.const.append(const_dict)

    # 添加变量
    def add_vari(self, name: str, vari_type: str, value):
        vari_dict = {
            'name': name,
            'type': vari_type,
            'value': value,
            'region': self.part_no

        }
        self.vari.append(vari_dict)

    def info(self):
        const_temp = []
        vari_temp = []
        func_temp = []

        for i in self.const:
            const_temp.append([i.get('name'), i.get('type'), i.get('value'), i.get('region')])
        for i in self.vari:
            vari_temp.append([i.get('name'), i.get('type'), i.get('value'), i.get('region')])
        for k, v in self.func.items():
            temp = [k[0] for k in v.get('args')]
            func_temp.append([k, v.get('return'), ' '.join(temp)])

        const_header = ['常量', '类型', '值', '作用域']
        vari_header = ['变量', '类型', '值', '作用域']
        func_header = ['函数', '返回值', '参数']
        print('常量声明表"')
        print(tabulate(const_temp, headers=const_header, tablefmt='fancy_grid'))
        print('变量声明表:')
        print(tabulate(vari_temp, headers=vari_header, tablefmt='fancy_grid'))
        print('函数声明表:')
        print(tabulate(func_temp, headers=func_header, tablefmt='fancy_grid'))
        print(self.func)
