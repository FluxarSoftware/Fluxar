from src.lang.dist.functions.function import BaseFunction
from src.lang.dist.results import RTResult
from src.lang.dist.values import String, Number, List
from src.lang.dist.errors import RTError
from src.lang.dist.other.perlin import perlin

from src.lang.handler import run
import math, random, os

class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args):
        res = RTResult()
        exec_ctx = self.generate_new_context()
        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
        if res.should_return(): return res
        return_value = res.register(method(exec_ctx))
        if res.should_return(): return res
        return res.success(return_value)
    
    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} method defined')
    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    
    def __repr__(self):
        return f"<built-in function {self.name}>"

    ##########################

    def execute_run(self, exec_ctx):
        fn = exec_ctx.symbol_table.get("fn")
        if not isinstance(fn, String):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument must be string",
                exec_ctx
            ))
        fn = fn.value
        try:
            with open(f"{fn}", "r") as f:
                script = f.read()
        except Exception as e:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                f"Failed to load script \"{fn}\"\n" + str(e),
                exec_ctx
            ))
        _, error = run(fn, script)
        if error:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                f"Failed to finish executing script \"{fn}\"\n" +
                error.as_string(),
                exec_ctx
            ))
        return RTResult().success(Number.null)
    execute_run.arg_names = ["fn"]

    def execute_printf(self, exec_ctx):
        print(str(exec_ctx.symbol_table.get('value')))
        return RTResult().success(Number.null)
    execute_printf.arg_names = ['value']
    def execute_print_ret(self, exec_ctx):
        return RTResult().success(String(str(exec_ctx.symbol_table.get('value'))))
    execute_print_ret.arg_names = ['value']

    def execute_input(self, exec_ctx):
        text = exec_ctx.symbol_table.get('text')
        inpt = input()
        return RTResult().success(String(inpt))
    execute_input.arg_names = ['text']
    def execute_input_int(self, exec_ctx):
        text = exec_ctx.symbol_table.get('text')
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer. Try again!")
        return RTResult().success(Number(number))
    execute_input_int.arg_names = ['text']

    def execute_clear(self, exec_ctx):
        os.system('cls' if os.name == 'nt' else 'clear')
        return RTResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_is_number(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get('value'), Number)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_number.arg_names = ['value']
    def execute_is_string(self, exec_ctx):
        is_string = isinstance(exec_ctx.symbol_table.get('value'), String)
        return RTResult().success(Number.true if is_string else Number.false)
    execute_is_string.arg_names = ['value']
    def execute_is_list(self, exec_ctx):
        is_list = isinstance(exec_ctx.symbol_table.get('value'), List)
        return RTResult().success(Number.true if is_list else Number.false)
    execute_is_list.arg_names = ['value']
    def execute_is_function(self, exec_ctx):
        is_function = isinstance(exec_ctx.symbol_table.get('value'), BaseFunction)
        return RTResult().success(Number.true if is_function else Number.false)
    execute_is_function.arg_names = ['value']

    #############################
    # TABLE FUNCTIONS
    #############################

    def execute_table_len(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get('list')
        if not isinstance(list_, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument must be table",
                exec_ctx
            ))
        return RTResult().success(Number(len(list_.elements)))
    execute_table_len.arg_names = ['table']

    def execute_table_insert(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get('list')
        value = exec_ctx.symbol_table.get('value')

        if not isinstance(list_, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))
        list_.elements.append(value)
        return RTResult().success(Number.null)
    execute_table_insert.arg_names = ['list', 'value']

    def execute_table_remove(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get('list')
        index = exec_ctx.symbol_table.get('index')

        if not isinstance(list_, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))
        if not isinstance(index, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be number",
                exec_ctx
            ))
        try:
            element = list_.elements.pop(index.value)
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                'Element at this index could not be removed from list because index is out of range',
                exec_ctx
            ))
        return RTResult().success(element)
    execute_table_remove.arg_names = ['list', 'index']

    def execute_table_extend(self, exec_ctx):
        listA = exec_ctx.symbol_table.get('listA')
        listB = exec_ctx.symbol_table.get('listB')

        if not isinstance(listA, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))
        if not isinstance(listB, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be list",
                exec_ctx
            ))
        listA.elements.extend(listB.elements)
        return RTResult().success(Number.null)
    execute_table_extend.arg_names = ['listA', 'listB']

    def execute_table_clear(self, exec_ctx):
        table = exec_ctx.symbol_table.get("table")
        if table is None or not isinstance(table, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "clear() takes a table as an argument",
                exec_ctx
            ))
        for key in table.elements:
            table.elements.pop(key)
        return RTResult().success(None)
    execute_table_clear.arg_names = ['table']

    def execute_table_concat(self, exec_ctx):
        sep = exec_ctx.symbol_table.get("sep")
        i = exec_ctx.symbol_table.get("i")
        j = exec_ctx.symbol_table.get("j")
        table = exec_ctx.symbol_table.get("t")

        if sep is None:
            sep = ""
        if i is None:
            i = 1
        if j is None:
            j = len(table.elements)

        if not isinstance(table, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Invalid argument type for table.concat()",
                exec_ctx
            ))
        try:
            sep = str(sep)
            i = str(i)
            j = str(j)
            if int(i) < int(1) or int(i) > int(len(table.elements)) or int(j) < int(1):
                return RTResult().failure(RTError(
                    self.pos_start, self.pos_end,
                    "Invalid range for table.concat()",
                    exec_ctx
                ))
            result = sep.join(map(str, table.elements[int(i) - int(1):int(j)]))
            return RTResult().success(String(result))
        except ValueError:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Invalid argument for table.concat()",
                exec_ctx
            ))
    execute_table_concat.arg_names = ['t', 'sep', 'i', 'j']

    def execute_table_find(self, exec_ctx):
        haystack = exec_ctx.symbol_table.get("haystack")
        needle = exec_ctx.symbol_table.get("needle")
        init = exec_ctx.symbol_table.get("init")
        if haystack is None or not isinstance(haystack, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Invalid argument type for table.find()",
                exec_ctx
            ))
        # make for me table.find function
        if needle is None:
            needle = ""
        if init is None:
            init = 1
        try:
            needle = str(needle)
            init = str(init)
            if int(init) < int(1) or int(init) > int(len(haystack.elements)):
                return RTResult().failure(RTError(
                    self.pos_start, self.pos_end,
                    "Invalid range for table.find()",
                    exec_ctx
                ))
            result = haystack.elements[int(init) - int(1):].index(needle)
            return RTResult().success(Number(result))
        except ValueError:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Invalid argument for table.find()",
                exec_ctx
            ))
    execute_table_find.arg_names = ['haystack', 'needle', 'init']

    #############################
    # MATH FUNCTIONS
    #############################

    def execute_math_abs(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "abs() takes 1 argument",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of abs() must be a number",
                exec_ctx
            ))
        return RTResult().success(Number(abs(x.value)))
    execute_math_abs.arg_names = ['value']

    def execute_math_acos(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "math.acos() takes one argument",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of math.acos() must be a number",
                exec_ctx
            ))
        result = math.acos(x.value)
        return RTResult().success(Number(result))
    execute_math_acos.arg_names = ['value']

    def execute_math_asin(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "math.asin() takes one argument",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of math.asin() must be a number",
                exec_ctx
            ))
        result = math.asin(x.value)
        return RTResult().success(Number(result))
    execute_math_asin.arg_names = ['value']

    def execute_math_atan(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "atan() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of atan() must be a number",
                exec_ctx
            ))
        result = math.atan(x.value)
        return RTResult().success(Number(result))
    execute_math_atan.arg_names = ['value']

    def execute_math_atan2(self, exec_ctx):
        y = exec_ctx.symbol_table.get("y")
        x = exec_ctx.symbol_table.get("x")
        if y is None or x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "atan2() missing arguments 'y' and 'x'",
                exec_ctx
            ))
        if not isinstance(y, Number) or not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Both arguments of atan2() must be numbers",
                exec_ctx
            ))
        result = math.atan2(y.value, x.value)
        return RTResult().success(Number(result))
    execute_math_atan2.arg_names = ['y', 'x']

    def execute_math_ceil(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "ceil() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of ceil() must be a number",
                exec_ctx
            ))
        result = math.ceil(x.value)
        return RTResult().success(Number(result))
    execute_math_ceil.arg_names = ['value']

    def execute_math_clamp(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        min_value = exec_ctx.symbol_table.get("min")
        max_value = exec_ctx.symbol_table.get("max")

        if x is None or min_value is None or max_value is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "clamp() missing arguments 'x', 'min', and 'max'",
                exec_ctx
            ))
        if not isinstance(x, Number) or not isinstance(min_value, Number) or not isinstance(max_value, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Arguments of clamp() must be numbers",
                exec_ctx
            ))
        result = max(min(x.value, max_value.value), min_value.value)
        return RTResult().success(Number(result))
    execute_math_clamp.arg_names = ['value', 'min', 'max']

    def execute_math_cos(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "cos() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of cos() must be a number",
                exec_ctx
            ))
        result = math.cos(x.value)
        return RTResult().success(Number(result))
    execute_math_cos.arg_names = ['value']

    def execute_math_cosh(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "cosh() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of cosh() must be a number",
                exec_ctx
            ))
        result = math.cosh(x.value)
        return RTResult().success(Number(result))
    execute_math_cosh.arg_names = ['value']

    def execute_math_deg(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "deg() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of deg() must be a number",
                exec_ctx
            ))
        result = math.degrees(x.value)
        return RTResult().success(Number(result))
    execute_math_deg.arg_names = ['value']

    def execute_math_exp(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "exp() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of exp() must be a number",
                exec_ctx
            ))
        result = math.exp(x.value)
        return RTResult().success(Number(result))
    execute_math_exp.arg_names = ['value']

    def execute_math_floor(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "floor() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of floor() must be a number",
                exec_ctx
            ))
        result = math.floor(x.value)
        return RTResult().success(Number(result))
    execute_math_floor.arg_names = ['value']

    def execute_math_fmod(self, exec_ctx):
        x = exec_ctx.symbol_table.get("x")
        y = exec_ctx.symbol_table.get("y")
        if x is None or y is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "fmod() missing arguments 'x' or 'y'",
                exec_ctx
            ))
        if not isinstance(x, Number) or not isinstance(y, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Both arguments of fmod() must be numbers",
                exec_ctx
            ))
        if y.value == 0:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Division by zero in fmod()",
                exec_ctx
            ))
        result = math.fmod(x.value, y.value)
        return RTResult().success(Number(result))
    execute_math_fmod.arg_names = ['x', 'y']

    def execute_math_frexp(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "frexp() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of frexp() must be a number",
                exec_ctx
            ))
        mantissa, exponent = math.frexp(x.value)
        result = [Number(mantissa), Number(exponent)]
        return RTResult().success(List(result))
    execute_math_frexp.arg_names = ['value']

    def execute_math_ldexp(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        e = exec_ctx.symbol_table.get("e")
        if x is None or e is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "ldexp() missing arguments 'x' or 'e'",
                exec_ctx
            ))
        if not isinstance(x, Number) or not isinstance(e, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Both arguments of ldexp() must be numbers",
                exec_ctx
            ))
        result = math.ldexp(x.value, int(e.value))
        return RTResult().success(Number(result))
    execute_math_ldexp.arg_names = ['value', 'e']

    def execute_math_log(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        base = exec_ctx.symbol_table.get("base")
        if x is None or base is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "log() missing arguments 'x' or 'base'",
                exec_ctx
            ))
        if not isinstance(x, Number) or not isinstance(base, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Both arguments of log() must be numbers",
                exec_ctx
            ))
        if x.value <= 0 or base.value <= 0 or base.value == 1:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Invalid argument(s) in log()",
                exec_ctx
            ))
        result = math.log(x.value, base.value)
        return RTResult().success(Number(result))
    execute_math_log.arg_names = ['value', 'base']

    def execute_math_log10(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "log10() missing argument 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of log10() must be a number",
                exec_ctx
            ))
        if x.value <= 0:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Invalid argument in log10()",
                exec_ctx
            ))
        result = math.log10(x.value)
        return RTResult().success(Number(result))
    execute_math_log10.arg_names = ['value']

    def execute_math_max(self, exec_ctx):
        args = exec_ctx.symbol_table.get("args")
        if args is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "max() missing argument 'args'",
                exec_ctx
            ))
        if not isinstance(args, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of max() must be a list",
                exec_ctx
            ))
        if len(args.elements) == 0:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "max() cannot be called with an empty list",
                exec_ctx
            ))
        max_value = max(args.elements, key=lambda x: x.value)
        return RTResult().success(max_value)
    execute_math_max.arg_names = ['args']

    def execute_math_min(self, exec_ctx):
        args = exec_ctx.symbol_table.get("args")
        if args is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "min() missing argument 'args'",
                exec_ctx
            ))
        if not isinstance(args, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of min() must be a list",
                exec_ctx
            ))
        if len(args.elements) == 0:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "min() cannot be called with an empty list",
                exec_ctx
            ))
        min_value = min(args.elements, key=lambda x: x.value)
        return RTResult().success(min_value)
    execute_math_min.arg_names = ['args']

    def execute_math_modf(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if x is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "modf() missing 1 required positional argument: 'x'",
                exec_ctx
            ))
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "modf() argument must be a number",
                exec_ctx
            ))
        integral_part = Number(math.floor(x.value))
        fractional_part = Number(x.value - integral_part.value)

        result = List([integral_part, fractional_part])
        return RTResult().success(result)
    execute_math_modf.arg_names = ['value']

    def execute_math_noise(self, exec_ctx):
        x = exec_ctx.symbol_table.get("x")
        y = exec_ctx.symbol_table.get("y")
        if x is None or y is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "noise() takes three arguments",
                exec_ctx
            ))
        if not isinstance(x, Number) or not isinstance(y, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "All arguments of noise() must be numbers",
                exec_ctx
            ))
        noise_value = Number(perlin(x.value, y.value))
        return RTResult().success(noise_value)
    execute_math_noise.arg_names = ['x', 'y']

    def execute_math_pow(self, exec_ctx):
        x = exec_ctx.symbol_table.get("x")
        y = exec_ctx.symbol_table.get("y")
        if not isinstance(x, Number) or not isinstance(y, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Both arguments of pow() must be numbers",
                exec_ctx
            ))
        result = x.value ** y.value
        return RTResult().success(Number(result))
    execute_math_pow.arg_names = ['x', 'y']

    def execute_math_rad(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of rad() must be a number",
                exec_ctx
            ))
        result = math.radians(x.value)
        return RTResult().success(Number(result))
    execute_math_rad.arg_names = ['value']

    def execute_math_random(self, exec_ctx):
        min_value = exec_ctx.symbol_table.get("min")
        max_value = exec_ctx.symbol_table.get("max")
        if min_value is None or max_value is None:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "math.random() takes two arguments",
                exec_ctx
            ))
        if not isinstance(min_value, Number) or not isinstance(max_value, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Both arguments of math.random() must be numbers",
                exec_ctx
            ))
        min_int = int(min_value.value)
        max_int = int(max_value.value)
        if min_int > max_int:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "min value cannot be greater than max value in math.random()",
                exec_ctx
            ))
        random_int = random.randint(min_int, max_int)
        return RTResult().success(Number(random_int))
    execute_math_random.arg_names = ['min', 'max']

    def execute_math_randomseed(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of randomseed() must be a number",
                exec_ctx
            ))
        return RTResult().success(Number(random.seed(x.value)))
    execute_math_randomseed.arg_names = ['value']

    def execute_math_round(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of round() must be a number",
                exec_ctx
            ))
        result = round(x.value)
        return RTResult().success(Number(result))
    execute_math_round.arg_names = ['value']

    def execute_math_sign(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of sign() must be a number",
                exec_ctx
            ))
        result = math.copysign(1, x.value)
        return RTResult().success(Number(result))
    execute_math_sign.arg_names = ['value']

    def execute_math_sin(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of sin() must be a number",
                exec_ctx
            ))
        result = math.sin(x.value)
        return RTResult().success(Number(result))
    execute_math_sin.arg_names = ['value']

    def execute_math_sinh(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of sinh() must be a number",
                exec_ctx
            ))
        result = math.sinh(x.value)
        return RTResult().success(Number(result))
    execute_math_sinh.arg_names = ['value']

    def execute_math_sqrt(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of sqrt() must be a number",
                exec_ctx
            ))
        if x.value < 0:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of sqrt() must be a non-negative number",
                exec_ctx
            ))
        result = math.sqrt(x.value)
        return RTResult().success(Number(result))
    execute_math_sqrt.arg_names = ['value']

    def execute_math_tan(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of tan() must be a number",
                exec_ctx
            ))
        result = math.tan(x.value)
        return RTResult().success(Number(result))
    execute_math_tan.arg_names = ['value']

    def execute_math_tanh(self, exec_ctx):
        x = exec_ctx.symbol_table.get("value")
        if not isinstance(x, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument of tanh() must be a number",
                exec_ctx
            ))
        result = math.tanh(x.value)
        return RTResult().success(Number(result))
    execute_math_tanh.arg_names = ['value']

