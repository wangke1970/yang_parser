#!/usr/bin/env python3
from yang_yacc_rfc import get_yang_object
import copy
import os
import re
import utils
import pickle
import yang_yacc_rfc
import sys
import signal
from itertools import chain

modules = {}

def create_data_all(w_dir):
    d = {}
    l = utils.file_name(w_dir)
    for i in l:
        print(w_dir + i)
        module_submodule_name, module_submodule = get_yang_object(w_dir + i)
        d[module_submodule_name] = module_submodule
    return d

def get_prefix_module(d):
    dd = {}
    for k,v in d.items():
        dd[k] = v['prefix']
    return dd
    
def submodule_to_module(d):
    l = []
    ll = []
    dd = {}
    for k,v in d.items():
        ll.extend(v['include_file'])
        if v['file_relationship'] != None:
            d[v['file_relationship']]['body'].children = v['body'].children + d[v['file_relationship']]['body'].children
            d[v['file_relationship']]['prefix']['modules_prefix'].update(v['prefix']['modules_prefix'])
            d[v['file_relationship']]['prefix']['prefix_modules'].update(v['prefix']['prefix_modules'])
            l.append(k)
    diff = set(ll) - set(l)
    if diff != set():
        print('Error: Lose submodule filename: ', diff, ' .yang file')
    for i in l:
        del d[i]
    for k,v in d.items():
        del v['file_relationship']
        del v['header']
        del v['include_file']
        dd[k] = v['body']
    return dd

def grouping_node_dict(node_list):
    d = {}
    for i in node_list:
        if i.type_name == 'grouping':
            i.parents = None
            d[i.leaf] = i.children
    return d        

def uses_grouping_stmt(node):
    state = 1
    while state:
        utils.preorder_add_parents(node)
        state = 0
        for i in node.children:
            if i.type_name == 'uses' and ':' not in i.leaf:
                ret = find_grouping_backward(i)                
                #refine-stmt extend
                for ii in i.children:
                    if ii.type_name == 'when':
                        ii.type_name = '_uses_when'
                        ii.children = ret
                        break
                ll = i.children
                node.children.extend(ll)
                node.children.extend(ret)
                node.children.remove(i)
                state = 1
                break
            elif i.type_name != 'uses' and i.children != []:
                uses_grouping_stmt(i)
            else:
                continue

def find_grouping_backward(node):
    state = 1
    node_tp = node.parents
    while state:
        for i in node_tp.children:
            if i.type_name == 'grouping' and i.leaf == node.leaf:
                tp = i.parents
                i.parents = None
                l = copy.deepcopy(i.children)
                i.parents = tp
                return l
            else:
                continue
        node_tp = node_tp.parents
        if node_tp == None:
            state = 0
    print('Error find grouping:',node.leaf)
    return None

def uses_grouping_stmt_otherfile(node):
    state = 1
    while state:
        state = 0
        for i in node.children:
            if i.type_name == 'uses' and ':' in i.leaf:
                ret = i.leaf.split(':')
                try:
                    dd = grouping_node_dict(modules[ret[0]].children)
                except Exception as e:
                    print('Error Lose file :',e,'.yang')
                    exit(0)                  
                try:
                    group_tp = dd[ret[1]]
                except Exception as e:
                    print('Error Lose grouping node :',ret[1],ret[0]+'.yang')
                    exit(0)
                l = copy.deepcopy(group_tp)
                # uses node children when node 
                for ii in i.children:
                    if ii.type_name == 'when':
                        ii.type_name = '_uses_when'
                        ii.children = l
                        break
                ll = i.children
                node.children.extend(ll)
                node.children.extend(l)
                node.children.remove(i)
                state = 1
                break
            elif i.type_name != 'uses' and i.children != []:
                uses_grouping_stmt_otherfile(i)
            else:
                continue        


def modules_parents_node():
    for k,_ in modules.items():
        utils.preorder_add_parents(modules[k])

def find_path(node):
    l = []
    g = utils.preorder_iter(node)
#    path_node = None
    for i in g:
        if i.type_name == 'path':
            l.append((i.leaf,i))
    if l == []:
        return None,None
    else:
        return l.pop()

def _find_node_list(node_name,node_list,prefix_name):
    for i in node_list:
        if node_name == i.leaf and i.type_name in ('container','leaf','list','leaf-list','identity','anyxml','identityref','anydata','rpc','input','output','action') and i.prefix==prefix_name:
            return i
        elif i.type_name =='choice':
            gg = utils.levelorder_iter(i)
            for ii in gg:
                if node_name == ii.leaf and ii.type_name in ('container','leaf','list','leaf-list','identity','anyxml','anydata','rpc','input','output','action') and ii.prefix==prefix_name:
                    return ii
        else:
            continue
    return None

