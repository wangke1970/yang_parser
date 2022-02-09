import os

def file_name(file_dir):
    l =[]
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.yang':
                l.append(os.path.join(file))
    return l

def preorder(node):
    if not node:
        return []
    ret = []
    node_list = [node]
    while node_list:
        node = node_list.pop(0)
        if node:
            ret.append(node)
            for i in node.children[::-1]:
                node_list.insert(0,i)
    return ret

def preorder_iter(node):
    if not node:
        return []
    node_list = [node]
    while node_list:
        node = node_list.pop(0)
        if node:
            yield node
            for i in node.children[::-1]:
                node_list.insert(0,i)
    return True 

def preorder_add_parents(node):
    if not node:
        return []
    ret = []
    node_list = [node]
    while node_list:
        node = node_list.pop(0)
        if node:
            if node.type_name in ('_uses_when','_augment_when'):
                continue            
            ret.append(node)
            for i in node.children[::-1]:
                i.parents = node
                node_list.insert(0,i)
    return ret  
            
def preorder_add_parents_no_augment(node):
    if not node:
        return []
    ret = []
    node_list = [node]
    while node_list:
        node = node_list.pop(0)
        if node:
            if node.type_name in ('augment','leaf','leaf-list','_uses_when','_augment_when'):
                continue
            ret.append(node)
            for i in node.children[::-1]:
                i.parents = node
                node_list.insert(0,i)
    return ret

def preorder_remove_parents(node):
    if not node:
        return []
    ret = []
    node_list = [node]
    while node_list:
        node = node_list.pop(0)
        if node:
            ret.append(node)
            for i in node.children[::-1]:
                i.parents = None
                node_list.insert(0,i)
    return ret  

def levelorder(node):
    if not node:
        return []
    level = [node]
    ret = []
    while level:
        for node in level:
            ret.append(node)
        level = [child for node in level for child in node.children]
    return ret

def levelorder_iter(node):
    if not node:
        return []
    level = [node]
    while level:
        for node in level:
            yield node
        level = [child for node in level for child in node.children]
    return True

def remove_stmt(node,l):
    state = 1
    while state:
        state = 0
        for i in node.children:
            if i.type_name in l:
                node.children.remove(i)
                state = 1
                break
            else:
                remove_stmt(i,l)
                
          

