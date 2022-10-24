# 表达式的分析
import pickle

from tree import Tree

my_tree = Tree(0, '开始')
ID_STATUS = 700
pre = 0
pos = 0
tokens = []  # token表
right = []
error = []  # (line,token,error_type)

errorType = {
    '0': '不能匹配标识符',
    '1': '不能匹配常数',
    '2': '缺少左括号(',
    '3': '缺少右括号)',
    '4': '缺少分号;',
    '5': '缺少花括号{',
    '6': '缺少花括号}',
    '7': '缺少关系运算符',
    '8': '赋值表达式缺少=',
    '9': '常量声明匹配缺少const',
    '10': '错误的常量类型',
    '11': '错误的变量类型',
    '12': '错误的函数类型',
    '13': 'do while语句缺少while',
    '14': '程序找不到main入口',
    '15': '其他类型'
}


def get_token():
    if pos >= len(tokens):
        return '#'
    return tokens[pos][1]


def get_next_token():
    if pos + 1 >= len(tokens):
        return '#'
    return tokens[pos + 1][1]


def get_token_status():
    if pos >= len(tokens):
        return '#'
    return int(tokens[pos][2])


# 保存字符
def catch(root):
    global pos
    if get_token() in ['{', '}', ';', ',']:
        right.append(f'<界符>{get_token()}\n')
    elif get_token() in ['!', '*', '/', '%', '+', '-', '>', '<', '=', '&', '|', '^', '[', ']', '(', ')', '.']:
        right.append(f'<运算符>{get_token()}\n')
    elif get_token() == 'main':
        right.append(f'<程序入口>{get_token()}\n')
    else:
        right.append(f'{get_token()}\n')
    my_tree.add_child(root, get_token())
    pos += 1


# 保存错误
def get_error(error_type):
    error.append((tokens[pos - 1][0], tokens[pos - 1][1], errorType.get(str(error_type))))


def id(root):
    right.append('<标识符>')
    my_tree.add_child(root, '标识符')
    current_root = my_tree.current_root()
    if get_token_status() == 700:
        catch(current_root)
    else:
        get_error(0)


def e1(root):
    right.append('<算数表达式>')
    my_tree.add_child(root, '算数表达式')
    current_root = my_tree.current_root()
    e2(current_root)
    e1_(current_root)
    my_tree.add_child(current_root, '$___expr_end')


def e1_(root):
    if get_token() == '+' or get_token() == '-':
        catch(root)
        e1(root)


def e2(root):
    right.append('<项>')
    my_tree.add_child(root, '项')
    current_root = my_tree.current_root()
    e3(current_root)
    e2_(current_root)


def e2_(root):
    if get_token() in ['*', '/', '%']:
        catch(root)
        e2(root)


def e3(root):
    global pos, error
    right.append('<因子>')
    my_tree.add_child(root, '因子')
    current_root = my_tree.current_root()
    if get_token_status() == ID_STATUS:
        temp_pos = pos
        error_len = len(error)
        e6(current_root)
        if len(error) > error_len:  # 如果不是函数调用，则匹配变量
            error = error[:error_len]
            my_tree.remove_tree(current_root)
            my_tree.add_child(root, '因子')
            current_root = my_tree.current_root()
            pos = temp_pos
            e5(current_root)

    elif get_token() == '(':
        catch(current_root)
        e1(current_root)
        if get_token() == ')':
            catch(current_root)
        else:
            get_error(3)
    else:
        e4(current_root)


def e4(root):
    right.append('<常量>')
    my_tree.add_child(root, '常量')
    current_root = my_tree.current_root()
    if get_token_status() in [400, 500, 800]:
        catch(current_root)
    else:
        get_error(1)


def e5(root):
    right.append('<变量>')
    my_tree.add_child(root, '变量')
    current_root = my_tree.current_root()
    id(current_root)


