# coding: utf8
from pycropml.transpiler.pseudo_tree import Node
from pycropml.transpiler.codeGenerator import CodeGenerator
from pycropml.transpiler.rules.fortranRules import FortranRules
from pycropml.transpiler.interface import middleware
from pycropml.transpiler.generators.docGenerator import DocGenerator
from pycropml.transpiler import lib
import os
from path import Path
#from pycropml.transpiler.Parser import parser
#from pycropml.transpiler.ast_transform import AstTransformer, transform_to_syntax_tree
import shutil


# get the path of fortran subroutine list_sub
# This subroutine is used to hnndle dynamic arrays

dir_lib = Path(os.path.dirname(lib.__file__))

f_src=dir_lib/"f90"/"list_sub.f90"
  
#f_src = open(list_path, 'rb')

#file_dest = dir_lib  
#f_dest = open(file_dest, 'wb')

#shutil.copyfileobj(f_src, f_dest) 


class FortranGenerator(CodeGenerator, FortranRules):
    """This class contains the specific properties of 
    fortran language and use the NodeVisitor to generate a fortran
    code source from a well formed syntax tree.
    """
   
    def __init__(self, tree, model=None, name = None):
        CodeGenerator.__init__(self)
        FortranRules.__init__(self)
        self.tree = tree
        self.indent_with=' '*4 
        self.model=model           # crop2ml models
        self.name = name
        self.initialValue=[] 
        self.z = middleware(self.tree)
        self.z.transform(self.tree)
        self.mod_parameters=[]
        self.index=[]
        if self.model: 
            self.doc= DocGenerator(model, '!')
            '''for inp in self.model.inputs: # get constant parameters in models
                if inp.inputtype=="parameter":
                    #print(inp.name, model.name)
                    if inp.parametercategory=="constant":
                        self.mod_parameters.append(inp.name)'''
            #print(self.mod_parameters)
    
    def visit_notAnumber(self, node):
        pass
        
    def visit_comparison(self, node):
        #self.write('(')
        self.visit_binary_op(node)
        #self.write(')')

    def visit_binary_op(self, node):
        op = node.op
        prec = self.binop_precedence.get(op, 0)
        self.operator_enter(prec)
        self.visit(node.left)
        self.write(u" %s " % self.binary_op[op].replace('_', ' '))
        if "type" in dir(node.right):
            if node.right.type=="binary_op" and node.right.op not in ("+","-") :
                self.write("(")
                self.visit(node.right)
                self.write(")")
            else:
                self.visit(node.right)
        else:
            self.visit(node.right)
        self.operator_exit()
    
    def visit_unary_op(self, node):
        op = node.operator
        prec = self.unop_precedence[op]
        self.operator_enter(prec)
        self.write(u"%s" % self.unary_op[op])
        self.visit(node.value)
        self.operator_exit()


    def body(self, statements):
        self.new_line = True
        self.indentation += 1
        if isinstance(statements, list):
            for stmt in statements:
                if stmt.type!="declaration":
                    self.visit(stmt) 
        else: self.visit(statements)
        self.indentation -= 1
    '''https://rosettacode.org/wiki/Operator_precedence#Fortran'''
    binop_precedence = {
        'or': 1,
        'and': 2,
        # unary: 'not': 3, '!': 3,
        'in': 4, 'not_in': 4, 'is': 4, 'is_not': 4, '<': 4, '<=': 4, '>': 4, '>=': 4, '!=': 4, '==': 4,
        '|': 5,
        '^': 6,
        '&': 7,
        '<<': 8, '>>': 8,
        '+': 9, '-': 9,
        '*': 11, '@': 11, '/': 11, '//': 11, '%': 11,
        # unary: '+': 11, '-': 11, '~': 11
        '**': 12,
    }
    
    unop_precedence = {
        'not': 3, '!': 3,
        '+': 10, '-': 10, '~': 10,
        }


    def visit_import(self, node):
        pass

    def visit_assignment(self, node):
        if node.value.type=="cond_expr_node":
            self.visit_cond_expr_node(node)
        elif node.value.type == "custom_call":
            self.newline(node)
            node =Node("subroutine", receiver = node.target,function=node.value.function, args=node.value.args ) 
            self.write('call ')
            self.visit(node)
        elif node.value.type =="list" and not node.value.elements:
            self.write("\n        deallocate(%s)\n"%node.target.name)
        elif node.value.type == "notAnumber":
            self.visit_notAnumber(node)
        else:
            self.newline(node)
            self.visit(node.target)
            self.write(' = ')
            self.visit(node.value)
    
    def visit_tab(self, node):
        self.write("[")
        self.visit(node.receiver)
        self.write("(:")
        self.visit(node.index)
        self.write("-1),")
        self.visit(node.receiver)
        self.write("(")
        self.visit(node.index)
        self.write("+1:)]")
        

    def visit_cond_expr_node(self, node):
        self.newline(node)
        self.write(u"IF (")
        self.visit(node.value.test)
        self.write(') THEN')
        self.newline(node)
        self.indentation+=1
        self.visit(node.target)
        self.write("=")
        self.visit(node.value.true_val)
        self.newline(node)
        self.indentation-=1
        self.write(u"ELSE ")
        self.newline(node)
        self.indentation+=1
        self.visit(node.target)
        self.write("=")
        self.visit(node.value.false_val)
        self.newline(node)
        self.indentation-=1
        self.write(u"END IF ")

        
    def visit_if_statement(self, node):
        self.newline(node)
        self.write('IF(')
        self.visit(node.test)
        self.write(') THEN')
        self.newline(node)
        self.body(node.block)
        self.newline(node)
        while True:
            else_ = node.otherwise
            if len(else_) == 0:                        
                self.newline(node)               
                self.write(u"END IF")
                break
            elif len(else_) == 1 and else_[0].type=='elseif_statement':
                self.visit(else_[0])                        
                self.newline(node)               
                self.write(u"END IF")
            else:
                self.visit(else_)                        
                self.newline(node)               
                self.write(u"END IF")
                break
            break

    def visit_elseif_statement(self, node):
        self.newline()
        self.write('ELSE IF ( ')
        self.visit(node.test)
        self.write(') THEN')
        self.newline(node)
        self.body(node.block)
        self.newline(node)      

    def visit_else_statement(self, node):
        self.newline()
        self.write('ELSE')
        self.newline(node)    
        self.body(node.block)
        self.newline(node)
    
    def visit_float(self, node):
        self.write(node.value)

    def visit_int(self, node):
        self.write(str(node.value))     
        
    def visit_bool(self, node):
        self.write(".TRUE.") if node.value==True else self.write(".FALSE.")

    def visit_str(self, node):
        self.emit_string(node)
        
    def visit_pair(self, node):
        self.visit(node.key)
        self.write(u": ")
        self.visit(node.value)         

    def visit_ExprStatNode(self, node):
        self.newline(node)
        self.visit(node.expr)
    
    def visit_list(self, node):
        self.write(u'(/')
        self.comma_separated_list(node.elements)
        self.write(u'/)')    

    
    def visit_standard_method_call(self, node):
        l = node.receiver.pseudo_type
        if isinstance(l, list):
            l = l[0]
        z = self.methods[l][node.message] 
        if callable(z):
            self.visit(z(node))
        else:
            if not node.args:
                self.write(z)
                self.write('(')
                self.visit(node.receiver)
                self.write(')')
            else:
                "%s.%s"%(self.visit(node.receiver),self.write(z))
                self.write("(")
                self.comma_separated_list(node.args)
                self.write(")")
   
    def visit_method_call(self, node):
        "%s.%s"%(self.visit(node.receiver),self.write(node.message))                

    def visit_index(self, node):
        if "sequence" not in dir(node.sequence):
            self.visit(node.sequence)
            self.write(u"(")
            if isinstance(node.index.type, tuple):
                self.emit_sequence(node.index)
            else:
                
                if node.index.type=='standard_method_call':
                    self.visit(node.index)
                    if node.index.message=="index" :
                        self.write(u")")
                elif node.index.type=="int":
                    z=int(node.index.value)+1
                    if z!=0: self.write(str(z))
                    if int(node.index.value)<0:
                        if z!=0: self.write("%z +")
                        self.write(" SIZE(%s)"%node.sequence.name)
                    self.write(u")")
                elif "name" in dir(node.index):
                    if node.index.name in self.index:
                        self.visit(node.index)
                        self.write(u")")
                    else:
                        self.visit(node.index)
                        self.write(u"+1)")
                else:
                    if checkList(self.index, self.checkIndex(node)):
                        self.visit(node.index)
                        self.write(u")")
                    else:
                        self.visit(node.index)
                        self.write(u"+1 )")
        else:
            self.visit(node.sequence.sequence)
            self.write(u"(")
            self.visit(node.sequence.index)
            self.write(" ,")
            self.visit(node.index)
            self.write(" )")
    
    def visit_sliceindex(self, node):
        self.visit(node.receiver.sequence)
        self.write(u"(")
        self.visit(node.receiver.index)
        #self.write(" + 1")
        if node.message=="sliceindex_from":
            self.visit(node.args)
            self.write(u":")
        if node.message=="sliceindex_to":
            self.write(u":")
            self.visit(node.args)
        if node.message=="sliceindex":
            self.visit(node.args[0])
            self.write(u":")
            self.visit(node.args[1])
        if node.message=="slice_":
            #self.visit(node.args[0])
            self.write(u",:)")
            #self.visit(node.args[1]) 
        #self.write(u")")
    
    def visit_continuestatnode(self, node):
        self.newline(node)
        self.write('continue')
        

    def visit_breakstatnode(self, node):
        self.newline(node)
        self.write('exit')

    def visit_module(self, node):
        if self.model is not None:
            self.write("MODULE %smod"%self.model.name.capitalize())
        else:
            self.write("Module Test")
        self.newline(node)
        self.indentation += 1 
        self.newline(node)
        if "list" in self.z.dependencies : 
            self.write("USE list_sub")
            self.newline(node) 
            if self.model:
                f_dest = os.path.join(self.model.path,"src","f90","list_sub.f90") 
                shutil.copyfile(f_src, f_dest)         
        for dependency in self.z.dependencies:
            if dependency!="list" and dependency.split("_")[0]=="model":
                self.write("USE %smod" %dependency.split("model_")[1].capitalize())
            self.newline(node)        
        self.write("IMPLICIT NONE")
        self.newline(node)
        self.indentation -= 1 
        self.write("CONTAINS")
        self.newline(node)
        self.indentation += 1    
        self.visit(node.body)
        self.newline(extra=1)
        self.indentation -= 1        
        self.newline(node)
        self.indentation -= 1        
        self.write("END MODULE")

    def visit_function_definition(self, node):
        self.nb=0       
        self.newline(node)
        #self.body("")
        self.write("SUBROUTINE ")
        self.write("%s("%node.name)
        parameters=[]
        node_params=[]
        for pa in node.params:
            if pa.name not in self.mod_parameters:
                parameters.append(pa.name)
                node_params.append(pa)
        parameters = parameters+[e for e in self.transform_return(node)[0] if e not in parameters]
        self.write(', &\n        '.join(parameters))
        self.write(')') 
        self.indentation += 1
        self.initialValue=[]
        newNode = self.add_features(node)
        self.visit_declaration(newNode) #self.visit_decl(node)           
        if self.initialValue:
            for n in self.initialValue:
                if len(n.value)>=1:
                    self.write("%s = " %n.name)
                    self.write(u'(/')
                    self.comma_separated_list(n.value)
                    self.write(u'/)')
                    self.newline(node) 
        self.indentation -=1
        self.newline(node)
        if self.model and node.name.startswith("model_"):
            self.write(self.doc.desc)
            self.newline(node)
            self.write(self.doc.inputs_doc)
            self.newline(node)
            self.write(self.doc.outputs_doc)
            self.newline(node)
        self.body(node.block)
        self.newline(node)
        self.write("END SUBROUTINE %s"%node.name)
        self.newline(node)
    
    def transform_return(self, node):
        returnvalues=node.block[-1].value
        if returnvalues.type=="tuple":
            output = [elt.name for elt in returnvalues.elements]
            node_output = [elt for elt in returnvalues.elements]
        else:
            output = [returnvalues.name]
            node_output = [returnvalues]
        return output, node_output
    
    def retrieve_params(self, node):
        parameters=[]
        node_params=[]
        for pa in node.params:
            parameters.append(pa.name)
            node_params.append(pa)
        return node.params
    
    def internal_declaration(self, node):
        statements  = node.block
        if isinstance(statements, list):
            intern_decl=statements[0].decl if statements[0].type=="declaration" else None
            for stmt in statements[1:]:
                if stmt.type=="declaration":
                    intern_decl=intern_decl+stmt.decl
                if self.z.ForSequence:
                    for i in range(self.z.nbForSeq):
                        intern_decl = intern_decl+[Node(type="int", name="i_cyml%s"%i, pseudo_type="int")]
        else: intern_decl=statements.decl if statements.type=="declaration" else None
        return intern_decl
    
    def add_features(self, node):
        self.internal = self.internal_declaration(node)
        internal_name=[]
        if self.internal is not None:
            self.internal = self.internal if isinstance(self.internal,list) else [self.internal]
            for inter in self.internal:
                if 'elements' in dir(inter):# and not isinstance(inter.pseudo_type, list) 
                    self.initialValue.append(Node(type="initial",name = inter.name, pseudo_type=inter.pseudo_type, value = inter.elements))
            internal_name= [e.name  for e in self.internal]
        self.params = self.retrieve_params(node)
        params_name = [e.name  for e in self.params]
        outputs = self.transform_return(node)[1]
        if not isinstance(outputs, list):
            outputs=[outputs]
        outputs_name = [e.name  for e in outputs]
        
        variables = self.params+self.internal if self.internal else self.params
        newNode=[]
        for var in variables:
            if var not in newNode:
                if var.name in params_name and var.name not in outputs_name:
                    var.feat = "IN"
                    newNode.append(var)
                if var.name in params_name and var.name in outputs_name:
                    var.feat = "INOUT"
                    newNode.append(var)
                if var.name in internal_name and var.name in outputs_name:
                    var.feat = "OUT"
                    newNode.append(var)
                if var.name in internal_name and var.name not in outputs_name:
                    newNode.append(var)
        return newNode
    
    def part_declaration(self, node):
        self.visit_decl(node)
        if node.name in self.mod_parameters:
            self.write(", PARAMETER :: %s = %s"%(node.name, valParam(self.model,node.name)))
        elif 'feat' in dir(node):         
            self.write(", INTENT(%s) "%(node.feat))

    

    def visit_declaration(self, node):
        self.newline(node)
        for n in node:
            if n.name not in self.mod_parameters:
                self.newline(node)             
                if 'value' not in dir(n) and n.type not in ("list", "tuple", "dict", "array") or n in self.params and n.type!="array":
                    self.part_declaration(n)
                    self.write(':: %s'%(n.name)) 
                elif 'elements' not in dir(n) and n.type in("list","array"):
                    self.part_declaration(n)
                    self.write(":: %s"%n.name)
                elif 'value' in dir(n) and n.pseudo_type in ("int", "float", "str", "bool") and n not in self.params : 
                    self.part_declaration(n)
                    self.write(':: %s'%(n.name))
                    self.write(" = ")
                    if n.type=="local":
                        self.write(n.value)
                    else: self.visit(n)
                elif 'elements' in dir(n) and n.type in ("list", "tuple", "local", "array"):
                    if n.type=="list":
                        self.part_declaration(n)
                        self.write(":: %s"%n.name)  
                    if n.type=="array":
                        self.part_declaration(n)
                        self.write(" , DIMENSION(")                
                        self.comma_separated_list(n.elts)
                        self.write(" ):: %s"%n.name) 
            else:
                self.newline(node)
                self.part_declaration(n)                         
        self.newline(node)
        
    def visit_implicit_return(self, node):
        pass
        """self.newline(node)
        if node.value is None:
            self.write('return')
        else:
            self.write('return ')
        self.visit(node.value)"""

    def visit_list_decl(self, node):        
        if not isinstance(node[1], list):
            self.write(self.types[node[1]])
            self.write(', ALLOCATABLE ')
            self.write(", DIMENSION(:)")
        else:
            node = node[1]
            self.write(self.types[node[1]])
            self.write(', ALLOCATABLE')
            self.write(", DIMENSION(:,:) ") 

    def visit_datetime_decl(self, node):
        return self.visit_str_decl(node)  
    
    def visit_datetime(self, node):
        return self.visit_str(node)
    
    def visit_array_decl(self, node): 
        self.write(self.types[node.pseudo_type[1]])
        self.write(" , DIMENSION(")
        if node.dim == 0: self.write(":")
        else: self.comma_separated_list(node.elts)
        self.write(" )")  

    def visit_float_decl(self, node):
        self.write(self.types[node])

    def visit_int_decl(self, node):
        self.write(self.types[node])  

    def visit_str_decl(self, node):
        self.write(self.types[node])       

    def visit_bool_decl(self, node):
        self.write(self.types[node])  
                    
    def visit_decl(self, nodeT):
        node = nodeT.pseudo_type
        if isinstance(node, list) or node[0]=="array" :
            if node[0]=="list":
                self.visit_list_decl(node)  
            if node[0]=="array":
                self.visit_array_decl(nodeT)                  
        else:
            if node=="float":
                self.visit_float_decl(node)
            if node=="int":
                self.visit_int_decl(node)       
            if node=="str":
                self.visit_str_decl(node) 
            if node=="bool":
                self.visit_str_decl(node)
            if node=="datetime":
                self.visit_str_decl(node)                 
        
    def visit_call(self, node):
        want_comma = []
        def write_comma():
            if want_comma:
                self.write(', ')
            else:
                want_comma.append(True)
        if "attrib" in dir(node):
             self.write(u"%s.%s"%(node.namespace,self.visit(node.function)))
        else:
            self.write(self.visit(node.function))
        self.write('(')
        if isinstance(node.args, list):
            for arg in node.args:
                write_comma()
                self.visit(arg)
        else: self.visit(node.args)
        self.write(')')
    
    def visit_standard_call(self, node):
        node.function = self.functions[node.namespace][node.function]
        if callable(node.function):
           self.visit(node.function(node)) 
        else: self.visit_call(node) 

    def visit_subroutine(self,node):         
        self.write(node.function)
        self.write('(')
        self.comma_separated_list(node.args)
        if "elements" in dir(node.receiver):
            elts = node.receiver.elements
        else: elts = [node.receiver]
        for n in elts:
            if n not in node.args:
                self.write(',')
                self.write(n.name)
        self.write(')')        
        
    def visit_importfrom(self, node):
        """self.newline(node)
        self.write('from %s import ' % (node.namespace))
        for idx, item in enumerate(node.name):
            if idx:
                self.write(', ')
            self.write(item)"""

    def visit_custom_call(self, node):
        want_comma = []
        def write_comma():
            if want_comma:
                self.write(', ')
            else:
                want_comma.append(True)            
        self.write(node.function)
        self.write('(')
        self.visit(node.receiver)
        write_comma()
        for arg in node.args:
            write_comma()
            self.visit(arg)
        self.write(')')
    
    def visit_for_statement(self, node):
        self.newline(node)
        self.write("DO i_cyml%s = 1, SIZE("%self.nb)
        if "sequences" in dir(node):
            self.visit(node.sequences)
            self.write(")")
        self.newline(node)
        self.indentation +=1
        if "iterators" in dir(node):
            self.visit(node.iterators)
            self.write(" = ")
            self.visit(node.sequences)
            self.write("(i_cyml%s)"%self.nb)
            self.nb = self.nb+1
            self.newline(node)
            self.indentation -=1
        self.body(node.block)
        self.newline(node)       
        self.write("END DO")
    
    def visit_for_iterator_with_index(self, node):
        self.visit(node.index)
        self.write(' , ')
        self.visit(node.iterator)        

    """def visit_for_sequence_with_index(self, node):
        
        self.write(" in enumerate(")
        self.visit(node.sequence)
        self.write('):')"""
    
    def visit_for_iterator(self, node):
        self.visit(node.iterator)
        
    def visit_for_sequence(self, node):        
        self.visit(node.sequence)
    
    def visit_for_range_statement(self, node):
        self.newline(node)
        self.write("DO ")
        self.index.append(node.index.name)
        self.visit(node.index)
        self.write(" = ")
        if "value" in dir(node.start):
            self.write(str(int(node.start.value)+1))
        else:
            self.visit(node.start)
            if "name" in dir(node.start):
                if node.start.name not in self.index:
                    self.write(" + 1 ")  
            else:
                self.write(" + 1 ") 
        self.write(' , ')
        self.visit(node.end)
        if node.step.value!=1:
            self.write(', ')
            self.visit(node.step)
        self.body(node.block)
        self.newline(node)       
        self.write("END DO")
        
    def visit_while_statement(self, node):
        self.newline(node)
        self.write('DO WHILE ( ')
        self.visit(node.test)
        self.write(' ) ')
        self.body_or_else(node)
        self.newline(node)       
        self.write("END DO")
    
    def checkIndex(self, node):
        indexNames=[]
        if node.type=="index":
            if node.index.type=="binary_op":
                z1=node.index
                while z1.type=="binary_op":
                    if "name" in dir(z1.left):
                        indexNames.append(z1.left.name)
                    if "name" in dir(z1.right):
                        indexNames.append(z1.right.name)
                    z1=z1.left  
        return indexNames

def valParam(model,name):
    for mod in model.inputs:
        if mod.name==name:
            val = mod.default
    return val

def checkList(list1, list2):
    test=False
    for i in list1:
        for j in list2:
            if i==j:
                test=True
                break
    return test
            
class FortranCompo(FortranGenerator):
    """ This class used to generates states, rates and auxiliary classes
        for Fortran90 language.
    """
    def __init__(self, tree=None, model=None, name = None):
        self.tree = tree
        self.model=model
        self.name = name
        FortranGenerator.__init__(self,tree, model, self.name)
    
    '''def visit_function_definition(self, node):
        pass'''
    '''def visit_assignment(self, node):
        print(node.value.type)'''
    
    def visit_importfrom(self, node):
        '''self.newline(node)
        self.write('Use ')
        for idx, item in enumerate(node.name):
            if idx:
                self.write(', ')
            self.write("%smod"%item.split("model_")[1].capitalize())'''
     
