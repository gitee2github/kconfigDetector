"""
语法分析代码, 借助ply.yacc包实现
语法识别完成后会生成两个文件, 其文件名格式均为, tag_arch
    * tag_arch_config.json: 
        文件会按照原语句格式进行存储, 存储数据结构为config_class.py的Config类
    * tag_arch_dep.json:
        文件按照自定义模型抽取配置信息, 存储数据结构为config_class.py的Config_dep类

主函数为ParseKconfig(file, config_file, dep_file, folder)
其参数含义是：
    * file: 预处理后的Kconfig文件路径
    * config_file: 解析识别后的tag_arch_config.json文件
    * dep_file: 解析识别后的tag_arch_dep.json
    * folder: 可指定结果保存路, 默认为当前路径下的result文件夹
"""

import os
import ply.yacc as yacc
import re
import time

from .config_class import check_line_and
from .config_class import Node as config_class_Node
from .config_class import Group as config_class_Group
from .config_lex import *
# import tools.config_lex as config_lex
from .utils import load_Kconfig as utils_load_Kconfig
from .utils import write_json_file as utils_write_json_file


display_switch = True
CONFIGDEP_FLAG = False


##########################      function      ##########################
def set_last_node(node, type):
    global last_node
    last_node = node


def set_last_node_dep():
    """ 处理上一个config的dep信息 """
    global last_node
    group_end = GROUP[-1] if len(GROUP) > 0 else None
    if last_node.type == 'mainmenu':
        return
    # 组关系关键字在Group里填写
    elif last_node.type == 'choice':
        dis = ""
        for item in GROUP[1:]:
            if item.node.detail is not None:
                if len(item.display) > 0:
                    dis = check_line_and(dis) + '( ' + item.display + ' )'
        if len(dis) > 0:
            default = group_end.node.dep_temp.get_default() if group_end else None
            for item in default:
                if len(item) > 1:
                    group_end.node.config_dep.set_restrict(
                        item[0], '!(' + dis + ') && (' + item[1] + ')')
                else:
                    group_end.node.config_dep.set_restrict(
                        item[0], '!(' + dis + ')')
    elif last_node.type == 'config':
        if group_end and group_end.node.type == 'choice' and group_end.node.detail.type == '':
            group_end.node.set_detail_type(last_node.detail.type)
        dis = ""
        for item in GROUP[1:]:
            if item.node.detail is not None:
                if len(item.display) > 0:
                    dis = check_line_and(dis) + '( ' + item.display + ' )'

        if len(last_node.dep_temp.get_display()) > 0:
            dis = check_line_and(dis) + last_node.dep_temp.get_display()
        else:
            dis = check_line_and(dis) + 'y'

        default = last_node.dep_temp.get_default()
        if len(dis) > 0:
            for item in default:
                if len(item) > 1:
                    last_node.config_dep.set_restrict(
                        item[0], '!(' + dis + ') && (' + item[1] + ')')
                else:
                    last_node.config_dep.set_restrict(item[0], '!(' + dis + ')')


def check_spword(char):
    if len(char) > 2 and char[0] == '"' and char[1] == '$':
        return "SP_WORD"
    elif len(char) > 1 and char[0] == '$':
        return "SP_WORD"


def set_groupDep_configDep(node):
    result = []
    for item in GROUP:
        if item.node.detail is not None:
            result.append(item.node.detail)
    if node.type == 'config':
        node.set_config_group(result)

    dep = ""
    for item in GROUP[1:]:
        if item.node.detail is not None:
            if len(item.node.detail.get_depends()) > 0:
                if item.node.detail.get_depends()[1] == '"' and item.node.detail.get_depends()[-1] == '"':
                    dep = check_line_and(dep) + item.node.detail.get_depends()
                else:
                    dep = check_line_and(dep) + '( ' + item.node.detail.get_depends() + ' )'

    node.config_dep.set_depends(dep)
    return node


##########################      yacc        ##########################
SELECT = {}  # {(father, kid) : [if_expr]}


def update_select(kid, if_expr):
    if len(if_expr) > 0:
        if_expr = '[' + if_expr + ']'
    else:
        if_expr = ""
    father = last_node.name
    key = (father, kid)
    if SELECT.get(key, None):
        SELECT[key].append(if_expr)
    else:
        SELECT[key] = [if_expr]


