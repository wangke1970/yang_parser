import ply.lex as lex
from ply.lex import TOKEN
import os

"""
keywords = ('GROUPING','ANYXML', 'LEAF', 'CONTAINER', 'TYPE', 'MODULE','SUBMODULE','LIST', 'TYPEDEF',  'EMPTY',  'IDENTITYREF',
            'USES','UNITS','LEAFREF','UNION','CHOICE','CASE','ENUM','IMPORT','IDENTITY','CONFIG','INCLUDE','EXTENSION','ARGUMENT','PREFIX',
            'ORGANIZATION','CONTACT','DESCRIPTION','REFERENCE','REVISION','ACTION','ANYDATA','AUGMENT','BASE','BIT','DEFAULT','DEVIATE','DEVIATION','FEATURE',
            'INPUT','KEY','LENGTH','MANDATORY','MODIFIER','MUST','NOTIFICATION','OUTPUT','PATTERN','POSITION','PRESENCE','RANGE','REFINE',
            'RPC','STATUS','UNIQUE','VALUE','WHEN','ADD','CURRENT','DELETE','DEPRECATED','OBSOLETE','REPLACE','SYSTEM','UNBOUNDED',
            'USER','AND','OR','NOT','PATH')
"""
keywords = ('GROUPING','ANYXML', 'LEAF', 'CONTAINER', 'TYPE', 'MODULE','SUBMODULE','LIST', 'TYPEDEF',  'EMPTY',  'IDENTITYREF',
            'USES','LEAFREF','UNION','CHOICE','CASE','ENUM','IMPORT','IDENTITY','CONFIG','INCLUDE','EXTENSION','ARGUMENT','PREFIX',
            'ORGANIZATION','CONTACT','DESCRIPTION','REFERENCE','REVISION','ACTION','ANYDATA','AUGMENT','BASE','BIT','DEFAULT','DEVIATE','DEVIATION','FEATURE',
            'INPUT','KEY','LENGTH','MANDATORY','MODIFIER','MUST','NOTIFICATION','OUTPUT','PATTERN','POSITION','PRESENCE','RANGE','REFINE',
            'RPC','STATUS','UNIQUE','VALUE','WHEN','ADD','CURRENT','DELETE','DEPRECATED','OBSOLETE','REPLACE','SYSTEM','UNBOUNDED',
            'USER','AND','OR','NOT','PATH','NAMESPACE','UNITS',)
# 'NAMESPACE','UNITS',


keyword_map = {}
for key in keywords:
    keyword_map[key.lower()] = key

reserved = {
            'belongs-to' : 'BELONGS_TO',
            'yin-element' : 'YIN_ELEMENT',
            'leaf-list' : 'LEAF_LIST',
            'yang-version' : 'YANG_VERSION',
            'error-app-tag' : 'ERROR_APP_TAG',
            'error-message' : 'ERROR_MESSAGE',
            'fraction-digits' : 'FRACTION_DIGITS',
            'if-feature' : 'IF_FEATURE',
            'max-elements' : 'MAX_ELEMENTS',
            'min-elements' : 'MIN_ELEMENTS',
            'ordered-by' : 'ORDERED_BY',
            'require-instance' : 'REQUIRE_INSTANCE',
            'revision-date' : 'REVISION_DATE',
            'invert-match' : 'INVERT_MATCH',
            'not-supported' : 'NOT_SUPPORTED',
            }

reserved = dict(reserved,**keyword_map)
            
#tokens = ['NUMBER', 'STRING','ID','ABSOLUTE_SCHEMA_NODEID','ns','units','default','contact','enum'] + list(reserved.values())        
#tokens = ['NUMBER', 'STRING','ID','ABSOLUTE_SCHEMA_NODEID','ns','DATE'] + list(reserved.values()) 
tokens = ['STRING','ID','ABSOLUTE_SCHEMA_NODEID','ns'] + list(reserved.values()) 


literals = ['{', '}', ';', '(', ')', '.', '+', '|']

def yang_lexer():

    prefix = r'[_A-Za-z0-9\-%][._\-A-Za-z0-9\|\+]*'
#    identifier = r'(?:(' + prefix + r'):)?(?:' + prefix + r')'
    identifier = r'((' + prefix + r'):)?(' + prefix + r')'
    absolute_schema_nodeid = r"(/" + identifier + r")+"
