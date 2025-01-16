use crate::scanner::{Token, TokenType::*, TokenType};
use crate::expr::{Expr::*, Expr, LiteralValue};
use crate::statements::Statement;

pub struct Parser {
    tokens: Vec<Token>,
    current: usize,
    next_id: usize,
}
#[derive(Debug)]
enum FunctionKind { Function, Method }
impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, current: 0, next_id: 0 }
    }
    pub fn get_id(&mut self) -> usize {
        let id = self.next_id;
        self.next_id += 1;
        id
    }
    fn advance(&mut self) -> Token {
        if !self.is_at_end() { self.current += 1; }
        self.previous()
    }
    fn previous(&mut self) -> Token {
        self.tokens[self.current - 1].clone()
    }
    fn is_at_end(&mut self) -> bool {
        let peek = self.tokens[self.current].clone();
        peek.token_type == Eof
    }
    pub fn parse(&mut self) -> Result<Vec<Statement>, String> {
        let mut stmts = vec![];
        let mut errors = vec![];
        while !self.is_at_end() {
            let stmt = self.declaration();
            match stmt {
                Ok(s) => stmts.push(s),
                Err(msg) => {
                    errors.push(msg);
                    self.synchronize();
                },
            }
        }
        if errors.len() == 0 { Ok(stmts) } else {
            Err(errors.join("\n"))
        }
    }
    fn declaration(&mut self) -> Result<Statement, String> {
        if self.match_token(Var) { self.var_declaration() }
        else if self.match_token(Fun) { self.function(FunctionKind::Function) }
        else if self.match_token(Class) { self.class_declaration() }
        else { self.statement() }
    }
    fn var_declaration(&mut self) -> Result<Statement, String> {
        let initializer;
        let token = self.consume(Identifier, "Expected variable name.")?;
        let var_type = if self.match_token(TokenType::Colon) {
            Some(self.consume(TokenType::Identifier, "Expected type annotation")?)
        } else { None };

        if self.match_token(Equal) { initializer = self.expression()?; }
        else { initializer = Literal { id: self.get_id(), value: LiteralValue::Nil }; }
        self.consume(Semicolon, "Expected ';' after variable declaration!")?;
        Ok(Statement::Var { name: token, var_type, initializer })
    }
    fn class_declaration(&mut self) -> Result<Statement, String> {
        let name = self.consume(Identifier, "Expected name after 'class' keyword.")?;
        let mut generics = Vec::new();
        if self.match_token(TokenType::Less) {
            loop {
                generics.push(self.consume(Identifier, "Expected type parameter.")?);
                if !self.match_token(Comma) { break; }
            }
            self.consume(Greater, "Expected '>' after type parameters.")?;
        }
        let superclass = if self.match_token(TokenType::Less) {
            self.consume(Identifier, "Expected superclass name after '<'.")?;
            Some(Expr::Variable { id: self.get_id(), var_type: None, name: self.previous() })
        } else { None };
        self.consume(LeftBrace, "Expected '{' before class body.")?;

        let mut methods = vec![];
        while !self.check(RightBrace) && !self.is_at_end() {
            let method = self.function(FunctionKind::Method)?;
            methods.push(Box::new(method));
        }
        self.consume(RightBrace, "Expected '}' after class body.")?;
        Ok(Statement::Class {name, generics, methods, superclass})
    }
    fn function(&mut self, kind: FunctionKind) -> Result<Statement, String> {
        let name = self.consume(Identifier, &format!("Expected {kind:?} name"))?;
        if self.match_token(Gets) {
            let cmd_body = self.consume(StringLit, "Expected command body")?;
            self.consume(Semicolon, "Expected ';' after command body")?;
            return Ok(Statement::CmdFunction { name, cmd: cmd_body.lexeme });
        }
        self.consume(LeftParen, &format!("Expected '(' after {kind:?} name"))?;

        let mut generics = Vec::new();
        if self.match_token(Less) {
            loop {
                generics.push(self.consume(Identifier, "Expected type parameter.")?);
                if !self.match_token(Comma) { break; }
            }
            self.consume(Greater, "Expected '>' after type parameters.")?;
        }
        let mut parameters = vec![];
        if !self.check(RightParen) {
            loop {
                if parameters.len() >= 255 {
                    let peek = self.tokens[self.current].clone();
                    let location = peek.line_number;
                    return Err(format!("Line {location}: Can't have more than 255 arguments"));
                }
                let param = self.consume(Identifier, "Expected parameter name")?;
                parameters.push(param);
                if !self.match_token(Comma) { break; }
            }
        }
        self.consume(RightParen, "Expected ')' after parameters")?;
        let return_type = if self.match_token(Arrow) {
            Some(self.consume(Identifier, "Expected return type after '->'")?)
        } else { None };
        
        self.consume(LeftBrace, &format!("Expected '{{' before {kind:?} body"))?;
        let body = match self.block_statement()? {
            Statement::Block { statements } => statements,
            _ => panic!("Block statement parsed something that was not a block"),
        };
        Ok(Statement::Function { name, params: parameters, generics, return_type, body })
    }
    fn statement(&mut self) -> Result<Statement, String> {
        if self.match_token(Print) { self.print_statement() }
        else if self.match_token(LeftBrace) { self.block_statement() } 
        else if self.match_token(If) { self.if_statement() }
        else if self.match_token(While) { self.while_statement() }
        else if self.match_token(For) { self.for_statement() }
        else if self.match_token(Return) { self.return_statement() }
        else { self.expression_statement() }
    }
    fn print_statement(&mut self) -> Result<Statement, String> {
        let value = self.expression()?;
        self.consume(Semicolon, "Expected ';' after value.")?;
        Ok(Statement::Print { expression: value })
    }
    fn block_statement(&mut self) -> Result<Statement, String> {
        let mut statements = vec![];
        while !self.check(RightBrace) && !self.is_at_end() {
            let decl = self.declaration()?;
            statements.push(Box::new(decl));
        }
        self.consume(RightBrace, "Expected '}' after a block.")?;
        Ok(Statement::Block { statements })
    }
    fn if_statement(&mut self) -> Result<Statement, String> {
        self.consume(LeftParen, "Expected '(' after 'if'")?;
        let predicate = self.expression()?;
        self.consume(RightParen, "Expected ')' after if-predicate")?;
        
        let then = Box::new(self.statement()?);
        let els = if self.match_token(Else) {
            let stm = self.statement()?;
            Some(Box::new(stm))
        } else { None };
        Ok(Statement::IfStmt { predicate, then, els })
    }
    fn while_statement(&mut self) -> Result<Statement, String> {
        self.consume(LeftParen, "Expected '(' after 'while'")?;
        let condition = self.expression()?;
        self.consume(RightParen, "Expected ')' after condition.")?;
        let body = Box::new(self.statement()?);
        Ok(Statement::WhileStmt { condition, body })
    }
    fn for_statement(&mut self) -> Result<Statement, String> {
        self.consume(LeftParen, "Expected '(' after 'for'.")?;
        let initializer;
        if self.match_token(Semicolon) { initializer = None;
        } else if self.match_token(Var) {
            let var_decl = self.var_declaration()?;
            initializer = Some(var_decl);
        } else {
            let expr = self.expression_statement()?;
            initializer = Some(expr);
        }
        let condition;
        if !self.check(Semicolon) {
            let expr = self.expression()?;
            condition = Some(expr);
        } else { condition = None; }
        self.consume(Semicolon, "Expected ';' after loop condition.")?;

        let increment;
        if !self.check(RightParen) {
            let expr = self.expression()?;
            increment = Some(expr);
        } else { increment = None; }
        self.consume(RightParen, "Expected ')' after for clauses.")?;

        let mut body = self.statement()?;
        if let Some(incr) = increment {
            body = Statement::Block {
                statements: vec![
                    Box::new(body),
                    Box::new(Statement::Expression { expression: incr }),
                ],
            };
        }
        let cond;
        match condition {
            None => {cond = Expr::Literal { id: self.get_id(), value: LiteralValue::True }}
            Some(c) => cond = c,
        }
        body = Statement::WhileStmt { condition: cond, body: Box::new(body) };
        if let Some(init) = initializer {
            body = Statement::Block { statements: vec![Box::new(init), Box::new(body)] };
        } Ok(body)
    }
    fn return_statement(&mut self) -> Result<Statement, String> {
        let value;
        let keyword = self.previous();
        if !self.check(Semicolon) { value = Some(self.expression()?); }
        else { value = None; }
        self.consume(Semicolon, "Expected ';' after return value")?;
        Ok(Statement::ReturnStmt { keyword, value })
    }
    fn expression_statement(&mut self) -> Result<Statement, String> {
        let expr = self.expression()?;
        self.consume(Semicolon, "Expected ';' after expression.")?;
        Ok(Statement::Expression { expression: expr })
    }
    fn expression(&mut self) -> Result<Expr, String> {
        self.assignment()
    }
    fn function_expression(&mut self) -> Result<Expr, String> {
        let paren = self.consume(LeftParen, "Expected '(' after anonymous function")?;
        let mut generics = Vec::new();
        if self.match_token(Less) {
            loop {
                generics.push(self.consume(Identifier, "Expected type parameter.")?);
                if !self.match_token(Comma) {
                    break;
                }
            }
            self.consume(Greater, "Expected '>' after type parameters.")?;
        }
        let mut parameters = vec![];
        if !self.check(RightParen) {
            loop {
                if parameters.len() >= 255 {
                    let peek = self.tokens[self.current].clone();
                    let location = peek.line_number;
                    return Err(format!("Line {location}: Can't have more than 255 arguments"));
                }
                let param = self.consume(Identifier, "Expected parameter name")?;
                parameters.push(param);
                if !self.match_token(Comma) { break; }
            }
        }
        let return_type = if self.match_token(Greater) {
            Some(self.consume(Identifier, "Expected return type after '->'")?)
        } else { None };

        self.consume(RightParen, "Expected ')' after anonymous function parameters")?;
        self.consume(LeftBrace, "Expected '{' after anonymous function declaration")?;
        let body = match self.block_statement()? {
            Statement::Block { statements } => statements,
            _ => panic!("Block statement parsed something that was not a block")
        };
        Ok(Expr::AnonFunction { id: self.get_id(), paren, generics, arguments: parameters, return_type, body })
    }
    fn assignment(&mut self) -> Result<Expr, String> {
        let expr = self.pipe()?;
        if self.match_token(Equal) {
            let value = self.expression()?;
            match expr {
                Variable { id: _, var_type: _, name } => { Ok(Assign { id: self.get_id(), name, value: Box::from(value) }) },
                Get { id: _, object, name } => { Ok(Set { id: self.get_id(), object, name, value: Box::new(value) }) }
                _ => Err("Invalid assignment target!".to_string())
            }
        } else { Ok(expr) }
    }
    fn pipe(&mut self) -> Result<Expr, String> {
        let mut expr = self.or()?;
        while self.match_token(Pipe) {
            let pipe = self.previous();
            let function = self.or()?;
            expr = Call {
                id: self.get_id(), callee: Box::new(function),
                paren: pipe, arguments: vec![expr], generics: vec![],
            };
        }
        Ok(expr)
    }
    fn or(&mut self) -> Result<Expr, String> {
        let mut expr = self.and()?;
        while self.match_token(Or) {
            let operator = self.previous();
            let right = self.and()?;
            expr = Logical {
                id: self.get_id(), left: Box::new(expr),
                operator, right: Box::new(right),
            };
        }
        Ok(expr)
    }
    fn and(&mut self) -> Result<Expr, String> {
        let mut expr = self.equality()?;
        while self.match_token(And) {
            let operator = self.previous();
            let right = self.equality()?;
            expr = Logical {
                id: self.get_id(), left: Box::new(expr), 
                operator, right: Box::new(right),
            };
        }
        Ok(expr)
    }
    fn equality(&mut self) -> Result<Expr, String> {
        let mut expr = self.comparison()?;
        while self.match_tokens(&[BangEqual, EqualEqual]) {
            let operator = self.previous();
            let rhs = self.comparison()?;
            expr = Binary {
                id: self.get_id(), left: Box::from(expr), 
                operator: operator, right: Box::from(rhs), 
            };
        }
        Ok(expr)
    }
    fn comparison(&mut self) -> Result<Expr, String> {
        let mut expr = self.term()?;
        while self.match_tokens(&[Greater, GreaterEqual, Less, LessEqual]) {
            let operator = self.previous();
            let rhs = self.term()?;
            expr = Binary {
                id: self.get_id(),
                left: Box::from(expr),
                operator: operator,
                right: Box::from(rhs),
            }
        }
        Ok(expr)
    }
    fn term(&mut self) -> Result<Expr, String> {
        let mut expr = self.factor()?;
        while self.match_tokens(&[Minus, Plus]) {
            let operator = self.previous();
            let rhs = self.factor()?;
            expr = Binary {
                id: self.get_id(),
                left: Box::from(expr), 
                operator: operator,
                right: Box::from(rhs),
            };
        }
        Ok(expr)
    }
    fn factor(&mut self) -> Result<Expr, String> {
        let mut expr = self.unary()?;
        while self.match_tokens(&[Slash, Star]) {
            let operator = self.previous();
            let rhs = self.unary()?;
            expr = Binary {
                id: self.get_id(),
                left: Box::from(expr),
                operator: operator, 
                right: Box::from(rhs),
            };
        }
        Ok(expr)
    }
    fn unary(&mut self) -> Result<Expr, String> {
        if self.match_tokens(&[Bang, Minus]) {
            let operator = self.previous();
            let rhs = self.unary()?;
            Ok(Unary { id: self.get_id(), operator: operator, right: Box::from(rhs) })
        } else { self.call() }
    }
    fn call(&mut self) -> Result<Expr, String> {
        let mut expr = self.primary()?;
        loop {
            if self.match_token(LeftParen) { expr = self.finish_call(expr)?; }
            else if self.match_token(Dot) {
                let name = self.consume(Identifier, "Expected token after dot-accessor")?;
                expr = Get { id: self.get_id(), object: Box::new(expr), name };
            }
            else { break; }
        }
        Ok(expr)
    }
    fn finish_call(&mut self, callee: Expr) -> Result<Expr, String> {
        let mut arguments = vec![];
        let mut generics = vec![];

        if self.match_token(Less) {
            loop {
                let generic = self.consume(Identifier, "Expected type parameter.")?;
                generics.push(generic);
                if !self.match_token(Comma) { break; }
            }
            self.consume(Greater, "Expected '>' after type parameters.")?;
        }
        if !self.check(RightParen) {
            loop {
                let arg = self.expression()?;
                arguments.push(arg);

                if arguments.len() >= 255 {
                    let peek = self.tokens[self.current].clone();
                    let location = peek.line_number;
                    return Err(format!("Line {location}: Can't have more than 255 arguments"));
                }
                if !self.match_token(Comma) { break; }
            }
        }
        let paren = self.consume(RightParen, "Expected ')' after arguments.")?;
        Ok(Call { id: self.get_id(), callee: Box::new(callee), paren, arguments, generics })
    }
    fn primary(&mut self) -> Result<Expr, String> {
        let result;
        let token = self.tokens[self.current].clone();
        match token.token_type {
            LeftParen => {
                self.advance();
                let expr = self.expression()?;
                self.consume(RightParen, "Expected ')'")?;
                result = Grouping { id: self.get_id(), expression: Box::from(expr) };
            },
            False | True | Nil | Number | StringLit => {
                self.advance();
                result = Literal { id: self.get_id(), value: LiteralValue::from_token(token) }
            },
            Identifier => {
                self.advance();
                if self.match_token(Less) {
                    let mut generics = Vec::new();
                    loop {
                        generics.push(self.consume(Identifier, "Expected type parameter.")?);
                        if !self.match_token(Comma) { break; }
                    }
                    self.consume(Greater, "Expected '>' after type parameters.")?;
                    if self.match_token(LeftParen) {
                        // It's a function call with generics
                        let paren = self.previous(); // Capture the '(' token
                        let mut arguments = vec![];
                        if !self.check(RightParen) {
                            loop {
                                let arg = self.expression()?;
                                arguments.push(arg);
                                if !self.match_token(Comma) { break; }
                            }
                        }
                        self.consume(RightParen, "Expected ')' after arguments.")?;
                        result = Expr::Call {
                            id: self.get_id(),
                            callee: Box::new(Expr::Variable {
                                id: self.get_id(),
                                var_type: None, name: token 
                            }),
                            paren, arguments,
                            generics
                        };
                    } else {
                        // It's a generic class instantiation
                        self.consume(LeftParen, "Expected '(' after type parameters")?;
                        let paren = self.previous(); // Capture the '(' token
                        let mut arguments = vec![];
                        if !self.check(RightParen) {
                            loop {
                                let arg = self.expression()?;
                                arguments.push(arg);
                                if !self.match_token(Comma) { break; }
                            }
                        }
                        self.consume(RightParen, "Expected ')' after arguments.")?;
                        result = Expr::Call {
                            id: self.get_id(),
                            callee: Box::new(Expr::Variable {
                                id: self.get_id(),
                                var_type: None, name: token
                            }),
                            paren,
                            arguments,
                            generics
                        };
                    }
                } else {
                    result = Expr::Variable {
                        id: self.get_id(), var_type: None,
                        name: self.previous(),
                    };
                }
            },
            Fun => {
                self.advance();
                result = self.function_expression()?;
            },
            TokenType::This => {
                self.advance();
                result = Expr::This { id: self.get_id(), keyword: token };
            },
            TokenType::Super => {
                // Should always occur with a method call
                self.advance(); self.consume(TokenType::Dot, "Expected '.' after 'super'.")?;
                let method = self.consume(TokenType::Identifier, "Expected superclass method name")?;
                result = Expr::Super { id: self.get_id(), keyword: token, method };
            }
            _ => return Err("Expected expression".to_string()),
        }
        Ok(result)
    }
    fn consume(&mut self, token_type: TokenType, msg: &str) -> Result<Token, String> {
        let token = self.tokens[self.current].clone();
        if token.token_type == token_type {
            self.advance();
            let token = self.previous();
            Ok(token)
        } else { Err(format!("Line {}: {}", token.line_number, msg)) }
    }
    fn check(&mut self, typ: TokenType) -> bool {
        let token = self.tokens[self.current].clone();
        token.token_type == typ
    }
    fn synchronize(&mut self) {
        self.advance();
        while !self.is_at_end() {
            if self.previous().token_type == Semicolon { return; }
            let peek = self.tokens[self.current].clone();
            match peek.token_type {
                Class | Fun | Var | For | If | While | Print | Return => return,
                _ => (),
            }
            self.advance();
        }
    }
    fn match_token(&mut self, typ: TokenType) -> bool {
        let peek = self.tokens[self.current].clone();
        if self.is_at_end() { false
        } else {
            if peek.token_type == typ {
                self.advance(); true
            } else { false }
        }
    }
    fn match_tokens(&mut self, typs: &[TokenType]) -> bool {
        for typ in typs {
            if self.match_token(*typ) {
                return true;
            }
        }
        false
    }
}