def e6(root):
    right.append('<函数调用>')
    my_tree.add_child(root, '函数调用')
    current_root = my_tree.current_root()
    id(current_root)
    if get_token() == '(':
        catch(current_root)
        e7(current_root)
        if get_token() == ')':
            catch(current_root)
            my_tree.add_child(current_root, '$___call_end')
        else:
            get_error(3)
    else:
        get_error(2)


def e7(root):
    right.append('<实参列表>')
    my_tree.add_child(root, '实参列表')
    current_root = my_tree.current_root()
    if get_token() in ['(', '!'] or get_token_status() in [ID_STATUS, 400, 500, 800]:
        e8(current_root)
    else:
        my_tree.add_child(current_root, 'ε')


def e8(root):
    right.append('<实参>')
    my_tree.add_child(root, '实参')
    current_root = my_tree.current_root()
    a1(current_root)
    e8_(current_root)


def e8_(root):
    if get_token() == ',':
        catch(root)
        e8(root)


def a1(root):
    global error, pos
    right.append('<表达式>')
    my_tree.add_child(root, '表达式')
    current_root = my_tree.current_root()
    if get_token_status() == ID_STATUS and get_next_token() == '=':
        d1(current_root)  # 先匹配赋值表达式
    else:
        b1(current_root)
    my_tree.add_child(current_root, '$___total_expr_end')


def b1(root):
    right.append('<布尔表达式>')
    my_tree.add_child(root, '布尔表达式')
    current_root = my_tree.current_root()
    b2(current_root)
    b1_(current_root)
    my_tree.add_child(current_root, '$___bool_expr_end')


def b1_(root):
    if get_token() == '||':
        catch(root)
        b1(root)


def b2(root):
    right.append('<布尔项>')
    my_tree.add_child(root, '布尔项')
    current_root = my_tree.current_root()
    b3(current_root)
    b2_(current_root)


def b2_(root):
    if get_token() == '&&':
        catch(root)
        b2(root)


def b3(root):
    global pos, error
    right.append('<布尔因子>')
    my_tree.add_child(root, '布尔因子')
    current_root = my_tree.current_root()
    if get_token() == '!':
        catch(current_root)
        b1(current_root)
    else:
        error_len = len(error)
        temp_pos = pos
        c1(current_root)
        if len(error) > error_len:
            error = error[:error_len]
            my_tree.remove_tree(current_root)
            my_tree.add_child(root, '布尔因子')
            current_root = my_tree.current_root()
            pos = temp_pos
            e1(current_root)


def c1(root):
    right.append('<关系表达式>')
    my_tree.add_child(root, '关系表达式')
    current_root = my_tree.current_root()
    e1(current_root)
    c2(current_root)
    e1(current_root)
    my_tree.add_child(current_root, '$___rel_expr_end')


def c2(root):
    right.append('<关系运算符>')
    my_tree.add_child(root, '关系运算符')
    current_root = my_tree.current_root()
    if get_token() in ['>', '<', '>=', '<=', '==', '!=']:
        catch(current_root)
    else:
        get_error(7)


def d1(root):
    right.append('<赋值表达式>')
    my_tree.add_child(root, '赋值表达式')
    current_root = my_tree.current_root()
    id(current_root)
    if get_token() == '=':
        catch(current_root)
        a1(current_root)
        my_tree.add_child(current_root, '$___fu_zhi_end')
    else:
        get_error(8)


def l1(root):
    right.append('<语句>')
    my_tree.add_child(root, '语句')
    current_root = my_tree.current_root()
    if get_token() in ['const', 'int', 'char', 'float', 'void']:
        l2(current_root)
    elif get_token() in ['if', 'for', 'while', 'do', 'return', '{'] or get_token_status() == ID_STATUS:
        m1(current_root)
    else:
        l2(current_root)


