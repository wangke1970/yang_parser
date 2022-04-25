import ply.yacc as yacc
# Get the token map from the test_yang_lexer_rfc . This is required.
from yang_lexer_rfc import tokens
from yang_lexer_rfc import yang_lexer
import os
import sys
import logging
import utils
import re

class node:
    def __init__(self,type_name,leaf = None,children = None):
        self.type_name = type_name
        self.parents = None
        self.path_absolute_for_xml = ''
        self.path_absolute_list = None
        self.leaf_leaf = None
        self.state = False
        self.prefix = None
        self.config = 'true'
        if children:
            self.children = children
        else:
            self.children = []
        if isinstance(leaf, str):    
            if self.type_name in ('when','must'):
                self.leaf = leaf
            else:    
                self.leaf = leaf.replace('\"','').replace("\'",'')
        else:
            self.leaf = leaf

    def node_path_str(self):
        if self.type_name == 'module':
            self.path_absolute_for_xml = ''
        else:
            if self.type_name in ('leaf-list','list'):
                self.path_absolute_for_xml = '/' + self.prefix + ':' + self.leaf+'[{}]'
            else:
                self.path_absolute_for_xml = '/' + self.prefix + ':' + self.leaf
        tp = self.parents
        while tp:
            if tp.type_name in ('choice','case','module','input','output'):
                pass
            else:
                if tp.type_name == 'augment':
                    self.path_absolute_for_xml = tp.leaf +  self.path_absolute_for_xml
                else:    
                    if tp.type_name in ('leaf-list','list'):
                        self.path_absolute_for_xml = '/' + tp.prefix + ':' + tp.leaf + '[{}]' +  self.path_absolute_for_xml
                    else:    
                        # rpc add type_name and leaf
                        if tp.type_name == 'rpc':
                            self.path_absolute_for_xml = '/' + tp.prefix + ':' + tp.type_name + '/' + tp.prefix + ':' + tp.leaf +  self.path_absolute_for_xml
                        else:
                            self.path_absolute_for_xml = '/' + tp.prefix + ':' + tp.leaf +  self.path_absolute_for_xml
            tp = tp.parents
        return self.path_absolute_for_xml       

    def node_path_list(self):
        l=[]
        if self.type_name == 'module':
#            self.path_absolute_list = []
            pass    
        else:
            if self.type_name in ('leaf-list','list'):
#                self.path_absolute_list = [self.prefix+':'+ self.leaf+"[0]"]
                l.append(self.prefix+':'+ self.leaf+"[{}]")
            else:
#                self.path_absolute_list = [self.prefix+':'+ self.leaf]
                l.append(self.prefix+':'+ self.leaf)
        tp = self.parents
        while tp:
            if tp.type_name in ('choice','case','module','input','output'):
                pass
            else:
                if tp.type_name == 'augment':
#                    self.path_absolute_list = [tp.leaf] +  self.path_absolute_list
                    pass
                else:    
                    if tp.type_name in ('leaf-list','list'):
#                        self.path_absolute_list = [tp.prefix+':'+ tp.leaf+"[0]"] +  self.path_absolute_list
                        l.insert(0,tp.prefix+':'+ tp.leaf+"[{}]")
                    else:
#                        self.path_absolute_list = [tp.prefix+':'+ tp.leaf] +  self.path_absolute_list
                        if tp.type_name == 'rpc':
                            l.insert(0,tp.prefix+':'+ tp.leaf)
                            l.insert(0,tp.prefix+':'+ tp.type_name)
                        else:
                            l.insert(0,tp.prefix+':'+ tp.leaf)
            tp = tp.parents
        return l       


    def module_name(self):
        while True:
            if self.type_name != 'module':
                self = self.parents
                if self == None:
                    print('maybe parents error')
                    return None
            else:
                break
        return self.leaf
