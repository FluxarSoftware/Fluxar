use crate::expr::{Expr, LiteralValue};
use crate::scanner::Token;
use crate::type_::Type;
use crate::statements::Statement;
use std::collections::HashMap;

// use std::cell::RefCell;
// use std::rc::Rc;

#[derive(Copy, Clone, PartialEq)]
enum FunctionType { None, Function, Method }

#[allow(dead_code)]
pub struct Resolver {
    scopes: Vec<HashMap<String, bool>>,
    current_function: FunctionType,
    locals: HashMap<usize, usize>,
}
impl Resolver {
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self {
            scopes: vec![],
            current_function: FunctionType::None,
            locals: HashMap::new(),
        }
    }
    #[allow(dead_code)]
    pub fn resolve(mut self, statements: &Vec<&Statement>) -> Result<HashMap<usize, usize>, String> {
        self.resolve_many(statements)?; Ok(self.locals)
    }
    fn resolve_internal(&mut self, statement: &Statement) -> Result<(), String> {
        match statement {
            Statement::Block { statements: _ } => self.resolve_block(statement)?,
            Statement::Var { name: _, var_type: _, initializer: _ } => self.resolve_var(statement)?,
            Statement::Class { name, generics, methods, superclass } => { 
                if let Some(super_expr) = superclass {
                    if let Expr::Variable { id: _, var_type: _, name: super_name } = super_expr {
                        if super_name.lexeme == name.lexeme {
                            return Err("A class cannot inherit from itself".to_string());
                        }
                    }
                    self.resolve_expr(super_expr)?; self.begin_scope();
                    self.scopes.last_mut().unwrap().insert("super".to_string(), true);
                }
                self.declare(name)?; self.define(name); self.begin_scope();
                self.scopes.last_mut().unwrap().insert("this".to_string(), true);
                for generic in generics {
                    self.declare(generic)?;
                    self.define(generic);
                }
                for method in methods {
                    let declaration = FunctionType::Method;
                    self.resolve_function(method, declaration)?;
                }
                self.end_scope();
                if superclass.is_some() {
                    self.end_scope();
                }
             },
            Statement::Function { name: _, params: _, generics: _, return_type: _, body: _ } => self.resolve_function(statement, FunctionType::Function)?,
            Statement::Expression { expression } => self.resolve_expr(expression)?,
            Statement::IfStmt { predicate: _, then: _, els: _ } => self.resolve_if_stmt(statement)?,
            Statement::Print { expression } => self.resolve_expr(expression)?,
            Statement::ReturnStmt { keyword: _, value } => {
                if self.current_function == FunctionType::None { return Err("Return statement is not allowed outside of a function".to_string()); }
                if let Some(value) = value { self.resolve_expr(value)?; }
            },
            Statement::WhileStmt { condition, body } => {
                self.resolve_expr(condition)?;
                self.resolve_internal(body.as_ref())?;
            },
            Statement::CmdFunction { name: _, cmd: _ } => self.resolve_var(statement)?,
        }
        Ok(())
    }
    fn resolve_many(&mut self, statements: &Vec<&Statement>) -> Result<(), String> {
        for statement in statements { self.resolve_internal(statement)?; } Ok(())
    }
    fn resolve_block(&mut self, statement: &Statement) -> Result<(), String> {
        match statement {
            Statement::Block { statements } => {
                self.begin_scope();
                self.resolve_many(&statements.iter().map(|b| b.as_ref()).collect())?;
                self.end_scope();
            }
            _ => panic!("Wrong type"),
        }
        Ok(())
    }
    fn resolve_var(&mut self, statement: &Statement) -> Result<(), String> {
        if let Statement::Var { name, var_type, initializer } = statement {
            self.declare(name)?;
            if let Some(var_type) = var_type {
                let expected_type = self.resolve_type(var_type)?;
                let actual_type = self.infer_type(initializer)?;
    
                if expected_type != actual_type {
                    return Err(format!(
                        "Type error: expected {:?}, but found {:?} for variable {}",
                        expected_type, actual_type, name.lexeme
                    ));
                }
            }    
            self.resolve_expr(initializer)?;
            self.define(name);
        } else if let Statement::CmdFunction { name, cmd: _ } = statement {
            self.declare(name)?; self.define(name);
        } else { panic!("Wrong type in resolve var"); }
        Ok(())
    }
    fn resolve_function(&mut self, statement: &Statement, fn_type: FunctionType) -> Result<(), String> {
        if let Statement::Function { name, generics, return_type, params, body } = statement {
            self.declare(name)?; self.define(name);
            self.resolve_function_helper(params, generics, return_type, &body.iter().map(|b| 
                b.as_ref()).collect(), fn_type)
        } else { panic!("Wrong type in resolve function"); }
    }
    fn resolve_function_helper(
        &mut self, params: &Vec<Token>, generics: &Vec<Token>, return_type: &Option<Token>,
        body: &Vec<&Statement>, resolving_function: FunctionType
    ) -> Result<(), String> {
        let enclosing_function = self.current_function;
        self.current_function = resolving_function;
        self.begin_scope();

        for generic in generics {
            self.declare(generic)?;
            self.define(generic);
        }
        for param in params {
            self.declare(param)?;
            self.define(param);
        }
        if let Some(return_type) = return_type {
            self.declare(return_type)?;
            self.define(return_type);
        }
        self.resolve_many(body)?;
        self.end_scope(); self.current_function = enclosing_function;
        Ok(())
    }
    fn resolve_if_stmt(&mut self, statement: &Statement) -> Result<(), String> {
        if let Statement::IfStmt { predicate, then, els } = statement {
            self.resolve_expr(predicate)?;
            self.resolve_internal(then.as_ref())?;
            if let Some(els) = els {
                self.resolve_internal(els.as_ref())?;
            }
            Ok(())
        } else { panic!("Wrong type in resolve if statement"); }
    }
    fn begin_scope(&mut self) { self.scopes.push(HashMap::new()); }
    fn end_scope(&mut self) { self.scopes.pop().expect("Stack underflow"); }
    fn declare(&mut self, name: &Token) -> Result<(), String> {
        let size = self.scopes.len();
        if self.scopes.is_empty() { return Ok(()); }
        if self.scopes[size - 1].contains_key(&name.lexeme.clone()) {
            return Err("A variable with this name is already in scope".to_string())
        }; self.scopes[size - 1].insert(name.lexeme.clone(), false); Ok(())
    }
    fn define(&mut self, name: &Token) {
        if self.scopes.is_empty() { return; }
        let size = self.scopes.len();
        self.scopes[size - 1].insert(name.lexeme.clone(), true);
    }
    fn resolve_expr(&mut self, expr: &Expr) -> Result<(), String> {
        match expr {
            Expr::Assign { id: _, name: _, value: _ } => self.resolve_expr_assign(expr, expr.get_id()),
            Expr::AnonFunction { id: _, paren: _, generics, arguments, return_type, body } 
                => self.resolve_function_helper(generics, arguments, return_type, 
                    &body.iter().map(|b| b.as_ref()).collect(),
                    FunctionType::Function),
            Expr::Binary { id: _, left, operator: _, right } => {
                self.resolve_expr(left)?;
                self.resolve_expr(right)
            },
            Expr::Call { id: _, callee, paren: _, arguments, generics } => {
                self.resolve_expr(callee.as_ref())?;
                for arg in arguments {
                    self.resolve_expr(arg)?;
                }
                for generic in generics {
                    let var_type = Some(generic.clone());
                    self.resolve_expr(&Expr::Variable {
                        id: expr.get_id(), var_type,
                        name: generic.clone(),
                    })?;
                }
                Ok(())
            },
            Expr::Get { id: _, object, name: _ } => self.resolve_expr(object),
            Expr::Grouping { id: _, expression } => self.resolve_expr(expression),
            Expr::Literal { id: _, value: _ } => Ok(()),
            Expr::Logical { id: _, left, operator: _, right } => {
                self.resolve_expr(left)?;
                self.resolve_expr(right)
            },
            Expr::Set { id: _, object, name: _, value } => {
                self.resolve_expr(value)?;
                self.resolve_expr(object)
            }
            Expr::This { id: _, keyword } => {
                if self.current_function != FunctionType::Method {
                    return Err("Cannot use 'this' keyword outside of a class".to_string());
                }; self.resolve_local(keyword, expr.get_id())
            },
            Expr::Super { id: _, keyword, method: _ } => {
                if self.current_function != FunctionType::Method { return Err("Cannot use 'super' keyword outside of a class".to_string()); }
                if self.scopes.len() < 3 || !self.scopes[self.scopes.len() - 3].contains_key("super") {
                    return Err("Class has no superclass".to_string());
                }; self.resolve_local(keyword, expr.get_id())
            }
            Expr::Variable { id: _, var_type: _, name: _ } => self.resolve_expr_var(expr, expr.get_id()),
            Expr::Unary { id: _, operator: _, right } => self.resolve_expr(right),
        }
    }
    fn resolve_expr_var(&mut self, expr: &Expr, resolve_id: usize) -> Result<(), String> {
        match expr {
            Expr::Variable { id: _, var_type: _, name } => {
                if !self.scopes.is_empty() {
                    if let Some(false) = self.scopes[self.scopes.len() - 1].get(&name.lexeme) {
                        return Err("Can't read local variable in it's own initializer".to_string());
                    }
                }
                self.resolve_local(name, resolve_id)
            },
            Expr::Call { id: _, callee, paren: _, arguments: _, generics: _ } => match callee.as_ref() {
                Expr::Variable { id: _, var_type: _, name } => self.resolve_local(&name, resolve_id),
                _ => panic!("Wrong type in resolve_expr_var"),
            },
            _ => panic!("Wrong type in resolve_expr_var"),
        }
    }
    fn resolve_local(&mut self, name: &Token, resolve_id: usize) -> Result<(), String> {
        let size = self.scopes.len();
        if size == 0 { return Ok(()); }

        for i in (0..=(size - 1)).rev() {
            let scope = &self.scopes[i];
            if scope.contains_key(&name.lexeme) {
                self.locals.insert(resolve_id, size - 1 - i);
                return Ok(());
            }
        }
        Ok(())
    }
    fn resolve_expr_assign(&mut self, expr: &Expr, resolve_id: usize) -> Result<(), String> {
        if let Expr::Assign { id: _, name, value } = expr {
            self.resolve_expr(value.as_ref())?;
            self.resolve_local(name, resolve_id)?;
        } else { panic!("Wrong type in resolve assign"); }
        Ok(())
    }
    fn resolve_type(&self, token: &Token) -> Result<Type, String> {
        Type::from_str(&token.lexeme)
    }
    fn infer_type(&self, expr: &Expr) -> Result<Type, String> {
        match expr {
            Expr::Literal { id: _, value } => match &value {
                LiteralValue::Number(_) => Ok(Type::Int),
                LiteralValue::StringValue(_) => Ok(Type::String),
                _ => Err(format!("Unknown literal type")),
            },
            Expr::Call { callee, arguments, generics, .. } => {
                let callee_type = self.infer_type(callee)?;
                if let Type::Generic(ref type_name) = callee_type {
                    if type_name == "Box" {
                        if generics.len() == 1 {
                            let generic_type = self.resolve_type(&generics[0])?;
                            return Ok(Type::Class(Box::new(generic_type)));
                        } else {
                            return Err(format!("Box type requires exactly one generic parameter"));
                        }
                    }
                }
                for arg in arguments {
                    self.infer_type(arg)?;
                }
                Ok(callee_type)
            },
            Expr::Variable { name, var_type, .. } => {
                if let Some(var_type) = var_type {
                    self.resolve_type(var_type)
                } else {
                    Err(format!("Cannot infer type for variable {}", name.lexeme))
                }
            },
            _ => Err(format!("Cannot infer type for expression")),
        }
    }
}