IMPLY = {}  # {(father, kid) : [group + config_dis + if_expr]}


def update_imply(kid, imply_if):
    key = (last_node.name, kid)
    if IMPLY.get(key, None):
        IMPLY[key].append(imply_if)
    else:
        IMPLY[key] = [imply_if]

display_count = -1

def test_print(func, p):
    global display_count
    display_count += 1
    if display_count == 0 and display_switch:
        line = ""
        for item in p:
            if isinstance(item, str):
                if item != '\n':
                    line += item.replace('\n\t\t', ' ').replace(
                        '\t\t', '').replace('\n', '') + ' '
            elif isinstance(item, dict):
                line += item['string'] + ' '
        if len(line) > 0:
            if len(func + ' : ' + line) > 50:
                result = func + ' : ' + line
                result = line[:50] + '...'
            else:
                result = func + ' : ' + line
            rows, columns = os.popen('stty size', 'r').read().split()
            print(("\rparse => " + result).ljust(int(columns) - 30),
                  end='\r',
                  flush=True)
    else:
        display_count = -1 if display_count == 100 else display_count

def handle_quote(target):
    if target is None:
        return target
    if len(target) >= 2 and (target[0] == '"' or target[0] == "'") and \
            (target[-1] == '"' or target[-1] == "'"):
        target = target[1:-1]
    return target


##########################      grammar     ##########################
PATH_STACK = []

root = config_class_Node("root", "root", 'root')
last_node = root
all_node = {}

GROUP = []


def reset_data():
    global root, last_node, all_node, choice_index, choice_index_list, SELECT, IMPLY, PATH_STACK, GROUP
    root = config_class_Node("root", "root", 'root')
    GROUP = [config_class_Group(root)]
    last_node = root
    all_node = {}
    choice_index = 0
    choice_index_list = []
    SELECT = {}
    IMPLY = {}
    PATH_STACK = []


PRECEDENCE = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'NOT'),
    ('left', 'OPEN_PARENT', 'CLOSE_PARENT'),
    ('left', 'GREATER_EQUAL'),
    ('left', 'LESS_EQUAL'),
    ('left', 'GREATER'),
    ('left', 'LESS'),
    ('left', 'UNEQUAL'),
    ('left', 'EQUAL'),
)


def p_input(p):
    """
    input : input mainmenu_stmt
        | input config_stmt
        | input menu_stmt
        | input if_stmt
        | input choice_stmt
        | input groupend_stmt
        | input comment_stmt
        | input source_stmt
        | input type_stmt
        | input depends_stmt
        | input select_imply_stmt
        | input prompt_stmt
        | input default_stmt
        | input help_stmt
        | input range_stmt
        | input visible_stmt
        | input modules_stmt
        | input optional_stmt

        | input path_stmt
        | input endpath_stmt

        | empty
    """
    # | input assignment_stmt
    test_print("input", p)


def p_path_stmt(p):
    """
    path_stmt : PATH QUOTE_WORD EOL
    """
    p[2] = handle_quote(p[2])
    PATH_STACK.append(p[2])

    test_print("path_stmt", p)


def p_endpath_stmt(p):
    """
    endpath_stmt : ENDPATH EOL
    """
    if len(PATH_STACK) > 0:
        PATH_STACK.pop()
    else:
        print("parse error => path")

    test_print("endpath_stmt", p)


def p_mainmenu_stmt(p):
    """
    mainmenu_stmt : MAINMENU QUOTE_WORD EOL
    """
    p[2] = handle_quote(p[2])
    global root
    root.set_type(p[1])
    root.set_name(p[2])
    root.set_path(PATH_STACK[-1])

    test_print("mainmenu_stmt", p)


##########################      config       ##########################


def p_config_stmt(p):
    """
    config_stmt : CONFIG WORD EOL
                | MENUCONFIG WORD EOL
    """
    set_last_node_dep()

    node = config_class_Node(p[2], p[1], PATH_STACK[-1])

    node = set_groupDep_configDep(node)

    Father = GROUP[-1]
    Father.node.kids.append(node)

    # if Father.node.type == 'choice' and Father.node.detail.type == 'tristate':
    #     node.config_dep.set_restrict('! y', '')

    set_last_node(node, 'config')

    # 记录需要打印数据，可能有重名config情况
    global all_node
    item = all_node.get(p[2], None)
    if not item:
        all_node[p[2]] = [node]
    else:
        all_node[p[2]].append(node)

    test_print("config_stmt " + p[1], p)