"""
                
    # augment include case choice stmt      
    def node_path_list_augment(self):
        l = []
        l.append(self.leaf)
        tp = self.parents
        while tp:
            l.insert(0,tp.leaf)
            tp = tp.parents
        return l

    def level_next(self):
        node_tp = self.parents
        if node_tp == None:
            return None
        index_num = node_tp.children.index(self)
        if index_num == None:
            print('error get next node not in array!')
        list_len = len(node_tp.children)
        list_len = list_len - 1
        index_num = index_num + 1
        if index_num > list_len:
            return node_tp.children[list_len]
        else:
            return node_tp.children[index_num]

    def erase(self):
        node_tp = self.parents
        if node_tp == None:
            return None
        self.parents = None
        node_tp.children.remove(self)
        return 1
"""

logging.basicConfig(
    level = logging.DEBUG,
    filename = "parselog.txt",
    filemode = "w",
    format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

def yang_parser():
    include_file = []
    import_file = []
    def p_yang(p):
        """yang : module_stmt
                | submodule_stmt
        """
        p[0] = p[1]
        
    def p_module_stmt(p):
        """module_stmt : MODULE identifier_arg_str block
        """
        p[0] = node(p[1],p[2],p[3])
        
    def p_submodule_stmt(p):
        """submodule_stmt : SUBMODULE identifier_arg_str block
        """
        p[0] = node(p[1],p[2],p[3])
        
    def p_block(p):
        """block  : '{' elements '}'   
        """
        p[0] = p[2]
        
    
    def p_elements(p):
        """elements : empty
                    | stmts
        """
        p[0] = p[1]             
        
    def p_stmts(p):
        """stmts : stmt
                 | stmts stmt
        """                  
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[1].append(p[2])
            p[0] = p[1]
    
    def p_stmt(p):
        """stmt : block
                | yang_version_stmt
                | belongs_to_stmt
                | namespace_stmt
                | prefix_stmt
                | organization_stmt
                | contact_stmt
                | description_stmt
                | reference_stmt
                | revision_stmt
                | import_stmt
                | include_stmt
                | extension_stmt
                | feature_stmt
                | identity_stmt
                | typedef_stmt
                | grouping_stmt
                | augment_stmt
                | rpc_stmt
                | notification_stmt
                | deviation_stmt
                | container_stmt
                | leaf_stmt
                | leaf_list_stmt
                | choice_stmt
                | anydata_stmt
                | anyxml_stmt
                | uses_stmt  
                | revision_date_stmt
                | status_stmt
                | argument_stmt
                | yin_element_stmt
                | units_stmt
                | default_stmt
                | error_message_stmt
                | error_app_tag_stmt
                | modifier_stmt
                | value_stmt
                | position_stmt
                | presence_stmt
                | config_stmt
                | input_stmt
                | output_stmt
                | when_stmt
                | must_stmt
                | base_stmt
                | if_feature_stmt
                | range_stmt
                | enum_stmt
                | type_stmt
                | pattern_stmt
                | length_stmt
                | path_stmt
                | require_instance_stmt
                | bit_stmt
                | mandatory_stmt
                | action_stmt
                | fraction_digits_stmt
                | list_stmt
                | ordered_by_stmt
                | min_elements_stmt
                | max_elements_stmt
                | key_stmt
                | unique_stmt
                | case_stmt
                | refine_stmt
                | deviate_op_stmt
                | ext_stmt

        """
        p[0] = p[1]
        
    def p_ext_stmt(p):
        """ext_stmt : identifier string ';'
                    | identifier ';'
                    | identifier string block
                    | identifier block
                    | identifier identifier block
                    | identifier identifier ';'
        """
        if len(p) == 4 and p[3] == ';':
            p[0] = node(p[1],p[2],[])
        elif len(p) == 4 and p[3] != ';':
            p[0] = node(p[1],p[2],p[3])
        elif len(p) == 3 and p[2] == ';':            
#            p[0] = node(p[1],p[1])
            p[0] = node(p[1],'')            
        elif len(p) == 3 and p[2] !=';':
            p[0] = node(p[1],p[1],p[2])
        else:
            p[0] = node(p[1],p[1],p[3])
        
    
    def p_action_stmt(p):
        """action_stmt : ACTION identifier_arg_str ';'
                       | ACTION identifier_arg_str block
        """    
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
 
    def p_input_stmt(p):
        """input_stmt : INPUT block 
        """             
        p[0] = node(p[1],p[1],p[2])

    def p_output_stmt(p):
        """output_stmt : OUTPUT block 
        """             
        p[0] = node(p[1],p[1],p[2])
    
    def p_yang_version_stmt(p):
        """yang_version_stmt : YANG_VERSION integer_value_str ';' 
        """
        p[0] = node(p[1],p[2])
    
    def p_import_stmt(p):
        """import_stmt : IMPORT identifier_arg_str block
        """    
        p[2] = p[2].replace('\"','').replace("\'",'')
        p[0] = node(p[1],p[2],p[3])
                    
    def p_include_stmt(p):
        """include_stmt : INCLUDE identifier_arg_str ';'
                        | INCLUDE identifier_arg_str block
        """
        p[0] = node(None,None)
        p[2] = p[2].replace('\"','').replace("\'",'')
        include_file.append(p[2])
    
    def p_namespace_stmt(p):
        """namespace_stmt : ns ';'
                          | NAMESPACE string ';'
        """
        if p[2]==';':
            s = p[1].replace('namespace','').replace('"','').replace("'",'').replace(' ','').replace('\t','').replace('\n','').replace('\r','')
            p[0] = node('namespace',s)
        else:
            p[0] = node(p[1],p[2])
    
    def p_prefix_stmt(p):
        """prefix_stmt : PREFIX string ';'
                       | PREFIX identifier ';'
        """
        p[0] = node(p[1],p[2])
        
    def p_belongs_to_stmt(p):
        """belongs_to_stmt : BELONGS_TO identifier_arg_str block
        """
        p[0] = node(p[1],p[2],p[3])
                                                         
    def p_organization_stmt(p):
        """organization_stmt : ORGANIZATION string ';'
                             | ORGANIZATION identifier ';'
        """
        p[0] = node(p[1],p[2])
        
#    def p_contact_stmt(p):
#        """contact_stmt : contact ';'
#        """ 
#        s = p[1].replace('contact','').replace('"','').replace("'",'').replace(' ','').replace('\t','').replace('\n','').replace('\r','')
#        p[0] = node('contact',s)
        
    def p_contact_stmt(p):
        """contact_stmt : CONTACT string ';'
                        | CONTACT identifier ';'
        """ 
        p[0] = node(p[1],p[2])


    def p_description_stmt(p):
        """description_stmt : DESCRIPTION string ';'
                            | DESCRIPTION identifier ';'
        """
        p[0] = node(p[1],p[2])
        
    def p_reference_stmt(p):
        """reference_stmt : REFERENCE string ';'
                          | REFERENCE identifier ';'
        """    
        p[0] = node(p[1],p[2])
    
#    def p_units_stmt(p):
#        """units_stmt : UNITS string ';'
#                      | UNITS identifier ';'
#                      | UNITS descendant_schema_nodeid ';'
#        """
#        p[0] = node(p[1],p[2])

    def p_units_stmt(p):
        """units_stmt : xxxunits
                      | UNITS string ';'
        """
        if len(p)==4:
            p[0] = node(p[1],p[2])
        else:    
            s = p[1].replace('units','').replace('"','').replace("'",'').replace(' ','').replace('\t','').replace('\n','').replace('\r','').replace(';','')
            p[0] = node('units',s)


    def p_revision_stmt(p):
        """revision_stmt : REVISION string ';'
                         | REVISION string block
                         | REVISION ID ';'
                         | REVISION ID block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
               
    def p_revision_date_stmt(p):
        """revision_date_stmt : REVISION_DATE string ';'
                              | REVISION_DATE ID ';'
        """
        p[0] = node(p[1],p[2])
        
    def p_extension_stmt(p):
        """extension_stmt : EXTENSION identifier_arg_str ';'
                          | EXTENSION identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_argument_stmt(p):
        """argument_stmt : ARGUMENT identifier_arg_str ';'
                         | ARGUMENT identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_yin_element_stmt(p):
        """yin_element_stmt : YIN_ELEMENT yin_element_arg ';'
        """
        p[0] = node(p[1],p[2])
        
    def p_yin_element_arg(p):
        """yin_element_arg : identifier
                           | string
        """
        p[0] = p[1]
    
    def p_identity_stmt(p):
        """identity_stmt : IDENTITY identifier_arg_str ';'
                         | IDENTITY identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
    
    def p_base_stmt(p):
        """base_stmt : BASE identifier_ref_arg_str ';' 
        """
        p[0] = node(p[1],p[2])
             
    def p_identifier_ref_arg_str(p):
        """identifier_ref_arg_str : identifier_ref_arg
                                  | string
        """
        p[0] = p[1]
        
    def p_identifier_ref_arg(p):
        """ identifier_ref_arg : identifier
    
        """
        p[0] = p[1]
    
    def p_feature_stmt(p):
        """feature_stmt : FEATURE identifier_arg_str ';'
                        | FEATURE identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
    
    def p_if_feature_stmt(p):
        """if_feature_stmt : IF_FEATURE if_feature_expr_str ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_if_feature_expr_str(p):
        """if_feature_expr_str : if_feature_expr
                               | string
        """
        p[0] = p[1]
    
    def p_if_feature_expr(p):
        """if_feature_expr : if_feature_term
                           | if_feature_expr OR if_feature_term
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + 'or' + p[2]
    
    def p_if_feature_term(p):
        """if_feature_term : if_feature_factor
                           | if_feature_term AND if_feature_factor
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + 'and' + p[2]
                           
    def p_if_feature_factor(p):
        """if_feature_factor : NOT if_feature_factor
                             | '(' if_feature_expr ')' 
                             | identifier_ref_arg
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = node(p[1],p[2])
        else:
            p[0] = p[2]
        
    def p_typedef_stmt(p):
        """typedef_stmt : TYPEDEF identifier_arg_str block
        """
        p[0] = node(p[1],p[2],p[3])
    
    def p_type_stmt(p):
        """type_stmt : TYPE identifier_ref_arg_str ';'
                     | TYPE identifier_ref_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])        
        else:
            p[0] = node(p[1],p[2],p[3])
             
    
    def p_fraction_digits_stmt(p):
        """fraction_digits_stmt : FRACTION_DIGITS string ';'
                                | FRACTION_DIGITS identifier ';'
        """
        p[0] = node(p[1],p[2])
        
    def p_length_stmt(p):
        """length_stmt : LENGTH length_arg_str ';'
                       | LENGTH length_arg_str block                    
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
    
    def p_length_arg_str(p):
        """length_arg_str : string
                          | identifier
        """        
        p[0] = p[1]
        
        
#    def p_length_arg(p):
#        """length_arg : length_part
#                      | length_arg  '|' length_part
#        """
#        if len(p) == 4:
#            p[0] = p[1] + '|' + str(p[3])
#        else:
#            p[0] = str(p[1])

    
#    def p_length_part(p):
#        """length_part : length_boundary
#                       | length_boundary '.' '.' length_boundary
#        """
#        if len(p) == 2:
#            p[0] = str(p[1])
#        else:
#            p[0] = str(p[1]) + '..' + str(p[4])
        
        
#    def p_length_boundary(p):
#        """length_boundary : identifier
#                           | string
#        """
#        p[0] = p[1]              
    
    def p_pattern_stmt(p):
        """pattern_stmt : PATTERN string ';' 
                        | PATTERN string block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
                    
    def p_modifier_stmt(p):
        """modifier_stmt : MODIFIER INVERT_MATCH ';'
                         | MODIFIER string ';'
        """
        p[0] = node(p[1],p[2])                
        

    def p_default_stmt(p):
        """default_stmt : xxxdefault
                        | DEFAULT string ';'
        """
        if len(p)==4:
            p[0] = node(p[1],p[2])
        else:    
            s = p[1].replace('default','').replace('"','').replace("'",'').replace(' ','').replace('\t','').replace('\n','').replace('\r','').replace(';','')
            p[0] = node('default',s)
    
#    def p_default_stmt(p):
#        """default_stmt : DEFAULT string ';'
#                        | DEFAULT identifier ';'
#        """
#        p[0] = node(p[1],p[2])        
              
    def p_enum_stmt(p):
        """enum_stmt : xxxenum ';'
                     | xxxenum block
                     | ENUM string ';'
                     | ENUM string block
     
        """
        if len(p)==3:
            s = p[1].replace('enum','').replace('"','').replace("'",'').replace(' ','').replace('\t','')
            if p[2]==';':
                p[0] = node('enum',s)
            else:    
                p[0] = node('enum',s,p[2])
        elif p[3]==';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
            
    
