##############################
# IMPORTS
#############################

from src.lang.dist.values import Number, SymbolTable, Context
from src.lang.dist.functions.builtin import BuiltInFunction

from src.lang.lexer import Lexer
from src.lang.parser import Parser
from src.lang.interpreter import Interpreter

#############################
# RUN
#############################

# Main
global_symbol_table = SymbolTable()
global_symbol_table.set("cors_run", BuiltInFunction.run)
global_symbol_table.set("null", Number.null)
global_symbol_table.set("true", Number.true)
global_symbol_table.set("false", Number.false)
global_symbol_table.set("clear", BuiltInFunction.clear)
global_symbol_table.set("cls", BuiltInFunction.clear)
global_symbol_table.set("printf", BuiltInFunction.printf)
global_symbol_table.set("printret", BuiltInFunction.print_ret)
global_symbol_table.set("input", BuiltInFunction.input)
global_symbol_table.set("input_int", BuiltInFunction.input_int)

# Is
global_symbol_table.set("isnumber", BuiltInFunction.isnumber)
global_symbol_table.set("isstring", BuiltInFunction.isstring)
global_symbol_table.set("islist", BuiltInFunction.islist)
global_symbol_table.set("isfunction", BuiltInFunction.isfunction)

# Tables
global_symbol_table.set("table.insert", BuiltInFunction.insert)
global_symbol_table.set("table.remove", BuiltInFunction.remove)
global_symbol_table.set("table.extend", BuiltInFunction.extend)
global_symbol_table.set("table.clear", BuiltInFunction.tclear)
global_symbol_table.set("table.concat", BuiltInFunction.concat)
global_symbol_table.set("table.find", BuiltInFunction.find)
global_symbol_table.set("table.len", BuiltInFunction.len)

# Math
global_symbol_table.set("math.abs", BuiltInFunction.abs)
global_symbol_table.set("math.acos", BuiltInFunction.acos)
global_symbol_table.set("math.asin", BuiltInFunction.asin)
global_symbol_table.set("math.atan", BuiltInFunction.atan)
global_symbol_table.set("math.atan2", BuiltInFunction.atan2)
global_symbol_table.set("math.ceil", BuiltInFunction.ceil)
global_symbol_table.set("math.clamp", BuiltInFunction.clamp)
global_symbol_table.set("math.cos", BuiltInFunction.cos)
global_symbol_table.set("math.cosh", BuiltInFunction.cosh)
global_symbol_table.set("math.deg", BuiltInFunction.deg)
global_symbol_table.set("math.exp", BuiltInFunction.exp)
global_symbol_table.set("math.floor", BuiltInFunction.floor)
global_symbol_table.set("math.fmod", BuiltInFunction.fmod)
global_symbol_table.set("math.frexp", BuiltInFunction.frexp)
global_symbol_table.set("math.ldexp", BuiltInFunction.ldexp)
global_symbol_table.set("math.log", BuiltInFunction.log)
global_symbol_table.set("math.log10", BuiltInFunction.log10)
global_symbol_table.set("math.max", BuiltInFunction.max)
global_symbol_table.set("math.min", BuiltInFunction.min)
global_symbol_table.set("math.modf", BuiltInFunction.modf)
global_symbol_table.set("math.noise", BuiltInFunction.noise)
global_symbol_table.set("math.pow", BuiltInFunction.pow)
global_symbol_table.set("math.rad", BuiltInFunction.rad)
global_symbol_table.set("math.random", BuiltInFunction.random)
global_symbol_table.set("math.randomseed", BuiltInFunction.randomseed)
global_symbol_table.set("math.round", BuiltInFunction.round)
global_symbol_table.set("math.sign", BuiltInFunction.sign)
global_symbol_table.set("math.sin", BuiltInFunction.sin)
global_symbol_table.set("math.sinh", BuiltInFunction.sinh)
global_symbol_table.set("math.sqrt", BuiltInFunction.sqrt)
global_symbol_table.set("math.tan", BuiltInFunction.tan)
global_symbol_table.set("math.tanh", BuiltInFunction.tanh)
global_symbol_table.set("math.huge", Number.math_huge)
global_symbol_table.set("math.pi", Number.math_pi)

def run(fn, text):
    # Generate Tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    # Run program
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