def p_comment(p):
    """
    comment_stmt : COMMENT QUOTE_WORD EOL
    """
    set_last_node_dep()

    p[2] = handle_quote(p[2])
    node = config_class_Node(p[2], p[1], PATH_STACK[-1])

    set_last_node(node, p[1])

    test_print("comment_stmt", p)


##########################      group       ##########################
def p_menu(p):  # depends visible
    """
    menu_stmt : MENU QUOTE_WORD EOL
    """
    set_last_node_dep()

    p[2] = handle_quote(p[2])
    node = config_class_Node(p[2], p[1], PATH_STACK[-1])

    set_last_node(node, p[1])

    GROUP.append(config_class_Group(node))

    test_print("menu_stmt", p)


def p_if(p):
    """
    if_stmt : IF expr EOL
    """
    set_last_node_dep()

    node = config_class_Node(p[2]['string'], p[1], PATH_STACK[-1])
    set_last_node(node, p[1])

    group = config_class_Group(node)
    group.set_group_dep(p[2]['dep'])
    GROUP.append(group)

    test_print("if_stmt", p)


choice_index = 0
choice_index_list = []


def p_choice(p):  # type prompt depends
    """
    choice_stmt : CHOICE WORD EOL
                | CHOICE EOL
    """
    set_last_node_dep()

    global choice_index, choice_index_list
    node = config_class_Node('choice' + str(choice_index), p[1], PATH_STACK[-1])
    choice_index_list.append(choice_index)
    choice_index += 1
    if p[2] != '\n':
        node.set_detail_value('prompt', p[2])

    node = set_groupDep_configDep(node)

    set_last_node(node, p[1])

    GROUP.append(config_class_Group(node))

    test_print("choice_stmt", p)


def p_groupend_stmt(p):
    """
    groupend_stmt : ENDMENU EOL
                | ENDIF EOL
                | ENDCHOICE EOL
    """
    target = GROUP.pop()

    if target.node.type == 'menu' and p[1] == 'endmenu':
        pass
    elif target.node.type == 'if' and p[1] == 'endif':
        pass
    elif target.node.type == 'choice' and p[1] == 'endchoice':
        ####################################################
        #
        # 实现choice组内互斥放在depends依赖里判断
        #
        ####################################################
        choice = target.node.detail
        child = target.node.kids

        if choice.type == 'bool':
            for item in child:
                choice_config = '( ' + item.name
                for tmp in child:
                    if tmp != item:
                        choice_config = check_line_and(choice_config)
                        choice_config += ' !' + tmp.name
                choice_config += ' )'
                item.config_dep.set_depends(choice_config)

        elif choice.type == 'tristate':
            pass
        else:
            print("warming, the choice group in {} has no type define! ".format(
                GROUP[-1].node.path))

    test_print("groupend_stmt " + p[1], p)


##########################     optional     ##########################


def p_type_option(p):
    """
    prompt_stmt_opt : QUOTE_WORD if_expr
                    | empty
    """
    if p[1] is None:
        p[0] = None
    else:
        p[1] = handle_quote(p[1])

        string = None
        dep = None
        if p[2] is None:
            string = p[1]
            dep = ""
        else:
            string = p[1] + p[2]['string']
            dep = p[2]['dep']
        p[0] = {
            'string': string,
            'dep': dep,
        }

    test_print("prompt_stmt_opt", p)


def p_type_stmt(p):  # config choice
    """
    type_stmt : INT prompt_stmt_opt EOL
            | HEX prompt_stmt_opt EOL
            | STRING prompt_stmt_opt EOL
            | BOOL prompt_stmt_opt EOL
            | TRISTATE prompt_stmt_opt EOL
    """
    last_node.set_detail_type(p[1])
    if GROUP[-1].node.type == 'choice' and GROUP[-1].node.detail.type == "":
        GROUP[-1].node.set_detail_type(p[1])
    if p[2] is not None:
        last_node.set_detail_value("prompt", p[2]['string'])

        if last_node.type == "choice":
            target = GROUP[-1]
            if target.node.type != 'choice':
                raise
            target.set_group_display(p[2]['dep'])
        elif last_node.type == 'config':
            last_node.dep_temp.set_display(p[2]['dep'])

    test_print("type_stmt", p)