#    def p_enum_stmt(p):
#        """enum_stmt : ENUM string ';'
#                     | ENUM string block
#                     | ENUM identifier ';'
#                     | ENUM identifier block
#     
#        """
#        if p[3] == ';':
#            p[0] = node(p[1],p[2])
#        else:
#            p[0] = node(p[1],p[2],p[3])                 
    
    def p_range_stmt(p):
        """range_stmt : RANGE range_arg_str ';'
                      | RANGE range_arg_str block
                     
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
    
    def p_range_arg_str(p):
        """range_arg_str : identifier
                         | string
        """
        p[0] = p[1]
        
#    def p_range_arg(p):
#        """range_arg : range_arg '|' range_part
#                     | range_part
#        """
#        if len(p) == 4:
#            p[0] = p[1] + '|' + str(p[3])
#        else:
#            p[0] = str(p[1])
                     
#    def p_range_part(p):
#        """range_part : range_boundary
#                      | range_boundary '.' '.' range_boundary
#        """
#        if len(p) == 2:
#            p[0] = str(p[1])
#        else:
#            p[0] = str(p[1]) + '..' + str(p[4])
        
#    def p_range_boundary(p):
#        """range_boundary : identifier
#                          | string
#        """
#        p[0] = p[1]                  
        
    def p_path_stmt(p):
        """path_stmt : PATH string ';'
                     | PATH ABSOLUTE_SCHEMA_NODEID ';'
        """
        p[0] = node(p[1],p[2])
        
    def p_require_instance_stmt(p):
        """require_instance_stmt : REQUIRE_INSTANCE identifier ';'
                                 | REQUIRE_INSTANCE string ';'
        """
        p[0] = node(p[1],p[2])
    
    
    def p_bit_stmt(p):
        """ bit_stmt : BIT identifier_arg_str ';'
                     | BIT identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
                          
    def p_position_stmt(p):
        """position_stmt : POSITION position_value_arg_str ';'
        """
        p[0] = node(p[1],p[2]) 
        
    def p_position_value_arg_str(p):
        """position_value_arg_str : identifier
                                  | string
        """
        p[0] = p[1]
    
    def p_status_stmt(p):
        """status_stmt : STATUS status_arg_str ';'
                       | STATUS status_arg_str '{' identifier identifier ';' '}'
        """
        p[0] = node(p[1],p[2])
    
    def p_status_arg_str(p):
        """status_arg_str : identifier                        
                          | string
        """
        p[0] = p[1]
    
    def p_config_stmt(p):
        """config_stmt : CONFIG config_arg_str ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_config_arg_str(p):
        """config_arg_str : identifier
                          | string
        """
        p[0] = p[1]
        
    def p_mandatory_stmt(p):
        """mandatory_stmt : MANDATORY mandatory_arg_str ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_mandatory_arg_str(p):
        """mandatory_arg_str : identifier
                             | string
        """
        p[0] = p[1]
    
    def p_presence_stmt(p):
        """presence_stmt : PRESENCE string ';'
                         | PRESENCE identifier ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_ordered_by_stmt(p):
        """ordered_by_stmt : ORDERED_BY ordered_by_arg_str ';'
        """
        p[0] = node(p[1],p[2]) 
    
    def p_ordered_by_arg_str(p):
        """ordered_by_arg_str : identifier
                              | string
        """
        p[0] = p[1]
    
    def p_must_stmt(p):
        """must_stmt : MUST string ';'
                     | MUST string block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
                       
    def p_error_message_stmt(p):
        """error_message_stmt : ERROR_MESSAGE string ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_error_app_tag_stmt(p):
        """error_app_tag_stmt : ERROR_APP_TAG string ';'
        """
        p[0] = node(p[1],p[2])
        
    def p_min_elements_stmt(p):
        """min_elements_stmt : MIN_ELEMENTS min_value_arg_str ';'
        """
        p[0] = node(p[1],p[2]) 
        
    def p_min_value_arg_str(p):
        """min_value_arg_str : identifier
                             | string
        """
        p[0] = p[1]
    
    def p_max_elements_stmt(p):
        """max_elements_stmt : MAX_ELEMENTS max_value_arg_str ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_max_value_arg_str(p):
        """max_value_arg_str : identifier
                             | string
        """
        p[0] = p[1]
    
    def p_value_stmt(p):
        """value_stmt : VALUE integer_value_str ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_integer_value_str(p):
        """integer_value_str : identifier
                             | string
        """
        p[0] = p[1]
    
    def p_identifier_arg_str(p):
        """identifier_arg_str : string
                              | identifier
        """
        p[0] = p[1] 
                   
    def p_notification_stmt(p):
        """notification_stmt : NOTIFICATION identifier_arg_str ';'
                             | NOTIFICATION identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
    
    def p_grouping_stmt(p):
        """grouping_stmt : GROUPING identifier_arg_str ';' 
                         | GROUPING identifier_arg_str block
        """
        p[2] = p[2].replace('\"','').replace("\'",'')
        if p[3] == ';':
            p[0] = node(p[1],p[2])
            p[3] = []
        else:
            p[0] = node(p[1],p[2],p[3])
        
        
    def p_container_stmt(p):
        """container_stmt : CONTAINER identifier_arg_str ';'
                          | CONTAINER identifier_arg_str block                                           
    
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
             
    def p_leaf_stmt(p):
        """leaf_stmt : LEAF identifier_arg_str block
        """
        p[0] = node(p[1],p[2],p[3])                
             
    def p_leaf_list_stmt(p):
        """leaf_list_stmt : LEAF_LIST identifier_arg_str block
        """
        p[0] = node(p[1],p[2],p[3])
    
    def p_list_stmt(p):
        """list_stmt : LIST identifier_arg_str block
        """
        p[0] = node(p[1],p[2],p[3])
     
    def p_key_stmt(p):
        """key_stmt : KEY string ';'
                    | KEY key_arg ';'
        """
        p[0] = node(p[1],p[2])
    
    def p_key_arg(p):
        """key_arg : identifier
                   | key_arg identifier
        """
        if len(p) == 2:
            p[0] = str(p[1])
        else:
            p[0] = p[1] + ' ' +  str(p[2])                   
    
    def p_unique_stmt(p):
        """unique_stmt : UNIQUE unique_arg_str ';'
        """                
        p[0] = node(p[1],p[2])
    
    def p_choice_stmt(p):
        """choice_stmt : CHOICE identifier_arg_str ';'
                       | CHOICE identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
            
    def p_case_stmt(p):
        """case_stmt : CASE identifier_arg_str ';'
                     | CASE identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_anydata_stmt(p):
        """anydata_stmt : ANYDATA identifier_arg_str ';'
                        | ANYDATA identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_anyxml_stmt(p):
        """anyxml_stmt : ANYXML identifier_arg_str ';'
                       | ANYXML identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_uses_stmt(p):
        """uses_stmt : USES identifier_ref_arg_str ';'
                     | USES identifier_ref_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_refine_stmt(p):
        """refine_stmt : REFINE refine_arg_str ';'
                       | REFINE refine_arg_str block 
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_refine_arg_str(p):
        """refine_arg_str : string
                          | descendant_schema_nodeid
        """
        p[0] = p[1]
       
    def p_augment_stmt(p):
        """augment_stmt : AUGMENT augment_arg_str ';'
                        | AUGMENT augment_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_augment_arg_str(p):
        """augment_arg_str : string
                           | ABSOLUTE_SCHEMA_NODEID
                           | descendant_schema_nodeid
        """
        p[0] = p[1] 
        
    def p_unique_arg_str(p):
        """unique_arg_str : string
                          | unique_arg
        """
        p[0] = p[1]
        
    def p_unique_arg(p):
        """unique_arg : descendant_schema_nodeid
                      | unique_arg descendant_schema_nodeid 
        """
        if len(p) == 2:
            p[0] = str(p[1])
        else:
            p[0] = p[1] + ' ' + str(p[2])  
        
    def p_descendant_schema_nodeid(p):
        """descendant_schema_nodeid : identifier
                                    | identifier ABSOLUTE_SCHEMA_NODEID 
        """                      
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + p[2]
                          
    def p_when_stmt(p):
        """when_stmt : WHEN string ';'
                     | WHEN string block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_rpc_stmt(p):
        """rpc_stmt : RPC identifier_arg_str ';'
                    | RPC identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_deviation_stmt(p):
        """deviation_stmt : DEVIATION deviation_arg_str block
                          | DEVIATION deviation_arg_str ';'
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])
        
    def p_deviation_arg_str(p):
        """deviation_arg_str : string
                             | ABSOLUTE_SCHEMA_NODEID
                             | identifier
 
        """
        p[0] = p[1]
        
    def p_deviate_op_stmt(p):
        """deviate_op_stmt : DEVIATE identifier_arg_str ';'
                           | DEVIATE identifier_arg_str block
        """
        if p[3] == ';':
            p[0] = node(p[1],p[2])
        else:
            p[0] = node(p[1],p[2],p[3])        
        
