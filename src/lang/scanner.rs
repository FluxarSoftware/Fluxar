use core::str;
use std::{collections::HashMap, string::String};
fn get_keywords_hashmap() -> HashMap<&'static str, TokenType> { 
    HashMap::from([
        ("and", And), ("class", Class),
        ("else", Else), ("false", False),
        ("for", For), ("fun", Fun),
        ("if", If), ("nil", Nil),
        ("or", Or), ("print", Print),
        ("return", Return), ("super", Super),
        ("this", This), ("true", True),
        ("var", Var), ("while", While),
    ])
}
pub struct Scanner {
    source: String,
    pub tokens: Vec<Token>,
    start: usize,
    current: usize,
    line: usize,
    keywords: HashMap<&'static str, TokenType>,
}
impl Scanner {
    pub fn new(source: &str) -> Self {
        Self {
            source: source.to_string(),
            tokens: vec![], line: 1,
            start: 0, current: 0,
            keywords: get_keywords_hashmap()
        }
    }
    pub fn scan_tokens(self: &mut Self) -> Result<Vec<Token>, String> {
        let mut errors = vec![];
        while !self.is_at_end() {
            self.start = self.current;
            match self.scan_token() {
                Ok(_) => (),
                Err(msg) => errors.push(msg),
            }
        }
        self.tokens.push(Token { 
            token_type: Eof, 
            lexeme: "".to_string(),
            literal: None,
            line_number: self.line,
        });
        if errors.len() > 0 {
            let mut joined = "".to_string();
            // let _ = errors.iter().map(|msg| {
            //     joined.push_str(&msg);
            //     joined.push_str("\n");
            // });
            for error in errors {
                joined.push_str(&error);
                joined.push_str("\n");
            };
            return Err(joined);
        }
        Ok(self.tokens.clone())
    }
    fn is_digit(self: &Self, ch: char) -> bool {
        let uch: u8 = ch as u8;
        uch >= '0' as u8 && uch <= '9' as u8
    }
    fn is_alpha(self: &Self, ch: char) -> bool {
        let uch: u8 = ch as u8;
        (uch >= 'a' as u8 && uch <= 'z' as u8) 
        || (uch >= 'A' as u8 && uch <= 'Z' as u8)
        || (ch == '_')
    }
    fn is_alpha_numeric(self: &Self, ch: char) -> bool {
        self.is_alpha(ch) || self.is_digit(ch)
    }
    fn is_at_end(self: &Self) -> bool {
        self.current >= self.source.len()
    }
    fn scan_token(self: &mut Self) -> Result<(), String> {
        let c = self.advance();
        match c {
            '(' => self.add_token(LeftParen),
            ')' => self.add_token(RightParen),
            '{' => self.add_token(LeftBrace),
            '}' => self.add_token(RightBrace),
            ',' => self.add_token(Comma),
            '.' => self.add_token(Dot),
            '-' => self.add_token(Minus),
            '+' => self.add_token(Plus),
            ':' => self.add_token(Colon),
            ';' => self.add_token(Semicolon),
            '*' => self.add_token(Star),
            '!' => {
                let token = if self.char_match('=') { BangEqual } else { Bang };
                self.add_token(token);
            },
            '=' => {
                let token = if self.char_match('=') { EqualEqual } else { Equal };
                self.add_token(token);
            },
            '<' => {
                let token = if self.char_match('=') { LessEqual }
                else if self.char_match('-') { Gets } else { Less };
                self.add_token(token);
            },
            '>' => {
                let token = if self.char_match('=') { GreaterEqual } 
                else if self.char_match('-') { Arrow } else { Greater };
                self.add_token(token);
            },
            '/' => {
                if self.char_match('/') {
                    loop {
                        if self.peek() == '\n' || self.is_at_end() { break; }
                        self.advance();
                    }
                } else {
                    self.add_token(Slash);
                }
            },
            '|' => {
                if self.char_match('>') { self.add_token(Pipe); }
                else { return Err(format!("Expected '>' at line {}", self.line)); }
            }
            ' ' | '\r' | '\t' => {},
            '\n' => self.line += 1,
            '"' => self.string()?,

            c => {
                if self.is_digit(c) {
                    self.number()?;
                } else if self.is_alpha(c) {
                    self.identifier();
                } else {
                    return Err(format!("Unrecognized char at line {}: {}", self.line, c));
                }
            },
        }
        Ok(())
    }
    fn add_token(self: &mut Self, token_type: TokenType) {
        self.add_token_lit(token_type, None);
    }
    fn add_token_lit(self: &mut Self, token_type: TokenType, literal: Option<LiteralValue>) {
        let text = self.source[self.start..self.current].to_string();
        self.tokens.push(Token {
            token_type: token_type,
            lexeme: text,
            literal: literal,
            line_number: self.line
        });
    }
    fn string(self: &mut Self) -> Result<(), String> {
        while self.peek() != '"' && !self.is_at_end() {
            if self.peek() == '\n' { self.line += 1; }
            self.advance();
        }
        if self.is_at_end() {
            return Err("Unterminated string!".to_string());
        }
        self.advance();
        let value = &self.source[self.start + 1..self.current - 1];
        self.add_token_lit(StringLit, 
            Some(StringValue(value.to_string())));
        Ok(())
    }
    fn number(self: &mut Self) -> Result<(), String> {
        while self.is_digit(self.peek()) { self.advance(); }
        if self.peek() == '.' && self.is_digit(self.peek_next()) {
            self.advance();
            while self.is_digit(self.peek()) {
                self.advance();
            }
        }
        let substring = &self.source[self.start..self.current];
        let value = substring.parse::<f64>();
        match value {
            Ok(value) => self.add_token_lit(Number, Some(FValue(value))),
            Err(_) => return Err(format!("Could not parse number: {}", substring)),
        }
        Ok(())
    }
    fn identifier(self: &mut Self) {
        while self.is_alpha_numeric(self.peek()) {
            self.advance();
        }
        let substring = &self.source[self.start..self.current];
        if let Some(&t_type) = self.keywords.get(substring) {
            self.add_token(t_type);
        } else {
            self.add_token(Identifier);
        }
    }
    fn peek(self: &Self) -> char {
        if self.is_at_end() { return '\0'; }
        self.source.chars().nth(self.current).unwrap()
    }
    fn peek_next(self: &Self) -> char {
        if self.current + 1 >= self.source.len() { return '\0'; }
        self.source.chars().nth(self.current + 1).unwrap()
    }
    fn char_match(self: &mut Self, ch: char) -> bool {
        if self.is_at_end() { return false; }
        if self.source.chars().nth(self.current).unwrap() != ch { 
            return false;
        } else {
            self.current += 1;
            return true;
        }
    }
    fn advance(self: &mut Self) -> char {
        let c = self.source.chars().nth(self.current).unwrap();
        self.current += 1;
        c
    }
}
#[derive(Debug, Copy, Clone, PartialEq)]
pub enum TokenType {
    // Single-char tokens
    LeftParen, RightParen, LeftBrace, RightBrace,
    Comma, Dot, Minus, Plus, Colon, Semicolon, Slash, Star,

    // One or two chars
    Bang, BangEqual,
    Equal, EqualEqual,
    Greater, GreaterEqual,
    Less, LessEqual, 
    Pipe, Gets, Arrow,

    // Literals
    Identifier, StringLit, Number,

    // Keywords
    And, Class, Else, False, Fun, For, If, Nil, Or,
    Print, Return, Super, This, True, Var, While,

    Eof
}
use TokenType::*;
impl std::fmt::Display for TokenType {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}
#[derive(Debug, Clone)]
pub enum LiteralValue {
    FValue(f64),
    StringValue(String)
}
use LiteralValue::*;
#[derive(Debug, Clone)]
pub struct Token {
    pub token_type: TokenType,
    pub lexeme: String,
    pub literal: Option<LiteralValue>,
    pub line_number: usize
}
impl Token {
    pub fn to_string(self: &Self) -> String {
        format!("{} {} {:?}", self.token_type, self.lexeme, self.literal)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn handle_one_char_tokens() {
        let source = "(( ))";
        let mut scanner = Scanner::new(source);
        let _ = scanner.scan_tokens();

        assert_eq!(scanner.tokens.len(), 5);
        assert_eq!(scanner.tokens[0].token_type, LeftParen);
    }
}