# Main
Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.math_huge = Number(float('inf'))
Number.math_pi = Number(math.pi)

BuiltInFunction.run             = BuiltInFunction("run")
BuiltInFunction.print           = BuiltInFunction("println")
BuiltInFunction.print_ret       = BuiltInFunction("print_ret")
BuiltInFunction.input           = BuiltInFunction("input")
BuiltInFunction.input_int       = BuiltInFunction("input_int")
BuiltInFunction.clear           = BuiltInFunction("clear")

# Is
BuiltInFunction.isnumber        = BuiltInFunction("isnumber")
BuiltInFunction.isstring        = BuiltInFunction("isstring")
BuiltInFunction.islist          = BuiltInFunction("islist")
BuiltInFunction.isfunction      = BuiltInFunction("isfunction")

# Tables
BuiltInFunction.insert          = BuiltInFunction("table_insert")
BuiltInFunction.remove          = BuiltInFunction("table_remove")
BuiltInFunction.extend          = BuiltInFunction("table_extend")
BuiltInFunction.tclear          = BuiltInFunction("table_clear")
BuiltInFunction.concat          = BuiltInFunction("table_concat")
BuiltInFunction.find            = BuiltInFunction("table_find")
BuiltInFunction.len             = BuiltInFunction("table_len")

# Math
BuiltInFunction.abs             = BuiltInFunction("math_abs")
BuiltInFunction.acos            = BuiltInFunction("math_acos")
BuiltInFunction.asin            = BuiltInFunction("math_asin")
BuiltInFunction.atan            = BuiltInFunction("math_atan")
BuiltInFunction.atan2           = BuiltInFunction("math_atan2")
BuiltInFunction.ceil            = BuiltInFunction("math_ceil")
BuiltInFunction.clamp           = BuiltInFunction("math_clamp")
BuiltInFunction.cos             = BuiltInFunction("math_cos")
BuiltInFunction.cosh            = BuiltInFunction("math_cosh")
BuiltInFunction.deg             = BuiltInFunction("math_deg")
BuiltInFunction.exp             = BuiltInFunction("math_exp")
BuiltInFunction.floor           = BuiltInFunction("math_floor")
BuiltInFunction.fmod            = BuiltInFunction("math_fmod")
BuiltInFunction.frexp           = BuiltInFunction("math_frexp")
BuiltInFunction.ldexp           = BuiltInFunction("math_ldexp")
BuiltInFunction.log             = BuiltInFunction("math_log")
BuiltInFunction.log10           = BuiltInFunction("math_log10")
BuiltInFunction.max             = BuiltInFunction("math_max")
BuiltInFunction.min             = BuiltInFunction("math_min")
BuiltInFunction.modf            = BuiltInFunction("math_modf")
BuiltInFunction.noise           = BuiltInFunction("math_noise")
BuiltInFunction.pow             = BuiltInFunction("math_pow")
BuiltInFunction.rad             = BuiltInFunction("math_rad")
BuiltInFunction.random          = BuiltInFunction("math_random")
BuiltInFunction.randomseed      = BuiltInFunction("math_randomseed")
BuiltInFunction.round           = BuiltInFunction("math_round")
BuiltInFunction.sign            = BuiltInFunction("math_sign")
BuiltInFunction.sin             = BuiltInFunction("math_sin")
BuiltInFunction.sinh            = BuiltInFunction("math_sinh")
BuiltInFunction.sqrt            = BuiltInFunction("math_sqrt")
BuiltInFunction.tan             = BuiltInFunction("math_tan")
BuiltInFunction.tanh            = BuiltInFunction("math_tanh")