#    def p_string(p):
#        """string : STRING
#                  | keyword
#                  | string '+' STRING
#                  | identifier
#        """
#        if len(p) == 2:
#            p[0] = str(p[1])          
#        else:
#            p[0] = str(p[1]) + str(p[3])
       
    def p_string(p):
        """string : STRING
                  | string '+' STRING
        """
        if len(p) == 2:
            p[0] = str(p[1])          
        else:
            p[0] = str(p[1]) + str(p[3])



    def p_identifier(p):
        """identifier : ID
                      | keyword
        """       
        p[0] = p[1]
        
    def p_keyword(p):
        """keyword : GROUPING
                   | ANYXML
                   | LEAF
                   | LEAF_LIST
                   | CONTAINER
                   | TYPE
                   | MODULE
                   | SUBMODULE
                   | LIST
                   | TYPEDEF
                   | EMPTY 
                   | IDENTITYREF
                   | USES
                   | UNITS
                   | LEAFREF
                   | UNION
                   | CHOICE
                   | CASE
                   | ENUM
                   | IMPORT
                   | IDENTITY
                   | CONFIG
                   | INCLUDE
                   | EXTENSION
                   | ARGUMENT
                   | NAMESPACE
                   | PREFIX
                   | ORGANIZATION
                   | CONTACT
                   | DESCRIPTION
                   | REFERENCE
                   | REVISION
                   | ACTION
                   | ANYDATA
                   | AUGMENT
                   | BASE
                   | BIT
                   | DEFAULT
                   | DEVIATE
                   | DEVIATION
                   | FEATURE
                   | INPUT
                   | KEY
                   | LENGTH
                   | MANDATORY
                   | MODIFIER
                   | MUST
                   | NOTIFICATION
                   | OUTPUT
                   | PATTERN
                   | POSITION
                   | PRESENCE
                   | RANGE
                   | REFINE
                   | RPC
                   | STATUS
                   | UNIQUE
                   | VALUE
                   | WHEN
                   | ADD
                   | CURRENT
                   | DELETE
                   | DEPRECATED
                   | OBSOLETE
                   | REPLACE
                   | SYSTEM
                   | UNBOUNDED
                   | USER
                   | AND
                   | OR
                   | NOT
                   | PATH
                   | NOT_SUPPORTED
                   | ERROR_MESSAGE
        """
        p[0] = p[1]
        
    def p_empty(p):
        """empty :
        """        
        pass

    def p_error(p):
        if not p:
            print('Syntax Error in input:','lose }')
        else:
            print('Syntax Error in input file:',p.type,'\n',p.value,'\nLine:',p.lineno)
        sys.exit(1)
        