def l2(root):
    global error, pos
    right.append('<声明语句>')
    my_tree.add_child(root, '声明语句')
    current_root = my_tree.current_root()
    error_len = len(error)
    temp_pos = pos
    l11(current_root)
    if len(error) > error_len:
        error = error[:error_len]
        pos = temp_pos
        my_tree.remove_tree(current_root)
        my_tree.add_child(root, '声明语句')
        current_root = my_tree.current_root()
        l3(current_root)
        if len(error) > error_len:
            error = error[:error_len]
            pos = temp_pos
            my_tree.remove_tree(current_root)
            my_tree.add_child(root, '声明语句')
            current_root = my_tree.current_root()
            my_tree.add_child(current_root, 'ε')


def l3_(root):
    if get_token() == '(':
        catch(root)
        l13(root)
        if get_token() == ')':
            catch(root)
            if get_token() == ';':
                catch(root)
            else:
                get_error(4)
        else:
            get_error(3)
    else:
        l9_(root)
        l8_(root)


def l3(root):
    right.append('<值声明>')
    my_tree.add_child(root, '值声明')
    current_root = my_tree.current_root()
    if get_token() == 'const':
        l4(current_root)
    else:
        l7(current_root)


def l4(root):
    right.append('<常量声明>')
    my_tree.add_child(root, '常量声明')
    current_root = my_tree.current_root()
    if get_token() == 'const':
        catch(current_root)
        l5(current_root)
        l6(current_root)
    else:
        get_error(9)


def l5(root):
    right.append('<常量类型>')
    my_tree.add_child(root, '常量类型')
    current_root = my_tree.current_root()
    if get_token() in ['int', 'char', 'float']:
        catch(current_root)
    else:
        get_error(10)


def l6(root):
    right.append('<常量声明表>')
    my_tree.add_child(root, '常量声明表')
    current_root = my_tree.current_root()
    id(current_root)
    if get_token() == '=':
        catch(current_root)
        e4(current_root)
        l6_(current_root)
    else:
        get_error(8)


def l6_(root):
    if get_token() == ';':
        catch(root)
    elif get_token() == ',':
        catch(root)
        l6(root)
    else:
        get_error(4)


def l7(root):
    right.append('<变量声明>')
    my_tree.add_child(root, '变量声明')
    current_root = my_tree.current_root()
    l10(current_root)
    l8(current_root)
    my_tree.add_child(current_root, '$___shen_min_end')


def l8(root):
    right.append('<变量声明表>')
    my_tree.add_child(root, '变量声明表')
    current_root = my_tree.current_root()
    l9(current_root)
    l8_(current_root)


def l8_(root):
    if get_token() == ';':
        catch(root)
    elif get_token() == ',':
        catch(root)
        l8(root)
    else:
        get_error(4)


def l9(root):
    right.append('<单变量声明>')
    my_tree.add_child(root, '单变量声明')
    current_root = my_tree.current_root()
    e5(current_root)
    l9_(current_root)


def l9_(root):
    if get_token() == '=':
        catch(root)
        a1(root)


def l10(root):
    right.append('<变量类型>')
    my_tree.add_child(root, '变量类型')
    current_root = my_tree.current_root()
    if get_token() in ['int', 'char', 'float']:
        catch(current_root)
    else:
        get_error(11)


def l11(root):
    right.append('<函数声明>')
    my_tree.add_child(root, '函数声明')
    current_root = my_tree.current_root()
    l12(current_root)
    id(current_root)
    if get_token() == '(':
        catch(current_root)
        l13(current_root)
        if get_token() == ')':
            catch(current_root)
            if get_token() == ';':
                catch(current_root)
            else:
                get_error(4)
        else:
            get_error(3)
    else:
        get_error(2)


def l12(root):
    right.append('<函数类型>')
    my_tree.add_child(root, '函数类型')
    current_root = my_tree.current_root()
    if get_token() in ['int', 'char', 'float', 'void']:
        catch(current_root)
    else:
        get_error(12)


