use crate::environment::Environment;
use crate::expr::{
    LiteralValue, CallableImpl, 
    FluxarFunctionImpl, NativeFunctionImpl
};
use crate::statements::Statement;
use crate::scanner::Token;

use std::collections::HashMap;
use std::process::Command;
use std::rc::Rc;

pub struct Interpreter {
    pub specials: HashMap<String, LiteralValue>,
    pub environment: Environment,
}
impl Interpreter {
    pub fn new() -> Self {
        Self {
            specials: HashMap::new(),
            environment: Environment::new(HashMap::new()),
        }
    }
    pub fn resolve(&mut self, locals: HashMap<usize, usize>) { self.environment.resolve(locals); }
    pub fn with_env(env: Environment) -> Self { Self { specials: HashMap::new(), environment: env } }

    #[allow(dead_code)]
    pub fn for_anon(parent: Environment) -> Self {
        let env = parent.enclose();
        Self { specials: HashMap::new(), environment: env }
    }
    pub fn interpret(&mut self, stmts: Vec<&Statement>) -> Result<(), String> {
        for stmt in stmts {
            match stmt {
                Statement::Expression { expression } => {
                    expression.evaluate(self.environment.clone())?;
                },
                Statement::Print { expression } => {
                    let value = expression.evaluate(self.environment.clone())?;
                    println!("{}", value.to_string());
                },
                Statement::Var { name, initializer } => {
                    let value = initializer.evaluate(self.environment.clone())?;
                    self.environment.define(name.lexeme.clone(), value);
                },
                Statement::Block { statements } => {
                    let new_environment = self.environment.enclose();
                    // new_environment.enclosing = Some(Box::new(self.environment.clone()));

                    let old_environment = self.environment.clone();
                    self.environment = new_environment;
                    let block_result = self.interpret(
                        (*statements).iter().map(|b| b.as_ref()).collect());
                    self.environment = old_environment;
                    block_result?; 
                },
                Statement::Function { name, params: _, body: _ } => {
                    let callable = self.make_function(stmt);
                    let fun = LiteralValue::Callable(CallableImpl::FluxarFunction(callable));
                    self.environment.define(name.lexeme.clone(), fun);
                }
                Statement::Class { name, methods, superclass } => {
                    let mut methods_map = HashMap::new();
                    // Insert the methods of the superclass into the methods of this class
                    let superclass_value;
                    if let Some(superclass) = superclass {
                        let superclass = superclass.evaluate(self.environment.clone())?;
                        if let LiteralValue::FluxarClass { .. } = superclass {
                            superclass_value = Some(Box::new(superclass));
                        } else { return Err(format!("Superclass must be a class, not {}", superclass.to_type())); }
                    } else { superclass_value = None }

                    self.environment.define(name.lexeme.clone(), LiteralValue::Nil);
                    self.environment = self.environment.enclose();
                    if let Some(sc) = superclass_value.clone() {
                        self.environment.define("super".to_string(), *sc);
                    }
                    for method in methods {
                        if let Statement::Function { name, params: _, body: _ } = method.as_ref() {
                            let function = self.make_function(method);
                            methods_map.insert(name.lexeme.clone(), function);
                        } else { panic!("Something that was not a function was in the methods of a class"); }
                    }
                    let class = LiteralValue::FluxarClass { 
                        name: name.lexeme.clone(), methods: methods_map,
                        superclass: superclass_value
                    };
                    if !self.environment.assign_global(&name.lexeme, class) {
                        return Err(format!("Class definition failed for {}", name.lexeme));
                    }; self.environment = *self.environment.enclosing.clone().unwrap();
                },
                Statement::IfStmt { predicate, then, els } => {
                    let truth_value = predicate.evaluate(self.environment.clone())?;
                    if truth_value.is_true() == LiteralValue::True {
                        self.interpret(vec![then.as_ref()])?;
                    } else if let Some(els_stmt) = els {
                        self.interpret(vec![els_stmt.as_ref()])?;
                    }
                },
                Statement::WhileStmt { condition, body } => {
                    let mut flag = condition.evaluate(self.environment.clone())?;
                    while flag.is_true() == LiteralValue::True {
                        let statements = vec![body.as_ref()];
                        self.interpret(statements)?;
                        flag = condition.evaluate(self.environment.clone())?;
                    }
                },
                Statement::ReturnStmt { keyword: _, value } => {
                    let eval_val;
                    if let Some(value) = value {
                        eval_val = value.evaluate(self.environment.clone())?;
                    } else { eval_val = LiteralValue::Nil; }
                    self.specials.insert("return".to_string(), eval_val);
                },
                Statement::CmdFunction { name, cmd } => {
                    // Return a callable that runs a shell commmand, captures the stdout and returns it in a String
                    let cmd = cmd.clone();
                    let local_fn = move |_args: &Vec<LiteralValue>| {
                        let cmd = cmd.clone();
                        let parts = cmd.split(" ").collect::<Vec<&str>>();
                        let mut command = Command::new(parts[0].replace("\"", ""));
                        for part in parts[1..].iter() { command.arg(part.replace("\"", "")); }
                        let output = command.output().expect("Failed to run command");
                        return LiteralValue::StringValue(
                            std::str::from_utf8(output.stdout.as_slice())
                                .unwrap().to_string()
                        );
                    };
                    let fun_val = LiteralValue::Callable(
                        CallableImpl::NativeFunction(NativeFunctionImpl {
                            name: name.lexeme.clone(), arity: 0,
                            fun: Rc::new(local_fn)
                        })
                    ); self.environment.define(name.lexeme.clone(), fun_val);
                },
            };
        }
        Ok(())
    }
    fn make_function(&self, fn_stmt: &Statement) -> FluxarFunctionImpl {
        if let Statement::Function { name, params, body } = fn_stmt {
            let (arity, name_clone) = (params.len(), name.lexeme.clone());
            let params: Vec<Token> = params.iter().map(|t| (*t).clone()).collect();
            let body: Vec<Box<Statement>> = body.iter().map(|b| (*b).clone()).collect();

            let parent_env = self.environment.clone();
            let callable_impl = FluxarFunctionImpl {
                name: name_clone, arity, parent_env, params, body
            }; callable_impl
        } else { panic!("Tried to make a function from a non-function statement"); }
    }
}