#    unit_schema = identifier + r'/' + identifier
    
    t_ignore = ' \t'
    
    nonneg_integer = r"(0|([1-9][0-9]*))"
    integer = r"[+-]?" + nonneg_integer
    number = integer + r"(\.[0-9]+)?"

    string_double_quote = r'\"([^"\\]|\\.)*\"'
    string_single_quote = r"\'([^'\\]|\\.)*\'"
    string_yang = r'(' + string_double_quote + r'|' + string_single_quote + r')'
        
    date = r'[1-2][0-9]{3}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])'

    # URI - RFC 3986, Appendix A
    scheme = "[A-Za-z][-+.A-Za-z0-9]*"
    unreserved = "[-._~A-Za-z0-9]"
    pct_encoded = "%[0-9A-F]{2}"
    sub_delims = "[!$&'()*+,=]"
    pchar = ("(" + unreserved + "|" + pct_encoded + "|" +
             sub_delims + "|[:@])")
    segment = pchar + "*"
    segment_nz = pchar + "+"
    userinfo = ("(" + unreserved + "|" + pct_encoded + "|" +
                sub_delims + "|:)*")
    dec_octet = "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    ipv4address = "(" + dec_octet + r"\.){3}" + dec_octet
    h16 = "[0-9A-F]{1,4}"
    ls32 = "(" + h16 + ":" + h16 + "|" + ipv4address + ")"
    ipv6address = (
        "((" + h16 + ":){6}" + ls32 +
        "|::(" + h16 + ":){5}" + ls32 +
        "|(" + h16 + ")?::(" + h16 + ":){4}" + ls32 +
        "|((" + h16 + ":)?" + h16 + ")?::(" + h16 + ":){3}" + ls32 +
        "|((" + h16 + ":){,2}" + h16 + ")?::(" + h16 + ":){2}" + ls32 +
        "|((" + h16 + ":){,3}" + h16 + ")?::" + h16 + ":" + ls32 +
        "|((" + h16 + ":){,4}" + h16 + ")?::" + ls32 +
        "|((" + h16 + ":){,5}" + h16 + ")?::" + h16 +
        "|((" + h16 + ":){,6}" + h16 + ")?::)")
    ipvfuture = r"v[0-9A-F]+\.(" + unreserved + "|" + sub_delims + "|:)+"
    ip_literal = r"\[(" + ipv6address + "|" + ipvfuture + r")\]"
    reg_name = "(" + unreserved + "|" + pct_encoded + "|" + sub_delims + ")*"
    host = "(" + ip_literal + "|" + ipv4address + "|" + reg_name + ")"
    port = "[0-9]*"
    authority = "(" + userinfo + "@)?" + host + "(:" + port + ")?"
    path_abempty = "(/" + segment + ")*"
    path_absolute = "/(" + segment_nz + "(/" + segment + ")*)?"
    path_rootless = segment_nz + "(/" + segment + ")*"
    path_empty = pchar + "{0}"
    hier_part = ("(" + "//" + authority + path_abempty + "|" +
                 path_absolute + "|" + path_rootless + "|" + path_empty + ")")
    query = "(" + pchar + "|[/?])*"
    fragment = query
    uri = (scheme + ":" + hier_part + r"(\?" + query + ")?" +
           "(\#" + fragment + ")?")
    
    ns_uri = r'namespace\s+' + '(' + uri + '|' + string_yang +')'
    @TOKEN(ns_uri)
    def t_ns(t):
        t.lexer.lineno += t.value.count('\n')
        return t
    
#    def t_description(t):
#        r'description\s+[^\{]+?(?=;)'
#        t.lexer.lineno += t.value.count('\n')
#        return t
    
#    def t_units(t):
#        r'units\s+[^;]*'       
#        t.lexer.lineno += t.value.count('\n')
#        return t
    
#    def t_default(t):
#        r'default\s+[^;]*'
#        t.lexer.lineno += t.value.count('\n')
#        return t
    
#    def t_contact(t):
#        r'contact\s+[^\{]+?(?=;)'
#        r'contact(.+(?=;))+?'
#        t.lexer.lineno += t.value.count('\n')
#        return t
    
#    def t_enum(t):
#        r'enum\s+[^;{]*'
#        t.lexer.lineno += t.value.count('\n')
#        return t

    
    def t_line_terminaror(t):
        r'[\n\r]+'
        t.lexer.lineno += t.value.count('\n')

    def t_comment(t):
        r'(/\*([^*]|[\r\n\s]|(\*+([^*/]|[\r\n\s])))*\*+/)|(//.*)|(/\*.*)'
        t.lexer.lineno += t.value.count('\n')

    def t_error(t):
        msg = 'Illegal character %s' % repr(t.value[0]) + ' line:' + str(t.lexer.lineno)
        print(msg)
        t.lexer.skip(1)
            
#    def t_newline(t):
#        r'\n+'
#        t.lexer.lineno += len(t.value)


#    @TOKEN(unit_schema)
#    def t_UNIT_SCHEMA(t):
#        return t

#    @TOKEN(date)
#    def t_DATE(t):
#        return t    

#    @TOKEN(number)
#    def t_NUMBER(t):
#        return t

    @TOKEN(identifier)
    def t_ID(t):
        t.type = reserved.get(t.value, "ID")
        return t

    @TOKEN(absolute_schema_nodeid)
    def t_ABSOLUTE_SCHEMA_NODEID(t):
        return t

    @TOKEN(string_yang)
    def t_STRING(t):
        # remove escape + new line sequence used for strings
        # written across multiple lines of code
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value.replace('\n', '')
        t.value = t.value.replace('\r', '')
#        t.value = t.value.replace(',', ' ')
        return t    

    lexer = lex.lex()
#    lexer = lex.lex(debug=True)    
    return lexer

def read_file_as_str(file_path): 
    if not os.path.isfile(file_path): 
        raise TypeError(file_path + " does not exist") 
    text = open(file_path).read() 
    return text



if __name__ == '__main__':    
    lexer = yang_lexer()
    
#    data = read_file_as_str('/home/wang/source/test_ply/HUAWEI/huawei-bfd-static-mpls-te.yang')
    data = read_file_as_str('/home/wang/source/test_ply/ZTE/zxr10-iccp@2019-07-03.yang')
#    data = read_file_as_str('/home/wang/source/test_ply/bgp/openconfig-bgp-policy.yang')    
#    data = read_file_as_str('/home/wang/source/test_ply/bbb.yang')
    lexer.input(data)    
    while True:
        tok = lexer.token()
        if not tok: break      
        print(tok)