# augment need include case choice stmt
def find_node_list_augment(node_name,node_list):
    for i in node_list:
        if node_name == i.leaf and i.type_name in ('container','leaf','list','leaf-list','identity','anyxml','anydata','choice','case','rpc','input','output','action','notification'):
            return i
        elif i.type_name =='choice':
            gg = utils.levelorder_iter(i)
            for ii in gg:
                if node_name == ii.leaf and ii.type_name in ('container','leaf','list','leaf-list','identity','anyxml','anydata','rpc','input','output','action'):
                    return ii
        else:
            continue
    return None

def find_descendant_schema_node(node):
    node_tp = node.parents
    if node_tp == None:
        print('find node error in find_descendant_schema_node step 1')
    else:        
        l = node.leaf.split('/')
        for i in l:
            for ii in node_tp.children:
                if i == ii.leaf:
                    node_tp = ii
                    break
    if node_tp == None:
        print('find path error in find_descendant_schema_node step 2')
    else:
        return node_tp
    
# path ../../../a/b/c 
def find_relative_path_node(node):
    node_tp = node
#    if node.leaf == "../../../../../huawei-l2vpn:ldp-signaling/huawei-l2vpn:pws/huawei-l2vpn:pw/huawei-l2vpn:negotiation-vc-id":
#        print("bbbbb")
#    if node.leaf == '../../../../interfaces/interface/name':
#    if node.leaf ==  '../../../../vlan-groups/vlan-group/id':
#        print('ccc')
    if '../' in node.leaf:
        l = node_tp.leaf.split('/')
        # jump out leafref         
        node_tp = node_tp.parents
        node_tp = node_tp.parents        
        for j in l:
            # jump out case choice
            while True:
                if node_tp.type_name in ('case','choice'):
                    node_tp = node_tp.parents
                elif node_tp.type_name=='type' and node_tp.leaf == 'union':
                    node_tp = node_tp.parents
                else:
                    break
            if j == '..':
                node_tp = node_tp.parents
            else:
                if ':' in j:
                    prefix_name,node_name = j.split(':')                   
                    node_tp = _find_node_list(node_name,node_tp.children,prefix_name)
                else:
                    node_tp = _find_node_list(j,node_tp.children,node_tp.prefix)
                if node_tp == None:
                    return None
    return node_tp         
    

def find_augment_path_node(node_path,prefix):
#    if node_path == '/openconfig-interfaces:interfaces/openconfig-interfaces:interface/openconfig-interfaces:subinterfaces/openconfig-interfaces:subinterface/openconfig-if-ip:ipv6/openconfig-if-ip:addresses/openconfig-if-ip:address':
#        print('aaaa')
#    if node_path == '/openconfig-interfaces:interfaces/openconfig-interfaces:interface/openconfig-interfaces:subinterfaces/openconfig-interfaces:subinterface':
#        print('aaaa')

    identifier = r'[_A-Za-z][._\-A-Za-z0-9]*'
    node_steps = r'(/' + identifier + r':' + identifier + r')+'
    prefix_str = re.match(node_steps,node_path).group()
    if prefix_str == node_path:
        ret = node_path.split('/')[-1].split(':')[0]
        node = modules[ret]
        ret = '/' + ret + ':'
        path_l = list(filter(None,node_path.split(ret)))
#        path_l = node_path.split(ret)
#        path_l.pop(0)
    else:
        node = modules[prefix]
        path_local = node_path.replace(prefix_str,'')
        path_l = list(filter(None,path_local.split('/')))
        path_l.insert(0,prefix_str)
#    if '/' in node_path and ':' in node_path:
#        ret = node_path.split('/')[-1].split(':')[0]
#    node = modules[ret]
    #try:
    #    node = modules[ret]
    #except Exception as e:
    #    print('Error Lose file prefix is :',e)
    #    exit(0)         
    if ':' in path_l[0]:
        node_tp = None
        gg = utils.levelorder_iter(node)
        for i in gg:
            if i.type_name == 'augment' and i.leaf == path_l[0]:
                for ii in i.children:
                    if ii.leaf == path_l[1]:
                        node_tp = i
                        path_l = path_l[1:]
                        break
            if node_tp:   
                break
    else:
        node_tp = node
    if node_tp == None:
        print('find_augment_path_node error in step 1:','node_name:',i.leaf,'path:',node_path)
        return node_tp
    for i in path_l:
        node_tp = find_node_list_augment(i,node_tp.children)
        if node_tp == None:
            print('find_augment_path_node error in step 2:','node_name:',i,'path:',node_path)
            return node_tp
    return node_tp            

