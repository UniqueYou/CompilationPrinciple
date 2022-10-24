"""
/*******************************
*                              *
*        词法分析-单词识别        *
*                              *
********************************/

使用通过首字母判断单词的类别,然后通过正则去匹配
输入：词法分析文本
输出：
（1）right:正确单词四元式列表 [ (行号,单词，特种码，单词类型)]
    例子：[(13, 'abc', 700, '标识符'), (14, '12', 400, '整数'),………]
（2）error:错误单词二元式列表 [(行号,单词)]
    例子：[(16, '12a'), (18, '00.234e3'), (20, '0x3g')]

"""
import os
import pandas
import re


# 词法分析
class WordAnalysis:

    def __init__(self, code):
        self.code = code  # 代码
        self.error = []  # 错误列表
        self.right = []  # 正确列表
        self.line = 1  # 单词行号
        self.i = 0  # 单词索引
        self.split = ['{', '}', '[', ']', '(', ')', '%', '/', '+', '-', '*', '=', '>', '<', ' ', '\n', '\t', ';', '&',
                      '!', '|', ',', '\r', '^']  # 分隔符
        self.delimiter = ['{', '}', ';', ',']
        self.operator = ['!', '*', '/', '%', '+', '-', '>', '<', '=', '&', '|', '^', '[', ']', '(', ')', '.']
        self.key_dict = pandas.read_json(os.path.join(os.getcwd(), 'Sample.json'))
        # 识别实数的正则
        self.re_number = r"^(0[x|X])([0-9a-fA-F]+)|^(0[0-7])[0-7]*|^([0-9]+)(\.[0-9]+)?([e|E]([+|-])?[0-9]+)?"
        # 识别标识符
        self.re_id = r"^[a-zA-Z_][a-zA-Z0-9_]*"
        # 识别多行注释
        self.re_mul_cmt = r"^(\/\*)(?:[^\*]|\*+[^\/\*])*\*+\/"
        # 识别单行注释
        self.re_cmt = r"^(\/\/)[^\n]*"
        # 关系运算符
        self.re_rel = r"^>=?|^<=?|^[!|=]="
        # 赋值运算符
        self.re_ass = r"^="
        # 逻辑运算符
        self.re_log = r"^!|^&&|^\|\|"
        # 算数运算符
        self.re_ari = r"^(\+|-|\*|\/|%|&|\||\^|\(|\)|\[|\]|\.)"
        # 字符常量
        self.re_char = r"^'[0-9a-zA-z]'"
        # 字符串常量
        self.re_string = r'^".*"'
        # 界符
        self.re_delimiter = r"^[\{\}\;\,]"
        # 现在匹配的字符
        self.str = None
        # 匹配之前的下标
        self.pre = 0

    # 根据正则表达式匹配
    def match(self, re_string):
        self.pre = self.i
        temp = re.match(re_string, self.code[self.i:])
        if temp is not None:
            self.i += temp.end()
            self.str = temp.group()
        else:
            self.str = None
        return self.str

    def get_info(self, split_word):
        right = None
        if self.i < len(self.code):  # 如果识别还没有到末尾
            if self.code[self.i] not in split_word:  # 如果下一个识别符与标识符之间没有分割，则这一串是错误的
                while self.i < len(self.code):  # 匹配错串
                    if self.code[self.i] not in split_word:
                        self.i += 1
                    else:
                        break
                error = self.code[self.pre:self.i]
                self.error.append((self.line, error))
            else:
                right = self.code[self.pre:self.i]
        return right

    def run(self):
        while self.i < len(self.code):
            if self.code[self.i] == '\n':
                self.line += 1
            if self.code[self.i] in ['\n', '\t', ' ']:
                self.i += 1
                continue
            if self.code[self.i:self.i + 2] == '//':  # 识别单行注释
                self.match(self.re_cmt)
            elif self.code[self.i:self.i + 2] == '/*':  # 识别多行注释
                self.match(self.re_mul_cmt)
                if self.str:
                    self.line += self.str.count('\n')
                else:
                    self.error.append((self.line, self.code[self.i:]))
                    self.i = len(self.code) - 1
            elif 'z' >= self.code[self.i] >= 'a' or 'Z' >= self.code[self.i] >= 'A':  # 标识符和关键字
                self.match(self.re_id)
                right = self.get_info(self.split)
                if right:
                    if self.key_dict.get(str(right)) is not None:
                        self.right.append((self.line, right, self.key_dict.get(str(right))[0], '关键字'))
                    else:
                        self.right.append((self.line, right, self.key_dict.get('标识符')[0], '标识符'))
            elif '0' <= self.code[self.i] <= '9':  # 识别实数
                self.match(self.re_number)
                right = self.get_info(self.split)
                if right:
                    if right.isdigit() or '0x' in right or '0X' in right:
                        self.right.append((self.line, right, self.key_dict.get('整数')[0], '整数'))
                    else:
                        self.right.append((self.line, right, self.key_dict.get('实数(float)')[0], '实数(float)'))
            elif self.code[self.i] == "'":  # 字符常量
                self.match(self.re_char)
                right = self.get_info(self.split)
                if right:
                    self.right.append((self.line, right, self.key_dict.get('字符')[0], '字符'))
            elif self.code[self.i] == '"':  # 字符串常量
                self.match(self.re_string)
                right = self.get_info(self.split)
                if right:
                    self.right.append((self.line, right, self.key_dict.get('字符串')[0], '字符串'))
            elif self.code[self.i] in self.delimiter:  # 界符
                self.match(self.re_delimiter)
                self.right.append((self.line, self.str, self.key_dict.get(self.str)[0], '界符'))
            elif self.code[self.i] in self.operator:  # 运算符
                if self.match(self.re_rel):  # 关系运算符
                    self.right.append((self.line, self.str, self.key_dict.get(self.str)[0], '关系运算符'))
                elif self.match(self.re_log):
                    self.right.append((self.line, self.str, self.key_dict.get(self.str)[0], '逻辑运算符'))
                elif self.match(self.re_ari):
                    self.right.append((self.line, self.str, self.key_dict.get(self.str)[0], '算数运算符'))
                elif self.match(self.re_ass):
                    self.right.append((self.line, self.str, self.key_dict.get(self.str)[0], '赋值运算符'))
                else:
                    if self.match(r'[^\s]*'):
                        self.error.append((self.line, self.str))
                    else:
                        self.i += 1
            else:
                if self.match(r'[^\s]*'):
                    self.error.append((self.line, self.str))
                else:
                    self.i += 1
        temp = []
        for i in self.right:
            temp.append(str(i))
        for i in self.right:
            temp.append(str(i))
        with open('tokens.txt', 'w', encoding='utf-8') as fp:
            fp.write('\n'.join(temp))
        return self.right, self.error


if __name__ == '__main__':
    code = """
    /***********************
    词法测试用例
    ************************/
    //单行注释
    /*
    
    多行注释
    
    
    */
    //标识符和实数识别
    abc
    12
    1.2
    12a
    1.2e2+3
    00.234e3
    0x34
    0x3g
    0912
    //关键字识别
    char int float break const
    return  void continue do
    while for
    if else
    //界符和运算符识别
    {  } ; ,
    ! * / % + - * / | ^
    < <= > >= == !=
    && || =
    ( ) [ ] .
    char b='b'
    string c="acc"
    bool d=true
    void main()
    {	return 0;
    }
    """
    word = WordAnalysis(code)
    right, error = word.run()