def l13(root):
    right.append('<函数声明形参列表>')
    my_tree.add_child(root, '函数声明形参列表')
    current_root = my_tree.current_root()
    if get_token() in ['int', 'char', 'float']:
        l14(current_root)


def l14(root):
    right.append('<函数声明形参>')
    my_tree.add_child(root, '函数声明形参')
    current_root = my_tree.current_root()
    l10(current_root)
    l14_(current_root)


def l14_(root):
    if get_token() == ',':
        catch(root)
        l14(root)


def m1(root):
    right.append('<执行语句>')
    my_tree.add_child(root, '执行语句')
    current_root = my_tree.current_root()
    if get_token() == '{':  # 进入复合语句
        m6(current_root)
    elif get_token() in ['if', 'for', 'while', 'do', 'return']:
        m5(current_root)
    elif get_token_status() == ID_STATUS:
        m2(current_root)


def m2(root):
    global pos, error
    right.append('<数据处理语句>')
    my_tree.add_child(root, '数据处理语句')
    current_root = my_tree.current_root()
    error_len = len(error)
    temp_pos = pos
    m4(current_root)
    if len(error) > error_len:
        pos = temp_pos
        error = error[:error_len]
        my_tree.remove_tree(current_root)
        my_tree.add_child(root, '数据处理语句')
        current_root = my_tree.current_root()
        m3(current_root)


def m3(root):
    right.append('<赋值语句>')
    my_tree.add_child(root, '赋值语句')
    current_root = my_tree.current_root()
    d1(current_root)
    if get_token() == ';':
        catch(current_root)
    else:
        get_error(4)


def m4(root):
    right.append('<函数调用语句>')
    my_tree.add_child(root, '函数调用语句')
    current_root = my_tree.current_root()
    e6(current_root)
    if get_token() == ';':
        catch(current_root)
    else:
        get_error(4)


def m5(root):
    right.append('<控制语句>')
    my_tree.add_child(root, '控制语句')
    current_root = my_tree.current_root()
    token_temp = get_token()
    if token_temp == 'if':
        m8(current_root)
    elif token_temp == 'for':
        m9(current_root)
    elif token_temp == 'while':
        m10(current_root)
    elif token_temp == 'do':
        m11(current_root)
    elif token_temp == 'return':
        m17(current_root)
    else:
        get_error(15)


def m6(root):
    right.append('<复合语句>')
    my_tree.add_child(root, '复合语句')
    current_root = my_tree.current_root()
    if get_token() == '{':
        catch(current_root)
        m7(current_root)
        if get_token() == '}':
            catch(current_root)
        else:
            get_error(6)
    else:
        get_error(5)


def m7(root):
    right.append('<语句表>')
    my_tree.add_child(root, '语句表')
    current_root = my_tree.current_root()
    l1(current_root)
    m7_(current_root)


def m7_(root):
    if get_token() in ['int', 'char', 'float', 'void', 'const', '{', 'if', 'for', 'while', 'do',
                       'return'] or get_token_status() == ID_STATUS:
        m7(root)


def m8(root):
    right.append('<if语句>')
    my_tree.add_child(root, 'if语句')
    current_root = my_tree.current_root()
    if get_token() == 'if':
        catch(current_root)
        if get_token() == '(':
            catch(current_root)
            a1(current_root)
            if get_token() == ')':
                catch(current_root)
                my_tree.add_child(current_root, 'if为0跳转')
                l1(current_root)
                my_tree.add_child(current_root, 'if无条件跳转')
                my_tree.add_child(current_root, 'if为0跳转回填')
                m8_(current_root)
            else:
                get_error(3)
        else:
            get_error(2)

        my_tree.add_child(current_root, 'if无条件跳转回填')


def m8_(root):
    if get_token() == 'else':
        catch(root)
        l1(root)