"""        
def __find_absolute_path_node(node_path,module_name):
    if node_path == '/ietf-network-instance:network-instances/ietf-network-instance:network-instance/ietf-l2vpn:type':
        print('aaa')
    if '/' in node_path and ':' in node_path:
        ret = node_path.split('/')[-1].split(':')[0]
        node = modules[ret]
        ret = '/' + ret + ':'
        path_l = list(filter(None,node_path.split(ret)))                
    elif '/' in node_path and ':' not in node_path:
        node = modules[module_name]
        path_l = list(filter(None,node_path.split('/')))
    else:
        print('Error Syntax must absolute path step 1',node_path)
        return None
    node_tp = None
    for i in node.children:
        if i.leaf == path_l[0] and i.type_name == 'augment':
            node_tp = i
            break
        elif path_l[0] == i.leaf and i.type_name in ('container','leaf','list','leaf-list','identity','anyxml','identityref','anydata','rpc','input','output','action'):
            node_tp = i
            break
        else:
            continue
    if node_tp == None or node_tp.children == []:
        print('error in find_absolute_path_node step 1',node_path,module_name)
        return None
    for i in path_l[1:]:
        node_tp = find_node_list(i,node_tp.children)
        if node_tp == None:
            print('error in find_absolute_path_node in step 2:','node:',i,'node_path:',node_path)
            return node_tp
    return node_tp
"""    

def find_absolute_path_node(node_path,module_name):
#    if node_path == '/ietf-interfaces:interfaces/ietf-interfaces:interface/ietf-if-extensions:encapsulation/ietf-if-flexible-encapsulation:flexible/ietf-if-flexible-encapsulation:match/ietf-if-flexible-encapsulation:dot1q-vlan-tagged/ietf-if-flexible-encapsulation:outer-tag/ietf-if-flexible-encapsulation:vlan-id':
#        print('aaa')    
#    if node_path == '/network-instances/network-instance/config/name':
#        print('bbb')
    path_l = list(filter(None,node_path.split('/')))
    if ':' in path_l[0]:
        node = modules[path_l[0].split(':',1)[0]]
    else:
        node = modules[module_name]
    for i in path_l:
        if ':' in i:
            prefix_name,node_name = i.split(':',1)
        else:
            node_name = i
            prefix_name = module_name
        node = _find_node_list(node_name,node.children,prefix_name)
        if node==None:
            print('Error find node_name:',i,node_path)
            return None
    return node        

def path_stmt_syntax(node,module_name):
#    if node.type_name=='augment':
#        print('aaaa')
    if node.type_name == '_augment_when' or node.type_name == '_uses_when' or node.type_name=='typedef'or node.type_name=='augment' or node.type_name=='deviation':
        return
#    if node.type_name == 'path' and node.leaf == '/network-instances/network-instance/config/name':
#        print('ccc')
    elif node.type_name == 'path':
        node.leaf = node.leaf.lstrip()
        if '..' in node.leaf:
            node_tp = find_relative_path_node(node)
            if node_tp == None:
                print('find_relative_path_node error:',node.leaf,node.prefix)
                return
            # path in path
            nn,ret_node = find_path(node_tp)
            while nn:
                if '..' in nn:
                    node_tp = find_relative_path_node(ret_node)
                    nn,ret_node = find_path(node_tp)
                elif nn[0]=='/':
                    #node_module = ret_node.module_name()
                    node_module = ret_node.prefix
                    node_tp = find_absolute_path_node(nn,node_module)
                    nn,ret_node = find_path(node_tp)
                else:
                    pass
            node_up_up = node.parents.parents
            leaf_path_list = node_tp.node_path_list()
            leaf_path_str = '(/'+'/'.join(leaf_path_list)+')'
            leaf_path_str = leaf_path_str.replace('[0]','')
            path_point = yang_yacc_rfc.node('path_point',leaf_path_str,node_tp.children)
            l_tp = [path_point]           
            l_tp.extend(node_up_up.children)
            node_up_up.children = l_tp
            node_up_up.leafref = node.leaf_leaf
            for i in node_up_up.children:
                if i.type_name == 'type' and i.leaf == 'leafref':
                    node_up_up.children.remove(i)
                    break
        elif node.leaf[0]=='/':
            if ':' not in node.leaf:
                #module_name = node.module_name()
                module_name = node.prefix
            node_tp = find_absolute_path_node(node.leaf,module_name)
            if node_tp == None:
                #print('find absolute path node error:',node.leaf,node.prefix)
                return
            nn,ret_node = find_path(node_tp)
            while nn:
                if '..' in nn:
                    node_tp = find_relative_path_node(ret_node)
                    nn,ret_node = find_path(node_tp)
                elif nn[0]=='/':
                    #node_module = ret_node.module_name()
                    node_module = ret_node.prefix
                    node_tp = find_absolute_path_node(nn,node_module)
                    nn,ret_node = find_path(node_tp)
                else:
                    pass                    
            node_up_up = node.parents.parents
            leaf_path_list = node_tp.node_path_list()
            leaf_path_str = '(/'+'/'.join(leaf_path_list)+')'
            leaf_path_str = leaf_path_str.replace('[0]','')
            path_point = yang_yacc_rfc.node('path_point',leaf_path_str,node_tp.children)
            l_tp = [path_point]           
            l_tp.extend(node_up_up.children)
            node_up_up.children = l_tp
            node_up_up.leafref = node.leaf_leaf
            for i in node_up_up.children:
                if i.type_name == 'type' and i.leaf == 'leafref':
                    node_up_up.children.remove(i)
                    break            
        else:
            pass
    elif node.children != []:
        for i in node.children:
            path_stmt_syntax(i,module_name)
    else:
        return
    return 