def p_prompt_stmt(p):  # choice comment config
    """
    prompt_stmt : PROMPT QUOTE_WORD if_expr EOL
    """
    p[2] = handle_quote(p[2])

    if p[3] is None:
        last_node.set_detail_value("prompt", p[2])
    else:
        last_node.set_detail_value("prompt", p[2] + p[3]['string'])

        if last_node.type == "choice":
            target = GROUP[-1]
            if target.node.type != 'choice':
                raise
            target.set_group_display(p[3]['dep'])
        elif last_node.type == 'comment':
            pass
        elif last_node.type == 'config':
            last_node.dep_temp.set_display(p[3]['dep'])

    test_print("prompt_stmt", p)


def p_help_stmt(p):  # config choice
    """
    help_stmt : HELP HELP_CONTEXT EOL
            | HELP HELP_CONTEXT
    """
    help_context = p[2].replace('\n\t\t', ' ').replace('\t\t',
                                                       '').replace('\n', '')
    last_node.set_help(help_context)

    test_print("help_stmt", p)


def p_depends_stmt(p):  # config choice comment menu
    """
    depends_stmt : DEPENDS ON expr EOL
    """
    last_node.set_detail_value('depends', p[3]['string'])

    if last_node.type == "menu" or last_node.type == "choice":
        target = GROUP[-1]
        if target.node.type != last_node.type:
            raise
        target.set_group_dep(p[3]['dep'])
        if last_node.type == "choice":
            last_node.config_dep.set_depends('(' + p[3]['dep'] + ')')
    elif last_node.type == 'comment':
        pass
    elif last_node.type == 'config' or last_node.type == 'menuconfig':
        last_node.config_dep.set_depends('(' + p[3]['dep'] + ')')

    test_print("depends_stmt", p)


def p_select_imply_stmt(p):  # config
    """
    select_imply_stmt : SELECT QUOTE_WORD if_expr EOL
                    | SELECT WORD if_expr EOL
                    |  IMPLY WORD if_expr EOL
    """
    p[2] = handle_quote(p[2])

    if p[3] is None:
        last_node.set_detail_value(p[1], p[2])
        if last_node.type == 'config' or last_node.type == 'menuconfig':
            if p[1] == 'select':
                update_select(p[2], '')
            else:
                target = all_node.get(p[2], None)
                if target is None:
                    # last_node.dep_temp.set_imply([p[2], ''])
                    update_imply(p[2], '')

                else:
                    for item in target:
                        # 加子配置项的 ！dis
                        item.config_dep.set_restrict(last_node.name, '')
    else:
        last_node.set_detail_value(p[1], p[2] + ' ' + p[3]['string'])
        if last_node.type == 'config' or last_node.type == 'menuconfig':
            if p[1] == 'select':
                update_select(p[2], p[3]['dep'])
            else:
                target = all_node.get(p[2], None)
                if target is None:
                    # last_node.dep_temp.set_imply([p[2], p[3]['dep']])
                    update_imply(p[2], p[3]['dep'])
                else:
                    for item in target:
                        # 加子配置项的 ！dis
                        item.config_dep.set_restrict(last_node.name, p[3]['dep'])

    test_print("select_imply_stmt " + p[1], p)


def p_range_stmt(p):  # config
    """
    range_stmt : RANGE symbol symbol if_expr EOL
    """

    if p[4] is None:
        last_node.set_detail_value(
            p[1], '(' + p[2]['string'] + ' ' + p[3]['string'] + ')')
        last_node.config_dep.set_restrict(p[2]['dep'] + ' ' + p[3]['dep'], '')

    else:
        last_node.set_detail_value(
            p[1],
            '(' + p[2]['string'] + ' ' + p[3]['string'] + ')' + p[4]['string'])
        last_node.config_dep.set_restrict(p[2]['dep'] + ' ' + p[3]['dep'],
                                         p[4]['dep'])

    test_print("range_stmt", p)