def m9(root):
    right.append('for语句>')
    my_tree.add_child(root, 'for语句')
    current_root = my_tree.current_root()
    if get_token() == 'for':
        catch(current_root)
        if get_token() == '(':
            catch(current_root)
            a1(current_root)
            if get_token() == ';':
                catch(current_root)
                my_tree.add_child(current_root, 'for记录判断跳转值')
                a1(current_root)
                my_tree.add_child(current_root, 'for为0跳转')
                my_tree.add_child(current_root, 'for不为0跳转')
                if get_token() == ';':
                    catch(current_root)
                    a1(current_root)
                    my_tree.add_child(current_root, 'for判断跳转')
                    if get_token() == ')':
                        catch(current_root)
                        m12(current_root)
                    else:
                        get_error(2)
                else:
                    get_error(4)
            else:
                get_error(4)
        else:
            get_error(2)
        my_tree.add_child(current_root, 'for无条件跳转')
        my_tree.add_child(current_root, 'for回填')


def m10(root):
    right.append('<while语句>')
    my_tree.add_child(root, 'while语句')
    current_root = my_tree.current_root()

    if get_token() == 'while':
        catch(current_root)
        if get_token() == '(':
            catch(current_root)
            a1(current_root)
            if get_token() == ')':
                catch(current_root)
                my_tree.add_child(current_root, 'while记录回填值')
                my_tree.add_child(current_root, 'while为0跳转')
                m12(current_root)
                my_tree.add_child(current_root, 'while无条件跳转')
                my_tree.add_child(current_root, 'while回填')
            else:
                get_error(3)
        else:
            get_error(2)


def m11(root):
    right.append('<do while语句>')
    my_tree.add_child(root, 'do while语句')
    current_root = my_tree.current_root()
    if get_token() == 'do':
        catch(current_root)
        m13(current_root)
        if get_token() == 'while':
            catch(current_root)
            if get_token() == '(':
                catch(current_root)
                a1(current_root)
                if get_token() == ')':
                    catch(current_root)
                    if get_token() == ';':
                        catch(current_root)
                    else:
                        get_error(4)
                else:
                    get_error(3)
            else:
                get_error(2)
        else:
            get_error(13)


def m12(root):
    right.append('<循环语句>')
    my_tree.add_child(root, '循环语句')
    current_root = my_tree.current_root()
    if get_token() == '{':
        m13(current_root)
    elif get_token() in ['if', 'for', 'while', 'do', 'return', 'break', 'continue']:
        m15(current_root)
    else:
        l1(current_root)


def m13(root):
    right.append('<循环用复用语句>')
    my_tree.add_child(root, '循环用复用语句')
    current_root = my_tree.current_root()
    if get_token() == '{':
        catch(current_root)
        m14(current_root)
        if get_token() == '}':
            catch(current_root)
        else:
            get_error(6)
    else:
        get_error(5)


def m14(root):
    right.append('<循环语句表>')
    my_tree.add_child(root, '循环语句表')
    current_root = my_tree.current_root()
    m12(current_root)
    m14_(current_root)


def m14_(root):
    re_flag = False
    if get_token() in ['const', 'void', 'int', 'char', 'float']:  # 声明语句
        re_flag = True
    if get_token() in ['if', 'for', 'while', 'do', 'return', 'break', 'continue']:  # 控制语句
        re_flag = True
    if get_token_status() == ID_STATUS:  # 赋值语句，函数调用
        re_flag = True
    if get_token() == '{':  # 循环用复合语句
        re_flag = True
    if re_flag:
        m14(root)


def m15(root):
    right.append('<循环执行语句>')
    my_tree.add_child(root, '循环执行语句')
    current_root = my_tree.current_root()
    token_temp = get_token()
    if token_temp == 'if':
        m16(current_root)
    elif token_temp == 'for':
        m9(current_root)
    elif token_temp == 'while':
        m10(current_root)
    elif token_temp == 'do':
        m11(current_root)
    elif token_temp == 'return':
        m17(current_root)
    elif token_temp == 'break':
        m18(current_root)
    elif token_temp == 'continue':
        m19(current_root)