def augment_stmt_node(node):
    g = utils.levelorder_iter(node)
    global augment_list
    for i in g:
        if i.type_name == 'augment'and i.leaf[0] == '/':
            ret = i.leaf.split('/')
            augment_list.append((len(ret),i))
        
def augment_stmt_syntax():
    global augment_list
    augment_list.sort(key = lambda x:x[0])
    for i in augment_list:
        node_tp = find_augment_path_node(i[1].leaf,i[1].prefix)
        if node_tp:
            node_tp.children.extend(i[1].children)
#        else:
#            print('error find_augment_path_node:',i[1].leaf)
        

def augment_descendant_syntax(node,module_name):
#    l = []
    g = utils.levelorder(node)
    for i in g:
#        ret = i.leaf.split('/'+ module_name + ':')
#        if i.type_name == 'augment'and i.leaf[0] == '/' and ret[0] == '':
#            l.append((len(ret),i))
#        elif i.type_name == 'augment' and i.leaf[0] != '/':
        if i.type_name == 'augment' and i.leaf[0] != '/':
            node_tp = find_descendant_schema_node(i)
            node_tp.children.extend(i.children)
        else:
            continue
#    l.sort(key = lambda x:x[0])
#    for i in l:
#        node_tp = find_augment_path_node(i[1].leaf)
#        if node_tp:
#            node_tp.children.extend(i[1].children)
#        else:
#            print('error find_augment_path_node:',i[1].leaf)
        
def find_typedef_localfile(node):
    tp_node = node.parents
    while tp_node:
        for i in tp_node.children:
            if i.type_name == 'typedef' and i.leaf == node.leaf:
                tp = i.parents
                i.parents = None
                ret = copy.deepcopy(i.children)
                i.parents = tp
                return ret
            else:
                continue
        tp_node = tp_node.parents
    print('Error Lose typedef node:',node.leaf,'in',node.module_name()+'.yang')
    return []

def type_stmt_localfile(node):
    base_type = ('binary','bits','boolean','decimal64','empty','enumeration','identityref','int8','int16','int32','int64','string','uint8','uint16','uint32','uint64','instance-identifier')
    if node.type_name == 'type' and node.leaf == 'leafref':
        pass
    elif node.type_name == 'type' and ':' not in node.leaf and node.leaf not in base_type and node.children == []:
        ret = find_typedef_localfile(node)
        node.children = ret
        for i in node.children:
            type_stmt_localfile(i)
    elif node.type_name != 'type' and node.children != []:
        for i in node.children:
            type_stmt_localfile(i)
    elif node.type_name == 'type' and node.leaf == 'union':
        for i in node.children:
            type_stmt_localfile(i)
    else:
        return    

def type_stmt_external(node,k):
    state = 1
    while state:
        state = 0
        gg = utils.levelorder_iter(node)
        for i in gg:
            if i.type_name == 'type' and ':' in i.leaf and i.children == [] and i.state == False:
                ret = i.leaf.split(':',1)
                try:
                    tp_node = modules[ret[0]]
                except Exception as e:
                    print('Error Lose file :',e,'.yang')
                    exit(1)
                utils.preorder_remove_parents(tp_node)
                for j in tp_node.children:
                    if j.type_name == 'typedef' and j.leaf == ret[1]:
                        i.children = copy.deepcopy(j.children)
                        #i.children = j.children
                        utils.preorder_add_parents(tp_node)
                        i.state = True
                        state = 1
                        break
                    else:
                        continue
            elif i.type_name == 'type' and ':' in i.leaf and i.children != [] and i.state == False:
                ret = i.leaf.split(':',1)
                try:
                    tp_node = modules[ret[0]]
                except Exception as e:
                    print('Error Lose file :',e,'.yang')
                    exit(1)
                utils.preorder_remove_parents(tp_node)
                for j in tp_node.children:
                    if j.type_name == 'typedef' and j.leaf == ret[1]:
                        i.children.extend(copy.deepcopy(j.children))
                        #i.children.extend(j.children)
                        utils.preorder_add_parents(tp_node)
                        i.state = True
                        state = 1
                        break
                    else:
                        continue

            else:
                continue
            break
                     

def path_module_node(node):
    if node.type_name in ('leaf','leaf-list','anyxml','anydata'):
        node.node_path_str()
        node.path_absolute_list=node.node_path_list()
        return
    elif node.type_name in ('container','list'):
        node.node_path_str()
        node.path_absolute_list=node.node_path_list()
        if node.children != []:
            for i in node.children:
                path_module_node(i)        
    elif node.type_name in ('rpc','action'):
        node.node_path_str()
        node.path_absolute_list=node.node_path_list()
        if node.children != []:
            for i in node.children:
                path_module_node(i)        
    else:
        if node.children != []:
            for i in node.children:
                path_module_node(i)
                
                