#    parser = yacc.yacc(debug=True)
    parser = yacc.yacc()
#    parser = yacc.yacc(debug=True,debuglog=log)
    return  parser, include_file, import_file

def read_file_as_str(file_path): 
    if not os.path.isfile(file_path): 
        raise TypeError(file_path + " does not exist") 
    text = open(file_path).read() 
    return text

#this function use by i.children = []
def get_top_level(stmt_list,node_names):
    d = {}
    if stmt_list != []:       
        for i in stmt_list:
            if i.type_name in node_names and i.children == []:
                d[i.type_name] = i.leaf
    else:
        print('Error module empty ')
    return d

def submodule_belongs_to(stmt):
    if stmt.type_name == 'submodule' and stmt.children != []:       
        for i in stmt.children:
            if i.type_name == 'belongs-to':
                return i.leaf

def get_prefix(stmt):
    d = {}
    dd = {}
    gg = utils.levelorder_iter(stmt)
    for i in gg:
        if i.type_name == 'module' and i.children !=[]:
            for ii in i.children:
                if ii.type_name == 'prefix' and ii.children == []:
                    d[i.leaf] = ii.leaf
                    dd[ii.leaf] = i.leaf
                    break
        elif i.type_name == 'import' and i.children !=[]:
            for ii in i.children:
                if ii.type_name == 'prefix' and ii.children == []:
                    d[i.leaf] = ii.leaf
                    dd[ii.leaf] = i.leaf
        elif i.type_name == 'belongs-to' and i.children !=[]:
            for ii in i.children:
                if ii.type_name == 'prefix' and ii.children == []:
                    d[i.leaf] = ii.leaf
                    dd[ii.leaf] = i.leaf
                    break
        else:
            continue
    return d,dd
     