def p_optional(p):  # choice
    """
    optional_stmt : OPTIONAL EOL
    """
    last_node.set_detail_value('optional', True)

    test_print("optional_stmt", p)


def p_default_stmt(p):  # config choice
    """
    default_stmt : DEFAULT expr if_expr EOL
                | DEF_BOOL expr if_expr EOL
                | DEF_TRISTATE expr if_expr EOL
    """
    # bool的choice完成组内config的互斥条件
    if p[1] == 'def_bool':
        last_node.set_detail_type('bool')
        if GROUP[-1].node.type == 'choice' and GROUP[-1].node.detail.type == "":
            GROUP[-1].node.set_detail_type('bool')
    elif p[1] == 'def_tristate':
        last_node.set_detail_type('tristate')
        if GROUP[-1].node.type == 'choice' and GROUP[-1].node.detail.type == "":
            GROUP[-1].node.set_detail_type('tristate')

    if last_node.detail.type == "" and re.fullmatch('[0-9]+', p[2]['string']):
        last_node.set_detail_type('int')
    elif last_node.detail.type == "" and p[2]['string'][:2] == '0x':
        last_node.set_detail_type('hex')

    if p[3] is None or p[3] == '\n':
        last_node.set_detail_value("default", p[2]['string'])
        if last_node.type == 'choice' or last_node.type == 'config':
            last_node.dep_temp.set_restrict([p[2]['dep']])
    else:
        last_node.set_detail_value("default",
                                  p[2]['string'] + ' ' + p[3]['string'])
        if last_node.type == 'choice' or last_node.type == 'config':
            last_node.dep_temp.set_restrict([p[2]['dep'], p[3]['dep']])

    test_print("default_stmt", p)


def p_visible_stmt(p):
    """
    visible_stmt : VISIBILE if_expr EOL
    """

    last_node.set_detail_value('prompt', p[2]['string'])

    if last_node.type == "menu" and p[2] is not None:
        target = GROUP[-1]
        if target.node.type != 'menu':
            raise
        target.set_group_display(p[2]['dep'])

    test_print("visible_stmt", p)


def p_modules_stmt(p):
    """
    modules_stmt : MODULES EOL
    """
    last_node.set_detail_value("modules", True)

    test_print("modules_stmt", p)


def p_source(p):
    """
    source_stmt : SOURCE QUOTE_WORD EOL
    """
    test_print("source_stmt", p)


##########################     other      ##########################


def p_symbol(p):
    """
    symbol : WORD 
        | QUOTE_WORD
        | SP_WORD
    """

    # 处理 '\$\(.*\)' 字符，降低dep的难度
    string = p[1]
    dep = p[1]
    if len(p[1]) > 0 and p[1][0] == '$':
        dep = 'SP_WORD'
    elif len(p[1]) > 1 and p[1][0] == '"' and p[1][1] == '$':
        dep = 'SP_WORD'
    elif len(p[1]) > 2 and p[1][0] == '"' and p[1][-1] == '"':
        if re.fullmatch(r'-?[0-9]+', p[1][1:-1]) or \
                (len(p[1]) == 1 and (p[1][1] == 'y' or p[1][1] == 'm' or p[1][1] == 'n')):
            dep = handle_quote(p[1])
    p[0] = {
        'string': string,
        'dep': dep,
    }

    test_print("symbol", p)


def p_if_expr(p):
    """
    if_expr : IF expr
            | empty
    """
    string = None
    dep = None
    if len(p) > 1 and p[1] != None:
        dep = p[2]['dep']
        string = " if " + p[2]['string']

    if string is None and dep is None:
        p[0] = None
    else:
        p[0] = {
            'string': string,
            'dep': dep,
        }
    test_print("if_expr", p)