def node_add_constraint(node):
    gg = utils.levelorder(node)
    for i in gg:
        if i.type_name == 'when':
            if i.parents.type_name == 'augment':
                i.type_name = '_augment_when'
                for ii in i.parents.children:
                    if ii.type_name != '_augment_when':
                        i.children.append(ii)
        else:
            continue

def _module_namespaces(node):
    d = {}
    gg = utils.levelorder_iter(node)
    for i in gg:
        if i.type_name == 'module':
            module_str = i.leaf
            continue
        elif i.type_name == 'namespace':
            d[module_str] = i.leaf
            return d
        else:
            continue
    print('Error: Not find module namespace',node.leaf)
    return None
        
def node_add_prefix(prefix_name,node):
    gg = utils.levelorder_iter(node)
    for i in gg:
        if i.type_name == 'module':
            continue
        elif i.type_name == 'path' and ':' in i.parents.parents.leaf:
            i.prefix = i.parents.parents.leaf.split(':',1)[0]
        else:
            i.prefix = prefix_name
            
def refine_stmt_syntax(node,module_name):
    gg = utils.levelorder(node)
    for i in gg:
        if i.type_name == 'refine' and '/' not in i.leaf:
            for ii in i.parents.children:
                if ii.leaf == i.leaf and ii.type_name != 'refine':
                    ii.children.extend(i.children)
                    utils.preorder_add_parents(ii)
                    break
        elif i.type_name == 'refine' and '/'  in i.leaf:
            ret = find_descendant_schema_node(i)
            ret.children.extend(i.children)
            utils.preorder_add_parents(ret)
            break   

def typedef_stmt(node):
    base_type = ('binary','bits','boolean','decimal64','empty','enumeration','identityref','int8','int16','int32','int64','string','uint8','uint16','uint32','uint64','instance-identifier','union','leafref')
    gg = utils.levelorder_iter(node)
    for i in gg:
        if i.type_name == 'type' and i.leaf not in base_type:
            if i.parents.type_name == 'typedef' or i.parents.parents.type_name == 'typedef':
                if ':' in i.leaf:
                    find_typedef_external(i)
                else:
                    find_typedef_backward(i)
                i.state = True    
        else:
            continue

def find_typedef_backward(node):
    state = 1
    node_tp = node.parents
    while state:
        for i in node_tp.children:
            if i.leaf == node.leaf and i.type_name == 'typedef':
                node.children = i.children 
                return node
            else:
                continue
        node_tp = node_tp.parents
        if node_tp == None:
            state = 0
    print('Error find typedef node:',node.leaf)
    return None

def find_typedef_external(node):
    ret = node.leaf.split(':')[0]
    tp_node = modules[ret]
    for i in tp_node.children:
        if i.type_name == 'typedef' and node.leaf.split(':')[1] == i.leaf and node.state == False:
            node.children.extend(i.children)
            node.state = True
    return node

def add_constraint_path(node):
    gg = utils.levelorder_iter(node)
    l = []
    for i in gg:
        if i.type_name == 'config':
            i.parents.config = i.leaf
    gg = utils.levelorder_iter(node)    
    # container list config false ... 
    for i in gg:    
        if i.config == 'false':
            ggg = utils.levelorder_iter(i)
            for ii in ggg:
                ii.config = 'false'
            
def code_gen_module_node(node,code):
    if node.type_name in ('leaf','leaf-list','anyxml','anydata') and node.config == 'true':
        if node.path_absolute_list != None:
            ss = '/'.join(node.path_absolute_list)
            code.append(ss)
        return
    elif node.type_name in ('list','container') and node.config == 'true':
        if node.children != []:
            for i in node.children:
                code_gen_module_node(i,code)        
    elif node.type_name in ('augment','typedef'):
        return
    elif node.type_name in ('rpc','action'):
        return 
    else:
        if node.children != []:
            for i in node.children:
                code_gen_module_node(i,code)            