pattern_brack = re.compile(r'\[[^\[]+]')
pattern_identifier = re.compile(r'\b[_A-Za-z0-9%][._\-A-Za-z0-9\|\+]*:\b')

def replace_prefix(stmt,d):
    gg = utils.levelorder_iter(stmt)
    global pattern_brack
    global pattern_identifier
    for i in gg:
        if i.type_name not in ('uses','type','typedef','container','leaf','list','leaf-list','path','augment','leafref','identity','anyxml','identityref','anydata','must','when'):
            continue
        else:
            ll = pattern_identifier.findall(i.leaf)
            for ii in set(ll):
                if ii[:-1] in d:
                    ret = d[ii[:-1]] + ':'
                    i.leaf = i.leaf.replace(ii,ret)
            if i.type_name == 'path':
                i.leaf_leaf = i.leaf
                i.leaf = pattern_brack.sub('',i.leaf)
        

def get_yang_object(file):
    lexer = yang_lexer() 
    parser, include_file, import_file = yang_parser()
    s = read_file_as_str(file)    
    result = parser.parse(s,lexer = lexer)
    module_submodule = {}
    module_submodule['header'] = get_top_level(result.children,('namespace','yang-version'))
    module_submodule['include_file'] = include_file
    module_submodule['file_relationship'] = submodule_belongs_to(result)
    ret = get_prefix(result)
    replace_prefix(result,ret[1])
    d = {}
    d['modules_prefix'] = ret[0]
    d['prefix_modules'] = ret[1]
    module_submodule['prefix'] = d
    module_submodule['body'] = result
    return result.leaf,module_submodule

if __name__ == '__main__':
    d = get_yang_object('/home/wang/source/test_ply/M6000_V5.00.10-5.6.0/zxr10-netconf-defs@2019-07-16.yang')
    print('aaa')
    
    
    

 