def p_expr(p):
    """
    expr : symbol
	    | symbol LESS symbol
	    | symbol LESS_EQUAL symbol
	    | symbol GREATER symbol
	    | symbol GREATER_EQUAL symbol
	    | symbol EQUAL symbol
	    | symbol UNEQUAL symbol

        | NOT expr
	    | OPEN_PARENT expr CLOSE_PARENT
        | expr OR expr
	    | expr AND expr
    """
    string = None
    dep = None
    if len(p) == 2:
        string = p[1]['string']
        dep = p[1]['dep']
    elif len(p) == 3 and p[1] == '!':
        string = '! ' + p[2]['string']
        dep = '! ' + p[2]['dep']
    else:
        if p[2] == '<' or p[2] == '<=' or p[2] == '>' or p[2] == '>=' or p[
                2] == '=' or p[2] == '!=' or p[2] == '||' or p[2] == '&&':
            string = p[1]['string'] + ' ' + p[2] + ' ' + p[3]['string']
            dep = p[1]['dep'] + ' ' + p[2] + ' ' + p[3]['dep']
        elif p[1] == '(' and p[3] == ')':
            string = '( ' + p[2]['string'] + ' )'
            dep = '( ' + p[2]['dep'] + ' )'

    p[0] = {
        'string': string,
        'dep': dep,
    }

    test_print("expr", p)


##########################    assignment     ##########################

# def p_assigment_stmt(p):
#     '''
#     assignment_stmt : WORD assign_op assign_val EOL
#     '''

# def p_assign_op(p):
#     '''
#     assign_op : EQUAL
#             | COLON_EQUAL
#             | PLUS_EQUAL
#     '''

# def p_assign_val(p):
#     '''
#     assign_val : empty
#     '''


##########################    yacc default   ##########################
def p_empty(p):
    'empty :'


def p_error(p):
    if p is not None:
        if p.type != 'EOL':
            print("Syntax error!", end=" ")
            print(p)
            # print(p.lexer.lexdata[p.lexer.lexpos - 30:p.lexer.lexpos + 30])

parser = yacc.yacc()


######################### handle dep function #########################
def handle_select(target, lack_config):
    for item in target:
        father = item[0]
        kid = item[1]
        kid_ptr = all_node.get(kid, None)
        if kid_ptr is not None:
            for index in target[item]:
                if len(index) == 0:
                    for ptr in kid_ptr:
                        ptr.config_dep.set_select(father)
                else:
                    for ptr in kid_ptr:
                        ptr.config_dep.set_select(father + index)
        else:
            if kid not in lack_config:
                lack_config.append(kid)
    return lack_config


def handle_imply(target, lack_config):
    for item in target:
        father = item[0]
        kid = item[1]
        kid_node = all_node.get(kid, None)
        # 增加imply的group_dis
        if kid_node is not None:
            for restrict in target[item]:
                for ptr in kid_node:
                    kid_dis = ptr.dep_temp.get_display()
                    if_expr = ''
                    if len(kid_dis) > 0:
                        kid_dis = '!( ' + kid_dis + ' )'
                    if len(restrict) > 0:
                        kid_dis = check_line_and(kid_dis)
                        if_expr = kid_dis + restrict
                    ptr.config_dep.set_imply('( ' + father + ' )', if_expr)
        else:
            if kid not in lack_config:
                lack_config.append(kid)
    return lack_config


def ParseKconfig(file, config_file, dep_file, display):
    global display_switch
    display_switch = display

    reset_data()
    begin = time.time()
    parser.parse(utils_load_Kconfig(file), lexer=lexer)
    
    cost = time.time() - begin
    print("\nParse time\t\t{}".format(str(cost)))
    print("{:<40}".format("[Got All Config!]"))

    all_config = {}
    all_config_dep = {}
    for item in all_node:
        node_type = all_node[item][0].type
        if node_type == 'config' or node_type == 'menuconfig':
            all_config[item] = []
            all_config_dep[item] = []
            for tmp in all_node[item]:
                all_config[item].append(tmp.detail)
                all_config_dep[item].append(tmp.config_dep)
        if node_type == 'choice':
            all_config_dep[item] = []
            for tmp in all_node[item]:
                all_config_dep[item].append(tmp.config_dep)

    print("{:<40}".format("[Prepare write AllConfig]") + "file => " +
          config_file)
    utils_write_json_file(all_config, config_file)

    print("{:<40}".format("[Prepare write AllConfigDep]") + "file => " +
          dep_file)
    lack_config = handle_select(SELECT, [])
    lack_config = handle_imply(IMPLY, lack_config)
    utils_write_json_file(all_config_dep, dep_file)