# Part of code comes from https://cloud.tencent.com/developer/article/1568246 
class TreeNode(object):
    def __init__(self, name, parent=None):
        super(TreeNode, self).__init__()
        self.name = name
        self.parent = parent
        self.child = {}
        self.x_path = ''
        # hash key
        self.data = ''

    def __repr__(self) :
        return 'TreeNode(%s)' % self.name

    def __contains__(self, item):
        return item in self.child

    def __len__(self):
        """return number of children node"""
        return len(self.child)

    def __bool__(self):
        """always return True for exist node"""
        return True

    @property
    def path(self):
        """return path string (from root to current node) recursion"""
        if self.parent:
            ret = '%s/%s' % (self.parent.path.strip(), self.name)
            return ret
        else:
            return self.name

    def get_child(self, name, default=None):
        """get a child node of current node"""
        return self.child.get(name, default)

    def get_child_node(self, name, default=None):
        """get a child node of current node"""
        try:
            value = self.child[name]            
        except Exception as e:
            print('Error Iputput')
            return None
        return value

    def get_child_node_dict(self):
        """get a child node of current node"""
        d = {}
        try:
            for k,v in self.child.items():
                d[k]=v.data
        except Exception as e:
            print('Error Iputput')
        return d

    def add_child(self, name, data, x_path):
        obj = TreeNode(name)
        obj.data = data
        obj.x_path = x_path
        obj.parent = self
        self.child[name] = obj
        return obj

    def del_child(self, name):
        """remove a child node from current node"""
        if name in self.child:
            del self.child[name]    
        
    def find_child_by_path(self, path, create=False):
        """find child node by path/name, return None if not found"""
        # convert path to a list if input is a string
        path = path if isinstance(path, list) else path.split()
        cur = self
        for sub in path:
            # search
            obj = cur.get_child(sub)
            if obj is None:
                print('Error path check')
                break
            cur = obj
        return obj

    def find_child_by_name(self,name):
        if name in self.child.keys():
            ret = self.child[name]
            print('H:'+ret.data,'➔','P:'+ret.x_path)
            for _,v in self.child.items():
                v.find_child_by_name(name)            
        else:
            for _,v in self.child.items():
                v.find_child_by_name(name)
                    
    def items(self):
        return self.child.items()

    def dump(self,ss,indent=0):
        """dump tree to string"""
        # ┣ ┠
        tab = '    '*(indent-1) + '├ ' if indent > 0 else ''
        if self.data == '':
            ret = '%s%s%s' % (tab, str(self.name),'\n')
        else:    
            ret = '%s%s%s%s' % (tab, str(self.name)+' ->' ,self.data,'\n')
        ss[0] += ret
        for name, obj in self.items():
            obj.dump(ss,indent+1)
        
    def get_parent(self):
        if isinstance(self.parent.name,str):
            return self.parent
        else:
            if isinstance(self.parent.name, int):
                return self.parent.parent
            else:
                return None

def add_root_tree_node():
    root = TreeNode('')
    return root

# no leaf leaf-list define
global hash_path
hash_path = {}
def add_tree_node_in_folder(tree_node,node,prefix):
    global hash_path
    if node.type_name in ('leaf','leaf-list','anyxml','anydata'):
        prefix.append(node.prefix)
        if node.config == 'true':
            hash_key = str(hash(node.path_absolute_for_xml))
            hash_path[hash_key] = node.path_absolute_for_xml
            hash_path[node.path_absolute_for_xml]=hash_key
            ret = tree_node.add_child(node.type_name + ' ' + node.leaf,hash_key,node.path_absolute_for_xml)
        else:
            ret = tree_node.add_child(node.type_name + ' ' + node.leaf,'','')
        return
    elif node.type_name in ('container','list'):
        prefix.append(node.prefix)        
        if node.config == 'true':
            hash_key = str(hash(node.path_absolute_for_xml))
            hash_path[hash_key] = node.path_absolute_for_xml
            hash_path[node.path_absolute_for_xml]=hash_key
            ret = tree_node.add_child(node.type_name + ' ' + node.leaf, hash_key,node.path_absolute_for_xml)
        else:
            ret = tree_node.add_child(node.type_name + ' ' + node.leaf, '','')
        if node.children != []:
            for i in node.children:
                add_tree_node_in_folder(ret,i,prefix)        
    elif node.type_name in ('container','list') and node.config == 'false':
        return
    elif node.type_name in ('typedef','augment'):
        return
    else:
        if node.type_name in ('input','output'):
            ret = tree_node.add_child(node.type_name,'','')
        else:    
            ret = tree_node.add_child(node.type_name + ' ' + node.leaf,'','')
        if node.children != []:
            for i in node.children:
                add_tree_node_in_folder(ret,i,prefix)

# include leaf and leaf-list define 
def _add_tree_node_in_folder(tree_node,node):
    global hash_path
    if node.type_name in ('leaf','leaf-list','anyxml','anydata'):
        path = ''
        if hasattr(node, 'leafref'):
            path = '(path ' + node.leafref +')' 
        ret = tree_node.add_child(node.type_name + ' ' + node.leaf + path ,str(hash_path[node.path_absolute_for_xml]),node.path_absolute_for_xml)
        if node.children != []:
            for i in node.children:
                _add_tree_node_in_folder(ret,i)
    elif node.type_name in ('container','list') and node.config == 'true':
        ret = tree_node.add_child(node.type_name + ' ' + node.leaf, str(hash_path[node.path_absolute_for_xml]),node.path_absolute_for_xml)
        if node.children != []:
            for i in node.children:
                _add_tree_node_in_folder(ret,i)        
    elif node.type_name in ('container','list') and node.config == 'false':
        return
    elif node.type_name in ('typedef','augment'):
        return    
    else:
        ret = tree_node.add_child(node.type_name + ' ' + node.leaf,'','')
        if node.children != []:
            for i in node.children:
                _add_tree_node_in_folder(ret,i)
        return

