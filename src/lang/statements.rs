use crate::expr::Expr;
use crate::scanner::Token;

#[derive(Debug, Clone)]
pub enum Statement {
    Expression { expression: Expr },
    Print { expression: Expr },
    Var { name: Token, var_type: Option<Token>, initializer: Expr },
    Block { statements: Vec<Box<Statement>> },
    IfStmt { 
        predicate: Expr, then: Box<Statement>, 
        els: Option<Box<Statement>> 
    },
    WhileStmt { condition: Expr, body: Box<Statement> },
    ReturnStmt { keyword: Token, value: Option<Expr> },
    Class { name: Token, generics: Vec<Token>, methods: Vec<Box<Statement>>, superclass: Option<Expr> },
    Function { name: Token, params: Vec<Token>, generics: Vec<Token>, return_type: Option<Token>, body: Vec<Box<Statement>> },
    CmdFunction { name: Token, cmd: String },
}
impl Statement {
    #[allow(dead_code)]
    pub fn to_string(&self) -> String {
        use Statement::*;
        match self {
            Expression { expression } => expression.to_string(),
            Print { expression } => format!("(print {})", expression.to_string()),
            Var { name, var_type: _, initializer: _ } => format!("(var {name:?})"),
            Block { statements } => format!(
                "(block {})", statements.into_iter().map(|stmt| stmt.to_string()).collect::<String>()
            ),
            IfStmt { predicate: _, then: _, els: _ } => todo!(),
            WhileStmt { condition: _, body: _ } => todo!(),
            ReturnStmt { keyword: _, value: _ } => todo!(),
            Function { name: _, params: _, generics: _, return_type: _, body: _ } => todo!(),
            CmdFunction { name: _, cmd: _ } => todo!(),
            _ => todo!(),
        }
    }
}