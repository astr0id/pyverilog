from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog.utils.version
from pyverilog.vparser.parser import VerilogCodeParser
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

from pyverilog.utils.identifierreplace import replaceIdentifiers

import pyverilog.vparser.ast as AST

class Param():
  def __init__(self, param_name, param_value):
    self.name = param_name
    self.default_value = param_value
    self.occurence = []
  def add_occurence(self, path):
    self.occurence.append(path)
  def __repr__(self):
    return ("<Param %s %s\n\t%s>" % (self.name, self.default_value, str(self.occurence)))
  def __str__(self):
    return self.__repr__()

class ModuleWithParam():
  def __init__(self, module_name, module_ast):
    self.name = module_name
    self.ast = module_ast
    self.params = {}
    pass
  def add_param(self, param):
    self.params[param.name] = param

  def has_param(self, param_name):
    return param_name in self.params

  def add_occurence(self, param_name, code_path):
    self.params[param_name].add_occurence(code_path)

  def get_params(self):
    return [v for k, v in self.params.items()]

  def __repr__(self):
    return ("<ModuleWithParam %s \n%s>" % (self.name, str(self.params)))

  def __str__(self):
    return self.__repr__()

param_map = {}
modules_with_param = {}
current_module = None

def replace_parameter(module):
  assert type(module) == ModuleWithParam

  for param in module.get_params():
    replace_codepath(module.ast, param.name, param.default_value)
    # for occur in param.occurence:
    #   replace_codepath(module.ast, occur, param.default_value)


def replace_codepath(ast, name, value):
  ast.show()
  replaceIdentifiers(ast, {name: "10"})
  print("after replace")
  ast.show()

  codegen = ASTCodeGenerator()
  rslt = codegen.visit(ast)
  print(rslt)

  # print(code_path)
  # ast.show()
  # ast_tmp = ast
  # for idx in code_path[2:]:
  #   ast_tmp = ast_tmp.children()[idx]
  # print(ast_tmp, type(ast_tmp))
  # ast_tmp
  # print(ast_tmp, type(ast_tmp))
  # print("after replace")
  # ast.show()

def record_parameter(ast, code_path=[], current_module=None):
    global modules_with_param

    ########## Leaf Node ###########
    if type(ast) == AST.Identifier:
      identifier = ast
      print("identifier")
      print(identifier.name)
      if modules_with_param[current_module].has_param(identifier.name):
        modules_with_param[current_module].add_occurence(identifier.name, code_path)
      #if identifier.name in param_map[current_module]['param']:
      #  param_map[current_module]['param'][identifier.name] += [code_path]

    ################################
    elif len(ast.children()) == 0:
      pass #print(code_path)
    ################################

    ########## Non-Leaf Node ###########
    elif type(ast) == AST.ModuleDef:
      moduledef = ast
      # param_map[moduledef.name] = {'def': ast, 'param': {}}
      modules_with_param[moduledef.name] = ModuleWithParam(moduledef.name, ast)
      for idx, child in enumerate(ast.children()):
        record_parameter(child, code_path + [idx], current_module=moduledef.name)
    elif type(ast) == AST.Parameter:
      parameter = ast
      modules_with_param[current_module].add_param(Param(parameter.name, parameter.value.var))
      # param_map[current_module]['param'][parameter.name] = [(parameter.value.var)]
    ################################
    else:
      for idx, child in enumerate(ast.children()):
        record_parameter(child, code_path + [idx], current_module=current_module)
    ################################


def record_parameter_old(ast, code_path=[], current_module=None):
    global param_map

    ########## Leaf Node ###########
    if type(ast) == AST.Identifier:
      identifier = ast
      print("identifier")
      print(identifier.name)
      if identifier.name in param_map[current_module]['param']:
        param_map[current_module]['param'][identifier.name] += [code_path]
    ################################
    elif len(ast.children()) == 0:
      pass #print(code_path)
    ################################

    ########## Non-Leaf Node ###########
    elif type(ast) == AST.ModuleDef:
      moduledef = ast
      param_map[moduledef.name] = {'def': ast, 'param': {}}
      for idx, child in enumerate(ast.children()):
        record_parameter(child, code_path + [idx], current_module=moduledef.name)
    elif type(ast) == AST.Parameter:
      parameter = ast
      param_map[current_module]['param'][parameter.name] = [(parameter.value.var)]
    ################################
    else:
      for idx, child in enumerate(ast.children()):
        record_parameter(child, code_path + [idx], current_module=current_module)
    ################################

def code_gen(ast):
    if len(ast.children()) == 0:
      pass #print(code_path)
    elif type(ast) == AST.Instance:
      ## assume there's only one instance
      instance = ast
      target_ast = param_map[instance.module]['def']
      replace_parameter(target_ast=target_ast,
                        argument_list=instance.parameterlist) 
                        
    else:
      for idx, child in enumerate(ast.children()):
        code_gen(child)

def main():
    INFO = "Code converter from AST"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python example_codegen.py file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()
    
    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-I","--include",dest="include",action="append",
                         default=[],help="Include path")
    optparser.add_option("-D",dest="define",action="append", default=[],help="Macro Definition")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    codeparser = VerilogCodeParser(filelist,
                                   preprocess_include=options.include,
                                   preprocess_define=options.define)

    ast = codeparser.parse()
    record_parameter(ast, [])
    print(modules_with_param)

    for name, module in modules_with_param.items():
      print("replacing parameter in %s" % (name))
      replace_parameter(module)

    code_gen(ast)

    print(modules_with_param)
    directives = codeparser.get_directives()

    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    print(rslt)

if __name__ == '__main__':
    main()