def m16(root):
    right.append('<循环用if语句>')
    my_tree.add_child(root, '循环用if语句')
    current_root = my_tree.current_root()
    if get_token() == 'if':
        catch(current_root)
        if get_token() == '(':
            catch(current_root)
            a1(current_root)
            if get_token() == ')':
                catch(current_root)
                my_tree.add_child(current_root, 'if为0跳转')
                m12(current_root)
                my_tree.add_child(current_root, 'if无条件跳转')
                my_tree.add_child(current_root, 'if为0跳转回填')
                m16_(current_root)

            else:
                get_error(3)
        else:
            get_error(2)
    my_tree.add_child(current_root, 'if无条件跳转回填')


def m16_(root):
    if get_token() == 'else':
        catch(root)
        m12(root)


def m17(root):
    right.append('<return语句>')
    my_tree.add_child(root, 'return语句')
    current_root = my_tree.current_root()
    if get_token() == 'return':
        catch(current_root)
        m17_(current_root)


def m17_(root):
    if get_token() == ';':
        catch(root)
    else:
        a1(root)
        if get_token() == ';':
            catch(root)
        else:
            get_error(4)


def m18(root):
    right.append('<break语句>')
    my_tree.add_child(root, 'break语句')
    current_root = my_tree.current_root()
    if get_token() == 'break':
        catch(current_root)
        if get_token() == ';':
            catch(current_root)
        else:
            get_error(4)


def m19(root):
    right.append('<continue语句>')
    my_tree.add_child(root, 'continue语句')
    current_root = my_tree.current_root()
    if get_token() == 'continue':
        catch(current_root)
        if get_token() == ';':
            catch(current_root)
        else:
            get_error(4)


def k3(root):
    right.append('<函数定义形参>')
    my_tree.add_child(root, '函数定义形参')
    current_root = my_tree.current_root()
    l10(current_root)
    id(current_root)
    k3_(current_root)


def k1(root):
    right.append('<函数定义>')
    my_tree.add_child(root, '函数定义')
    current_root = my_tree.current_root()
    l12(current_root)
    id(current_root)
    if get_token() == '(':
        catch(current_root)
        k2(current_root)
        if get_token() == ')':
            catch(current_root)
            my_tree.add_child(current_root, '$___func_define')
            m6(current_root)
        else:
            get_error(3)
    else:
        get_error(2)


def k2(root):
    right.append('<函数定义行参列表>')
    my_tree.add_child(root, '函数定义行参列表')
    current_root = my_tree.current_root()
    if get_token() in ['int', 'char', 'float']:
        k3(current_root)
    else:
        my_tree.add_child(current_root, 'ε')


def k3_(root):
    if get_token() == ',':
        catch(root)
        k3(root)


def j1(root):
    right.append('<程序>')
    my_tree.add_child(root, '程序')
    current_root = my_tree.current_root()
    l2(current_root)
    j1_(current_root)


def j1_(root):
    try:
        if get_token() == 'main':
            catch(root)
            if get_token() == '(':
                catch(root)
                if get_token() == ')':
                    catch(root)
                    m6(root)
                    my_tree.add_child(root, '$___sys')
                    j2(root)
                else:
                    get_error(3)
            else:
                get_error(2)
        else:
            l2(root)
            j1_(root)
    except RecursionError:
        get_error(14)


def j2(root):
    right.append('<函数块>')
    my_tree.add_child(root, '函数块')
    current_root = my_tree.current_root()
    if get_token() in ['void', 'char', 'int', 'float']:
        k1(current_root)
        my_tree.add_child(current_root, 'ret')
        j2(current_root)
    else:
        my_tree.add_child(current_root, 'ε')


def grammar_main(token_list):
    global pos, tokens, right, error
    pos = 0
    right = []
    error = []
    tokens = token_list
    my_tree.tree_reset()
    j1(0)
    my_tree.print_tree()