def tree_dump(node):
    root = add_root_tree_node()
    try:
        _add_tree_node_in_folder(root,node)
    except Exception as e:
        print('input error check module name!',e)
    ss = {0:''}
    root.dump(ss)
    return ss[0]

def handler(signum, frame):
    exit()

def yang_stmt_node(w_dir):
    #'description',
    remove_node = ('description','reference','import','include','revision','yang-version','organization','contact','belongs-to','prefix',None)
    d = create_data_all(w_dir)
    global prefix_module
    global modules
    global module_namespace
    prefix_namespace = {}

    modules = submodule_to_module(d)
    prefix_module = get_prefix_module(d)
    modules_check_01 = [*prefix_module]
    modules_check_02 = [list(v['modules_prefix'].keys()) for v in prefix_module.values()]    
    modules_check_02 = set(tuple(list(chain.from_iterable(modules_check_02))))    
    lose_modules = [i for i in modules_check_02 if i not in modules_check_01]
    if lose_modules != []:
        print('Warning lose module file ..... :', lose_modules,'.yang')
    for k,_ in modules.items():
        utils.remove_stmt(modules[k],remove_node)        

# start type-stmt
    print('Starting type-stmt analysis ......')
    modules_parents_node()
    for k,_ in modules.items():
        typedef_stmt(modules[k]) 
    for k,_ in modules.items():
        type_stmt_external(modules[k],k)    
    for k,_ in modules.items():
        type_stmt_localfile(modules[k])
    modules_parents_node()
    
# start grouping-stmt  
    print('Starting grouping-stmt analysis ......')
    for k,_ in modules.items():
        uses_grouping_stmt(modules[k])
    for k,_ in modules.items():
        uses_grouping_stmt_otherfile(modules[k])         
    modules_parents_node()

# Start refine_stmt
    print('Starting refine-stmt analysis ......')
    for k,_ in modules.items():    
        refine_stmt_syntax(modules[k],k)
    for k,_ in modules.items():
        utils.remove_stmt(modules[k],('grouping','refine'))

# every node add prefix for namespace        
    print('Starting every node add prefix for namespace ...')
    for k,_ in modules.items():
        node_add_prefix(k,modules[k])           

# Start every node add constraint ...
    print('Start every node add constraint ......')
    for k,_ in modules.items():    
        node_add_constraint(modules[k])

# start augment_stmt
    print('Starting augment-stmt analysis ......')
    for k,_ in modules.items():
        augment_descendant_syntax(modules[k],k)
    global augment_list
    augment_list = []
    for k,_ in modules.items():
        augment_stmt_node(modules[k])
    augment_stmt_syntax()    

    for k,_ in modules.items():
        utils.preorder_add_parents_no_augment(modules[k])

# start path-stmt
    print('Starting path-stmt analysis ......')
    for k,_ in modules.items():
        path_stmt_syntax(modules[k],k)  

# Start every node add path ...
    print('Strat every node add path like /a/b/c/d......')
    for k,_ in modules.items():
        path_module_node(modules[k])

# Start add config
    for k,_ in modules.items():
        add_constraint_path(modules[k])


# dict prefix to namespace
    module_namespace ={}
    for k,_ in modules.items():
        module_namespace.update(_module_namespaces(modules[k]))

    f = open('yang_modules','wb')
    yang_object = (modules, module_namespace,prefix_module)
    pickle.dump(yang_object,f)
    
    return  modules, module_namespace,prefix_module

if __name__ == '__main__':

#    yang_module = yang_stmt_node('/home/wang/source/test_ply/bgp/')
#    yang_module = yang_stmt_node('/home/wang/source/test_ply/HUAWEI/')
#    yang_module = yang_stmt_node('/home/wang/source/test_ply/ChinaTeleCom/')
#    yang_module = yang_stmt_node('/home/wang/source/test_ply/optical-transport/')
#    yang_module = yang_stmt_node('/home/wang/source/test_ply/ZTE/')
    sys.setrecursionlimit(3000)
    if len(sys.argv) == 1:
        try:
            f = open('yang_modules','rb')
            yang_module = pickle.load(f)
        except Exception as e:
            print('Please input yang file directory ! [Error]:',e)
            exit()
    elif len(sys.argv) == 2:
#        try:
        yang_dir = sys.argv[1]
        yang_module = yang_stmt_node(yang_dir)
#        except Exception as e:
#            print('Please input yang file directory like /a/b/c/ ! [Error directory]:',e)
#            exit()
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)            
    while True:
        module_name_list = list(yang_module[2].keys())
        print('Choice Modeule:',module_name_list)
        try:
            module_name = input('module >')
        except Exception as e:
            break
        if module_name not in module_name_list:
            continue    
        root = add_root_tree_node()
        prefix = []
        try:
            add_tree_node_in_folder(root,yang_module[0][module_name],prefix)
        except Exception as e:
            print('input error check module name!',e)
            continue
        prefix = list(set(prefix))
        sss = {0:''}
        root.dump(sss)
        hash_all_tree = sss[0]
        ret_node_tree = root
        path_path = None
        ns_ns = yang_module[1]
        ns_short_list = [v['modules_prefix'] for _,v in yang_module[2].items()]
        ns_short = {}
        for i in ns_short_list:
            ns_short.update(i)
        while True:
            
            if path_path:
                path_path = path_path.replace('container ','').replace('list ','').replace('leaf-list ','').replace('leaf ','').replace('module ','')
                xml_path = input(path_path+'>')
            else:    
                ret_node_tree = ret_node_tree.child['module '+module_name]
                xml_path = input('/'+module_name+'>')
                path_path = ret_node_tree.path
            if xml_path == '':
                continue
            if xml_path == 'exit':
                break
            if xml_path == '*':
                print(hash_all_tree)
                continue
            if re.match(r'[-]?[0-9]+',xml_path):
                try:
                    def ns_matched(matched):
                        node_str = matched.group('ns')
                        node_str = node_str[0:-1]
                        return ns_short[node_str]+':'
                    
                    xml_path = xml_path.strip()
                    xml_path = hash_path[xml_path]
                    gg = utils.levelorder_iter(yang_module[0][module_name])
                    for i in gg:
                        if i.path_absolute_for_xml == xml_path:
                            print(tree_dump(i))
                            code = []
                            code_gen_module_node(i,code)
                            print('<Node>:')
                            print(' ',re.sub('(?P<ns>[_A-Za-z][._\-A-Za-z0-9]*:)',ns_matched,xml_path[1:]))
                            print('<SubNode>:')
                            if i.type_name in ('leaf','leaf-list'):
                                break
                            for c_s in code:
                                code_str = c_s
                                code_str_s = c_s.replace(xml_path[1:]+'/','')
                                code_str = re.sub('(?P<ns>[_A-Za-z][._\-A-Za-z0-9]*:)',ns_matched,code_str)
                                code_str_s = re.sub('(?P<ns>[_A-Za-z][._\-A-Za-z0-9]*:)',ns_matched,code_str_s)
                                #print(code_str)
                                print(' ',code_str_s)
#                            print(' List(list or leaf-list) node only one can replace [{}] to : ')  
#                            print(' [@nc:operation=create/insert/merge/replace @yang:create/insert/merge/replace=first/last/before/after https://localhost:8051/[@yang:value=xx>xxx]]')
#                            print(' if @nc:operation=create/insert/merge/replace in rpc')
#                            print(' [@yang:create/insert/merge/replace=first/last/before/after, [@yang:value=xxx]]')
                            break
                        else:
                            continue                    
                except Exception as e:
                    print('input error check node hash name!',e)
                    continue
            if re.match(r'cd [_A-Za-z][._\-A-Za-z0-9]*',xml_path):
                ret_node = xml_path.replace('cd ','').strip() 
                ret_tp = ret_node_tree.get_child_node(ret_node)
                if ret_tp:
                    ret_node_tree = ret_tp
                path_path = ret_node_tree.path
                continue
            # example find(leaf is-login-anytime)
            if re.match(r'find\([_A-Za-z][._\-A-Za-z0-9]* [_A-Za-z][._\-A-Za-z0-9]*\)',xml_path):
                ret_node_tree.find_child_by_name(xml_path.replace('find','').replace('(','').replace(')','').strip())
                continue
            if xml_path =='dir': 
                module_nodes = ret_node_tree.get_child_node_dict()
                for k,v in module_nodes.items():
                    if v:
                        print(k+'     ->'+v)
                    else:
                        print(k)
                path_path = ret_node_tree.path
                continue
            if xml_path =='.':
                path_path=''
                ret_node_tree = root
                continue
            if xml_path =='cd ..':
                ret_node_tree = ret_node_tree.get_parent()
                path_path = ret_node_tree.path
                continue
            if xml_path =='namespaces':
                ns_ns = yang_module[1]
                print('Show Module Prefix :')
                print(prefix)
                print("Namespaces in yang module :")
                print({k:v for k,v in ns_ns.items() if k in prefix})
                print("Module name to prefix :")
                print({k:v for k,v in ns_short.items() if k in prefix})
                print("Add namespace yang nc if need :")
                print("{'yang':'urn:ietf:params:xml:ns:yang:ietf-yang-types','nc':'urn:ietf:params:xml:ns:netconf:base:1.0'}")
                
    print('End...')
